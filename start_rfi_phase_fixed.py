#!/usr/bin/env python3
"""Actually start RFI phase and verify test case creation - fixed version"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import requests
import json

async def start_rfi_phase():
    # First, let's complete the Data Owner ID phase since it's a prerequisite
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        print("=== PREPARING TO START RFI PHASE ===")
        
        # 1. First complete the Data Owner ID phase (bypass the normal flow for testing)
        print("\n1. Completing Data Owner ID phase (for testing):")
        
        # Update the phase to complete
        await db.execute(text('''
            UPDATE workflow_phases
            SET status = 'Complete',
                state = 'Complete',
                actual_end_date = NOW()
            WHERE cycle_id = 55
            AND report_id = 156
            AND phase_name = 'Data Provider ID'
        '''))
        
        # Mark the assignment as completed
        await db.execute(text('''
            UPDATE universal_assignments
            SET status = 'Completed',
                completed_at = NOW()
            WHERE assignment_type = 'LOB Assignment'
            AND context_type = 'Attribute'
            AND context_data->>'cycle_id' = '55'
            AND context_data->>'report_id' = '156'
        '''))
        
        await db.commit()
        print("  ✅ Data Owner ID phase marked as complete")
    
    await engine.dispose()
    
    # 2. Get auth token
    print("\n2. Getting auth token:")
    login_resp = requests.post("http://localhost:8000/api/v1/auth/login", json={
        "email": "tester@example.com",
        "password": "password123"
    })
    
    if login_resp.status_code != 200:
        print(f"  ❌ Login failed: {login_resp.status_code}")
        return
        
    token = login_resp.json()["access_token"]
    print("  ✅ Got auth token")
    
    # 3. Start RFI phase
    print("\n3. Starting RFI phase:")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try different endpoint variations
    endpoints = [
        "http://localhost:8000/api/v1/cycles/55/reports/156/phases/request-info/start",
        "http://localhost:8000/api/v1/cycles/55/reports/156/rfi/start",
        "http://localhost:8000/api/v1/test-cycles/55/reports/156/phases/rfi/start"
    ]
    
    start_resp = None
    for endpoint in endpoints:
        print(f"\n  Trying endpoint: {endpoint}")
        start_resp = requests.post(
            endpoint,
            headers=headers,
            json={
                "notes": "Starting RFI phase to test test case creation"
            }
        )
        
        if start_resp.status_code == 200:
            print("  ✅ RFI phase started successfully")
            print(f"  Response: {json.dumps(start_resp.json(), indent=2)}")
            break
        else:
            print(f"  ❌ Failed with status {start_resp.status_code}")
            if start_resp.status_code == 404:
                continue
            else:
                print(f"  Response: {start_resp.text}")
    
    if not start_resp or start_resp.status_code != 200:
        print("\n  Trying to start via workflow orchestrator...")
        
        # Try using the workflow orchestrator endpoint
        orchestrator_resp = requests.post(
            "http://localhost:8000/api/v1/cycles/55/reports/156/workflow/update-phase-state",
            headers=headers,
            json={
                "phase_name": "Request Info",
                "new_state": "In Progress",
                "notes": "Starting RFI phase to test test case creation"
            }
        )
        
        if orchestrator_resp.status_code == 200:
            print("  ✅ RFI phase started via workflow orchestrator")
        else:
            print(f"  ❌ Workflow orchestrator failed: {orchestrator_resp.status_code}")
            print(f"  Response: {orchestrator_resp.text}")
    
    # 4. Check test cases created
    print("\n4. Checking test cases created:")
    
    # Connect back to DB to check
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        # First check if rfi_test_cases table exists
        table_check = await db.execute(text('''
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'rfi_test_cases'
            )
        '''))
        
        if not table_check.scalar():
            print("  ⚠️  rfi_test_cases table doesn't exist")
            
            # Check alternative tables
            print("\n  Checking alternative RFI-related tables:")
            
            # Check for RFI evidence or questions
            tables = await db.execute(text('''
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name LIKE '%rfi%' 
                OR table_name LIKE '%request%info%'
                ORDER BY table_name
            '''))
            
            for t in tables:
                print(f"    - {t.table_name}")
            
            # Check universal assignments for RFI
            rfi_assignments = await db.execute(text('''
                SELECT 
                    assignment_id,
                    assignment_type,
                    title,
                    context_data,
                    status,
                    created_at
                FROM universal_assignments
                WHERE context_data->>'cycle_id' = '55'
                AND context_data->>'report_id' = '156'
                AND (
                    assignment_type LIKE '%RFI%' 
                    OR assignment_type LIKE '%Request%'
                    OR context_data->>'phase_name' LIKE '%Request%'
                )
                ORDER BY created_at DESC
            '''))
            
            rfi_list = list(rfi_assignments)
            print(f"\n  Found {len(rfi_list)} RFI-related assignments:")
            
            for ra in rfi_list:
                print(f"\n  Assignment: {ra.title}")
                print(f"    Type: {ra.assignment_type}")
                print(f"    Status: {ra.status}")
                print(f"    Context: {json.dumps(ra.context_data, indent=6)}")
            
        else:
            # Check RFI test cases
            test_cases = await db.execute(text('''
                SELECT 
                    tc.test_case_id,
                    tc.test_case_number,
                    tc.account_number,
                    tc.status,
                    tc.created_at
                FROM rfi_test_cases tc
                WHERE tc.cycle_id = 55
                AND tc.report_id = 156
                ORDER BY tc.test_case_number
            '''))
            
            test_case_list = list(test_cases)
            print(f"\n  Found {len(test_case_list)} test cases:")
            
            for tc in test_case_list:
                print(f"\n  Test Case #{tc.test_case_number}:")
                print(f"    ID: {tc.test_case_id}")
                print(f"    Account: {tc.account_number}")
                print(f"    Status: {tc.status}")
                print(f"    Created: {tc.created_at}")
        
        # Check the RFI phase status
        rfi_phase = await db.execute(text('''
            SELECT 
                phase_id,
                phase_name,
                status,
                state,
                actual_start_date
            FROM workflow_phases
            WHERE cycle_id = 55
            AND report_id = 156
            AND phase_name = 'Request Info'
        '''))
        
        phase = rfi_phase.first()
        if phase:
            print(f"\n  RFI Phase Status: {phase.status} ({phase.state})")
            print(f"  Started at: {phase.actual_start_date}")
    
    await engine.dispose()

asyncio.run(start_rfi_phase())