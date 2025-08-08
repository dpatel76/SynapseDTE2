#!/usr/bin/env python3
"""Check available data providers for GBM LOB"""

import psycopg2
from psycopg2.extras import RealDictCursor

def check_data_providers():
    """Check data providers for GBM LOB"""
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/synapse_dt")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # First, get the GBM LOB ID
            cur.execute("SELECT * FROM lobs WHERE lob_name = 'GBM'")
            gbm_lob = cur.fetchone()
            
            if gbm_lob:
                print(f"✅ GBM LOB found:")
                print(f"   - LOB ID: {gbm_lob['lob_id']}")
                print(f"   - LOB Name: {gbm_lob['lob_name']}")
                
                # Check users in GBM LOB
                print(f"\n📋 All users in GBM LOB:")
                cur.execute("""
                    SELECT u.*, r.role_name
                    FROM users u
                    LEFT JOIN user_roles ur ON u.user_id = ur.user_id
                    LEFT JOIN roles r ON ur.role_id = r.role_id
                    WHERE u.lob_id = %s
                    ORDER BY u.user_id
                """, (gbm_lob['lob_id'],))
                
                users = cur.fetchall()
                for user in users:
                    print(f"   - {user['first_name']} {user['last_name']} ({user['email']}) - Role: {user['role_name']}")
                
                # Check specifically for Data Provider role users in GBM
                print(f"\n👥 Users with Data Provider role in GBM LOB:")
                cur.execute("""
                    SELECT u.*
                    FROM users u
                    JOIN user_roles ur ON u.user_id = ur.user_id
                    JOIN roles r ON ur.role_id = r.role_id
                    WHERE u.lob_id = %s
                    AND r.role_name = 'Data Provider'
                    ORDER BY u.user_id
                """, (gbm_lob['lob_id'],))
                
                data_providers = cur.fetchall()
                if data_providers:
                    for dp in data_providers:
                        print(f"   - {dp['first_name']} {dp['last_name']} ({dp['email']})")
                else:
                    print("   ❌ No users with Data Provider role found in GBM LOB")
                
                # Check what the API endpoint might be looking for
                print(f"\n🔍 Checking what role names exist:")
                cur.execute("SELECT DISTINCT role_name FROM roles ORDER BY role_name")
                roles = cur.fetchall()
                for role in roles:
                    print(f"   - {role['role_name']}")
                    
            else:
                print("❌ GBM LOB not found")
            
            # Check the Data Executive (CDO) user
            print(f"\n👤 Data Executive (CDO) details:")
            cur.execute("""
                SELECT u.*, l.lob_name, r.role_name
                FROM users u
                LEFT JOIN lobs l ON u.lob_id = l.lob_id
                LEFT JOIN user_roles ur ON u.user_id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.role_id
                WHERE u.email = 'cdo@example.com'
            """)
            cdo = cur.fetchone()
            if cdo:
                print(f"   - Name: {cdo['first_name']} {cdo['last_name']}")
                print(f"   - Email: {cdo['email']}")
                print(f"   - LOB: {cdo['lob_name']}")
                print(f"   - Role: {cdo['role_name']}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Checking Data Providers for GBM LOB...")
    print("=" * 60)
    check_data_providers()