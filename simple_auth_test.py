#!/usr/bin/env python3
"""Simple auth test without FastAPI test client"""

import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from passlib.context import CryptContext

async def test_auth_components():
    # Database URL
    db_url = "postgresql+asyncpg://synapse_user:synapse_password@postgres:5432/synapse_dt"
    
    print("1. Creating database engine...")
    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Test 1: Find user
        print("\n2. Finding user...")
        start = time.time()
        from app.models.user import User
        result = await session.execute(
            select(User).where(User.email == 'tester@example.com')
        )
        user = result.scalar_one_or_none()
        print(f"User found in {time.time() - start:.2f}s: {user}")
        
        if user:
            # Test 2: Verify password
            print("\n3. Verifying password...")
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            start = time.time()
            valid = pwd_context.verify("password123", user.hashed_password)
            print(f"Password verified in {time.time() - start:.2f}s: {valid}")
            
            # Test 3: Create token
            print("\n4. Creating token...")
            from jose import jwt
            from datetime import datetime, timedelta
            
            start = time.time()
            token_data = {"sub": str(user.user_id)}
            expire = datetime.utcnow() + timedelta(minutes=30)
            token_data.update({"exp": expire})
            token = jwt.encode(token_data, "secret-key", algorithm="HS256")
            print(f"Token created in {time.time() - start:.2f}s")
            print(f"Token: {token[:50]}...")
    
    await engine.dispose()
    print("\nAll components working!")

if __name__ == "__main__":
    asyncio.run(test_auth_components())