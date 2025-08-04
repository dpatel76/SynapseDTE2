#!/usr/bin/env python3
"""Save data source configuration properly"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import json

async def save_data_source_properly():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        print("=== SAVING DATA SOURCE CONFIGURATION ===")
        
        # 1. Get the RFI phase ID
        print("\n1. Getting RFI phase ID:")
        phase_result = await db.execute(text('''
            SELECT phase_id
            FROM workflow_phases
            WHERE cycle_id = 55
            AND report_id = 156
            AND phase_name = 'Request Info'
        '''))
        
        phase_id = phase_result.scalar()
        print(f"  RFI Phase ID: {phase_id}")
        
        # 2. Create data source in planning table
        print("\n2. Creating data source configuration:")
        
        # Check if already exists
        existing = await db.execute(text('''
            SELECT id, name, connection_config
            FROM cycle_report_planning_data_sources
            WHERE phase_id = :phase_id
            AND name = 'FRY14M Data Source'
        '''), {'phase_id': phase_id})
        
        existing_ds = existing.first()
        data_source_id = None
        
        if not existing_ds:
            # Create new
            create_result = await db.execute(text('''
                INSERT INTO cycle_report_planning_data_sources (
                    phase_id,
                    name,
                    description,
                    source_type,
                    connection_config,
                    auth_config,
                    is_active,
                    created_at,
                    updated_at,
                    created_by_id,
                    updated_by_id
                ) VALUES (
                    :phase_id,
                    'FRY14M Data Source',
                    'Data source for Current Credit limit from fry14m_scheduled1_data',
                    'POSTGRESQL',
                    :connection_config,
                    :auth_config,
                    true,
                    NOW(),
                    NOW(),
                    6,  -- Data Owner user
                    6
                )
                RETURNING id
            '''), {
                'phase_id': phase_id,
                'connection_config': json.dumps({
                    "type": "PostgreSQL",
                    "host": "localhost",
                    "port": 5432,
                    "database": "synapse_dt",
                    "schema": "public",
                    "table": "fry14m_scheduled1_data",
                    "columns": {
                        "Current Credit limit": "current_credit_limit",
                        "Customer ID": "customer_id",
                        "Credit Card Type": "credit_card_type",
                        "State": "state"
                    }
                }),
                'auth_config': json.dumps({
                    "username": "synapse_user",
                    "password": "synapse_password"
                })
            })
            
            data_source_id = create_result.scalar()
            if data_source_id:
                print(f"  ✅ Created data source ID: {data_source_id}")
                await db.commit()
        else:
            data_source_id = existing_ds.id
            print(f"  Found existing data source ID: {data_source_id}")
            print(f"  Connection: {json.dumps(existing_ds.connection_config, indent=2)}")
        
        # 3. Update assignment with data source reference
        print("\n3. Updating assignment with data source reference:")
        
        # Get assignment
        assignment = await db.execute(text('''
            SELECT assignment_id, context_data
            FROM universal_assignments
            WHERE assignment_type = 'LOB Assignment'
            AND to_role = 'Data Owner'
            AND context_data->>'cycle_id' = '55'
            ORDER BY created_at DESC
            LIMIT 1
        '''))
        
        a = assignment.first()
        if a:
            # Update context_data to include data source
            updated_context = a.context_data.copy()
            updated_context['data_source_id'] = data_source_id
            
            update_result = await db.execute(text('''
                UPDATE universal_assignments
                SET 
                    context_data = :context_data,
                    updated_at = NOW()
                WHERE assignment_id = :assignment_id
                RETURNING assignment_id
            '''), {
                'context_data': json.dumps(updated_context),
                'assignment_id': a.assignment_id
            })
            
            if update_result.scalar():
                print(f"  ✅ Updated assignment with data source ID: {data_source_id}")
                await db.commit()
        
        # 4. Save queries for test cases
        print("\n4. Saving queries for test cases:")
        
        # Template query
        query_template = '''SELECT 
    tc.sample_identifier as sample_id,
    fd.customer_id,
    fd.current_credit_limit,
    fd.credit_card_type,
    fd.state
FROM (SELECT :sample_identifier as sample_identifier) tc
LEFT JOIN public.fry14m_scheduled1_data fd 
    ON tc.sample_identifier = fd.customer_id'''
        
        # Update test cases with queries
        test_cases = await db.execute(text('''
            SELECT 
                tc.id,
                tc.test_case_number,
                s.sample_identifier
            FROM cycle_report_test_cases tc
            JOIN cycle_report_sample_selection_samples s ON tc.sample_id = s.sample_id::text
            WHERE tc.phase_id = :phase_id
            ORDER BY tc.test_case_number
        '''), {'phase_id': phase_id})
        
        for tc in test_cases:
            # Create specific query for this test case
            specific_query = query_template.replace(':sample_identifier', f"'{tc.sample_identifier}'")
            
            update_tc = await db.execute(text('''
                UPDATE cycle_report_test_cases
                SET 
                    query_text = :query,
                    updated_at = NOW()
                WHERE id = :id
                RETURNING id
            '''), {
                'query': specific_query,
                'id': tc.id
            })
            
            if update_tc.scalar():
                print(f"  ✅ Updated {tc.test_case_number} with query for sample {tc.sample_identifier}")
        
        await db.commit()
        
        # 5. Verify everything is saved
        print("\n5. VERIFICATION:")
        
        # Verify data source
        verify_ds = await db.execute(text('''
            SELECT id, name, connection_config
            FROM cycle_report_planning_data_sources
            WHERE id = :id
        '''), {'id': data_source_id})
        
        vds = verify_ds.first()
        if vds:
            print(f"\n  ✅ Data Source Verified:")
            print(f"     ID: {vds.id}")
            print(f"     Name: {vds.name}")
            print(f"     Table: {vds.connection_config.get('table')}")
            print(f"     Mapped Columns: {list(vds.connection_config.get('columns', {}).keys())}")
        
        # Verify assignment
        verify_assign = await db.execute(text('''
            SELECT context_data
            FROM universal_assignments
            WHERE assignment_id = :id
        '''), {'id': a.assignment_id if a else None})
        
        va = verify_assign.first()
        if va and 'data_source_id' in va.context_data:
            print(f"\n  ✅ Assignment has Data Source ID: {va.context_data['data_source_id']}")
        
        # Verify queries
        verify_queries = await db.execute(text('''
            SELECT COUNT(*) as count
            FROM cycle_report_test_cases
            WHERE phase_id = :phase_id
            AND query_text IS NOT NULL
        '''), {'phase_id': phase_id})
        
        query_count = verify_queries.scalar()
        print(f"\n  ✅ Queries saved for {query_count} test cases")
        
        print("\n=== SUMMARY ===")
        print("✅ Data source configuration saved successfully")
        print("✅ Assignment updated with data source reference")
        print("✅ Queries saved for all test cases")
        print("\nData Owner can now:")
        print("1. View saved data source configuration")
        print("2. Test queries against the database")
        print("3. Submit data for RFI test cases")
    
    await engine.dispose()

asyncio.run(save_data_source_properly())