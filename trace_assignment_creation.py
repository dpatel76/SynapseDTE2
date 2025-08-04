#!/usr/bin/env python3
"""Trace when these assignments were created"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def trace():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        # Get all assignments with their creation times
        assignments = await db.execute(text('''
            SELECT 
                assignment_id,
                title,
                context_data->>'attribute_id' as attribute_id,
                context_data->>'attribute_name' as attribute_name,
                created_at,
                created_by
            FROM universal_assignments
            WHERE assignment_type = 'LOB Assignment'
            AND context_type = 'Attribute'
            AND context_data->>'cycle_id' = '55'
            AND context_data->>'report_id' = '156'
            ORDER BY created_at
        '''))
        
        print("Assignment creation timeline:")
        for a in assignments:
            print(f"\n{a.created_at}: Created by user {a.created_by}")
            print(f"  Title: {a.title}")
            print(f"  Attribute ID: {a.attribute_id}")
        
        # Also check for other types of assignments that might have been created
        other_assignments = await db.execute(text('''
            SELECT 
                assignment_id,
                assignment_type,
                title,
                context_data,
                created_at
            FROM universal_assignments
            WHERE context_data->>'cycle_id' = '55'
            AND context_data->>'report_id' = '156'
            AND assignment_type != 'LOB Assignment'
            ORDER BY created_at
        '''))
        
        print("\n\nOther assignments for this cycle/report:")
        for a in other_assignments:
            print(f"\n{a.created_at}: Type = {a.assignment_type}")
            print(f"  Title: {a.title}")
            print(f"  Context: {a.context_data}")
    
    await engine.dispose()

asyncio.run(trace())