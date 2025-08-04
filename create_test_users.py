#!/usr/bin/env python3
"""Create test users for comprehensive testing."""

import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import datetime
import sys
sys.path.append('.')

from app.models.user import User
from app.models.enums import UserRole

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_USERS = [
    {
        "email": "admin@example.com",
        "password": "password123",
        "first_name": "Admin",
        "last_name": "User",
        "role": UserRole.ADMIN
    },
    {
        "email": "report_owner@example.com", 
        "password": "password123",
        "first_name": "Report",
        "last_name": "Owner",
        "role": UserRole.REPORT_OWNER
    },
    {
        "email": "tester@example.com",
        "password": "password123", 
        "first_name": "Test",
        "last_name": "User",
        "role": UserRole.TESTER
    }
]


async def create_test_users():
    """Create test users."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        try:
            for user_data in TEST_USERS:
                # Check if user exists
                query = select(User).where(User.email == user_data["email"])
                result = await db.execute(query)
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    print(f"User {user_data['email']} already exists - updating password")
                    existing_user.hashed_password = pwd_context.hash(user_data["password"])
                    existing_user.updated_at = datetime.utcnow()
                else:
                    # Create new user
                    new_user = User(
                        email=user_data["email"],
                        hashed_password=pwd_context.hash(user_data["password"]),
                        first_name=user_data["first_name"],
                        last_name=user_data["last_name"],
                        role=user_data["role"],
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_user)
                    print(f"Created user: {user_data['email']}")
            
            await db.commit()
            print("\nAll test users created/updated successfully!")
            
        except Exception as e:
            print(f"Error creating users: {str(e)}")
            await db.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_users())