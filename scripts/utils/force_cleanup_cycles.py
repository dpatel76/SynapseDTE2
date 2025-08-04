#!/usr/bin/env python3
"""
Force cleanup of all test cycle data by using CASCADE deletes.
This is a more aggressive approach that will remove ALL related data.
"""

import os
from dotenv import load_dotenv
import psycopg2
import sys

load_dotenv()

def force_cleanup_test_cycles():
    """Force remove all test cycle related data using CASCADE"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        sys.exit(1)
    
    # Convert async URL to sync URL if needed
    if database_url.startswith('postgresql+asyncpg://'):
        database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    # Connect to database with autocommit initially on
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        print("\n=== FORCE Test Cycle Data Cleanup ===\n")
        print("⚠️  WARNING: This will CASCADE DELETE all test cycle data!")
        print("This is a destructive operation that cannot be undone.\n")
        
        # First, let's see what we're dealing with
        cur.execute("SELECT COUNT(*) FROM test_cycles")
        cycle_count = cur.fetchone()[0]
        print(f"Found {cycle_count} test cycles to delete\n")
        
        if cycle_count == 0:
            print("No test cycles found. Database is already clean!")
            return
        
        print("Using CASCADE deletion to remove all dependent data...")
        print("This will delete data from ALL tables that reference test_cycles.\n")
        
        try:
            # First, try to delete with CASCADE (if constraints allow)
            # This query will fail if foreign keys don't have CASCADE option
            cur.execute("DELETE FROM test_cycles CASCADE")
            deleted_count = cur.rowcount
            
            print(f"✓ Successfully deleted {deleted_count} test cycles and all dependent data!")
            
        except (psycopg2.errors.FeatureNotSupported, psycopg2.errors.DependentObjectsStillExist, psycopg2.errors.ForeignKeyViolation) as e:
            print(f"CASCADE delete failed: {str(e)}")
            print("\nTrying manual cleanup in dependency order...")
            
            # Get all cycle IDs first
            cur.execute("SELECT cycle_id FROM test_cycles")
            cycle_ids = [row[0] for row in cur.fetchall()]
            print(f"Found cycle IDs: {cycle_ids}")
            
            # Tables to clean in groups (innermost dependencies first)
            cleanup_groups = [
                # Group 1: Leaf tables (no other tables depend on these)
                [
                    'observation_versions', 'observation_records', 'observation_management_audit_logs',
                    'test_execution_audit_logs', 'testing_execution_audit_logs', 'test_execution_versions',
                    'sample_selection_audit_log', 'scoping_audit_log', 'request_info_audit_log',
                    'request_info_audit_logs', 'data_owner_phase_audit_log', 'data_provider_phase_audit_log',
                    'data_owner_escalation_log', 'data_provider_escalation_log', 'data_owner_notifications',
                    'data_provider_notifications', 'cdo_notifications', 'sla_violation_tracking',
                    'data_owner_sla_violations', 'data_provider_sla_violations', 'historical_data_owner_assignments',
                    'historical_data_provider_assignments', 'scoping_decision_versions', 'metrics_execution',
                    'metrics_phases', 'attribute_scoping_recommendation_versions', 'report_owner_scoping_reviews',
                    'data_profiling_rule_versions', 'llm_audit_log', 'workflow_executions'
                ],
                # Group 2: Tables that depend on Group 1
                [
                    'individual_samples', 'sample_submissions', 'database_submissions', 'document_submissions',
                    'submission_documents', 'testing_test_executions', 'test_executions', 'observations',
                    'data_provider_submissions', 'scoping_submissions', 'tester_scoping_decisions',
                    'sample_records', 'llm_sample_generations'
                ],
                # Group 3: Tables that depend on Group 2
                [
                    'test_cases', 'samples', 'sample_sets', 'documents', 'observation_groups',
                    'observation_management_phases', 'test_execution_phases', 'testing_execution_phases',
                    'test_report_phases', 'sample_selection_phases', 'request_info_phases',
                    'data_profiling_phases', 'report_attributes', 'attribute_scoping_recommendations'
                ],
                # Group 4: Tables that depend on Group 3
                [
                    'workflow_phases', 'data_owner_assignments', 'data_provider_assignments',
                    'attribute_lob_assignments'
                ],
                # Group 5: Direct dependencies on test_cycles
                [
                    'cycle_reports'
                ]
            ]
            
            total_deleted = 0
            for group_num, group in enumerate(cleanup_groups, 1):
                print(f"\nCleaning group {group_num}...")
                for table in group:
                    try:
                        # Delete records for all our cycle IDs
                        placeholders = ','.join(['%s'] * len(cycle_ids))
                        cur.execute(f"DELETE FROM {table} WHERE cycle_id IN ({placeholders})", cycle_ids)
                        count = cur.rowcount
                        if count > 0:
                            print(f"  ✓ Deleted {count} records from {table}")
                            total_deleted += count
                    except psycopg2.errors.UndefinedTable:
                        pass  # Table doesn't exist
                    except psycopg2.errors.UndefinedColumn:
                        pass  # Table doesn't have cycle_id column
                    except Exception as e:
                        if 'column "cycle_id" does not exist' not in str(e):
                            print(f"  ⚠️  Error with {table}: {str(e)}")
            
            # Finally, delete the test cycles themselves
            cur.execute("DELETE FROM test_cycles")
            count = cur.rowcount
            print(f"\n✓ Deleted {count} test cycles")
            total_deleted += count
            
            print(f"\n✅ Cleanup completed! Deleted {total_deleted} total records.")
        
        # Verify cleanup
        cur.execute("SELECT COUNT(*) FROM test_cycles")
        remaining = cur.fetchone()[0]
        
        if remaining == 0:
            print("\n🎉 SUCCESS! All test cycle data has been removed!")
            print("\nThe system is now completely clean.")
            print("\nYou can now log in and create fresh test cycles with real data.")
            print("The dashboard will accurately reflect actual workflow progress.")
        else:
            print(f"\n❌ ERROR: {remaining} test cycles still remain!")
            print("Manual intervention may be required.")
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        pass
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    force_cleanup_test_cycles()