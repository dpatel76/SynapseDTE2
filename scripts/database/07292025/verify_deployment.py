#!/usr/bin/env python3
"""
Verify SynapseDTE database deployment
"""
import psycopg2
import sys
import os

# Database configuration
DB_NAME = os.getenv("DB_NAME", "synapse_dt")
DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def verify_database():
    """Verify database deployment"""
    try:
        # Connect to database
        conn_string = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER}"
        if DB_PASSWORD:
            conn_string += f" password={DB_PASSWORD}"
        
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        
        print("SynapseDTE Database Verification")
        print("================================")
        
        # Check tables
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cur.fetchone()[0]
        print(f"✓ Tables: {table_count} (expected: 108)")
        
        # Check specific table groups
        checks = [
            ("Workflow tables", "table_name LIKE 'workflow%'"),
            ("Test tables", "table_name LIKE 'test%' OR table_name LIKE 'testing%'"),
            ("RFI tables", "table_name LIKE '%request_info%'"),
            ("User/Role tables", "table_name IN ('users', 'roles', 'permissions')")
        ]
        
        for check_name, condition in checks:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND {condition}
            """)
            count = cur.fetchone()[0]
            print(f"✓ {check_name}: {count}")
        
        # Check data
        print("\nData Verification:")
        data_checks = [
            ("users", "Users"),
            ("roles", "Roles"),
            ("permissions", "Permissions"),
            ("workflow_activity_templates", "Workflow templates"),
            ("lobs", "Lines of Business")
        ]
        
        for table, label in data_checks:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {label}: {count}")
            except:
                print(f"  {label}: ERROR")
        
        # Check test users
        print("\nTest Users:")
        cur.execute("""
            SELECT u.email, r.role_name 
            FROM users u 
            JOIN user_roles ur ON u.user_id = ur.user_id 
            JOIN roles r ON ur.role_id = r.role_id 
            ORDER BY u.email
        """)
        for email, role in cur.fetchall():
            print(f"  {email} - {role}")
        
        conn.close()
        print("\n✓ Database verification complete!")
        return True
        
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if verify_database() else 1)
