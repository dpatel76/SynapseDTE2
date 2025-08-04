#!/usr/bin/env python3
"""Manually create the correct assignment"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import json
from datetime import datetime

async def manual_fix():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        print("=== MANUAL FIX: Creating the correct assignment ===")
        
        # Constants
        cycle_id = 55
        report_id = 156
        approved_scoping_version_id = '36bb8065-51ad-457d-b1ce-9e813b360b7c'
        approved_sample_version_id = '9ec77304-cd48-4a78-9843-6635ff4e7fea'  # Version 7
        
        # 1. Get the correct non-PK attribute from approved scoping version
        print("\n1. Getting approved non-PK attribute:")
        attr_result = await db.execute(text('''
            SELECT 
                sa.attribute_id,
                pa.attribute_name,
                pa.id as planning_attribute_id
            FROM cycle_report_scoping_attributes sa
            JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
            WHERE sa.version_id = :version_id
            AND sa.is_primary_key = false
            AND sa.report_owner_decision = 'approved'
        '''), {'version_id': approved_scoping_version_id})
        
        attr = attr_result.first()
        if not attr:
            print("ERROR: No approved non-PK attribute found!")
            return
            
        print(f"  Found: {attr.attribute_name} (ID: {attr.attribute_id})")
        
        # 2. Get the unique LOB from approved samples
        print("\n2. Getting unique LOB from approved samples:")
        lob_result = await db.execute(text('''
            SELECT DISTINCT 
                s.lob_id,
                l.lob_name
            FROM cycle_report_sample_selection_samples s
            JOIN lobs l ON s.lob_id = l.lob_id
            WHERE s.version_id = :version_id
            AND s.report_owner_decision = 'approved'
        '''), {'version_id': approved_sample_version_id})
        
        lob = lob_result.first()
        if not lob:
            print("ERROR: No LOB found in approved samples!")
            return
            
        print(f"  Found: {lob.lob_name} (ID: {lob.lob_id})")
        
        # 3. Get the Data Executive (CDO) for this LOB
        print("\n3. Getting Data Executive for LOB:")
        cdo_result = await db.execute(text('''
            SELECT 
                user_id,
                first_name,
                last_name,
                email
            FROM users
            WHERE role = 'Data Executive'
            AND lob_id = :lob_id
            AND is_active = true
            LIMIT 1
        '''), {'lob_id': lob.lob_id})
        
        cdo = cdo_result.first()
        if not cdo:
            print("ERROR: No Data Executive found for this LOB!")
            return
            
        print(f"  Found: {cdo.first_name} {cdo.last_name} (ID: {cdo.user_id})")
        
        # 4. Create the single correct assignment
        print("\n4. Creating the assignment:")
        
        # First check if it already exists
        existing = await db.execute(text('''
            SELECT assignment_id
            FROM universal_assignments
            WHERE assignment_type = 'LOB Assignment'
            AND context_type = 'Attribute'
            AND to_user_id = :to_user_id
            AND context_data->>'cycle_id' = :cycle_id
            AND context_data->>'report_id' = :report_id
            AND context_data->>'attribute_id' = :attribute_id
        '''), {
            'to_user_id': cdo.user_id,
            'cycle_id': str(cycle_id),
            'report_id': str(report_id),
            'attribute_id': str(attr.attribute_id)
        })
        
        if existing.first():
            print("  Assignment already exists!")
            return
        
        # Create the assignment
        context_data = {
            "cycle_id": cycle_id,
            "report_id": report_id,
            "attribute_id": str(attr.attribute_id),
            "attribute_name": attr.attribute_name,
            "lob_id": lob.lob_id,
            "lob_name": lob.lob_name,
            "phase_name": "Data Provider ID"
        }
        
        result = await db.execute(text('''
            INSERT INTO universal_assignments (
                assignment_type,
                from_role,
                to_role,
                from_user_id,
                to_user_id,
                title,
                description,
                task_instructions,
                context_type,
                context_data,
                priority,
                status,
                assigned_at,
                created_at,
                updated_at,
                created_by_id,
                updated_by_id
            ) VALUES (
                'LOB Assignment',
                'TESTER',
                'DATA_EXECUTIVE',
                3,  -- tester user (from previous logs)
                $1,
                $2,
                $3,
                'Review the attribute and assign an appropriate data owner from your LOB.',
                'Attribute',
                $5::jsonb,
                'Medium',
                'Assigned',
                $4,
                $4,
                $4,
                3,
                3
            )
            RETURNING assignment_id
        '''), {
            'to_user_id': cdo.user_id,
            'title': f"Assign Data Owner - {attr.attribute_name} ({lob.lob_name})",
            'description': f"Identify and assign data owner for {attr.attribute_name} in {lob.lob_name}",
            'context_data': json.dumps(context_data),
            'now': datetime.utcnow()
        })
        
        assignment_id = result.scalar()
        await db.commit()
        
        print(f"  Created assignment: {assignment_id}")
        print("\n✅ Success! Created 1 assignment as expected:")
        print(f"   - Attribute: {attr.attribute_name}")
        print(f"   - LOB: {lob.lob_name}")
        print(f"   - Assigned to: {cdo.first_name} {cdo.last_name}")
    
    await engine.dispose()

asyncio.run(manual_fix())