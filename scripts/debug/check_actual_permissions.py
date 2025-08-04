#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.rbac import Permission

async def check_permissions():
    DATABASE_URL = 'postgresql+asyncpg://dineshpatel@localhost:5432/synapse_dt'
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Permission).order_by(Permission.resource, Permission.action))
        permissions = result.scalars().all()
        
        print('Actual Permissions in Database:')
        print('=' * 40)
        
        resources = {}
        all_perms = []
        for perm in permissions:
            if perm.resource not in resources:
                resources[perm.resource] = []
            resources[perm.resource].append(perm.action)
            all_perms.append(f"{perm.resource}:{perm.action}")
        
        for resource, actions in resources.items():
            print(f'{resource}: {actions}')
        
        print(f'\nAll permissions ({len(all_perms)}):')
        for perm in all_perms:
            print(f'  {perm}')

if __name__ == "__main__":
    asyncio.run(check_permissions()) 