"""
Database initialization script for FinGuard AI.
Creates database, tables, and demo user.
"""
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from passlib.context import CryptContext

# Import models to ensure they're registered
from app.db.models import Base, User, Transaction, Explanation, Alert, Merchant, Device, FraudPattern
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_database():
    """Create database if it doesn't exist."""
    # Connect to postgres database to create finguard_db
    admin_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/postgres"
    
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    
    try:
        async with engine.connect() as conn:
            # Check if database exists
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname='{settings.POSTGRES_DB}'")
            )
            exists = result.scalar()
            
            if not exists:
                print(f"Creating database {settings.POSTGRES_DB}...")
                await conn.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}"))
                print(f"✅ Database {settings.POSTGRES_DB} created")
            else:
                print(f"✅ Database {settings.POSTGRES_DB} already exists")
    finally:
        await engine.dispose()


async def create_tables():
    """Create all tables."""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ All tables created")
    finally:
        await engine.dispose()


async def create_demo_user():
    """Create demo user if not exists.

    Ensure the demo user has the fixed UUID used by the auth fallback so
    tokens issued by the demo/login fallback map to a real DB user and
    avoid foreign key constraint failures when storing transactions.
    """
    import uuid as _uuid

    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    DEMO_USER_ID = _uuid.UUID("00000000-0000-0000-0000-000000000001")

    try:
        async with AsyncSessionLocal() as session:
            # Check if demo user exists by username
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.username == "demo"))
            user = result.scalar_one_or_none()
            
            if not user:
                print("Creating demo user...")
                # Hash password with bcrypt
                import bcrypt
                password_bytes = "demo".encode('utf-8')
                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(password_bytes, salt)
                
                # Create demo user with deterministic UUID so JWT fallback matches DB user id
                demo_user = User(
                    id=DEMO_USER_ID,
                    email="demo@finguard.ai",
                    username="demo",
                    hashed_password=hashed.decode('utf-8'),
                    is_active=True,
                    is_superuser=False,
                )
                session.add(demo_user)
                await session.commit()
                print("✅ Demo user created (username: demo, password: demo, id=00000000-0000-0000-0000-000000000001)")
            else:
                # If user exists but has a different id, warn but do not overwrite
                if getattr(user, 'id', None) != DEMO_USER_ID:
                    print("⚠️ Demo user exists with a different id; consider recreating to match the expected demo UUID")
                print("✅ Demo user already exists")
    finally:
        await engine.dispose()


async def initialize_fraud_patterns():
    """Initialize common fraud patterns for RAG system."""
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    patterns = [
        {
            "pattern_name": "Rapid Transaction Sequence",
            "pattern_type": "behavioral",
            "description": "Multiple transactions in quick succession from the same account",
            "indicators": ["time_gap < 60s", "same_merchant", "increasing_amounts"],
            "mitigation_strategies": ["velocity_check", "2fa_required", "transaction_limit"]
        },
        {
            "pattern_name": "Unusual Location",
            "pattern_type": "device",
            "description": "Transaction from geographically distant location",
            "indicators": ["distance > 500km", "time_gap < 2h"],
            "mitigation_strategies": ["location_verification", "manual_review"]
        },
        {
            "pattern_name": "Card Testing",
            "pattern_type": "merchant",
            "description": "Small test transactions before large fraud",
            "indicators": ["amount < $1", "multiple_attempts", "different_cards"],
            "mitigation_strategies": ["captcha", "rate_limiting", "merchant_alert"]
        }
    ]
    
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(select(FraudPattern))
            existing = result.scalars().all()
            
            if not existing:
                print("Initializing fraud patterns...")
                for p in patterns:
                    pattern = FraudPattern(**p)
                    session.add(pattern)
                await session.commit()
                print(f"✅ Initialized {len(patterns)} fraud patterns")
            else:
                print(f"✅ Fraud patterns already initialized ({len(existing)} patterns)")
    finally:
        await engine.dispose()


async def main():
    """Main initialization function."""
    print("=" * 60)
    print("FinGuard AI - Database Initialization")
    print("=" * 60)
    
    try:
        print("\n1. Creating database...")
        await create_database()
        
        print("\n2. Creating tables...")
        await create_tables()
        
        print("\n3. Creating demo user...")
        await create_demo_user()
        
        print("\n4. Initializing fraud patterns...")
        await initialize_fraud_patterns()
        
        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Login with username='demo', password='demo'")
        print("  2. Start submitting transactions")
        print("  3. View fraud detection results")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
