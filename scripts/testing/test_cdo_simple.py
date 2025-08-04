#!/usr/bin/env python3
"""Simple test for CDO dashboard data"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")

def test_cdo_data():
    """Test CDO data"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        print("=== Testing CDO Dashboard Data ===\n")
        
        # 1. Check assignments
        cur.execute("SELECT COUNT(*) FROM data_provider_assignments WHERE cdo_id = 5")
        count = cur.fetchone()[0]
        print(f"1. Total assignments for CDO 5: {count}")
        
        # 2. Get assignment details with all joins
        cur.execute("""
            SELECT 
                dpa.assignment_id,
                dpa.cycle_id,
                dpa.report_id,
                dpa.attribute_id,
                dpa.status,
                ra.attribute_name,
                tc.cycle_name,
                r.report_name,
                u.first_name || ' ' || u.last_name as data_provider_name
            FROM data_provider_assignments dpa
            LEFT JOIN report_attributes ra ON (
                dpa.attribute_id = ra.attribute_id 
                AND dpa.cycle_id = ra.cycle_id 
                AND dpa.report_id = ra.report_id
            )
            LEFT JOIN test_cycles tc ON dpa.cycle_id = tc.cycle_id
            LEFT JOIN reports r ON dpa.report_id = r.report_id
            LEFT JOIN users u ON dpa.data_provider_id = u.user_id
            WHERE dpa.cdo_id = 5
        """)
        
        assignments = cur.fetchall()
        print(f"\n2. Assignment details with joins:")
        for a in assignments:
            print(f"   Assignment {a[0]}:")
            print(f"     - Cycle: {a[6]} (ID: {a[1]})")
            print(f"     - Report: {a[7]} (ID: {a[2]})")
            print(f"     - Attribute: {a[5]} (ID: {a[3]})")
            print(f"     - Data Provider: {a[8]}")
            print(f"     - Status: {a[4]}")
            print()
        
        # 3. Check if report_attributes exist
        cur.execute("""
            SELECT COUNT(*) 
            FROM report_attributes 
            WHERE cycle_id = 9 AND report_id = 156
        """)
        attr_count = cur.fetchone()[0]
        print(f"3. Report attributes for cycle 9, report 156: {attr_count}")
        
        # 4. Check specific attributes
        cur.execute("""
            SELECT attribute_id, attribute_name, is_primary_key
            FROM report_attributes
            WHERE attribute_id IN (274, 306)
        """)
        attrs = cur.fetchall()
        print(f"\n4. Specific attributes (274, 306):")
        for a in attrs:
            print(f"   - ID {a[0]}: {a[1]} (PK: {a[2]})")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_cdo_data()