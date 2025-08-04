#!/usr/bin/env python3
"""Create test users for comprehensive testing."""

import asyncio
import os
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import datetime
import sys
sys.path.append('.')

from app.models.user import User

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@localhost/mydatabase")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_USERS = [
    {
        "email": "admin@example.com",
        "password": "password123",
        "first_name": "Admin",
        "last_name": "User",
        "role": "Admin"
    },
    {
        "email": "report_owner@example.com", 
        "password": "password123",
        "first_name": "Report",
        "last_name": "Owner",
        "role": "Report Owner"
    },
    {
        "email": "tester@example.com",
        "password": "password123", 
        "first_name": "Test",
        "last_name": "User",
        "role": "Tester"
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
                    print(f"User {user_data['email']} already exists - updating")
                    existing_user.hashed_password = pwd_context.hash(user_data["password"])
                    existing_user.role = user_data["role"]
                    existing_user.first_name = user_data["first_name"]
                    existing_user.last_name = user_data["last_name"]
                    existing_user.is_active = True
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
            
            # Verify users
            print("\nVerifying users:")
            for user_data in TEST_USERS:
                query = select(User).where(User.email == user_data["email"])
                result = await db.execute(query)
                user = result.scalar_one_or_none()
                if user:
                    print(f"✓ {user.email} - Role: {user.role}")
                else:
                    print(f"✗ {user_data['email']} - NOT FOUND")
            
        except Exception as e:
            print(f"Error creating users: {str(e)}")
            await db.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_users())