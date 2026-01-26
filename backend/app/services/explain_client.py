"""
Client for communicating with the explanation service (LLM + RAG)
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
import httpx
from loguru import logger

from app.core.config import settings


class ExplainClient:
    """HTTP client for explanation service communication"""
    
    def __init__(self):
        self.base_url = settings.EXPLAIN_SERVICE_URL
        self.timeout = 30  # Longer timeout for LLM processing
        
    async def generate_explanation(self, transaction_data: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate AI explanation for transaction risk
        
        Args:
            transaction_data: Complete transaction data with ML results
            query: Optional specific question about the transaction
            
        Returns:
            Dict containing summary, reasons, suggested_actions, etc.
        """
        try:
            payload = {
                "transaction": transaction_data,
                "query": query,
                "llm_model": settings.LLM_MODEL_NAME
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/explain",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result
                else:
                    logger.error(f"Explanation service error: {response.status_code} - {response.text}")
                    return self._get_default_explanation(transaction_data)
                    
        except httpx.TimeoutException:
            logger.error("Explanation service timeout")
            return self._get_default_explanation(transaction_data)
        except Exception as e:
            logger.error(f"Explanation service communication failed: {e}")
            return self._get_default_explanation(transaction_data)
    
    async def get_fraud_patterns(self, pattern_type: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """Get known fraud patterns from RAG system"""
        try:
            params = {
                "type": pattern_type,
                "limit": limit
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/patterns",
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to get fraud patterns: {e}")
            return []
    
    async def query_fraud_knowledge(self, question: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Query fraud knowledge base using RAG"""
        try:
            payload = {
                "question": question,
                "user_id": user_id
            }
            
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.base_url}/query",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"answer": "Unable to retrieve answer at this time.", "sources": []}
                    
        except Exception as e:
            logger.error(f"Failed to query knowledge base: {e}")
            return {"answer": "Service temporarily unavailable.", "sources": []}
    
    async def health_check(self) -> bool:
        """Check if explanation service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    def _get_default_explanation(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return default explanation when service fails"""
        risk_score = transaction_data.get("risk_score", 0)
        risk_level = transaction_data.get("risk_level", "low")
        
        return {
            "summary": f"Transaction analyzed with risk score {risk_score:.1f} ({risk_level} risk).",
            "reasons": [
                {
                    "reason": "Automated analysis completed",
                    "severity": "low",
                    "impact_score": 0.3
                }
            ],
            "suggested_actions": [
                {
                    "action": "Monitor transaction",
                    "priority": "low",
                    "description": "Keep transaction under observation"
                }
            ],
            "confidence": 0.5,
            "model_used": "default",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }