#!/usr/bin/env python3
"""
Add missing source_test_execution_id column to observation_management_audit_logs table
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
    
    # Add the missing column
    cur.execute("""
        ALTER TABLE cycle_report_observation_mgmt_audit_logss 
        ADD COLUMN IF NOT EXISTS source_test_execution_id INTEGER,
        ADD CONSTRAINT observation_management_audit_logs_source_test_execution_id_fkey 
        FOREIGN KEY (source_test_execution_id) 
        REFERENCES testing_test_executions(execution_id)
    """)
    print('✅ Added source_test_execution_id column to observation_management_audit_logs table')
    
    conn.commit()
    cur.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')