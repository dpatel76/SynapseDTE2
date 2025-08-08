#!/usr/bin/env python3
"""Test login functionality"""
import asyncio
import sys
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.auth import verify_password

async def test_login():
    """Test login with direct database access"""
    async with AsyncSessionLocal() as db:
        # Test user lookup
        result = await db.execute(select(User).where(User.email == "tester@synapse.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User not found")
            return False
            
        print(f"✅ User found: {user.email}, {user.first_name} {user.last_name}")
        print(f"   Role: {user.role}")
        print(f"   Active: {user.is_active}")
        print(f"   Has password: {bool(user.hashed_password)}")
        
        # Test password
        if verify_password("Test@123", user.hashed_password):
            print("✅ Password verification successful")
            return True
        else:
            print("❌ Password verification failed")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_login())
    sys.exit(0 if result else 1)