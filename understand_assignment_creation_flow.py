#!/usr/bin/env python3
"""Understand why multiple assignments were created"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def understand():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        print("=== CHECKING WORKFLOW ACTIVITIES ===")
        
        # Check workflow activities table structure first
        columns = await db.execute(text('''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'workflow_activities'
            ORDER BY column_name
            LIMIT 10
        '''))
        
        print("\nWorkflow activities columns:")
        for c in columns:
            print(f"  - {c.column_name}")
        
        # Check the phase history
        print("\n\n=== CHECKING PHASE HISTORY ===")
        phases = await db.execute(text('''
            SELECT 
                phase_id,
                phase_name,
                status,
                state,
                actual_start_date,
                created_at,
                updated_at
            FROM workflow_phases
            WHERE cycle_id = 55 
            AND report_id = 156
            ORDER BY phase_order, created_at
        '''))
        
        print("\nAll phases for this cycle/report:")
        for p in phases:
            print(f"  {p.phase_name}: status={p.status}, state={p.state}")
            if p.phase_name == 'Data Provider ID':
                print(f"    Phase ID: {p.phase_id}")
                print(f"    Started: {p.actual_start_date}")
        
        # Now let's check backend logs to see if there's a pattern
        print("\n\n=== ANALYZING ASSIGNMENT CREATION PATTERN ===")
        
        # The 5 assignments were all created at the same millisecond
        # This suggests they were created in a single loop iteration
        # Let's check if there are 5 scoping versions with approved "Current Credit limit"
        
        versions_with_attr = await db.execute(text('''
            SELECT 
                v.version_id,
                v.version_number,
                v.version_status,
                sa.attribute_id,
                pa.attribute_name,
                sa.report_owner_decision
            FROM cycle_report_scoping_versions v
            JOIN cycle_report_scoping_attributes sa ON v.version_id = sa.version_id
            JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
            WHERE v.phase_id = 467  -- Scoping phase ID
            AND pa.attribute_name = 'Current Credit limit'
            AND sa.is_primary_key = false
            AND sa.report_owner_decision = 'approved'
            ORDER BY v.version_number
        '''))
        
        print("\nVersions with approved 'Current Credit limit':")
        attr_ids = []
        for v in versions_with_attr:
            print(f"  Version {v.version_number} ({v.version_status}): attribute_id={v.attribute_id}")
            attr_ids.append(v.attribute_id)
        
        # Compare with the assignments created
        print(f"\nFound {len(attr_ids)} versions with approved 'Current Credit limit'")
        
        # Check which attribute IDs were used in assignments
        assignments = await db.execute(text('''
            SELECT 
                context_data->>'attribute_id' as attribute_id,
                created_at
            FROM universal_assignments
            WHERE assignment_type = 'LOB Assignment'
            AND context_type = 'Attribute'
            AND context_data->>'cycle_id' = '55'
            AND context_data->>'report_id' = '156'
            ORDER BY created_at
        '''))
        
        print("\nAttribute IDs in assignments:")
        assignment_attr_ids = []
        for a in assignments:
            assignment_attr_ids.append(a.attribute_id)
            print(f"  {a.attribute_id}")
        
        # Check if they match
        print(f"\nDo assignment attribute IDs match the versions? {set(assignment_attr_ids) == set(str(id) for id in attr_ids)}")
    
    await engine.dispose()

asyncio.run(understand())