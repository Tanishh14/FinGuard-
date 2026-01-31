"""
Generate demo transaction data for FinGuard AI.
Creates realistic transactions for testing the system.
"""
import asyncio
import random
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.db.models import User, Transaction
from app.core.config import settings


async def generate_demo_transactions(count=50):
    """Generate demo transactions for testing."""
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    merchants = [
        "Amazon", "Walmart", "Target", "BestBuy", "Starbucks",
        "McDonald's", "Shell", "Uber", "Netflix", "Apple"
    ]
    
    devices = [
        f"device_{i:03d}" for i in range(1, 11)
    ]
    
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
    countries = ["US"] * 5
    
    try:
        async with AsyncSessionLocal() as session:
            # Get demo user
            result = await session.execute(select(User).where(User.username == "demo"))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ Demo user not found. Run init_db.py first.")
                return
            
            print(f"Generating {count} demo transactions for user {user.username}...")
            
            now = datetime.utcnow()
            transactions = []
            
            for i in range(count):
                # Mix of normal and suspicious patterns
                is_suspicious = i % 10 == 0  # 10% suspicious
                
                # Base transaction time
                tx_time = now - timedelta(days=random.randint(0, 30), 
                                          hours=random.randint(0, 23),
                                          minutes=random.randint(0, 59))
                
                # Transaction amount
                if is_suspicious:
                    amount = random.uniform(500, 5000)  # Large amounts
                else:
                    amount = random.uniform(5, 300)  # Normal amounts
                
                # Risk scoring (simplified)
                if is_suspicious:
                    risk_score = random.uniform(70, 95)
                    risk_level = "high" if risk_score > 80 else "medium"
                    is_fraudulent = risk_score > 85
                    anomaly_score = random.uniform(0.7, 0.95)
                else:
                    risk_score = random.uniform(5, 40)
                    risk_level = "low" if risk_score < 25 else "medium"
                    is_fraudulent = False
                    anomaly_score = random.uniform(0.05, 0.4)
                
                tx = Transaction(
                    transaction_id=f"tx_{i:05d}_{int(tx_time.timestamp())}",
                    user_id=user.id,
                    merchant_id=random.choice(merchants),
                    device_id=random.choice(devices),
                    amount=round(amount, 2),
                    currency="USD",
                    location_city=random.choice(cities),
                    location_country=random.choice(countries),
                    transaction_type="purchase",
                    category=random.choice(["groceries", "electronics", "travel", "dining", "fuel"]),
                    time_of_day=tx_time.hour,
                    day_of_week=tx_time.weekday(),
                    is_weekend=tx_time.weekday() >= 5,
                    risk_score=round(risk_score, 2),
                    risk_level=risk_level,
                    is_fraudulent=is_fraudulent,
                    confidence_score=round(random.uniform(0.7, 0.95), 2),
                    anomaly_score=round(anomaly_score, 3),
                    graph_risk_score=round(random.uniform(0.1, 0.8), 2),
                    transaction_time=tx_time,
                    processed_at=tx_time + timedelta(milliseconds=random.randint(100, 500)),
                    features={
                        "hour": tx_time.hour,
                        "day_of_week": tx_time.weekday(),
                        "amount": amount,
                        "merchant": random.choice(merchants)
                    }
                )
                transactions.append(tx)
            
            # Bulk insert
            session.add_all(transactions)
            await session.commit()
            
            print(f"✅ Generated {count} transactions")
            print(f"   - Normal transactions: {count - count//10}")
            print(f"   - Suspicious transactions: {count//10}")
            print(f"   - Fraudulent transactions: {sum(1 for tx in transactions if tx.is_fraudulent)}")
            
    finally:
        await engine.dispose()


async def main():
    print("=" * 60)
    print("FinGuard AI - Demo Data Generator")
    print("=" * 60)
    
    try:
        await generate_demo_transactions(count=50)
        
        print("\n" + "=" * 60)
        print("✅ Demo data generation complete!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. View dashboard metrics")
        print("  2. Browse transaction history")
        print("  3. View anomaly detection results")
        print("  4. Explore GNN fraud rings")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
