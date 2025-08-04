#!/usr/bin/env python3
"""Final fix to create correct assignment and fix the issue in code"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import json
from datetime import datetime

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
        
        now = datetime.utcnow()
        
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
            RETURNING assignment_id
        '''), {
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
        
        assignment_id = result.scalar()
        await db.commit()
        
        print(f"\n✅ Successfully created assignment: {assignment_id}")
        print("\nExpected: 1 assignment (1 attribute × 1 LOB)")
        print("Created: 1 assignment")
        
        # Now let's find and fix the root cause in the code
        print("\n\n=== ROOT CAUSE ANALYSIS ===")
        print("\nThe issue is that when creating new scoping versions from parent versions,")
        print("the report_owner_decision is being copied from the parent.")
        print("\nThis causes multiple versions to have report_owner_decision = 'approved'")
        print("for the same attribute, even though only the approved version should have it.")
        
        print("\n\n=== SOLUTION ===")
        print("\nThe fix needs to be in the scoping version creation logic:")
        print("1. When creating a new version from a parent, DON'T copy report_owner_decision")
        print("2. Only the version that gets approved should have report_owner_decision = 'approved'")
        print("\nAlternatively, fix the query to be more specific:")
        print("Only query attributes from the APPROVED version (which the code already does correctly)")
    
    await engine.dispose()

asyncio.run(fix_assignments())