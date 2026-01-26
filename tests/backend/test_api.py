"""
API endpoint tests for FinGuard AI Backend
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json
from datetime import datetime, timedelta

from main import app
from app.core.config import settings


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_transaction_data():
    """Mock transaction data for testing"""
    return {
        "transaction_id": "test_txn_123",
        "amount": 150.0,
        "currency": "USD",
        "merchant_id": "test_merchant_456",
        "device_id": "test_device_789",
        "location_lat": 40.7128,
        "location_lng": -74.0060,
        "location_country": "US",
        "location_city": "New York",
        "transaction_type": "purchase",
        "category": "electronics"
    }


@pytest.fixture
def mock_ml_response():
    """Mock ML service response"""
    return {
        "anomaly_score": 0.85,
        "graph_risk_score": 0.72,
        "combined_risk_score": 78.5,
        "risk_level": "high",
        "features_used": ["amount", "user_avg_amount", "merchant_risk_score"],
        "model_confidence": 0.88,
        "fraud_type_prediction": "card_not_present"
    }


@pytest.fixture
def mock_explanation_response():
    """Mock explanation service response"""
    return {
        "summary": "Transaction shows high risk due to unusual amount and new device.",
        "reasons": [
            {
                "reason": "Amount is 300% higher than user average",
                "severity": "high",
                "impact_score": 0.7
            }
        ],
        "suggested_actions": [
            {
                "action": "Require additional verification",
                "priority": "high",
                "description": "Request OTP or biometric authentication"
            }
        ],
        "confidence": 0.85,
        "model_used": "llama3",
        "prompt_tokens": 150,
        "completion_tokens": 200,
        "total_tokens": 350
    }


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_detailed_health_check(self, client):
        """Test detailed health check"""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        assert "database" in data["components"]


class TestTransactionEndpoints:
    """Test transaction-related endpoints"""
    
    @patch("app.services.ml_client.MLClient.predict")
    @patch("app.services.explain_client.ExplainClient.generate_explanation")
    def test_analyze_transaction_success(self, mock_explain, mock_ml, client, mock_transaction_data, 
                                        mock_ml_response, mock_explanation_response):
        """Test successful transaction analysis"""
        # Mock responses
        mock_ml.return_value = mock_ml_response
        mock_explain.return_value = mock_explanation_response
        
        # Mock authentication
        with patch("app.core.dependencies.get_current_active_user") as mock_user:
            mock_user.return_value = type('User', (), {'id': 'test_user_123', 'username': 'test_user', 'is_active': True})()
            
            response = client.post(
                "/api/v1/transactions/analyze",
                json=mock_transaction_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "risk_score" in data
            assert "risk_level" in data
            assert "explanation" in data
            assert data["risk_level"] == "high"
    
    def test_analyze_transaction_invalid_data(self, client):
        """Test transaction analysis with invalid data"""
        invalid_data = {
            "amount": -100,  # Invalid negative amount
            "merchant_id": "test"
        }
        
        with patch("app.core.dependencies.get_current_active_user") as mock_user:
            mock_user.return_value = type('User', (), {'id': 'test_user_123', 'is_active': True})()
            
            response = client.post(
                "/api/v1/transactions/analyze",
                json=invalid_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 422  # Validation error
    
    @patch("app.services.ml_client.MLClient.predict")
    def test_analyze_transaction_ml_failure(self, mock_ml, client, mock_transaction_data):
        """Test transaction analysis when ML service fails"""
        # Mock ML service failure
        mock_ml.return_value = {"error": "ML service unavailable"}
        
        with patch("app.core.dependencies.get_current_active_user") as mock_user:
            mock_user.return_value = type('User', (), {'id': 'test_user_123', 'is_active': True})()
            
            response = client.post(
                "/api/v1/transactions/analyze",
                json=mock_transaction_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Should still succeed with default values
            assert response.status_code == 200
            data = response.json()
            assert data["risk_score"] == 0.0
            assert data["risk_level"] == "low"


class TestExplanationEndpoints:
    """Test explanation-related endpoints"""
    
    @patch("app.services.explain_client.ExplainClient.generate_explanation")
    def test_explain_transaction(self, mock_explain, client, mock_explanation_response):
        """Test transaction explanation endpoint"""
        mock_explain.return_value = mock_explanation_response
        
        with patch("app.core.dependencies.get_current_active_user") as mock_user:
            mock_user.return_value = type('User', (), {'id': 'test_user_123', 'is_active': True})()
            
            request_data = {
                "transaction_id": "test_txn_123",
                "query": "Why is this transaction high risk?"
            }
            
            response = client.post(
                "/api/v1/explain/transaction",
                json=request_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "reasons" in data
            assert "suggested_actions" in data
    
    @patch("app.services.explain_client.ExplainClient.query_fraud_knowledge")
    def test_query_fraud_knowledge(self, mock_query, client):
        """Test fraud knowledge query endpoint"""
        mock_query.return_value = {
            "answer": "Card-not-present fraud involves...",
            "sources": ["fraud_pattern_123"],
            "confidence": 0.92
        }
        
        with patch("app.core.dependencies.get_current_active_user") as mock_user:
            mock_user.return_value = type('User', (), {'id': 'test_user_123', 'is_active': True})()
            
            response = client.post(
                "/api/v1/explain/query?question=What is card-not-present fraud?",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data


class TestAuthentication:
    """Test authentication and authorization"""
    
    def test_unauthenticated_access(self, client):
        """Test access without authentication"""
        response = client.post("/api/v1/transactions/analyze", json={})
        assert response.status_code == 401  # Unauthorized
    
    def test_invalid_token(self, client):
        """Test access with invalid token"""
        response = client.post(
            "/api/v1/transactions/analyze",
            json={},
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestRateLimiting:
    """Test rate limiting (if implemented)"""
    
    def test_rate_limiting(self, client):
        """Test rate limiting on API endpoints"""
        # Note: Rate limiting would need to be implemented in middleware
        # This is a placeholder test
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])