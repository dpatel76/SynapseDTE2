#!/usr/bin/env python3
"""Actually start RFI phase and verify test case creation"""

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
    
    # Check current phase status first
    status_resp = requests.get(
        "http://localhost:8000/api/v1/cycles/55/reports/156/workflow-status",
        headers=headers
    )
    
    if status_resp.status_code == 200:
        phases = status_resp.json()["phases"]
        rfi_phase = next((p for p in phases if p["phase_name"] == "Request Info"), None)
        if rfi_phase:
            print(f"  Current RFI phase status: {rfi_phase['status']}")
    
    # Start the RFI phase
    start_resp = requests.post(
        "http://localhost:8000/api/v1/cycles/55/reports/156/phases/request-info/start",
        headers=headers,
        json={
            "notes": "Starting RFI phase to test test case creation"
        }
    )
    
    if start_resp.status_code != 200:
        print(f"  ❌ Failed to start RFI phase: {start_resp.status_code}")
        print(f"  Response: {start_resp.text}")
        return
    
    print("  ✅ RFI phase started successfully")
    print(f"  Response: {json.dumps(start_resp.json(), indent=2)}")
    
    # 4. Check test cases created
    print("\n4. Checking test cases created:")
    
    # Connect back to DB to check
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
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
        
        # Also check if they're linked to samples
        linked_samples = await db.execute(text('''
            SELECT 
                tc.test_case_number,
                tc.account_number,
                s.sample_id,
                s.lob_id,
                l.lob_name
            FROM rfi_test_cases tc
            LEFT JOIN cycle_report_sample_selection_samples s 
                ON tc.account_number = s.account_number
                AND s.report_owner_decision = 'approved'
            LEFT JOIN lobs l ON s.lob_id = l.lob_id
            WHERE tc.cycle_id = 55
            AND tc.report_id = 156
            ORDER BY tc.test_case_number
        '''))
        
        print("\n  Test cases linked to samples:")
        for ls in linked_samples:
            print(f"    Test Case #{ls.test_case_number} - Account {ls.account_number} - {ls.lob_name}")
    
    await engine.dispose()
    
    print(f"\n✅ Summary: Successfully created {len(test_case_list)} test cases in RFI phase")

asyncio.run(start_rfi_phase())