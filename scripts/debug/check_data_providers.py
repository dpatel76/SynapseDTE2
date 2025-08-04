#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from app.models.user import User
from app.models.lob import LOB

async def check_data_owners():
    engine = create_async_engine('sqlite+aiosqlite:///./synapse_dt.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=== DATA PROVIDERS CHECK ===\n")
        
        # Check for data providers
        data_owners = await session.execute(
            select(User, LOB)
            .join(LOB, User.lob_id == LOB.lob_id)
            .where(and_(
                User.role == 'Data Owner',
                User.is_active == True
            ))
        )
        data_owners = data_owners.all()
        
        print(f'Found {len(data_owners)} active data providers:')
        for user, lob in data_owners:
            print(f'  {user.first_name} {user.last_name} ({user.email}) - LOB: {lob.lob_name} (ID: {lob.lob_id})')
        
        # Check all users with Data Owner role (including inactive)
        all_dp = await session.execute(
            select(User.user_id, User.first_name, User.last_name, User.email, User.role, User.is_active, User.lob_id)
            .where(User.role == 'Data Owner')
        )
        all_dp = all_dp.all()
        
        print(f'\nAll users with Data Owner role ({len(all_dp)}):')
        for user in all_dp:
            print(f'  {user.first_name} {user.last_name} ({user.email}) - Active: {user.is_active}, LOB: {user.lob_id}')

if __name__ == "__main__":
    asyncio.run(check_data_owners()) 