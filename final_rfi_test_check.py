#!/usr/bin/env python3
"""Final check for RFI test cases with correct table structure"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def final_check():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        print("=== FINAL RFI TEST CASE CHECK ===")
        
        # 1. Get all columns for test cases table
        print("\n1. Full structure of cycle_report_test_cases:")
        columns = await db.execute(text('''
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'cycle_report_test_cases'
            ORDER BY ordinal_position
        '''))
        
        all_columns = list(columns)
        print(f"  Total columns: {len(all_columns)}")
        
        # Check if there's a cycle_id column
        has_cycle_id = any(c.column_name == 'cycle_id' for c in all_columns)
        has_report_id = any(c.column_name == 'report_id' for c in all_columns)
        
        print(f"  Has cycle_id: {has_cycle_id}")
        print(f"  Has report_id: {has_report_id}")
        
        # 2. Check test cases using phase_id
        print("\n2. Checking test cases by phase_id:")
        
        # First get the RFI phase_id
        phase_result = await db.execute(text('''
            SELECT phase_id, status, state
            FROM workflow_phases
            WHERE cycle_id = 55
            AND report_id = 156
            AND phase_name = 'Request Info'
        '''))
        
        phase = phase_result.first()
        if phase:
            print(f"  RFI Phase ID: {phase.phase_id}")
            print(f"  Status: {phase.status}, State: {phase.state}")
            
            # Check test cases for this phase
            test_cases = await db.execute(text('''
                SELECT 
                    id,
                    test_case_number,
                    test_case_name,
                    sample_id,
                    status,
                    created_at
                FROM cycle_report_test_cases
                WHERE phase_id = :phase_id
                ORDER BY test_case_number
            '''), {'phase_id': phase.phase_id})
            
            tc_list = list(test_cases)
            print(f"\n  Found {len(tc_list)} test cases for RFI phase:")
            
            for tc in tc_list:
                print(f"\n  Test Case #{tc.test_case_number}:")
                print(f"    ID: {tc.id}")
                print(f"    Name: {tc.test_case_name}")
                print(f"    Sample ID: {tc.sample_id}")
                print(f"    Status: {tc.status}")
        
        # 3. Check approved samples that should have become test cases
        print("\n3. Checking approved samples:")
        
        # Get sample selection phase
        sample_phase_result = await db.execute(text('''
            SELECT phase_id
            FROM workflow_phases
            WHERE cycle_id = 55
            AND report_id = 156
            AND phase_name = 'Sample Selection'
            AND status = 'Complete'
        '''))
        
        sample_phase_id = sample_phase_result.scalar()
        
        if sample_phase_id:
            # Get approved version
            version_result = await db.execute(text('''
                SELECT version_id
                FROM cycle_report_sample_selection_versions
                WHERE phase_id = :phase_id
                AND version_status = 'approved'
                ORDER BY version_number DESC
                LIMIT 1
            '''), {'phase_id': sample_phase_id})
            
            version_id = version_result.scalar()
            
            if version_id:
                # Get approved samples
                samples = await db.execute(text('''
                    SELECT 
                        sample_id,
                        account_number,
                        lob_id
                    FROM cycle_report_sample_selection_samples
                    WHERE version_id = :version_id
                    AND report_owner_decision = 'approved'
                    ORDER BY account_number
                '''), {'version_id': version_id})
                
                sample_list = list(samples)
                print(f"  Found {len(sample_list)} approved samples")
                
                for s in sample_list:
                    print(f"    Sample {s.sample_id}: Account {s.account_number}")
        
        # 4. Summary
        print("\n4. SUMMARY:")
        if phase and phase.status == 'In Progress':
            if len(tc_list) == 4:
                print("  ✅ SUCCESS: RFI phase is in progress and has 4 test cases!")
            else:
                print(f"  ⚠️  RFI phase is in progress but has {len(tc_list)} test cases (expected 4)")
        else:
            print("  ⚠️  RFI phase needs to be started to create test cases")
            print("\n  To start RFI phase manually, run:")
            print("  UPDATE workflow_phases SET status='In Progress', state='In Progress', actual_start_date=NOW()")
            print("  WHERE cycle_id=55 AND report_id=156 AND phase_name='Request Info';")
    
    await engine.dispose()

asyncio.run(final_check())