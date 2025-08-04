#!/usr/bin/env python
"""Create a test user with known password"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User
from app.infrastructure.external_services.auth_service_impl import AuthServiceImpl

DATABASE_URL = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"

async def create_or_update_test_user():
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    auth_service = AuthServiceImpl()
    
    async with async_session() as session:
        # Update existing owner user
        result = await session.execute(
            select(User).where(User.email == "owner@synapse.com")
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update password
            hashed_password = auth_service.hash_password("password123")
            user.hashed_password = hashed_password
            print(f"Updated password for user: {user.email}")
            
            await session.commit()
            print("Password updated successfully!")
            
            # Verify
            if auth_service.verify_password("password123", hashed_password):
                print("Password verification successful!")
            else:
                print("Password verification failed!")
        else:
            print("User not found! Creating new user...")
            # Create new user
            new_user = User(
                email="owner@synapse.com",
                first_name="Test",
                last_name="Owner",
                role="Report Owner",
                is_active=True,
                hashed_password=auth_service.hash_password("password123")
            )
            session.add(new_user)
            await session.commit()
            print("User created successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_or_update_test_user())