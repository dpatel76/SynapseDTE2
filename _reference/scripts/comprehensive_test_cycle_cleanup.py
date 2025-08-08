#!/usr/bin/env python3
"""
Comprehensive Test Cycle Cleanup Script

This script safely removes test cycles and all their dependent data while respecting
foreign key constraints and maintaining data integrity.

Usage:
    python comprehensive_test_cycle_cleanup.py --cycle-id <cycle_id>
    python comprehensive_test_cycle_cleanup.py --all-cycles --confirm
    python comprehensive_test_cycle_cleanup.py --dry-run --cycle-id <cycle_id>

Author: Generated for SynapseDTE
Date: 2025-07-18
"""

import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_cycle_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestCycleCleanup:
    """Handles comprehensive test cycle cleanup operations"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        
        # Define deletion order based on foreign key dependencies
        # Tables are ordered from most dependent to least dependent
        self.deletion_order = [
            # Activity and workflow history (most dependent)
            'workflow_activity_history',
            'workflow_activity_dependencies',
            
            # Phase-specific audit and review tables
            'cycle_report_test_execution_audit',
            'cycle_report_test_execution_reviews',
            'cycle_report_data_profiling_rule_versions',
            
            # Test execution results and data
            'cycle_report_test_execution_results',
            'cycle_report_test_execution_database_tests',
            'cycle_report_test_execution_document_analyses',
            'cycle_report_test_executions',
            
            # Test report data
            'cycle_report_test_report_generation',
            'cycle_report_test_report_sections',
            
            # Observation management
            'cycle_report_observation_mgmt_approvals',
            'cycle_report_observation_mgmt_impact_assessments',
            'cycle_report_observation_mgmt_resolutions',
            'cycle_report_observation_mgmt_observation_records',
            'cycle_report_observation_mgmt_audit_logs',
            
            # Request for information
            'cycle_report_request_info_testcase_source_evidence',
            'cycle_report_request_info_document_versions',
            'cycle_report_request_info_phases',
            'cycle_report_request_info_audit_logs',
            
            # Sample selection
            'cycle_report_sample_selection_samples',
            'cycle_report_sample_selection_versions',
            'cycle_report_sample_selection_audit_logs',
            'cycle_report_sample_records',
            'cycle_report_sample_sets',
            
            # Data profiling
            'cycle_report_data_profiling_results',
            'cycle_report_data_profiling_files',
            'cycle_report_data_profiling_rules',
            'cycle_report_data_profiling_attribute_scores',
            'cycle_report_data_profiling_uploads',
            
            # Scoping phase
            'cycle_report_scoping_tester_decisions',
            'cycle_report_scoping_report_owner_reviews',
            'cycle_report_scoping_decision_versions',
            'cycle_report_scoping_submissions',
            'cycle_report_scoping_attribute_recommendation_versions',
            'cycle_report_scoping_attribute_recommendations',
            'cycle_report_scoping_decisions',
            'cycle_report_scoping_versions',
            'cycle_report_scoping_audit_logs',
            
            # Planning phase
            'cycle_report_planning_pde_mapping_review_history',
            'cycle_report_planning_pde_mapping_reviews',
            'cycle_report_planning_pde_mapping_approval_rules',
            'cycle_report_planning_pde_mappings',
            'cycle_report_planning_pde_classifications',
            'cycle_report_planning_attribute_version_history',
            'cycle_report_planning_attributes',
            'cycle_report_planning_data_sources',
            'cycle_report_planning_versions',
            
            # Data owner and assignment tables
            'cycle_report_data_owner_lob_attribute_versions',
            'cycle_report_data_owner_lob_attribute_assignments',
            'historical_data_owner_assignments',
            'data_owner_sla_violations',
            'data_owner_phase_audit_logs',
            'data_owner_assignments',
            'attribute_lob_assignments',
            
            # Test cases and core testing data
            'cycle_report_test_cases',
            'test_executions',  # Legacy table
            'observations',     # Legacy table
            
            # Documents and files
            'cycle_report_documents',
            
            # Metrics and audit logs
            'execution_metrics',
            'phase_metrics',
            'llm_audit_logs',
            
            # Workflow management
            'workflow_activities',
            'workflow_phases',
            
            # Core relationship table
            'cycle_reports',
            
            # Main table (least dependent)
            'test_cycles'
        ]
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """
        self.cursor.execute(query, (table_name,))
        return self.cursor.fetchone()['exists']
    
    def get_cycle_info(self, cycle_id: int) -> Optional[Dict[str, Any]]:
        """Get information about a test cycle"""
        query = """
            SELECT 
                tc.cycle_id,
                tc.cycle_name,
                tc.description,
                tc.test_executive_id,
                tc.start_date,
                tc.end_date,
                tc.status,
                tc.workflow_id,
                u.username as test_executive_name,
                COUNT(cr.report_id) as report_count
            FROM test_cycles tc
            LEFT JOIN users u ON tc.test_executive_id = u.user_id
            LEFT JOIN cycle_reports cr ON tc.cycle_id = cr.cycle_id
            WHERE tc.cycle_id = %s
            GROUP BY tc.cycle_id, u.username;
        """
        self.cursor.execute(query, (cycle_id,))
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def get_all_cycles(self) -> List[Dict[str, Any]]:
        """Get information about all test cycles"""
        query = """
            SELECT 
                tc.cycle_id,
                tc.cycle_name,
                tc.description,
                tc.status,
                tc.start_date,
                tc.end_date,
                COUNT(cr.report_id) as report_count,
                COUNT(wp.phase_id) as phase_count,
                COUNT(wa.activity_id) as activity_count
            FROM test_cycles tc
            LEFT JOIN cycle_reports cr ON tc.cycle_id = cr.cycle_id
            LEFT JOIN workflow_phases wp ON tc.cycle_id = wp.cycle_id
            LEFT JOIN workflow_activities wa ON tc.cycle_id = wa.cycle_id
            GROUP BY tc.cycle_id
            ORDER BY tc.cycle_id;
        """
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def count_related_records(self, cycle_id: int) -> Dict[str, int]:
        """Count records in all related tables for a given cycle"""
        counts = {}
        
        for table_name in self.deletion_order:
            if not self.table_exists(table_name):
                counts[table_name] = 0
                continue
            
            # Determine the appropriate foreign key column
            if table_name == 'test_cycles':
                where_clause = f"cycle_id = {cycle_id}"
            elif 'cycle_report_' in table_name:
                # Check if table has cycle_id column
                column_query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = 'cycle_id';
                """
                self.cursor.execute(column_query, (table_name,))
                if self.cursor.fetchone():
                    where_clause = f"cycle_id = {cycle_id}"
                else:
                    # Skip tables without cycle_id
                    counts[table_name] = 0
                    continue
            else:
                # Legacy tables
                where_clause = f"cycle_id = {cycle_id}"
            
            try:
                count_query = f"SELECT COUNT(*) as count FROM {table_name} WHERE {where_clause};"
                self.cursor.execute(count_query)
                result = self.cursor.fetchone()
                counts[table_name] = result['count'] if result else 0
            except Exception as e:
                logger.warning(f"Could not count records in {table_name}: {e}")
                counts[table_name] = 0
        
        return counts
    
    def delete_cycle_data(self, cycle_id: int, dry_run: bool = False) -> Dict[str, int]:
        """Delete all data related to a test cycle"""
        deleted_counts = {}
        
        logger.info(f"{'DRY RUN: ' if dry_run else ''}Starting cleanup for cycle {cycle_id}")
        
        for table_name in self.deletion_order:
            if not self.table_exists(table_name):
                deleted_counts[table_name] = 0
                continue
            
            # Determine the appropriate foreign key column and deletion strategy
            if table_name == 'test_cycles':
                delete_query = f"DELETE FROM {table_name} WHERE cycle_id = %s;"
                params = (cycle_id,)
            elif 'cycle_report_' in table_name:
                # Check if table has cycle_id column
                column_query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = 'cycle_id';
                """
                self.cursor.execute(column_query, (table_name,))
                if self.cursor.fetchone():
                    delete_query = f"DELETE FROM {table_name} WHERE cycle_id = %s;"
                    params = (cycle_id,)
                else:
                    # Skip tables without cycle_id
                    deleted_counts[table_name] = 0
                    continue
            else:
                # Legacy tables
                delete_query = f"DELETE FROM {table_name} WHERE cycle_id = %s;"
                params = (cycle_id,)
            
            try:
                if not dry_run:
                    self.cursor.execute(delete_query, params)
                    deleted_count = self.cursor.rowcount
                else:
                    # For dry run, just count what would be deleted
                    count_query = delete_query.replace("DELETE FROM", "SELECT COUNT(*) as count FROM").replace("WHERE cycle_id = %s;", "WHERE cycle_id = %s;")
                    self.cursor.execute(count_query, params)
                    result = self.cursor.fetchone()
                    deleted_count = result['count'] if result else 0
                
                deleted_counts[table_name] = deleted_count
                
                if deleted_count > 0:
                    logger.info(f"{'Would delete' if dry_run else 'Deleted'} {deleted_count} records from {table_name}")
                
            except Exception as e:
                logger.error(f"Error {'simulating deletion from' if dry_run else 'deleting from'} {table_name}: {e}")
                deleted_counts[table_name] = 0
                
                if not dry_run:
                    # Rollback transaction on error
                    self.connection.rollback()
                    raise
        
        if not dry_run:
            self.connection.commit()
            logger.info(f"Successfully cleaned up test cycle {cycle_id}")
        
        return deleted_counts
    
    def cleanup_orphaned_records(self, dry_run: bool = False) -> Dict[str, int]:
        """Clean up orphaned records that reference non-existent cycles"""
        orphaned_counts = {}
        
        logger.info(f"{'DRY RUN: ' if dry_run else ''}Starting orphaned records cleanup")
        
        # Find orphaned records in each table
        for table_name in self.deletion_order[:-1]:  # Skip test_cycles table
            if not self.table_exists(table_name):
                orphaned_counts[table_name] = 0
                continue
            
            # Check if table has cycle_id column
            column_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = 'cycle_id';
            """
            self.cursor.execute(column_query, (table_name,))
            if not self.cursor.fetchone():
                orphaned_counts[table_name] = 0
                continue
            
            # Find orphaned records
            orphan_query = f"""
                SELECT COUNT(*) as count 
                FROM {table_name} t 
                WHERE t.cycle_id NOT IN (SELECT cycle_id FROM test_cycles);
            """
            
            try:
                self.cursor.execute(orphan_query)
                result = self.cursor.fetchone()
                orphan_count = result['count'] if result else 0
                
                if orphan_count > 0:
                    if not dry_run:
                        delete_query = f"""
                            DELETE FROM {table_name} 
                            WHERE cycle_id NOT IN (SELECT cycle_id FROM test_cycles);
                        """
                        self.cursor.execute(delete_query)
                        deleted_count = self.cursor.rowcount
                    else:
                        deleted_count = orphan_count
                    
                    orphaned_counts[table_name] = deleted_count
                    logger.info(f"{'Would clean up' if dry_run else 'Cleaned up'} {deleted_count} orphaned records from {table_name}")
                else:
                    orphaned_counts[table_name] = 0
                    
            except Exception as e:
                logger.error(f"Error cleaning orphaned records from {table_name}: {e}")
                orphaned_counts[table_name] = 0
                
                if not dry_run:
                    self.connection.rollback()
                    raise
        
        if not dry_run:
            self.connection.commit()
            logger.info("Successfully cleaned up orphaned records")
        
        return orphaned_counts
    
    def generate_cleanup_report(self, cycle_id: int, deleted_counts: Dict[str, int]) -> str:
        """Generate a detailed cleanup report"""
        total_deleted = sum(deleted_counts.values())
        
        report = f"""
Test Cycle Cleanup Report
========================
Cycle ID: {cycle_id}
Cleanup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Records Deleted: {total_deleted}

Deletion Summary by Table:
-------------------------
"""
        
        for table_name, count in deleted_counts.items():
            if count > 0:
                report += f"{table_name}: {count} records\n"
        
        report += f"""
Tables with zero deletions: {len([t for t, c in deleted_counts.items() if c == 0])}

Cleanup completed successfully.
"""
        
        return report


def main():
    parser = argparse.ArgumentParser(description='Comprehensive Test Cycle Cleanup Script')
    parser.add_argument('--cycle-id', type=int, help='Specific cycle ID to clean up')
    parser.add_argument('--all-cycles', action='store_true', help='Clean up all test cycles')
    parser.add_argument('--orphaned-only', action='store_true', help='Clean up only orphaned records')
    parser.add_argument('--dry-run', action='store_true', help='Simulate cleanup without making changes')
    parser.add_argument('--confirm', action='store_true', help='Confirm destructive operations')
    parser.add_argument('--db-host', default='localhost', help='Database host')
    parser.add_argument('--db-port', default='5432', help='Database port')
    parser.add_argument('--db-name', default='synapse_dt', help='Database name')
    parser.add_argument('--db-user', default='postgres', help='Database user')
    parser.add_argument('--db-password', help='Database password')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.cycle_id and not args.all_cycles and not args.orphaned_only:
        parser.error("Must specify --cycle-id, --all-cycles, or --orphaned-only")
    
    if (args.all_cycles or args.orphaned_only) and not args.confirm and not args.dry_run:
        parser.error("Must specify --confirm for destructive operations or use --dry-run")
    
    # Database configuration
    db_config = {
        'host': args.db_host,
        'port': args.db_port,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password or input("Database password: ")
    }
    
    cleanup = TestCycleCleanup(db_config)
    
    try:
        cleanup.connect()
        
        if args.orphaned_only:
            # Clean up orphaned records only
            logger.info("Cleaning up orphaned records...")
            deleted_counts = cleanup.cleanup_orphaned_records(dry_run=args.dry_run)
            
            total_deleted = sum(deleted_counts.values())
            logger.info(f"Orphaned records cleanup completed. Total records {'would be ' if args.dry_run else ''}deleted: {total_deleted}")
            
        elif args.cycle_id:
            # Clean up specific cycle
            cycle_info = cleanup.get_cycle_info(args.cycle_id)
            if not cycle_info:
                logger.error(f"Test cycle {args.cycle_id} not found")
                sys.exit(1)
            
            logger.info(f"Found test cycle: {cycle_info['cycle_name']} (ID: {args.cycle_id})")
            logger.info(f"Test Executive: {cycle_info['test_executive_name']}")
            logger.info(f"Reports: {cycle_info['report_count']}")
            
            # Count related records
            counts = cleanup.count_related_records(args.cycle_id)
            total_records = sum(counts.values())
            logger.info(f"Total related records to {'simulate deletion' if args.dry_run else 'delete'}: {total_records}")
            
            # Perform cleanup
            deleted_counts = cleanup.delete_cycle_data(args.cycle_id, dry_run=args.dry_run)
            
            # Generate report
            report = cleanup.generate_cleanup_report(args.cycle_id, deleted_counts)
            print(report)
            
            # Save report to file
            report_filename = f"cleanup_report_cycle_{args.cycle_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w') as f:
                f.write(report)
            logger.info(f"Cleanup report saved to {report_filename}")
            
        elif args.all_cycles:
            # Clean up all cycles
            cycles = cleanup.get_all_cycles()
            logger.info(f"Found {len(cycles)} test cycles to clean up")
            
            for cycle in cycles:
                logger.info(f"Processing cycle {cycle['cycle_id']}: {cycle['cycle_name']}")
                deleted_counts = cleanup.delete_cycle_data(cycle['cycle_id'], dry_run=args.dry_run)
                total_deleted = sum(deleted_counts.values())
                logger.info(f"Cycle {cycle['cycle_id']}: {total_deleted} records {'would be ' if args.dry_run else ''}deleted")
            
            logger.info("All cycles cleanup completed")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        sys.exit(1)
    finally:
        cleanup.disconnect()


if __name__ == '__main__':
    main()