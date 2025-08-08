#\!/usr/bin/env python3
"""List all test users"""

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User

async def list_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()
        
        print("Active users:")
        for user in users:
            print(f"- {user.email} ({user.role})")

if __name__ == "__main__":
    asyncio.run(list_users())
EOF < /dev/null