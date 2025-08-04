#!/usr/bin/env python3
"""Trace the exact execution to find the bug"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import json

async def trace_bug():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        print("=== TRACING THE BUG ===")
        
        # The bug must be that the phase was started multiple times
        # Or the _create_universal_assignments was called with different version_ids
        
        # Let's check if there are multiple "LOB Assignment" type assignments
        # but with different context_data
        
        print("\n1. Checking all LOB Assignments for this cycle/report:")
        assignments = await db.execute(text('''
            SELECT 
                assignment_id,
                context_data,
                created_at,
                from_user_id
            FROM universal_assignments
            WHERE assignment_type = 'LOB Assignment'
            AND context_type = 'Attribute'
            ORDER BY created_at DESC
            LIMIT 10
        '''))
        
        for a in assignments:
            context = a.context_data
            if context.get('cycle_id') == 55 and context.get('report_id') == 156:
                print(f"\nAssignment {a.assignment_id}:")
                print(f"  Created: {a.created_at}")
                print(f"  Attribute ID: {context.get('attribute_id')}")
                print(f"  Attribute Name: {context.get('attribute_name')}")
                print(f"  LOB: {context.get('lob_name')}")
        
        # Let's check if there's something with the workflow orchestrator
        # that might have triggered multiple calls
        
        print("\n\n2. Checking workflow activities:")
        activities = await db.execute(text('''
            SELECT 
                activity_id,
                activity_name,
                activity_type,
                cycle_id,
                report_id,
                phase_name,
                created_at
            FROM workflow_activities
            WHERE cycle_id = 55 
            AND report_id = 156
            AND phase_name = 'Data Provider ID'
            ORDER BY created_at DESC
            LIMIT 10
        '''))
        
        for a in activities:
            print(f"\n{a.created_at}: {a.activity_name} ({a.activity_type})")
        
        # Theory: Maybe the issue is in the temporal workflow
        # Let's check if there were multiple workflow executions
        
        print("\n\n3. My hypothesis:")
        print("The bug is likely that:")
        print("- The query IS correct and returns 1 attribute")
        print("- But something is calling _create_universal_assignments multiple times")
        print("- Or there's a bug in how scoped_attributes list is being built")
        
        # Let me check if there's something weird with the attribute list building
        print("\n\n4. Let's simulate the exact code flow:")
        
        # Get approved version
        approved_version_result = await db.execute(
            text('''
                SELECT version_id, version_number 
                FROM cycle_report_scoping_versions 
                WHERE phase_id = 467 
                AND version_status = 'approved'
                ORDER BY version_number DESC 
                LIMIT 1
            ''')
        )
        approved_version_row = approved_version_result.first()
        print(f"Approved version: {approved_version_row.version_id}")
        
        # Now let's trace if there's an issue with how the loop works
        # or if scoped_attributes gets populated incorrectly
    
    await engine.dispose()

asyncio.run(trace_bug())