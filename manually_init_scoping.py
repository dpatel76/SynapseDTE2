#!/usr/bin/env python3
"""Manually initialize scoping attributes"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import uuid

# Database connection
DATABASE_URL = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def initialize_scoping():
    """Manually initialize scoping attributes"""
    async with AsyncSessionLocal() as db:
        print("Manually initializing scoping attributes...")
        
        # Get phase IDs
        phases_result = await db.execute(text("""
            SELECT phase_id, phase_name 
            FROM workflow_phases 
            WHERE cycle_id = 58 AND report_id = 156 
            AND phase_name IN ('Planning', 'Scoping')
        """))
        phases = {row[1]: row[0] for row in phases_result.fetchall()}
        
        planning_phase_id = phases.get('Planning')
        scoping_phase_id = phases.get('Scoping')
        
        if not planning_phase_id or not scoping_phase_id:
            print("❌ Missing required phases")
            return
            
        print(f"Planning phase ID: {planning_phase_id}")
        print(f"Scoping phase ID: {scoping_phase_id}")
        
        # Get the existing version
        version_result = await db.execute(text("""
            SELECT version_id 
            FROM cycle_report_scoping_versions 
            WHERE phase_id = :phase_id AND version_status = 'draft'
            ORDER BY version_number DESC
            LIMIT 1
        """), {"phase_id": scoping_phase_id})
        version = version_result.first()
        
        if not version:
            print("❌ No draft version found")
            return
            
        version_id = version[0]
        print(f"Using version: {version_id}")
        
        # Get planning attributes
        attrs_result = await db.execute(text("""
            SELECT id, attribute_name, data_type, is_primary_key, is_cde
            FROM cycle_report_planning_attributes
            WHERE phase_id = :phase_id AND is_active = true
        """), {"phase_id": planning_phase_id})
        planning_attrs = attrs_result.fetchall()
        
        print(f"Found {len(planning_attrs)} planning attributes")
        
        # Check existing scoping attributes
        existing_result = await db.execute(text("""
            SELECT COUNT(*) 
            FROM cycle_report_scoping_attributes
            WHERE version_id = :version_id
        """), {"version_id": str(version_id)})
        existing_count = existing_result.scalar()
        
        if existing_count > 0:
            print(f"⚠️  Version already has {existing_count} attributes")
            response = input("Delete existing and recreate? (y/n): ")
            if response.lower() == 'y':
                await db.execute(text("""
                    DELETE FROM cycle_report_scoping_attributes
                    WHERE version_id = :version_id
                """), {"version_id": str(version_id)})
                await db.commit()
                print("Deleted existing attributes")
            else:
                return
        
        # Create scoping attributes
        created = 0
        for attr in planning_attrs:
            attr_id = str(uuid.uuid4())
            await db.execute(text("""
                INSERT INTO cycle_report_scoping_attributes (
                    attribute_id, version_id, phase_id, planning_attribute_id,
                    final_status, created_by_id, updated_by_id,
                    created_at, updated_at
                ) VALUES (
                    :attr_id, :version_id, :phase_id, :planning_attr_id,
                    'pending', 3, 3,  -- Using user_id 3 (tester)
                    NOW(), NOW()
                )
            """), {
                "attr_id": attr_id,
                "version_id": str(version_id),
                "phase_id": scoping_phase_id,
                "planning_attr_id": attr.id
            })
            created += 1
            
            if created % 10 == 0:
                print(f"Created {created} attributes...")
        
        # Update version counts
        await db.execute(text("""
            UPDATE cycle_report_scoping_versions 
            SET total_attributes = :total, 
                scoped_attributes = 0,
                updated_at = NOW()
            WHERE version_id = :version_id
        """), {
            "total": created,
            "version_id": str(version_id)
        })
        
        await db.commit()
        print(f"\n✅ Successfully created {created} scoping attributes!")
        
        # Verify
        verify_result = await db.execute(text("""
            SELECT COUNT(*) 
            FROM cycle_report_scoping_attributes sa
            JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
            WHERE sa.version_id = :version_id
        """), {"version_id": str(version_id)})
        final_count = verify_result.scalar()
        print(f"✅ Verified: {final_count} attributes with valid planning references")

if __name__ == "__main__":
    asyncio.run(initialize_scoping())