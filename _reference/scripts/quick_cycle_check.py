#!/usr/bin/env python3
"""
Quick Test Cycle Check Script
Simple script to check what test cycles exist and basic related data counts
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
db_config = {
    'host': 'localhost',
    'port': '5432',
    'database': 'synapse_dt',
    'user': 'synapse_user',
    'password': 'synapse_password'
}

def check_test_cycles():
    """Check what test cycles exist and their basic stats"""
    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        print("=== TEST CYCLES OVERVIEW ===")
        
        # Get all test cycles with basic info
        query = """
            SELECT 
                tc.cycle_id,
                tc.cycle_name,
                tc.description,
                tc.status,
                tc.start_date,
                tc.end_date,
                tc.test_executive_id,
                COUNT(DISTINCT cr.report_id) as report_count
            FROM test_cycles tc
            LEFT JOIN cycle_reports cr ON tc.cycle_id = cr.cycle_id
            GROUP BY tc.cycle_id
            ORDER BY tc.cycle_id;
        """
        
        cursor.execute(query)
        cycles = cursor.fetchall()
        
        print(f"Found {len(cycles)} test cycles:\n")
        
        for cycle in cycles:
            print(f"Cycle ID: {cycle['cycle_id']}")
            print(f"  Name: {cycle['cycle_name']}")
            print(f"  Status: {cycle['status']}")
            print(f"  Executive ID: {cycle['test_executive_id']}")
            print(f"  Reports: {cycle['report_count']}")
            print(f"  Start Date: {cycle['start_date']}")
            print(f"  End Date: {cycle['end_date']}")
            print()
        
        # Check workflow phases
        print("=== WORKFLOW PHASES COUNT ===")
        cursor.execute("SELECT COUNT(*) as count FROM workflow_phases;")
        phase_count = cursor.fetchone()['count']
        print(f"Total workflow phases: {phase_count}")
        
        # Check workflow activities
        print("\n=== WORKFLOW ACTIVITIES COUNT ===")
        cursor.execute("SELECT COUNT(*) as count FROM workflow_activities;")
        activity_count = cursor.fetchone()['count']
        print(f"Total workflow activities: {activity_count}")
        
        # Check cycle reports
        print("\n=== CYCLE REPORTS COUNT ===")
        cursor.execute("SELECT COUNT(*) as count FROM cycle_reports;")
        cycle_reports_count = cursor.fetchone()['count']
        print(f"Total cycle reports: {cycle_reports_count}")
        
        # Check some key cycle_report_* tables
        print("\n=== CYCLE REPORT DATA ===")
        
        tables_to_check = [
            'cycle_report_planning_attributes',
            'cycle_report_scoping_decisions', 
            'cycle_report_data_profiling_rules',
            'cycle_report_sample_selection_versions',
            'cycle_report_test_execution_results',
            'cycle_report_test_report_sections'
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table};")
                count = cursor.fetchone()['count']
                print(f"{table}: {count} records")
            except Exception as e:
                print(f"{table}: Table doesn't exist or error - {e}")
        
        # Total estimated records that would be deleted
        print("\n=== TOTAL ESTIMATED IMPACT ===")
        total_cycles = len(cycles)
        print(f"Cycles to delete: {total_cycles}")
        print(f"Estimated workflow phases: {phase_count}")
        print(f"Estimated workflow activities: {activity_count}")
        print(f"Estimated cycle reports: {cycle_reports_count}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_test_cycles()