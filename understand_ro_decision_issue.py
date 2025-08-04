#!/usr/bin/env python3
"""Understand why report_owner_decision is 'approved' in multiple versions"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def understand():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        print("=== UNDERSTANDING REPORT OWNER DECISION ACROSS VERSIONS ===")
        
        # Get all versions and their statuses
        versions = await db.execute(text('''
            SELECT 
                v.version_id,
                v.version_number,
                v.version_status,
                v.parent_version_id,
                v.created_at,
                v.approved_at,
                COUNT(sa.attribute_id) as total_attrs,
                COUNT(CASE WHEN sa.report_owner_decision = 'approved' THEN 1 END) as ro_approved_attrs
            FROM cycle_report_scoping_versions v
            LEFT JOIN cycle_report_scoping_attributes sa ON v.version_id = sa.version_id
            WHERE v.phase_id = 467
            GROUP BY v.version_id, v.version_number, v.version_status, v.parent_version_id, v.created_at, v.approved_at
            ORDER BY v.version_number
        '''))
        
        print("\nVersion history with report owner decisions:")
        for v in versions:
            print(f"\nVersion {v.version_number} ({v.version_status}):")
            print(f"  Created: {v.created_at}")
            print(f"  Approved: {v.approved_at}")
            print(f"  Total attributes: {v.total_attrs}")
            print(f"  RO approved attributes: {v.ro_approved_attrs}")
            if v.parent_version_id:
                print(f"  Parent version: {v.parent_version_id}")
        
        # Check the specific attribute across versions
        print("\n\n=== CHECKING 'Current Credit limit' DECISIONS ACROSS VERSIONS ===")
        
        attr_history = await db.execute(text('''
            SELECT 
                v.version_number,
                v.version_status,
                sa.attribute_id,
                sa.report_owner_decision,
                sa.report_owner_decided_at,
                sa.report_owner_decided_by_id,
                sa.created_at,
                sa.updated_at
            FROM cycle_report_scoping_attributes sa
            JOIN cycle_report_scoping_versions v ON sa.version_id = v.version_id
            JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
            WHERE pa.attribute_name = 'Current Credit limit'
            AND v.phase_id = 467
            ORDER BY v.version_number
        '''))
        
        print("\n'Current Credit limit' decision history:")
        for a in attr_history:
            print(f"\nVersion {a.version_number} ({a.version_status}):")
            print(f"  Attribute ID: {a.attribute_id}")
            print(f"  RO Decision: {a.report_owner_decision}")
            print(f"  RO Decided at: {a.report_owner_decided_at}")
            print(f"  RO Decided by: {a.report_owner_decided_by_id}")
            print(f"  Created: {a.created_at}")
            print(f"  Updated: {a.updated_at}")
        
        print("\n\n=== THEORY: Attributes are being copied with decisions ===")
        print("When creating new versions, report owner decisions might be copied from parent versions")
    
    await engine.dispose()

asyncio.run(understand())