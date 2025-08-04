#!/usr/bin/env python3
"""Check raw phase data from database"""

import psycopg2
import json
from psycopg2.extras import RealDictCursor

def check_phase_data():
    conn = psycopg2.connect(
        host="localhost",
        database="synapse_dt",
        user="postgres",
        password="postgres"
    )
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get phase data directly from database
    cur.execute("""
        SELECT phase_data
        FROM workflow_phases
        WHERE cycle_id = 13 
        AND report_id = 156 
        AND phase_name = 'Sample Selection'
    """)
    
    result = cur.fetchone()
    
    if result and result['phase_data']:
        phase_data = result['phase_data']
        samples = phase_data.get('samples', [])
        
        print(f"\nTotal samples in database: {len(samples)}\n")
        
        # Look for S007 and S009
        for sample in samples:
            if sample.get('sample_id') in ['C13_R156_S007', 'C13_R156_S009']:
                print(f"Sample {sample['sample_id']}:")
                print(f"  Tester Decision: {sample.get('tester_decision', 'None')}")
                print(f"  Report Owner Decision: {sample.get('report_owner_decision', 'None')}")
                print(f"  Is Submitted: {sample.get('is_submitted', False)}")
                print(f"  Updated At: {sample.get('updated_at', 'Unknown')}")
                print()
    else:
        print("No phase data found")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_phase_data()