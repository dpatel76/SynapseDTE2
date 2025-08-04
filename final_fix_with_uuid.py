#!/usr/bin/env python3
"""Final fix with proper UUID generation"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import json
from datetime import datetime
import uuid

async def fix_assignments():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        print("=== FINAL FIX ===")
        
        # First, clear any existing assignments
        result = await db.execute(text('''
            DELETE FROM universal_assignments
            WHERE assignment_type = 'LOB Assignment'
            AND context_type = 'Attribute'
            AND context_data->>'cycle_id' = '55'
            AND context_data->>'report_id' = '156'
        '''))
        print(f"Cleared {result.rowcount} existing assignments")
        
        # Create the correct single assignment
        context_data = {
            "cycle_id": 55,
            "report_id": 156,
            "attribute_id": "3483880c-4e1a-4311-9dfd-4d0dc72918ea",  # Current Credit limit from approved version
            "attribute_name": "Current Credit limit",
            "lob_id": 338,
            "lob_name": "GBM",
            "phase_name": "Data Provider ID"
        }
        
        assignment_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        result = await db.execute(text('''
            INSERT INTO universal_assignments (
                assignment_id,
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
                :assignment_id::uuid,
                :assignment_type,
                :from_role,
                :to_role,
                :from_user_id,
                :to_user_id,
                :title,
                :description,
                :task_instructions,
                :context_type,
                :context_data,
                :priority,
                :status,
                :assigned_at,
                :created_at,
                :updated_at,
                :created_by_id,
                :updated_by_id
            )
        '''), {
            'assignment_id': assignment_id,
            'assignment_type': 'LOB Assignment',
            'from_role': 'TESTER',
            'to_role': 'DATA_EXECUTIVE',
            'from_user_id': 3,
            'to_user_id': 5,  # David Brown (Data Executive for GBM)
            'title': 'Assign Data Owner - Current Credit limit (GBM)',
            'description': 'Identify and assign data owner for Current Credit limit in GBM',
            'task_instructions': 'Review the attribute and assign an appropriate data owner from your LOB.',
            'context_type': 'Attribute',
            'context_data': json.dumps(context_data),
            'priority': 'Medium',
            'status': 'Assigned',
            'assigned_at': now,
            'created_at': now,
            'updated_at': now,
            'created_by_id': 3,
            'updated_by_id': 3
        })
        
        await db.commit()
        
        print(f"\n✅ Successfully created assignment: {assignment_id}")
        print("\nExpected: 1 assignment (1 attribute × 1 LOB)")
        print("Created: 1 assignment")
        
        # Verify the assignment was created
        verify = await db.execute(text('''
            SELECT 
                assignment_id,
                title,
                context_data->>'attribute_name' as attribute_name,
                context_data->>'lob_name' as lob_name,
                to_user_id
            FROM universal_assignments
            WHERE assignment_type = 'LOB Assignment'
            AND context_type = 'Attribute'
            AND context_data->>'cycle_id' = '55'
            AND context_data->>'report_id' = '156'
        '''))
        
        print("\nVerification:")
        for row in verify:
            print(f"  Assignment {row.assignment_id}:")
            print(f"    Attribute: {row.attribute_name}")
            print(f"    LOB: {row.lob_name}")
            print(f"    Assigned to user: {row.to_user_id}")
    
    await engine.dispose()

asyncio.run(fix_assignments())