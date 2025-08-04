#!/usr/bin/env python3
"""List tables related to scoping and sample selection"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def list_tables():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%scoping%' 
                 OR table_name LIKE '%sample%'
                 OR table_name LIKE '%attribute%')
            ORDER BY table_name
        """))
        
        print("Tables:")
        for row in result:
            print(f"  - {row.table_name}")
    
    await engine.dispose()

asyncio.run(list_tables())