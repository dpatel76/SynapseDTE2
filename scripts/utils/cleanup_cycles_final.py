#!/usr/bin/env python3
"""
Script to clean up all test cycle related data from the database.
This will remove all test cycles and related data to start fresh.
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
    
    # Connect to database with autocommit for better control
    conn = psycopg2.connect(database_url)
    conn.autocommit = True  # Each statement commits immediately
    cur = conn.cursor()
    
    try:
        print("\n=== Starting Test Cycle Data Cleanup ===\n")
        
        # List of tables to clean in dependency order
        cleanup_sequence = [
            # Tables that depend on others go first
            ('observations', 'observation cleanup'),
            ('observation_groups', 'observation group cleanup'),
            ('test_execution_results', 'test execution results cleanup'),
            ('test_executions', 'test execution cleanup'),
            ('workflow_phase_transitions', 'workflow transition cleanup'),
            ('workflow_phases', 'workflow phase cleanup'),
            ('cycle_report_assignments', 'cycle assignment cleanup'),
            ('cycle_reports', 'cycle report cleanup'),
            ('test_cycles', 'test cycle cleanup'),
        ]
        
        print("Current data counts:")
        for table, _ in cleanup_sequence:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {table}: {count}")
            except psycopg2.errors.UndefinedTable:
                print(f"  {table}: (table doesn't exist)")
        
        print("\n⚠️  Proceeding with cleanup...\n")
        
        # Execute cleanup
        for table, description in cleanup_sequence:
            try:
                cur.execute(f"DELETE FROM {table}")
                count = cur.rowcount
                if count > 0:
                    print(f"✓ Deleted {count} records from {table}")
                else:
                    print(f"  {table} was already empty")
            except psycopg2.errors.UndefinedTable:
                print(f"  Skipped {table} (table doesn't exist)")
            except Exception as e:
                print(f"⚠️  Error deleting from {table}: {str(e)}")
        
        # Also clean up LLM audit logs
        try:
            cur.execute("DELETE FROM llm_audit_logs WHERE context_type = 'test_cycle'")
            count = cur.rowcount
            if count > 0:
                print(f"✓ Deleted {count} test cycle related LLM audit logs")
        except psycopg2.errors.UndefinedTable:
            pass
        
        print("\n✅ Cleanup completed!")
        print("\nVerifying cleanup...")
        
        # Verify cleanup
        all_clean = True
        for table, _ in cleanup_sequence:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                if count > 0:
                    print(f"  ❌ {table}: {count} records remaining")
                    all_clean = False
                else:
                    print(f"  ✅ {table}: clean")
            except psycopg2.errors.UndefinedTable:
                print(f"  ✅ {table}: (doesn't exist)")
        
        if all_clean:
            print("\n🎉 All test cycle data has been successfully removed!")
            print("\nYou can now start fresh with new test cycles.")
            print("\nNext steps:")
            print("1. Log in as test.manager@example.com") 
            print("2. Navigate to Test Cycles page")
            print("3. Create a new test cycle (e.g., 'Q1 2025 Testing')")
            print("4. Add reports to the cycle and assign testers")
            print("5. The dashboard will show real data based on actual workflow progress")
            print("\nRemember: The visualization will update as testers progress through phases!")
        else:
            print("\n⚠️  Some data remains. This might be due to foreign key constraints.")
            print("You may need to manually investigate and clean up remaining data.")
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    cleanup_test_cycles()