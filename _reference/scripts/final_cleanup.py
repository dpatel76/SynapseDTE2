#!/usr/bin/env python3
"""
Final cleanup script - handles the last remaining stubborn records
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def final_cleanup():
    """Final cleanup of stubborn records"""
    
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'synapse_dt',
        'user': 'synapse_user',
        'password': 'synapse_password'
    }
    
    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        print("=== Final Cleanup ===")
        
        # Get remaining cycles
        cursor.execute("SELECT cycle_id, cycle_name FROM test_cycles ORDER BY cycle_id;")
        cycles = cursor.fetchall()
        
        print(f"Found {len(cycles)} remaining test cycles:")
        for cycle in cycles:
            print(f"  Cycle {cycle['cycle_id']}: {cycle['cycle_name']}")
        
        # Clean up the problematic tables manually
        cleanup_queries = [
            # These are the tables causing foreign key issues
            "DELETE FROM cycle_report_scoping_submissions WHERE cycle_id IN (21, 50, 54);",
            "DELETE FROM cycle_report_planning_data_sources WHERE cycle_id IN (21, 50, 54);",
            
            # Clean up any remaining cycle-specific data
            "DELETE FROM cycle_report_planning_attributes WHERE cycle_id IN (21, 50, 54);",
            "DELETE FROM cycle_report_scoping_decisions WHERE cycle_id IN (21, 50, 54);", 
            "DELETE FROM cycle_report_data_profiling_rules WHERE cycle_id IN (21, 50, 54);",
            "DELETE FROM activity_states WHERE cycle_id IN (21, 50, 54);",
            "DELETE FROM workflow_activities WHERE cycle_id IN (21, 50, 54);",
            "DELETE FROM workflow_phases WHERE cycle_id IN (21, 50, 54);",
            "DELETE FROM cycle_reports WHERE cycle_id IN (21, 50, 54);",
            
            # Finally delete the test cycles
            "DELETE FROM test_cycles WHERE cycle_id IN (21, 50, 54);"
        ]
        
        total_deleted = 0
        
        for query in cleanup_queries:
            try:
                cursor.execute(query)
                deleted = cursor.rowcount
                total_deleted += deleted
                if deleted > 0:
                    table_name = query.split("FROM ")[1].split(" WHERE")[0]
                    print(f"Deleted {deleted} records from {table_name}")
            except Exception as e:
                print(f"Warning: {e}")
                connection.rollback()
                continue
        
        connection.commit()
        print(f"Total records deleted: {total_deleted}")
        
        # Final verification
        print("\n=== Final Verification ===")
        cursor.execute("SELECT COUNT(*) as count FROM test_cycles;")
        remaining_cycles = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM cycle_reports;")
        remaining_reports = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM workflow_phases;")
        remaining_phases = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM workflow_activities;")
        remaining_activities = cursor.fetchone()['count']
        
        print(f"Remaining test_cycles: {remaining_cycles}")
        print(f"Remaining cycle_reports: {remaining_reports}")
        print(f"Remaining workflow_phases: {remaining_phases}")
        print(f"Remaining workflow_activities: {remaining_activities}")
        
        if remaining_cycles == 0:
            print("\n✅ SUCCESS: All test cycles successfully deleted!")
        else:
            print(f"\n⚠️  {remaining_cycles} test cycles still remain")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Final cleanup failed: {e}")

if __name__ == '__main__':
    final_cleanup()