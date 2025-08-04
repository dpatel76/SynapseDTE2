#!/usr/bin/env python
"""Debug the cycles API issue"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func
from app.models.test_cycle import TestCycle

load_dotenv()

async def debug_cycles_api():
    # Direct database query
    conn = await asyncpg.connect(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
    
    print("=== Direct Database Query ===")
    cycles = await conn.fetch("""
        SELECT cycle_id, cycle_name, status, test_manager_id
        FROM test_cycles
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    print(f"Total cycles in database: {len(cycles)}")
    for cycle in cycles[:5]:
        print(f"  - ID: {cycle['cycle_id']}, Name: {cycle['cycle_name']}, Status: {cycle['status']}")
    
    await conn.close()
    
    # SQLAlchemy query (mimicking API)
    print("\n=== SQLAlchemy Query (API Style) ===")
    engine = create_async_engine(os.getenv('DATABASE_URL'), echo=True)
    
    async with AsyncSession(engine) as db:
        # Count query
        count_result = await db.execute(select(func.count(TestCycle.cycle_id)))
        total = count_result.scalar()
        print(f"Total count from SQLAlchemy: {total}")
        
        # Main query with pagination
        query = select(TestCycle).options(
            selectinload(TestCycle.test_manager)
        ).offset(0).limit(10).order_by(TestCycle.created_at.desc())
        
        result = await db.execute(query)
        cycles = result.scalars().all()
        print(f"Cycles returned by SQLAlchemy: {len(cycles)}")
        
        for cycle in cycles[:5]:
            print(f"  - ID: {cycle.cycle_id}, Name: {cycle.cycle_name}, Status: {cycle.status}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_cycles_api())