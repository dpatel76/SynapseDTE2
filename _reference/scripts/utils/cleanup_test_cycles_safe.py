#!/usr/bin/env python3
"""
Script to clean up all test cycle related data from the database.
This will remove all test cycles and related data to start fresh.
"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
import sys

load_dotenv()

def safe_delete(cur, conn, table_name):
    """Safely delete from a table, handling cases where the table doesn't exist"""
    try:
        cur.execute(f"DELETE FROM {table_name}")
        count = cur.rowcount
        print(f"Deleted {count} records from {table_name}")
        return count
    except psycopg2.errors.UndefinedTable:
        print(f"  Skipped {table_name} (table doesn't exist)")
        conn.rollback()  # Reset transaction after error
        # Need to create a new cursor after rollback
        return 0

def safe_count(cur, conn, table_name):
    """Safely count records in a table"""
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cur.fetchone()[0]
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        return 0

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
    
    # Connect to database
    conn = psycopg2.connect(database_url)
    
    try:
        print("\n=== Starting Test Cycle Data Cleanup ===\n")
        
        # Get counts before deletion
        print("Current data counts:")
        
        cur = conn.cursor()
        
        # Test cycles
        count = safe_count(cur, conn, "test_cycles")
        print(f"  Test cycles: {count}")
        
        # Cycle reports
        count = safe_count(cur, conn, "cycle_reports")
        print(f"  Cycle reports: {count}")
        
        # Workflow phases
        count = safe_count(cur, conn, "workflow_phases")
        print(f"  Workflow phases: {count}")
        
        # Test executions
        count = safe_count(cur, conn, "cycle_report_test_execution_test_executions")
        print(f"  Test executions: {count}")
        
        # Observations
        count = safe_count(cur, conn, "observations")
        print(f"  Observations: {count}")
        
        # Observation groups
        count = safe_count(cur, conn, "observation_groups")
        print(f"  Observation groups: {count}")
        
        print("\n⚠️  Proceeding with cleanup...\n")
        
        print("Deleting data in correct order to respect foreign key constraints...")
        
        # Delete in reverse dependency order
        # Create new cursor for deletions
        cur = conn.cursor()
        
        # 1. Delete observations (depends on observation_groups)
        safe_delete(cur, conn, "observations")
        
        # 2. Delete observation groups (depends on cycle_reports)
        safe_delete(cur, conn, "observation_groups")
        
        # 3. Delete test execution results
        safe_delete(cur, conn, "test_execution_results")
        
        # 4. Delete test executions (depends on workflow_phases)
        safe_delete(cur, conn, "cycle_report_test_execution_test_executions")
        
        # 5. Delete workflow phase transitions
        safe_delete(cur, conn, "workflow_phase_transitions")
        
        # 6. Delete workflow phases (depends on cycle_reports)
        safe_delete(cur, conn, "workflow_phases")
        
        # 7. Delete cycle report assignments if exists
        safe_delete(cur, conn, "cycle_report_assignments")
        
        # 8. Delete cycle reports (depends on test_cycles)
        safe_delete(cur, conn, "cycle_reports")
        
        # 9. Delete test cycles
        safe_delete(cur, conn, "test_cycles")
        
        # 10. Delete any LLM audit logs related to test cycles
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM llm_audit_logs WHERE context_type = 'test_cycle'")
            print(f"Deleted {cur.rowcount} LLM audit logs")
        except psycopg2.errors.UndefinedTable:
            print("  Skipped llm_audit_logs (table doesn't exist)")
            conn.rollback()
        
        # Commit the transaction
        conn.commit()
        
        print("\n✅ Cleanup completed successfully!")
        print("\nVerifying cleanup...")
        
        # Verify all data is deleted
        tables = [
            'test_cycles', 'cycle_reports', 'workflow_phases', 
            'test_executions', 'observations', 'observation_groups'
        ]
        
        cur = conn.cursor()
        all_clean = True
        for table in tables:
            count = safe_count(cur, conn, table)
            if count > 0:
                print(f"  ❌ {table}: {count} records remaining")
                all_clean = False
            else:
                print(f"  ✅ {table}: clean")
        
        if all_clean:
            print("\n🎉 All test cycle data has been successfully removed!")
            print("You can now start fresh with new test cycles.")
            print("\nNext steps:")
            print("1. Log in as test.manager@example.com")
            print("2. Create a new test cycle")
            print("3. Add reports to the cycle")
            print("4. The dashboard will show real data based on actual workflow progress")
        else:
            print("\n⚠️  Some data remains. Please check the tables above.")
            
    except Exception as e:
        print(f"\n❌ Error during cleanup: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_test_cycles()