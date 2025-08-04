#!/usr/bin/env python3
"""
Create test user for clean architecture testing
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.auth import get_password_hash


async def create_test_user():
    """Create tester@example.com with password123"""
    async with AsyncSessionLocal() as db:
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == "tester@example.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("✅ Test user already exists: tester@example.com")
            return
        
        # Create new user
        hashed_password = get_password_hash("password123")
        new_user = User(
            email="tester@example.com",
            hashed_password=hashed_password,
            first_name="Test",
            last_name="User",
            role="Tester",
            is_active=True
        )
        
        db.add(new_user)
        await db.commit()
        
        print("✅ Created test user: tester@example.com / password123")
        print(f"   Role: {new_user.role}")
        print(f"   Active: {new_user.is_active}")


if __name__ == "__main__":
    asyncio.run(create_test_user())