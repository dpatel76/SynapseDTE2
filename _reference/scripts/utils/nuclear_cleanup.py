#!/usr/bin/env python3
"""
Nuclear option: Delete ALL test cycle data by finding and removing all dependencies.
This is the most aggressive cleanup approach.
"""

import os
from dotenv import load_dotenv
import psycopg2
import sys

load_dotenv()

def nuclear_cleanup():
    """Delete all test cycle data by clearing all dependencies first"""
    
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
        print("\n=== NUCLEAR CLEANUP: Removing ALL Test Cycle Data ===\n")
        print("⚠️  This will delete ALL data related to test cycles!")
        print("This is a last resort option.\n")
        
        # Get all test cycle IDs
        cur.execute("SELECT cycle_id FROM test_cycles")
        cycle_ids = [row[0] for row in cur.fetchall()]
        print(f"Found {len(cycle_ids)} test cycles to remove\n")
        
        if not cycle_ids:
            print("No test cycles found. Database is already clean!")
            return
        
        # Create placeholders for SQL IN clause
        placeholders = ','.join(['%s'] * len(cycle_ids))
        
        # Comprehensive list of all tables that might have cycle data
        # Ordered from leaf dependencies to root
        all_tables = [
            # First, tables that nothing depends on
            'sample_approval_history',
            'sample_generation_history', 
            'attribute_approval_history',
            'scoping_approval_history',
            'test_result_approvals',
            'data_source_logs',
            'validation_logs',
            'remediation_actions',
            'escalation_history',
            'notification_logs',
            'audit_trail',
            'system_logs',
            
            # Then tables with minimal dependencies
            'observation_versions',
            'observation_records', 
            'observation_management_audit_logs',
            'test_execution_audit_logs',
            'testing_execution_audit_logs',
            'test_execution_versions',
            'sample_selection_audit_log',
            'scoping_audit_log',
            'request_info_audit_log',
            'request_info_audit_logs',
            'data_owner_phase_audit_log',
            'data_provider_phase_audit_log',
            'data_owner_escalation_log',
            'data_provider_escalation_log',
            'data_owner_notifications',
            'data_provider_notifications',
            'cdo_notifications',
            'sla_violation_tracking',
            'data_owner_sla_violations',
            'data_provider_sla_violations',
            'historical_data_owner_assignments',
            'historical_data_provider_assignments',
            'scoping_decision_versions',
            'metrics_execution',
            'metrics_phases',
            'attribute_scoping_recommendation_versions',
            'report_owner_scoping_reviews',
            'data_profiling_rule_versions',
            'llm_audit_log',
            'workflow_executions',
            
            # Tables that depend on the above
            'individual_samples',
            'sample_submissions',
            'database_submissions',
            'document_submissions',
            'submission_documents',
            'testing_test_executions',
            'test_executions',
            'observations',
            'data_provider_submissions',
            'scoping_submissions',
            'tester_scoping_decisions',
            'sample_records',
            'llm_sample_generations',
            
            # Tables that depend on those
            'test_cases',
            'samples',
            'sample_sets',
            'documents',
            'observation_groups',
            'observation_management_phases',
            'test_execution_phases',
            'testing_execution_phases',
            'test_report_phases',
            'sample_selection_phases',
            'request_info_phases',
            'data_profiling_phases',
            'report_attributes',
            'attribute_scoping_recommendations',
            
            # Tables closest to test_cycles
            'workflow_phases',
            'data_owner_assignments',
            'data_provider_assignments',
            'attribute_lob_assignments',
            'cycle_reports',
        ]
        
        print("Deleting data from all related tables...\n")
        
        total_deleted = 0
        for table in all_tables:
            try:
                # Try to delete by cycle_id
                cur.execute(f"DELETE FROM {table} WHERE cycle_id IN ({placeholders})", cycle_ids)
                count = cur.rowcount
                if count > 0:
                    print(f"  ✓ Deleted {count} records from {table}")
                    total_deleted += count
            except psycopg2.errors.UndefinedTable:
                pass  # Table doesn't exist
            except psycopg2.errors.UndefinedColumn:
                # Table doesn't have cycle_id, try other approaches
                if table == 'sample_sets':
                    # Delete sample_sets by finding them through samples
                    try:
                        cur.execute(f"""
                            DELETE FROM sample_sets 
                            WHERE set_id IN (
                                SELECT DISTINCT set_id 
                                FROM cycle_report_sample_selection_samples 
                                WHERE cycle_id IN ({placeholders})
                            )
                        """, cycle_ids)
                        count = cur.rowcount
                        if count > 0:
                            print(f"  ✓ Deleted {count} records from {table} (via samples)")
                            total_deleted += count
                    except:
                        pass
            except Exception as e:
                # For debugging - only show real errors
                error_str = str(e)
                if ('does not exist' not in error_str and 
                    'constraint' in error_str):
                    print(f"  ⚠️  Constraint error with {table}: {error_str[:100]}...")
        
        # Now delete test_cycles
        print(f"\nDeleting test cycles...")
        try:
            cur.execute("DELETE FROM test_cycles")
            count = cur.rowcount
            print(f"✓ Deleted {count} test cycles")
            total_deleted += count
        except Exception as e:
            print(f"❌ Failed to delete test_cycles: {str(e)}")
            
            # If still failing, try to find what's blocking
            print("\nChecking for remaining blockers...")
            cur.execute("""
                SELECT DISTINCT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                  AND tc.constraint_name IN (
                    SELECT constraint_name 
                    FROM information_schema.constraint_column_usage 
                    WHERE table_name = 'test_cycles'
                  )
                ORDER BY tc.table_name
            """)
            
            blockers = cur.fetchall()
            if blockers:
                print("Tables still referencing test_cycles:")
                for table, column in blockers:
                    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IN ({placeholders})", cycle_ids)
                    count = cur.fetchone()[0]
                    if count > 0:
                        print(f"  - {table}.{column}: {count} records")
        
        # Final verification
        cur.execute("SELECT COUNT(*) FROM test_cycles")
        remaining = cur.fetchone()[0]
        
        print(f"\n{'='*60}")
        if remaining == 0:
            print("🎉 SUCCESS! All test cycle data has been removed!")
            print(f"Total records deleted: {total_deleted}")
            print("="*60)
            print("\nThe database is now completely clean.")
            print("\nYou can now create fresh test cycles with real data:")
            print("1. Log in as test.manager@example.com")
            print("2. Go to Test Cycles → Create New Cycle")
            print("3. Add reports and assign testers")
            print("4. Watch real workflow progress on the dashboard!")
        else:
            print(f"❌ PARTIAL SUCCESS: {remaining} test cycles remain")
            print(f"Deleted {total_deleted} related records")
            print("="*60)
            print("\nManual database intervention may be required.")
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    nuclear_cleanup()