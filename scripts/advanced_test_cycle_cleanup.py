#!/usr/bin/env python3
"""
Advanced Test Cycle Cleanup Script
Handles foreign key constraints by analyzing dependencies and using CASCADE operations
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def cleanup_remaining_cycles():
    """Clean up the remaining cycles using CASCADE deletes"""
    
    # Database configuration
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
        
        print("=== Advanced Test Cycle Cleanup ===")
        
        # Get remaining cycles
        cursor.execute("SELECT cycle_id, cycle_name FROM test_cycles ORDER BY cycle_id;")
        cycles = cursor.fetchall()
        
        print(f"Found {len(cycles)} remaining test cycles:")
        for cycle in cycles:
            print(f"  Cycle {cycle['cycle_id']}: {cycle['cycle_name']}")
        
        if not cycles:
            print("No cycles to clean up!")
            return
        
        print("\nStarting cleanup with CASCADE operations...")
        
        # For each remaining cycle, use a more aggressive approach
        for cycle in cycles:
            cycle_id = cycle['cycle_id']
            print(f"\nProcessing cycle {cycle_id}: {cycle['cycle_name']}")
            
            try:
                # Strategy 1: Try direct cascade delete from test_cycles
                print(f"  Attempting CASCADE delete for cycle {cycle_id}...")
                
                # First, try to delete cascade-able dependent records
                cascade_queries = [
                    # Delete in reverse dependency order with explicit handling
                    "DELETE FROM cycle_report_scoping_decisions WHERE cycle_id = %s;",
                    "DELETE FROM cycle_report_planning_pde_mappings WHERE cycle_id = %s;", 
                    "DELETE FROM cycle_report_planning_attributes WHERE cycle_id = %s;",
                    "DELETE FROM cycle_report_data_profiling_rules WHERE cycle_id = %s;",
                    "DELETE FROM activity_states WHERE cycle_id = %s;",
                    "DELETE FROM workflow_activities WHERE cycle_id = %s;",
                    "DELETE FROM workflow_phases WHERE cycle_id = %s;",
                    "DELETE FROM cycle_reports WHERE cycle_id = %s;",
                    "DELETE FROM test_cycles WHERE cycle_id = %s;"
                ]
                
                total_deleted = 0
                for query in cascade_queries:
                    try:
                        cursor.execute(query, (cycle_id,))
                        deleted = cursor.rowcount
                        total_deleted += deleted
                        if deleted > 0:
                            table_name = query.split("FROM ")[1].split(" WHERE")[0]
                            print(f"    Deleted {deleted} records from {table_name}")
                    except Exception as e:
                        print(f"    Warning: {e}")
                        connection.rollback()
                        continue
                
                connection.commit()
                print(f"  ✓ Successfully deleted cycle {cycle_id} ({total_deleted} total records)")
                
            except Exception as e:
                print(f"  ✗ Failed to delete cycle {cycle_id}: {e}")
                connection.rollback()
        
        # Verify cleanup
        print("\n=== Verification ===")
        cursor.execute("SELECT COUNT(*) as count FROM test_cycles;")
        remaining_cycles = cursor.fetchone()['count']
        
        if remaining_cycles == 0:
            print("✓ All test cycles successfully deleted!")
        else:
            print(f"⚠ {remaining_cycles} test cycles still remain")
            
        # Check for any remaining related data
        tables_to_check = [
            'cycle_reports',
            'workflow_phases', 
            'workflow_activities',
            'cycle_report_planning_attributes',
            'cycle_report_scoping_decisions',
            'cycle_report_data_profiling_rules'
        ]
        
        print("\nRemaining related data:")
        total_remaining = 0
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table};")
                count = cursor.fetchone()['count']
                total_remaining += count
                if count > 0:
                    print(f"  {table}: {count} records")
            except Exception as e:
                print(f"  {table}: Error checking - {e}")
        
        if total_remaining == 0:
            print("✓ No related data remaining!")
        else:
            print(f"Total remaining related records: {total_remaining}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Cleanup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cleanup_remaining_cycles()