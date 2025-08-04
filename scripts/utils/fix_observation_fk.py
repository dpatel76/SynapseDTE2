#!/usr/bin/env python3
"""
Fix observation foreign key constraint
"""

import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        database='synapse_dt',
        user='synapse_user',
        password='synapse_password'
    )
    
    cur = conn.cursor()
    
    # Drop the incorrect foreign key
    cur.execute("""
        ALTER TABLE cycle_report_observation_mgmt_observation_records 
        DROP CONSTRAINT IF EXISTS observation_records_source_test_execution_id_fkey
    """)
    print('✅ Dropped old foreign key constraint')
    
    # Add the correct foreign key
    cur.execute("""
        ALTER TABLE cycle_report_observation_mgmt_observation_records 
        ADD CONSTRAINT observation_records_source_test_execution_id_fkey 
        FOREIGN KEY (source_test_execution_id) 
        REFERENCES testing_test_executions(execution_id)
    """)
    print('✅ Added correct foreign key constraint')
    
    conn.commit()
    cur.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')