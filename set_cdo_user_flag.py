#!/usr/bin/env python3
"""
Set is_cdo flag for cdo@example.com
"""

import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("🔧 SETTING CDO FLAG FOR cdo@example.com")
    print("=" * 60)
    
    # Update cdo@example.com to have is_cdo = true
    cursor.execute("""
        UPDATE users 
        SET is_cdo = TRUE 
        WHERE email = 'cdo@example.com'
    """)
    
    rows_updated = cursor.rowcount
    conn.commit()
    
    if rows_updated > 0:
        print(f"✅ Updated cdo@example.com to have is_cdo = TRUE")
    else:
        print(f"❌ User cdo@example.com not found")
    
    # Also remove is_cdo from tester user
    cursor.execute("""
        UPDATE users 
        SET is_cdo = FALSE 
        WHERE email = 'tester@example.com'
    """)
    conn.commit()
    print(f"✅ Removed is_cdo flag from tester@example.com")
    
    # Verify the update
    cursor.execute("""
        SELECT user_id, email, first_name, last_name, role, is_cdo
        FROM users
        WHERE email IN ('cdo@example.com', 'tester@example.com')
        ORDER BY user_id
    """)
    
    users = cursor.fetchall()
    print("\n📋 Updated users:")
    for user in users:
        print(f"  ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Name: {user[2]} {user[3]}")
        print(f"  Role: {user[4]}")
        print(f"  Is CDO: {user[5]}")
        print()
    
    print("⚠️  Note: The user will need to log out and log back in to get a new token with CDO permissions")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()