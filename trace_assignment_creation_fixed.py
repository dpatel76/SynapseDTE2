#!/usr/bin/env python3
"""Trace when these assignments were created - fixed version"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def trace():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        # First check column names
        columns = await db.execute(text('''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'universal_assignments'
            ORDER BY column_name
        '''))
        
        print("Available columns:")
        for c in columns:
            print(f"  - {c.column_name}")
        
        # Get all assignments with their creation times
        assignments = await db.execute(text('''
            SELECT 
                assignment_id,
                title,
                context_data->>'attribute_id' as attribute_id,
                context_data->>'attribute_name' as attribute_name,
                created_at,
                from_user_id
            FROM universal_assignments
            WHERE assignment_type = 'LOB Assignment'
            AND context_type = 'Attribute'
            AND context_data->>'cycle_id' = '55'
            AND context_data->>'report_id' = '156'
            ORDER BY created_at
        '''))
        
        print("\n\nAssignment creation timeline:")
        for a in assignments:
            print(f"\n{a.created_at}: Created by user {a.from_user_id}")
            print(f"  Title: {a.title}")
            print(f"  Attribute ID: {a.attribute_id}")
    
    await engine.dispose()

asyncio.run(trace())