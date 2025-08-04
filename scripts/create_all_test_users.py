#!/usr/bin/env python
"""Create test users for all roles with known passwords"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User
from app.models.lob import LOB
from app.infrastructure.external_services.auth_service_impl import AuthServiceImpl

DATABASE_URL = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"

test_users = [
    {
        "email": "admin@synapse.com",
        "first_name": "System",
        "last_name": "Admin",
        "role": "Admin",
        "lob_id": None,
        "password": "admin123"
    },
    {
        "email": "executive@synapse.com",
        "first_name": "Test",
        "last_name": "Executive",
        "role": "Test Executive",
        "lob_id": None,
        "password": "exec123"
    },
    {
        "email": "dataexec@synapse.com",
        "first_name": "Data",
        "last_name": "Executive",
        "role": "Data Executive",
        "lob_id": None,
        "password": "dataexec123"
    },
    {
        "email": "owner@synapse.com",
        "first_name": "Report",
        "last_name": "Owner",
        "role": "Report Owner",
        "lob_id": None,
        "password": "password123"
    },
    {
        "email": "tester@synapse.com",
        "first_name": "Test",
        "last_name": "Tester",
        "role": "Tester",
        "lob_id": None,
        "password": "tester123"
    },
    {
        "email": "dataowner@synapse.com",
        "first_name": "Data",
        "last_name": "Owner",
        "role": "Data Owner",
        "lob_id": None,
        "password": "dataowner123"
    }
]

async def create_or_update_test_users():
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    auth_service = AuthServiceImpl()
    
    async with async_session() as session:
        # Get first LOB
        result = await session.execute(select(LOB).limit(1))
        lob = result.scalar_one_or_none()
        lob_id = lob.lob_id if lob else None
        
        for user_data in test_users:
            # Check if user exists
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Update password
                hashed_password = auth_service.hash_password(user_data["password"])
                user.hashed_password = hashed_password
                print(f"Updated password for existing user: {user.email}")
            else:
                # Create new user
                hashed_password = auth_service.hash_password(user_data["password"])
                user = User(
                    email=user_data["email"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    role=user_data["role"],
                    lob_id=user_data["lob_id"] or lob_id,
                    hashed_password=hashed_password,
                    is_active=True
                )
                session.add(user)
                print(f"Created new user: {user.email}")
            
        await session.commit()
        print("\nAll test users created/updated successfully!")
        print("\nTest credentials:")
        for user_data in test_users:
            print(f"  {user_data['role']}: {user_data['email']} / {user_data['password']}")

if __name__ == "__main__":
    asyncio.run(create_or_update_test_users())