"""
Data ingestion and feature extraction service
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sqlalchemy import func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.models import Transaction, Merchant, Device, FraudPattern


class FeatureExtractor:
    """Extract features from transaction data for ML models"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def extract_features(self, transaction_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Extract comprehensive features for ML models
        
        Features include:
        1. Basic transaction features
        2. Behavioral features (user history)
        3. Merchant features
        4. Device features
        5. Temporal features
        6. Graph-based features (simulated)
        """
        try:
            features = {}
            
            # 1. Basic transaction features
            features.update(self._extract_basic_features(transaction_data))
            
            # 2. Behavioral features (async)
            behavioral_features = await self._extract_behavioral_features(user_id, transaction_data)
            features.update(behavioral_features)
            
            # 3. Merchant features (async)
            merchant_features = await self._extract_merchant_features(transaction_data.get("merchant_id"))
            features.update(merchant_features)
            
            # 4. Device features (async)
            device_features = await self._extract_device_features(transaction_data.get("device_id"))
            features.update(device_features)
            
            # 5. Temporal features
            features.update(self._extract_temporal_features(transaction_data))
            
            # 6. Graph features (simulated - in production this would come from GNN)
            graph_features = await self._extract_graph_features(user_id, transaction_data)
            features.update(graph_features)
            
            # 7. Derived features
            features.update(self._create_derived_features(features))
            
            logger.debug(f"Extracted {len(features)} features for transaction")
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            # Return minimal feature set
            return self._extract_basic_features(transaction_data)
    
    def _extract_basic_features(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic transaction features"""
        features = {
            "amount": float(transaction_data.get("amount", 0)),
            "amount_log": np.log1p(float(transaction_data.get("amount", 0))),
            "currency": self._encode_currency(transaction_data.get("currency", "USD")),
            "transaction_type": self._encode_transaction_type(transaction_data.get("transaction_type", "purchase")),
            "category": self._encode_category(transaction_data.get("category", "other")),
        }
        
        # Location features if available
        if transaction_data.get("location_lat") and transaction_data.get("location_lng"):
            features["has_location"] = 1
            features["latitude"] = float(transaction_data["location_lat"])
            features["longitude"] = float(transaction_data["location_lng"])
        else:
            features["has_location"] = 0
            features["latitude"] = 0.0
            features["longitude"] = 0.0
        
        return features
    
    async def _extract_behavioral_features(self, user_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user behavioral features from historical data"""
        features = {}
        
        try:
            from sqlalchemy import select
            
            # Get user's transaction history
            query = select(Transaction).where(
                Transaction.user_id == user_id
            ).order_by(desc(Transaction.transaction_time)).limit(100)
            
            result = await self.db.execute(query)
            user_transactions = result.scalars().all()
            
            if not user_transactions:
                # New user features
                features.update({
                    "user_transaction_count": 0,
                    "user_avg_amount": 0.0,
                    "user_amount_std": 0.0,
                    "user_frequency_days": 0.0,
                    "is_new_user": 1,
                    "time_since_first_transaction": 0.0,
                })
                return features
            
            # Calculate statistics
            amounts = [t.amount for t in user_transactions]
            transaction_times = [t.transaction_time for t in user_transactions]
            
            # Time-based features
            if len(transaction_times) > 1:
                time_diffs = [(transaction_times[i] - transaction_times[i+1]).total_seconds() / 3600 
                             for i in range(len(transaction_times)-1)]
                avg_frequency = np.mean(time_diffs) if time_diffs else 0
            else:
                avg_frequency = 0
            
            # Amount statistics
            avg_amount = np.mean(amounts)
            amount_std = np.std(amounts) if len(amounts) > 1 else 0
            
            # Current transaction comparison
            current_amount = float(transaction_data.get("amount", 0))
            amount_ratio = current_amount / avg_amount if avg_amount > 0 else 1.0
            
            # Time since last transaction
            last_transaction_time = transaction_times[0]
            current_time = datetime.now()
            hours_since_last = (current_time - last_transaction_time).total_seconds() / 3600
            
            features.update({
                "user_transaction_count": len(user_transactions),
                "user_avg_amount": float(avg_amount),
                "user_amount_std": float(amount_std),
                "user_frequency_days": float(avg_frequency / 24),
                "amount_ratio": float(amount_ratio),
                "amount_deviation": float((current_amount - avg_amount) / amount_std) if amount_std > 0 else 0.0,
                "hours_since_last_transaction": float(hours_since_last),
                "is_new_user": 0,
                "time_since_first_transaction": float((current_time - transaction_times[-1]).total_seconds() / 86400),
                "user_fraud_rate": sum(1 for t in user_transactions if t.is_fraudulent) / len(user_transactions) if user_transactions else 0,
                "user_avg_risk_score": np.mean([t.risk_score for t in user_transactions]) if user_transactions else 0.0,
            })
            
        except Exception as e:
            logger.warning(f"Behavioral feature extraction failed: {e}")
            # Set default values
            features.update({
                "user_transaction_count": 0,
                "user_avg_amount": 0.0,
                "user_amount_std": 0.0,
                "user_frequency_days": 0.0,
                "is_new_user": 1,
            })
        
        return features
    
    async def _extract_merchant_features(self, merchant_id: Optional[str]) -> Dict[str, Any]:
        """Extract merchant-related features"""
        features = {}
        
        if not merchant_id:
            features.update({
                "merchant_risk_score": 0.5,
                "merchant_transaction_count": 0,
                "merchant_fraud_rate": 0.0,
                "merchant_avg_amount": 0.0,
                "is_known_merchant": 0,
            })
            return features
        
        try:
            from sqlalchemy import select
            
            # Get merchant from database
            query = select(Merchant).where(Merchant.id == merchant_id)
            result = await self.db.execute(query)
            merchant = result.scalar_one_or_none()
            
            if merchant:
                features.update({
                    "merchant_risk_score": float(merchant.risk_score) / 100.0,
                    "merchant_transaction_count": merchant.total_transactions,
                    "merchant_fraud_rate": merchant.fraud_count / merchant.total_transactions if merchant.total_transactions > 0 else 0.0,
                    "merchant_avg_amount": float(merchant.avg_transaction_amount) if merchant.avg_transaction_amount else 0.0,
                    "is_known_merchant": 1,
                    "merchant_category": self._encode_category(merchant.category) if merchant.category else 0,
                })
            else:
                # New merchant
                features.update({
                    "merchant_risk_score": 0.5,
                    "merchant_transaction_count": 0,
                    "merchant_fraud_rate": 0.0,
                    "merchant_avg_amount": 0.0,
                    "is_known_merchant": 0,
                })
                
        except Exception as e:
            logger.warning(f"Merchant feature extraction failed: {e}")
            features.update({
                "merchant_risk_score": 0.5,
                "merchant_transaction_count": 0,
                "merchant_fraud_rate": 0.0,
                "merchant_avg_amount": 0.0,
                "is_known_merchant": 0,
            })
        
        return features
    
    async def _extract_device_features(self, device_id: Optional[str]) -> Dict[str, Any]:
        """Extract device-related features"""
        features = {}
        
        if not device_id:
            features.update({
                "device_risk_score": 0.5,
                "device_transaction_count": 0,
                "device_associated_accounts": 1,
                "is_known_device": 0,
                "device_suspicious": 0,
            })
            return features
        
        try:
            from sqlalchemy import select
            
            # Get device from database
            query = select(Device).where(Device.id == device_id)
            result = await self.db.execute(query)
            device = result.scalar_one_or_none()
            
            if device:
                features.update({
                    "device_risk_score": float(device.risk_score) / 100.0,
                    "device_transaction_count": await self._count_device_transactions(device_id),
                    "device_associated_accounts": device.associated_accounts,
                    "is_known_device": 1,
                    "device_suspicious": 1 if device.is_suspicious else 0,
                    "device_type": self._encode_device_type(device.device_type) if device.device_type else 0,
                })
            else:
                # New device
                features.update({
                    "device_risk_score": 0.5,
                    "device_transaction_count": 0,
                    "device_associated_accounts": 1,
                    "is_known_device": 0,
                    "device_suspicious": 0,
                })
                
        except Exception as e:
            logger.warning(f"Device feature extraction failed: {e}")
            features.update({
                "device_risk_score": 0.5,
                "device_transaction_count": 0,
                "device_associated_accounts": 1,
                "is_known_device": 0,
                "device_suspicious": 0,
            })
        
        return features
    
    def _extract_temporal_features(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract temporal features"""
        current_time = datetime.now()
        
        features = {
            "hour_of_day": current_time.hour,
            "day_of_week": current_time.weekday(),
            "day_of_month": current_time.day,
            "month": current_time.month,
            "is_weekend": 1 if current_time.weekday() >= 5 else 0,
            "hour_sin": np.sin(2 * np.pi * current_time.hour / 24),
            "hour_cos": np.cos(2 * np.pi * current_time.hour / 24),
            "day_sin": np.sin(2 * np.pi * current_time.weekday() / 7),
            "day_cos": np.cos(2 * np.pi * current_time.weekday() / 7),
        }
        
        return features
    
    async def _extract_graph_features(self, user_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract graph-based features (simulated)
        
        In production, this would query a graph database (Neo4j) or use
        pre-computed GNN embeddings. Here we simulate with simple features.
        """
        features = {}
        
        try:
            from sqlalchemy import select
            
            # Get transactions from the same device
            device_id = transaction_data.get("device_id")
            if device_id:
                query = select(func.count(Transaction.id)).where(
                    and_(
                        Transaction.device_id == device_id,
                        Transaction.user_id != user_id
                    )
                )
                result = await self.db.execute(query)
                shared_device_count = result.scalar() or 0
                features["shared_device_count"] = shared_device_count
            else:
                features["shared_device_count"] = 0
            
            # Get transactions with same merchant by other users recently
            merchant_id = transaction_data.get("merchant_id")
            if merchant_id:
                recent_time = datetime.now() - timedelta(hours=24)
                query = select(func.count(Transaction.id)).where(
                    and_(
                        Transaction.merchant_id == merchant_id,
                        Transaction.user_id != user_id,
                        Transaction.transaction_time >= recent_time
                    )
                )
                result = await self.db.execute(query)
                merchant_activity_count = result.scalar() or 0
                features["merchant_activity_24h"] = merchant_activity_count
            else:
                features["merchant_activity_24h"] = 0
            
            # Simple graph risk score (simulated)
            graph_risk = 0.0
            if features.get("shared_device_count", 0) > 3:
                graph_risk += 0.3
            if features.get("merchant_activity_24h", 0) > 10:
                graph_risk += 0.2
            
            features["graph_risk_raw"] = min(graph_risk, 1.0)
            
        except Exception as e:
            logger.warning(f"Graph feature extraction failed: {e}")
            features.update({
                "shared_device_count": 0,
                "merchant_activity_24h": 0,
                "graph_risk_raw": 0.0,
            })
        
        return features
    
    def _create_derived_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Create derived/engineered features"""
        derived = {}
        
        # Interaction features
        if "amount" in features and "user_avg_amount" in features:
            derived["amount_user_ratio"] = features["amount"] / max(features["user_avg_amount"], 1.0)
            derived["amount_user_diff"] = features["amount"] - features["user_avg_amount"]
        
        # Risk combination
        risk_factors = []
        if "merchant_risk_score" in features:
            risk_factors.append(features["merchant_risk_score"])
        if "device_risk_score" in features:
            risk_factors.append(features["device_risk_score"])
        if "graph_risk_raw" in features:
            risk_factors.append(features["graph_risk_raw"])
        
        if risk_factors:
            derived["composite_risk"] = np.mean(risk_factors)
        
        # Behavioral flags
        if "amount_ratio" in features:
            derived["high_amount_flag"] = 1 if features["amount_ratio"] > 3.0 else 0
            derived["very_high_amount_flag"] = 1 if features["amount_ratio"] > 10.0 else 0
        
        if "hours_since_last_transaction" in features:
            derived["rapid_transaction_flag"] = 1 if features["hours_since_last_transaction"] < 1.0 else 0
        
        return derived
    
    async def _count_device_transactions(self, device_id: str) -> int:
        """Count transactions from a device"""
        from sqlalchemy import select, func
        
        query = select(func.count(Transaction.id)).where(Transaction.device_id == device_id)
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    # Encoding helper methods
    def _encode_currency(self, currency: str) -> int:
        """Simple currency encoding"""
        currency_map = {"USD": 1, "EUR": 2, "GBP": 3, "JPY": 4, "CAD": 5, "AUD": 6}
        return currency_map.get(currency.upper(), 0)
    
    def _encode_transaction_type(self, tx_type: str) -> int:
        """Simple transaction type encoding"""
        type_map = {
            "purchase": 1, "withdrawal": 2, "transfer": 3, 
            "deposit": 4, "refund": 5, "payment": 6
        }
        return type_map.get(tx_type.lower(), 0)
    
    def _encode_category(self, category: str) -> int:
        """Simple category encoding"""
        # Common categories
        category_map = {
            "groceries": 1, "electronics": 2, "clothing": 3,
            "travel": 4, "dining": 5, "entertainment": 6,
            "utilities": 7, "health": 8, "education": 9
        }
        return category_map.get(category.lower(), 0)
    
    def _encode_device_type(self, device_type: str) -> int:
        """Simple device type encoding"""
        device_map = {"mobile": 1, "desktop": 2, "tablet": 3}
        return device_map.get(device_type.lower(), 0)


async def initialize_fraud_patterns():
    """Initialize the fraud patterns database with common patterns"""
    logger.info("Initializing fraud patterns database...")
    
    # This would be called on startup to populate the fraud patterns
    # In production, this would load from a file or external source
    pass