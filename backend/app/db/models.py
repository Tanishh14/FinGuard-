"""
SQLAlchemy models for FinGuard AI
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, JSON, Text, BigInteger, Index
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class User(Base):
    """User model for authentication and audit trails"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    transactions = relationship("Transaction", back_populates="user")


class Transaction(Base):
    """Transaction model for storing all financial transactions"""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    merchant_id = Column(String(100), index=True, nullable=False)
    device_id = Column(String(100), index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    location_lat = Column(Float)
    location_lng = Column(Float)
    location_country = Column(String(2))
    location_city = Column(String(100))
    
    # Behavioral features
    transaction_type = Column(String(50))  # purchase, withdrawal, transfer, etc.
    category = Column(String(100))  # groceries, electronics, travel, etc.
    time_of_day = Column(Integer)  # hour of day
    day_of_week = Column(Integer)  # 0-6
    is_weekend = Column(Boolean)
    
    # Risk analysis
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20))  # low, medium, high, critical
    is_fraudulent = Column(Boolean, default=False)
    fraud_type = Column(String(100))  # card_not_present, account_takeover, etc.
    confidence_score = Column(Float, default=0.0)
    
    # ML features
    features = Column(JSON)  # Raw features used for ML
    anomaly_score = Column(Float)
    graph_risk_score = Column(Float)
    
    # Timestamps
    transaction_time = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    explanations = relationship("Explanation", back_populates="transaction")
    alerts = relationship("Alert", back_populates="transaction")
    
    __table_args__ = (
        Index('idx_transaction_composite', 'user_id', 'transaction_time'),
        Index('idx_risk_score', 'risk_score'),
        Index('idx_fraudulent', 'is_fraudulent'),
    )


class Explanation(Base):
    """LLM-generated explanations for risk scores"""
    __tablename__ = "explanations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), 
                           nullable=False, index=True)
    
    # Explanation content
    summary = Column(Text, nullable=False)
    reasons = Column(JSON)  # List of reason objects
    suggested_actions = Column(JSON)  # List of action objects
    confidence = Column(Float)
    
    # LLM metadata
    model_used = Column(String(100))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    transaction = relationship("Transaction", back_populates="explanations")


class Alert(Base):
    """Alerts generated for high-risk transactions"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), 
                           nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # fraud, anomaly, behavioral
    severity = Column(String(20), nullable=False)  # info, warning, critical
    message = Column(Text, nullable=False)
    
    # Alert status
    status = Column(String(20), default="pending")  # pending, reviewed, resolved, false_positive
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    # Notification status
    notification_sent = Column(Boolean, default=False)
    notification_method = Column(String(50))  # email, telegram, sms, push
    notification_time = Column(DateTime)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    transaction = relationship("Transaction", back_populates="alerts")


class Merchant(Base):
    """Merchant information and risk profiles"""
    __tablename__ = "merchants"
    
    id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    country = Column(String(2))
    risk_score = Column(Float, default=0.0)
    fraud_count = Column(Integer, default=0)
    total_transactions = Column(Integer, default=0)
    avg_transaction_amount = Column(Float)
    
    # Graph properties
    connected_users = Column(JSON)  # List of user IDs
    suspicious_patterns = Column(JSON)  # Detected patterns
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))


class Device(Base):
    """Device fingerprinting and risk assessment"""
    __tablename__ = "devices"
    
    id = Column(String(100), primary_key=True)
    device_type = Column(String(50))  # mobile, desktop, tablet
    os = Column(String(50))
    browser = Column(String(50))
    screen_resolution = Column(String(20))
    timezone = Column(String(50))
    
    # Risk indicators
    risk_score = Column(Float, default=0.0)
    is_suspicious = Column(Boolean, default=False)
    associated_accounts = Column(Integer, default=1)
    
    # Graph properties
    ip_addresses = Column(JSON)  # List of IPs used
    locations = Column(JSON)  # List of locations
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))


class FraudPattern(Base):
    """Known fraud patterns for RAG system"""
    __tablename__ = "fraud_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_name = Column(String(200), nullable=False)
    pattern_type = Column(String(100))  # behavioral, network, device, merchant
    description = Column(Text, nullable=False)
    indicators = Column(JSON)  # List of indicators
    mitigation_strategies = Column(JSON)  # List of strategies
    
    # Statistics
    detection_count = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)
    accuracy = Column(Float)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))


class SystemMetrics(Base):
    """System performance and monitoring metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Performance metrics
    request_count = Column(Integer, default=0)
    avg_response_time = Column(Float)
    error_count = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    
    # Fraud detection metrics
    transactions_processed = Column(Integer, default=0)
    fraud_detected = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    detection_accuracy = Column(Float)
    
    # System health
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    ml_model_latency = Column(Float)
    
    metadata = Column(JSON)