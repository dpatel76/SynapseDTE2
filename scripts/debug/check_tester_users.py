#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.user import User

async def check_tester_users():
    DATABASE_URL = 'postgresql+asyncpg://dineshpatel@localhost:5432/synapse_dt'
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all users with their roles
        result = await session.execute(
            select(User).where(User.is_active == True).order_by(User.role, User.email)
        )
        users = result.scalars().all()
        
        print(f"📊 Found {len(users)} active users:")
        print()
        
        # Group by role
        users_by_role = {}
        for user in users:
            role = user.role
            if role not in users_by_role:
                users_by_role[role] = []
            users_by_role[role].append(user)
        
        for role, role_users in sorted(users_by_role.items()):
            print(f"🔹 {role} ({len(role_users)} users):")
            for user in role_users:
                print(f"   - {user.email} (ID: {user.user_id}) - {user.first_name} {user.last_name}")
            print()
        
        # Check specifically for Tester role
        tester_users = [u for u in users if u.role == 'Tester']
        print(f"👤 Tester users specifically: {len(tester_users)}")
        
        if not tester_users:
            print("❌ No Tester users found! This explains why no testers show up in assignment.")
            print("   You need to create users with the 'Tester' role.")
        else:
            print("✅ Found Tester users:")
            for user in tester_users:
                print(f"   🔹 {user.email} - {user.first_name} {user.last_name} (Active: {user.is_active})")

if __name__ == "__main__":
    asyncio.run(check_tester_users()) 