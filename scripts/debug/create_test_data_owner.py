#!/usr/bin/env python3
"""
Create a test data owner user
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

sys.path.append('.')

from app.models.user import User
from app.core.security import get_password_hash
from app.models.lob import LOB

# Database connection
DATABASE_URL = "postgresql+asyncpg://synapsdte:synapsdte@localhost/synapsdte"

async def main():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == "test.dataowner@synapse.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"User already exists with ID: {existing_user.user_id}")
            # Update password to ensure we know it
            existing_user.hashed_password = get_password_hash("password123")
            await session.commit()
            print("Password updated to: password123")
        else:
            # Get first LOB
            lob_result = await session.execute(select(LOB).limit(1))
            lob = lob_result.scalar_one_or_none()
            
            if not lob:
                print("No LOB found in database")
                return
            
            # Create new data owner
            new_user = User(
                email="test.dataowner@synapse.com",
                first_name="Test",
                last_name="DataOwner",
                role="Data Owner",
                lob_id=lob.lob_id,
                is_active=True,
                hashed_password=get_password_hash("password123")
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            print(f"Created new data owner with ID: {new_user.user_id}")
            print(f"Email: test.dataowner@synapse.com")
            print(f"Password: password123")
            print(f"LOB ID: {lob.lob_id}")

if __name__ == "__main__":
    asyncio.run(main())