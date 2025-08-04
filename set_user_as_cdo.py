#!/usr/bin/env python3
"""
Set a user as CDO for testing
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update
import os

async def set_user_as_cdo(user_id: int):
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/synapseDV")
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        from app.models.user import User
        
        # Update user to have is_cdo = True
        await db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(is_cdo=True)
        )
        
        await db.commit()
        print(f"✅ User {user_id} has been set as CDO (is_cdo=True)")
        
        # Verify the update
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User details:")
            print(f"  Email: {user.email}")
            print(f"  Name: {user.first_name} {user.last_name}")
            print(f"  Role: {user.role}")
            print(f"  Is CDO: {user.is_cdo}")
        else:
            print(f"❌ User {user_id} not found")

async def main():
    print("🔧 SETTING USER AS CDO")
    print("=" * 60)
    
    # Set user 3 (test user) as CDO
    await set_user_as_cdo(3)
    
    print("\n⚠️  Note: The user will need to log in again to get a new token with CDO permissions")

if __name__ == "__main__":
    asyncio.run(main())