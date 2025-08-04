#!/usr/bin/env python3
"""Check for synapse.com users"""

import psycopg2
from psycopg2.extras import RealDictCursor

def check_users():
    conn = psycopg2.connect(
        host="localhost",
        database="synapse_dt",
        user="postgres",
        password="postgres"
    )
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check for synapse.com users
    cur.execute("""
        SELECT 
            u.user_id,
            u.email,
            u.first_name,
            u.last_name,
            r.role_name
        FROM users u
        LEFT JOIN user_roles ur ON u.user_id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.role_id
        WHERE u.email LIKE '%synapse.com%'
        ORDER BY u.user_id
    """)
    
    users = cur.fetchall()
    
    print("\nUsers with @synapse.com emails:")
    print("="*80)
    for user in users:
        print(f"{user['user_id']:3d} | {user['email']:30s} | {user['first_name']:10s} {user['last_name']:10s} | {user['role_name'] or 'No Role':20s}")
    
    # Check who owns cycle 13, report 156
    print("\n\nChecking who is assigned to Cycle 13, Report 156:")
    print("="*80)
    
    cur.execute("""
        SELECT 
            cr.cycle_id,
            cr.report_id,
            cr.tester_id,
            u.email as tester_email,
            u.first_name || ' ' || u.last_name as tester_name
        FROM cycle_reports cr
        LEFT JOIN users u ON cr.tester_id = u.user_id
        WHERE cr.cycle_id = 13 AND cr.report_id = 156
    """)
    
    assignment = cur.fetchone()
    if assignment:
        print(f"Tester ID: {assignment['tester_id']}")
        print(f"Tester Email: {assignment['tester_email']}")
        print(f"Tester Name: {assignment['tester_name']}")
    else:
        print("No assignment found")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_users()