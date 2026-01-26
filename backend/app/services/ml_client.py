"""
Client for communicating with the ML service
"""

import json
import asyncio
from typing import Dict, Any, Optional
import httpx
from loguru import logger

from app.core.config import settings


class MLClient:
    """HTTP client for ML service communication"""
    
    def __init__(self):
        self.base_url = settings.ML_SERVICE_URL
        self.timeout = settings.ML_MODEL_TIMEOUT
        
    async def predict(self, features: Dict[str, Any], transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send transaction data to ML service for prediction
        
        Returns:
            Dict containing anomaly_score, graph_risk_score, fraud_type, etc.
        """
        try:
            payload = {
                "features": features,
                "transaction_data": transaction_data,
                "timestamp": transaction_data.get("timestamp")
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/predict",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result
                else:
                    logger.error(f"ML service error: {response.status_code} - {response.text}")
                    return self._get_default_prediction()
                    
        except httpx.TimeoutException:
            logger.error("ML service timeout")
            return self._get_default_prediction()
        except Exception as e:
            logger.error(f"ML service communication failed: {e}")
            return self._get_default_prediction()
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded ML models"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/models")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Failed to get model info: {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}
    
    async def retrain_model(self, training_data: list) -> Dict[str, Any]:
        """Trigger model retraining with new data"""
        try:
            async with httpx.AsyncClient(timeout=300) as client:  # Longer timeout for training
                response = await client.post(
                    f"{self.base_url}/retrain",
                    json={"training_data": training_data},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Retraining failed: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Model retraining failed: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check if ML service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    def _get_default_prediction(self) -> Dict[str, Any]:
        """Return default prediction when ML service fails"""
        return {
            "anomaly_score": 0.0,
            "graph_risk_score": 0.0,
            "combined_risk_score": 0.0,
            "risk_level": "low",
            "features_used": [],
            "model_confidence": 0.5,
            "fraud_type_prediction": None,
            "error": "ML service unavailable, using default prediction"
        }