#!/usr/bin/env python3
"""Initialize scoping phase with direct SQL"""

import asyncio
from datetime import datetime
from app.core.database import AsyncSessionLocal
from sqlalchemy import text
import uuid

async def init_scoping():
    """Initialize scoping phase with initial version using direct SQL"""
    async with AsyncSessionLocal() as db:
        # Check if initial version already exists
        result = await db.execute(text("""
            SELECT version_id 
            FROM cycle_report_scoping_versions sv
            JOIN workflow_phases wp ON sv.phase_id = wp.phase_id
            WHERE wp.cycle_id = 55 AND wp.report_id = 156
        """))
        if result.scalar():
            print("✅ Initial version already exists")
            return
            
        # Get phase IDs
        result = await db.execute(text("""
            SELECT phase_id, phase_name
            FROM workflow_phases
            WHERE cycle_id = 55 AND report_id = 156
            AND phase_name IN ('Planning', 'Scoping')
        """))
        phases = {row.phase_name: row.phase_id for row in result}
        
        if 'Scoping' not in phases or 'Planning' not in phases:
            print("❌ Required phases not found!")
            return
            
        print(f"Found phases: Planning={phases['Planning']}, Scoping={phases['Scoping']}")
        
        # Create initial version
        version_id = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO cycle_report_scoping_versions (
                version_id, phase_id, version_number, version_status,
                total_attributes, scoped_attributes, declined_attributes,
                created_at, updated_at, created_by_id, updated_by_id
            ) VALUES (
                :version_id, :phase_id, 1, 'draft',
                0, 0, 0,
                :now, :now, 3, 3
            )
        """), {
            'version_id': version_id,
            'phase_id': phases['Scoping'],
            'now': datetime.utcnow()
        })
        
        print(f"Created version: {version_id}")
        
        # Get planning attributes
        result = await db.execute(text("""
            SELECT id, attribute_name
            FROM cycle_report_planning_attributes
            WHERE phase_id = :phase_id
        """), {'phase_id': phases['Planning']})
        
        planning_attrs = list(result)
        print(f"Found {len(planning_attrs)} planning attributes")
        
        # Insert scoping attributes
        for attr in planning_attrs:
            await db.execute(text("""
                INSERT INTO cycle_report_scoping_attributes (
                    attribute_id, version_id, phase_id, planning_attribute_id,
                    llm_recommendation, final_status,
                    created_at, updated_at, created_by_id, updated_by_id
                ) VALUES (
                    gen_random_uuid(), :version_id, :phase_id, :planning_id,
                    NULL, 'pending',
                    :now, :now, 3, 3
                )
            """), {
                'version_id': version_id,
                'phase_id': phases['Scoping'],
                'planning_id': attr.id,
                'now': datetime.utcnow()
            })
        
        # Update phase state
        await db.execute(text("""
            UPDATE workflow_phases
            SET state = 'In Progress',
                actual_start_date = :now,
                started_by = 3,
                updated_at = :now
            WHERE phase_id = :phase_id
        """), {
            'phase_id': phases['Scoping'],
            'now': datetime.utcnow()
        })
        
        # Update version statistics
        await db.execute(text("""
            UPDATE cycle_report_scoping_versions
            SET total_attributes = :count,
                updated_at = :now
            WHERE version_id = :version_id
        """), {
            'version_id': version_id,
            'count': len(planning_attrs),
            'now': datetime.utcnow()
        })
        
        await db.commit()
        
        print(f"✅ Successfully initialized scoping phase:")
        print(f"   - Created version 1")
        print(f"   - Imported {len(planning_attrs)} attributes")
        print(f"   - Phase state: In Progress")

if __name__ == "__main__":
    asyncio.run(init_scoping())