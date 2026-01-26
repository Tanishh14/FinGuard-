"""
Pydantic schemas for transaction data validation and serialization
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


# Enums
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TransactionType(str, Enum):
    PURCHASE = "purchase"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    REFUND = "refund"
    PAYMENT = "payment"


# Request Schemas
class TransactionCreate(BaseModel):
    """Schema for creating/analyzing a new transaction"""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code (ISO 4217)")
    merchant_id: str = Field(..., description="Merchant identifier")
    device_id: Optional[str] = Field(None, description="Device fingerprint")
    location_lat: Optional[float] = Field(None, description="Latitude")
    location_lng: Optional[float] = Field(None, description="Longitude")
    location_country: Optional[str] = Field(None, description="Country code (ISO 3166-1 alpha-2)")
    location_city: Optional[str] = Field(None, description="City name")
    transaction_type: TransactionType = Field(default=TransactionType.PURCHASE)
    category: Optional[str] = Field(None, description="Transaction category")
    
    # Optional behavioral context
    user_avg_transaction: Optional[float] = Field(None, description="User's average transaction amount")
    time_since_last_transaction: Optional[float] = Field(None, description="Time since last transaction in hours")
    device_trust_score: Optional[float] = Field(None, description="Device trust score (0-1)")
    
    class Config:
        schema_extra = {
            "example": {
                "transaction_id": "txn_123456789",
                "amount": 149.99,
                "currency": "USD",
                "merchant_id": "m_amazon_123",
                "device_id": "dev_abc123xyz",
                "location_lat": 37.7749,
                "location_lng": -122.4194,
                "location_country": "US",
                "location_city": "San Francisco",
                "transaction_type": "purchase",
                "category": "electronics",
                "user_avg_transaction": 89.50,
                "time_since_last_transaction": 2.5,
                "device_trust_score": 0.85
            }
        }


class ExplanationRequest(BaseModel):
    """Schema for requesting transaction explanation"""
    transaction_id: str = Field(..., description="Transaction to explain")
    query: Optional[str] = Field(None, description="Specific question about the transaction")
    regenerate: bool = Field(default=False, description="Force regeneration of explanation")


class TransactionUpdate(BaseModel):
    """Schema for updating transaction status"""
    is_fraudulent: Optional[bool] = Field(None, description="Mark as fraudulent")
    risk_level: Optional[RiskLevel] = Field(None, description="Update risk level")
    fraud_type: Optional[str] = Field(None, description="Type of fraud detected")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")


class TransactionAnalysisRequest(BaseModel):
    """Schema for batch transaction analysis"""
    transactions: List[TransactionCreate]
    batch_id: Optional[str] = Field(None, description="Batch identifier for tracking")
    async_processing: bool = Field(default=True, description="Process asynchronously")


# Response Schemas
class ReasonItem(BaseModel):
    """Individual reason for risk score"""
    reason: str = Field(..., description="Reason description")
    severity: str = Field(..., description="low, medium, high")
    impact_score: float = Field(..., ge=0, le=1, description="Impact on overall score")


class SuggestedAction(BaseModel):
    """Suggested action based on risk assessment"""
    action: str = Field(..., description="Action to take")
    priority: str = Field(..., description="low, medium, high, critical")
    description: Optional[str] = Field(None, description="Action description")


class ExplanationResponse(BaseModel):
    """Schema for explanation response"""
    transaction_id: str = Field(..., description="Transaction identifier")
    summary: str = Field(..., description="Summary explanation")
    reasons: List[ReasonItem] = Field(default_factory=list, description="Detailed reasons")
    suggested_actions: List[SuggestedAction] = Field(default_factory=list, description="Suggested actions")
    confidence: float = Field(..., ge=0, le=1, description="Explanation confidence")
    model_used: Optional[str] = Field(None, description="LLM model used")
    
    class Config:
        schema_extra = {
            "example": {
                "transaction_id": "txn_123456789",
                "summary": "This transaction shows high risk due to unusual spending pattern and new device usage.",
                "reasons": [
                    {
                        "reason": "Transaction amount is 300% higher than user's average",
                        "severity": "high",
                        "impact_score": 0.7
                    },
                    {
                        "reason": "Transaction made from a new device not seen in last 90 days",
                        "severity": "medium",
                        "impact_score": 0.4
                    }
                ],
                "suggested_actions": [
                    {
                        "action": "Require additional authentication",
                        "priority": "high",
                        "description": "Request OTP or biometric verification"
                    }
                ],
                "confidence": 0.85,
                "model_used": "llama3"
            }
        }


class TransactionResponse(BaseModel):
    """Schema for single transaction response"""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(..., description="Currency")
    merchant_id: str = Field(..., description="Merchant identifier")
    device_id: Optional[str] = Field(None, description="Device fingerprint")
    transaction_time: str = Field(..., description="ISO format timestamp")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    risk_level: RiskLevel = Field(..., description="Risk level category")
    is_fraudulent: bool = Field(..., description="Fraudulent flag")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in prediction")
    explanation: Optional[ExplanationResponse] = Field(None, description="AI explanation")
    recommended_action: str = Field(..., description="Recommended action")
    timestamp: str = Field(..., description="Processing timestamp")
    
    class Config:
        from_attributes = True


class TransactionItem(BaseModel):
    """Schema for transaction list item"""
    transaction_id: str
    amount: float
    currency: str
    merchant_id: str
    transaction_time: str
    risk_score: float
    risk_level: RiskLevel
    is_fraudulent: bool


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list response"""
    items: List[TransactionItem]
    total: int = Field(..., description="Total number of transactions")
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total number of pages")
    has_more: bool = Field(..., description="Whether there are more pages")


class FraudAlertResponse(BaseModel):
    """Schema for fraud alert response"""
    alert_id: str
    transaction_id: str
    amount: float
    merchant_id: str
    risk_score: float
    risk_level: RiskLevel
    alert_type: str
    severity: str
    message: str
    created_at: str
    status: str


class TransactionStats(BaseModel):
    """Schema for transaction statistics"""
    total_transactions: int
    today_transactions: int
    fraudulent_transactions: int
    high_risk_transactions: int
    total_amount: float
    fraud_amount: float
    avg_risk_score: float
    risk_score_distribution: Dict[str, int]


class RiskScoreDistribution(BaseModel):
    """Schema for risk score distribution"""
    low: int = Field(0, description="Low risk transactions")
    medium: int = Field(0, description="Medium risk transactions")
    high: int = Field(0, description="High risk transactions")
    critical: int = Field(0, description="Critical risk transactions")


class FraudTrend(BaseModel):
    """Schema for fraud trend data"""
    date: str
    total_transactions: int
    avg_risk_score: float
    fraudulent_transactions: int


class MLModelResponse(BaseModel):
    """Schema for ML model response"""
    anomaly_score: float = Field(..., ge=0, le=1, description="Anomaly detection score")
    graph_risk_score: float = Field(..., ge=0, le=1, description="Graph-based risk score")
    combined_risk_score: float = Field(..., ge=0, le=100, description="Combined risk score")
    risk_level: RiskLevel = Field(..., description="Risk level")
    features_used: List[str] = Field(..., description="Features used for prediction")
    model_confidence: float = Field(..., ge=0, le=1, description="Model confidence")
    fraud_type_prediction: Optional[str] = Field(None, description="Predicted fraud type")


class BatchProcessingResponse(BaseModel):
    """Schema for batch processing response"""
    batch_id: str
    total_transactions: int
    processed_transactions: int
    fraudulent_detected: int
    high_risk_detected: int
    status: str  # pending, processing, completed, failed
    estimated_completion_time: Optional[str] = Field(None, description="ISO format timestamp")
    results_url: Optional[str] = Field(None, description="URL to download results")