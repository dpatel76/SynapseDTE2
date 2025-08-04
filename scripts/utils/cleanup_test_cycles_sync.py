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
    cur = conn.cursor()
    
    try:
        print("\n=== Starting Test Cycle Data Cleanup ===\n")
        
        # Get counts before deletion
        print("Current data counts:")
        
        # Test cycles
        cur.execute("SELECT COUNT(*) FROM test_cycles")
        count = cur.fetchone()[0]
        print(f"  Test cycles: {count}")
        
        # Cycle reports
        cur.execute("SELECT COUNT(*) FROM cycle_reports")
        count = cur.fetchone()[0]
        print(f"  Cycle reports: {count}")
        
        # Workflow phases
        cur.execute("SELECT COUNT(*) FROM workflow_phases")
        count = cur.fetchone()[0]
        print(f"  Workflow phases: {count}")
        
        # Test executions
        cur.execute("SELECT COUNT(*) FROM cycle_report_test_execution_test_executions")
        count = cur.fetchone()[0]
        print(f"  Test executions: {count}")
        
        # Observations
        cur.execute("SELECT COUNT(*) FROM observations")
        count = cur.fetchone()[0]
        print(f"  Observations: {count}")
        
        # Observation groups
        cur.execute("SELECT COUNT(*) FROM observation_groups")
        count = cur.fetchone()[0]
        print(f"  Observation groups: {count}")
        
        # Confirmation
        print("\n⚠️  WARNING: This will delete ALL test cycle related data!")
        response = input("Are you sure you want to continue? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Cleanup cancelled.")
            return
        
        print("\nDeleting data in correct order to respect foreign key constraints...")
        
        # Delete in reverse dependency order
        
        # 1. Delete observations (depends on observation_groups)
        cur.execute("DELETE FROM observations")
        print(f"Deleted {cur.rowcount} observations")
        
        # 2. Delete observation groups (depends on cycle_reports)
        cur.execute("DELETE FROM observation_groups")
        print(f"Deleted {cur.rowcount} observation groups")
        
        # 3. Delete test execution results
        cur.execute("DELETE FROM test_execution_results")
        print(f"Deleted {cur.rowcount} test execution results")
        
        # 4. Delete test executions (depends on workflow_phases)
        cur.execute("DELETE FROM cycle_report_test_execution_test_executions")
        print(f"Deleted {cur.rowcount} test executions")
        
        # 5. Delete workflow phase transitions
        cur.execute("DELETE FROM workflow_phase_transitions")
        print(f"Deleted {cur.rowcount} workflow phase transitions")
        
        # 6. Delete workflow phases (depends on cycle_reports)
        cur.execute("DELETE FROM workflow_phases")
        print(f"Deleted {cur.rowcount} workflow phases")
        
        # 7. Delete cycle report assignments if exists
        try:
            cur.execute("DELETE FROM cycle_report_assignments")
            print(f"Deleted {cur.rowcount} cycle report assignments")
        except:
            conn.rollback()  # Rollback just this statement
            
        # 8. Delete cycle reports (depends on test_cycles)
        cur.execute("DELETE FROM cycle_reports")
        print(f"Deleted {cur.rowcount} cycle reports")
        
        # 9. Delete test cycles
        cur.execute("DELETE FROM test_cycles")
        print(f"Deleted {cur.rowcount} test cycles")
        
        # 10. Delete any LLM audit logs related to test cycles
        cur.execute("DELETE FROM llm_audit_logs WHERE context_type = 'test_cycle'")
        print(f"Deleted {cur.rowcount} LLM audit logs")
        
        # Commit the transaction
        conn.commit()
        
        print("\n✅ Cleanup completed successfully!")
        print("\nVerifying cleanup...")
        
        # Verify all data is deleted
        tables = [
            'test_cycles', 'cycle_reports', 'workflow_phases', 
            'test_executions', 'observations', 'observation_groups'
        ]
        
        all_clean = True
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            if count > 0:
                print(f"  ❌ {table}: {count} records remaining")
                all_clean = False
            else:
                print(f"  ✅ {table}: clean")
        
        if all_clean:
            print("\n🎉 All test cycle data has been successfully removed!")
            print("You can now start fresh with new test cycles.")
        else:
            print("\n⚠️  Some data remains. Please check the tables above.")
            
    except Exception as e:
        print(f"\n❌ Error during cleanup: {str(e)}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    cleanup_test_cycles()