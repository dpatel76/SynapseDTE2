#!/usr/bin/env python3
"""
Reset admin password
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User
from app.core.auth import get_password_hash
from app.core.config import settings

async def reset_admin_password():
    """Reset admin password to TestUser123!"""
    # Fix the database URL to use asyncpg
    db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find admin user
        result = await session.execute(
            select(User).where(User.email == "admin@synapsedt.com")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("❌ Admin user not found")
            return
        
        # Update password
        admin.hashed_password = get_password_hash("TestUser123!")
        
        await session.commit()
        print("✅ Admin password reset to: TestUser123!")

if __name__ == "__main__":
    asyncio.run(reset_admin_password())