#!/usr/bin/env python3
"""
Comprehensive script to clean up all test cycle related data from the database.
This will remove all test cycles and ALL related data to start fresh.
"""

import os
from dotenv import load_dotenv
import psycopg2
import sys

load_dotenv()

def cleanup_test_cycles():
    """Remove all test cycle related data from the database"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        sys.exit(1)
    
    # Convert async URL to sync URL if needed
    if database_url.startswith('postgresql+asyncpg://'):
        database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    # Connect to database with autocommit
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        print("\n=== Comprehensive Test Cycle Data Cleanup ===\n")
        
        # Get list of all tables that reference test_cycles
        cur.execute("""
            SELECT DISTINCT tc.table_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
              AND ccu.table_name = 'test_cycles'
              AND tc.table_schema = 'public'
            ORDER BY tc.table_name;
        """)
        
        dependent_tables = [row[0] for row in cur.fetchall()]
        
        print(f"Found {len(dependent_tables)} tables that depend on test_cycles")
        print("\nStarting cleanup...\n")
        
        # Delete from all dependent tables first
        total_deleted = 0
        for table in dependent_tables:
            try:
                cur.execute(f"DELETE FROM {table}")
                count = cur.rowcount
                if count > 0:
                    print(f"✓ Deleted {count} records from {table}")
                    total_deleted += count
            except psycopg2.errors.UndefinedTable:
                print(f"  Skipped {table} (table doesn't exist)")
            except Exception as e:
                print(f"⚠️  Error deleting from {table}: {str(e)}")
        
        # Now delete from test_cycles itself
        try:
            cur.execute("DELETE FROM test_cycles")
            count = cur.rowcount
            print(f"\n✓ Deleted {count} test cycles")
            total_deleted += count
        except Exception as e:
            print(f"\n⚠️  Error deleting test_cycles: {str(e)}")
        
        print(f"\n✅ Cleanup completed! Deleted {total_deleted} total records.")
        
        # Verify test_cycles is empty
        cur.execute("SELECT COUNT(*) FROM test_cycles")
        remaining = cur.fetchone()[0]
        
        if remaining == 0:
            print("\n🎉 All test cycle data has been successfully removed!")
            print("\nThe system is now clean and ready for fresh data.")
            print("\nNext steps:")
            print("1. Log in as test.manager@example.com")
            print("2. Navigate to 'Test Cycles' from the menu")
            print("3. Click 'Create New Cycle' and enter:")
            print("   - Cycle Name: e.g., 'Q1 2025 Regulatory Testing'")
            print("   - Start/End dates")
            print("   - Description")
            print("4. Add reports to the cycle")
            print("5. Assign testers to reports")
            print("\nThe dashboard will now show:")
            print("- Real cycle counts")
            print("- Actual at-risk reports (0 initially)")
            print("- True workflow progress as testers complete phases")
            print("- Accurate observations as they are created")
        else:
            print(f"\n⚠️  WARNING: {remaining} test cycles still remain!")
            print("Some foreign key constraints may still be preventing deletion.")
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    cleanup_test_cycles()