"""
Service layer tests for FinGuard AI
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from app.services.scoring_orchestrator import ScoringOrchestrator
from app.services.ml_client import MLClient
from app.services.explain_client import ExplainClient
from app.services.alerting import AlertingService
from app.services.ingestion import FeatureExtractor


class TestScoringOrchestrator:
    """Test scoring orchestrator service"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked dependencies"""
        mock_db = AsyncMock()
        mock_ml = AsyncMock()
        return ScoringOrchestrator(mock_db, mock_ml)
    
    @pytest.mark.asyncio
    async def test_process_transaction_success(self, orchestrator):
        """Test successful transaction processing"""
        # Mock dependencies
        orchestrator.feature_extractor.extract_features = AsyncMock(return_value={
            "amount": 150.0,
            "user_avg_amount": 50.0,
            "merchant_risk_score": 0.3
        })
        
        orchestrator.ml_client.predict = AsyncMock(return_value={
            "anomaly_score": 0.8,
            "graph_risk_score": 0.6,
            "model_confidence": 0.9
        })
        
        orchestrator.explain_client.generate_explanation = AsyncMock(return_value={
            "summary": "Test explanation",
            "reasons": [],
            "suggested_actions": []
        })
        
        # Test data
        transaction_data = {
            "transaction_id": "test_123",
            "amount": 150.0,
            "merchant_id": "test_merchant"
        }
        
        # Process transaction
        result = await orchestrator.process_transaction(transaction_data, "user_123")
        
        # Assertions
        assert "risk_score" in result
        assert "risk_level" in result
        assert "is_fraudulent" in result
        assert "explanation" in result
        assert result["transaction_id"] == "test_123"
    
    @pytest.mark.asyncio
    async def test_process_transaction_ml_failure(self, orchestrator):
        """Test transaction processing when ML fails"""
        orchestrator.feature_extractor.extract_features = AsyncMock(return_value={})
        orchestrator.ml_client.predict = AsyncMock(return_value={"error": "ML failed"})
        
        result = await orchestrator.process_transaction({}, "user_123")
        
        assert result["risk_score"] == 0.0
        assert result["risk_level"] == "low"
        assert "error" in result.get("ml_results", {})
    
    def test_calculate_combined_risk_score(self, orchestrator):
        """Test risk score calculation"""
        ml_results = {
            "anomaly_score": 0.8,
            "graph_risk_score": 0.6,
            "model_confidence": 0.9
        }
        
        risk_score = orchestrator._calculate_combined_risk_score(ml_results)
        
        assert isinstance(risk_score, float)
        assert 0 <= risk_score <= 100
    
    def test_determine_risk_level(self, orchestrator):
        """Test risk level determination"""
        assert orchestrator._determine_risk_level(10) == "low"
        assert orchestrator._determine_risk_level(40) == "medium"
        assert orchestrator._determine_risk_level(80) == "high"
        assert orchestrator._determine_risk_level(95) == "critical"


class TestMLClient:
    """Test ML client service"""
    
    @pytest.fixture
    def ml_client(self):
        return MLClient()
    
    @pytest.mark.asyncio
    async def test_predict_success(self, ml_client):
        """Test successful prediction"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "anomaly_score": 0.7,
                "graph_risk_score": 0.5
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await ml_client.predict(
                features={"amount": 100},
                transaction_data={"transaction_id": "test"}
            )
            
            assert "anomaly_score" in result
            assert result["anomaly_score"] == 0.7
    
    @pytest.mark.asyncio
    async def test_predict_failure(self, ml_client):
        """Test prediction failure"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await ml_client.predict({}, {})
            
            assert result["risk_level"] == "low"
            assert "error" in result


class TestExplainClient:
    """Test explanation client service"""
    
    @pytest.fixture
    def explain_client(self):
        return ExplainClient()
    
    @pytest.mark.asyncio
    async def test_generate_explanation_success(self, explain_client):
        """Test successful explanation generation"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "summary": "Test explanation",
                "reasons": []
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await explain_client.generate_explanation(
                transaction_data={"risk_score": 80}
            )
            
            assert "summary" in result
            assert result["summary"] == "Test explanation"
    
    @pytest.mark.asyncio
    async def test_get_fraud_patterns(self, explain_client):
        """Test fraud pattern retrieval"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"id": "pattern1", "description": "Test pattern"}
            ]
            mock_get.return_value.__aenter__.return_value = mock_response
            
            patterns = await explain_client.get_fraud_patterns("behavioral")
            
            assert isinstance(patterns, list)
            assert len(patterns) == 1


class TestAlertingService:
    """Test alerting service"""
    
    @pytest.fixture
    def alerting_service(self):
        return AlertingService()
    
    @pytest.mark.asyncio
    async def test_send_fraud_alert_no_channels(self, alerting_service):
        """Test alert sending with no channels configured"""
        # Clear channel configurations
        alerting_service.telegram_bot_token = None
        alerting_service.smtp_config["username"] = None
        
        success = await alerting_service.send_fraud_alert(
            "test_txn", 85.0, "high"
        )
        
        assert not success  # Should fail with no channels
    
    @patch("app.services.alerting.AlertingService._send_telegram_alert")
    @pytest.mark.asyncio
    async def test_send_fraud_alert_telegram(self, mock_telegram, alerting_service):
        """Test alert sending via Telegram"""
        mock_telegram.return_value = True
        
        alerting_service.telegram_bot_token = "test_token"
        alerting_service.telegram_chat_id = "test_chat"
        
        success = await alerting_service.send_fraud_alert(
            "test_txn", 85.0, "high"
        )
        
        assert success
        mock_telegram.assert_called_once()


class TestFeatureExtractor:
    """Test feature extraction service"""
    
    @pytest.fixture
    def feature_extractor(self):
        mock_db = AsyncMock()
        return FeatureExtractor(mock_db)
    
    @pytest.mark.asyncio
    async def test_extract_features_basic(self, feature_extractor):
        """Test basic feature extraction"""
        transaction_data = {
            "amount": 150.0,
            "currency": "USD",
            "transaction_type": "purchase"
        }
        
        features = await feature_extractor.extract_features(transaction_data, "user_123")
        
        assert "amount" in features
        assert "currency" in features
        assert "transaction_type" in features
        assert features["amount"] == 150.0
    
    def test_extract_temporal_features(self, feature_extractor):
        """Test temporal feature extraction"""
        features = feature_extractor._extract_temporal_features({})
        
        assert "hour_of_day" in features
        assert "day_of_week" in features
        assert "is_weekend" in features
        assert features["hour_of_day"] == datetime.now().hour


if __name__ == "__main__":
    pytest.main([__file__, "-v"])