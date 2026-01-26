"""
Orchestrator service that coordinates between ML models and explanation service
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

from app.core.config import settings
from app.services.ml_client import MLClient
from app.services.explain_client import ExplainClient
from app.services.ingestion import FeatureExtractor


class ScoringOrchestrator:
    """Orchestrates the complete fraud detection pipeline"""
    
    def __init__(self, db_session, ml_client: Optional[MLClient] = None):
        self.db = db_session
        self.ml_client = ml_client or MLClient()
        self.explain_client = ExplainClient()
        self.feature_extractor = FeatureExtractor(db_session)
        
    async def process_transaction(self, transaction_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Process a transaction through the complete fraud detection pipeline
        
        Steps:
        1. Extract features
        2. Call ML models for scoring
        3. Combine scores
        4. Generate explanation (if needed)
        5. Return complete analysis
        """
        try:
            logger.info(f"Processing transaction for user {user_id}")
            
            # Step 1: Extract features
            features = await self.feature_extractor.extract_features(
                transaction_data, user_id
            )
            
            # Add transaction ID if not present
            if "transaction_id" not in transaction_data:
                transaction_data["transaction_id"] = f"txn_{uuid.uuid4().hex[:16]}"
            
            # Step 2: Get ML predictions
            ml_results = await self.ml_client.predict(
                features=features,
                transaction_data=transaction_data
            )
            
            # Step 3: Calculate combined risk score
            risk_score = self._calculate_combined_risk_score(ml_results)
            risk_level = self._determine_risk_level(risk_score)
            is_fraudulent = risk_level in ["high", "critical"]
            
            # Step 4: Generate explanation for medium/high/critical risk
            explanation = None
            if risk_level in ["medium", "high", "critical"]:
                try:
                    explanation_data = {
                        **transaction_data,
                        "features": features,
                        "ml_results": ml_results,
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "is_fraudulent": is_fraudulent
                    }
                    
                    explanation = await self.explain_client.generate_explanation(
                        transaction_data=explanation_data
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate explanation: {e}")
                    # Create a basic explanation
                    explanation = self._create_basic_explanation(
                        risk_score, risk_level, ml_results
                    )
            
            # Step 5: Prepare response
            response = {
                "transaction_id": transaction_data["transaction_id"],
                "risk_score": risk_score,
                "risk_level": risk_level,
                "is_fraudulent": is_fraudulent,
                "fraud_type": ml_results.get("fraud_type_prediction"),
                "confidence_score": ml_results.get("model_confidence", 0.5),
                "anomaly_score": ml_results.get("anomaly_score", 0.0),
                "graph_risk_score": ml_results.get("graph_risk_score", 0.0),
                "features": features,
                "ml_results": ml_results,
                "explanation": explanation,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Transaction processed: risk_score={risk_score}, level={risk_level}")
            return response
            
        except Exception as e:
            logger.error(f"Error in transaction processing: {e}")
            # Return a safe default response
            return self._create_error_response(transaction_data, str(e))
    
    async def process_batch_transactions(self, transactions: list, user_id: str) -> Dict[str, Any]:
        """Process multiple transactions in batch"""
        logger.info(f"Processing batch of {len(transactions)} transactions")
        
        results = []
        for transaction in transactions:
            try:
                result = await self.process_transaction(transaction, user_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process transaction in batch: {e}")
                results.append({
                    "transaction_id": transaction.get("transaction_id", "unknown"),
                    "error": str(e),
                    "risk_score": 0.0,
                    "risk_level": "low",
                    "is_fraudulent": False
                })
        
        # Calculate batch statistics
        stats = self._calculate_batch_stats(results)
        
        return {
            "batch_id": f"batch_{uuid.uuid4().hex[:8]}",
            "total_transactions": len(transactions),
            "processed_transactions": len(results),
            "results": results,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_combined_risk_score(self, ml_results: Dict[str, Any]) -> float:
        """Calculate combined risk score from ML model outputs"""
        try:
            # Weights for different model scores
            weights = {
                "anomaly_score": 0.4,
                "graph_risk_score": 0.4,
                "model_confidence": 0.2
            }
            
            anomaly_score = ml_results.get("anomaly_score", 0.0)
            graph_score = ml_results.get("graph_risk_score", 0.0)
            confidence = ml_results.get("model_confidence", 0.5)
            
            # Invert confidence (lower confidence = higher risk)
            confidence_risk = 1.0 - confidence
            
            # Weighted sum
            weighted_sum = (
                anomaly_score * weights["anomaly_score"] +
                graph_score * weights["graph_risk_score"] +
                confidence_risk * weights["model_confidence"]
            )
            
            # Scale to 0-100
            risk_score = weighted_sum * 100
            
            # Apply sigmoid-like transformation for better distribution
            import math
            risk_score = 100 / (1 + math.exp(-0.1 * (risk_score - 50)))
            
            return round(risk_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.0
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score >= settings.RISK_SCORE_HIGH:
            return "critical" if risk_score > 90 else "high"
        elif risk_score >= settings.RISK_SCORE_MEDIUM:
            return "medium"
        elif risk_score >= settings.RISK_SCORE_LOW:
            return "low"
        else:
            return "low"
    
    def _create_basic_explanation(self, risk_score: float, risk_level: str, ml_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic explanation when LLM fails"""
        reasons = []
        
        anomaly_score = ml_results.get("anomaly_score", 0.0)
        if anomaly_score > 0.7:
            reasons.append({
                "reason": "High anomaly detection score indicates unusual behavior",
                "severity": "high",
                "impact_score": 0.7
            })
        
        graph_score = ml_results.get("graph_risk_score", 0.0)
        if graph_score > 0.6:
            reasons.append({
                "reason": "Suspicious connections detected in transaction network",
                "severity": "medium",
                "impact_score": 0.5
            })
        
        return {
            "summary": f"Transaction flagged as {risk_level} risk with score {risk_score:.1f}",
            "reasons": reasons,
            "suggested_actions": [
                {
                    "action": "Review transaction details",
                    "priority": risk_level,
                    "description": "Manually verify transaction authenticity"
                }
            ],
            "confidence": 0.6,
            "model_used": "rule_based"
        }
    
    def _calculate_batch_stats(self, results: list) -> Dict[str, Any]:
        """Calculate statistics for batch processing"""
        if not results:
            return {}
        
        total = len(results)
        fraud_count = sum(1 for r in results if r.get("is_fraudulent", False))
        high_risk_count = sum(1 for r in results if r.get("risk_level") in ["high", "critical"])
        
        risk_scores = [r.get("risk_score", 0) for r in results if isinstance(r.get("risk_score"), (int, float))]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        return {
            "total_transactions": total,
            "fraudulent_detected": fraud_count,
            "high_risk_detected": high_risk_count,
            "average_risk_score": round(avg_risk_score, 2),
            "fraud_rate_percent": round((fraud_count / total) * 100, 2) if total > 0 else 0
        }
    
    def _create_error_response(self, transaction_data: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create error response when processing fails"""
        return {
            "transaction_id": transaction_data.get("transaction_id", "unknown"),
            "risk_score": 0.0,
            "risk_level": "low",
            "is_fraudulent": False,
            "confidence_score": 0.0,
            "anomaly_score": 0.0,
            "graph_risk_score": 0.0,
            "features": {},
            "error": error,
            "timestamp": datetime.now().isoformat()
        }