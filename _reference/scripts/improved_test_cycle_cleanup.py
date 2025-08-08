#!/usr/bin/env python3
"""
Improved Test Cycle Cleanup Script
Fixed version that works with the actual database schema
"""

import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

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


class ImprovedTestCycleCleanup:
    """Handles comprehensive test cycle cleanup operations with actual schema"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        
        # Define deletion order based on actual database structure
        # Tables are ordered from most dependent to least dependent
        self.deletion_order = [
            # Start with actual existing tables that reference cycles
            'cycle_report_data_profiling_rules',
            'cycle_report_scoping_decisions', 
            'cycle_report_planning_attributes',
            
            # Workflow structure
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
                COUNT(cr.report_id) as report_count
            FROM test_cycles tc
            LEFT JOIN cycle_reports cr ON tc.cycle_id = cr.cycle_id
            WHERE tc.cycle_id = %s
            GROUP BY tc.cycle_id;
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
    
    def discover_cycle_tables(self) -> List[str]:
        """Discover all tables that have cycle_id column"""
        query = """
            SELECT DISTINCT t.table_name
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public' 
            AND c.column_name = 'cycle_id'
            AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name;
        """
        self.cursor.execute(query)
        tables = [row['table_name'] for row in self.cursor.fetchall()]
        logger.info(f"Discovered {len(tables)} tables with cycle_id column")
        return tables
    
    def count_related_records(self, cycle_id: int) -> Dict[str, int]:
        """Count records in all related tables for a given cycle"""
        counts = {}
        
        # Get all tables with cycle_id
        tables = self.discover_cycle_tables()
        
        for table_name in tables:
            try:
                count_query = f"SELECT COUNT(*) as count FROM {table_name} WHERE cycle_id = %s;"
                self.cursor.execute(count_query, (cycle_id,))
                result = self.cursor.fetchone()
                counts[table_name] = result['count'] if result else 0
            except Exception as e:
                logger.warning(f"Could not count records in {table_name}: {e}")
                counts[table_name] = 0
                # Rollback transaction to continue with other tables
                self.connection.rollback()
        
        return counts
    
    def delete_cycle_data(self, cycle_id: int, dry_run: bool = False) -> Dict[str, int]:
        """Delete all data related to a test cycle"""
        deleted_counts = {}
        
        logger.info(f"{'DRY RUN: ' if dry_run else ''}Starting cleanup for cycle {cycle_id}")
        
        # Get all tables with cycle_id in reverse dependency order
        all_tables = self.discover_cycle_tables()
        
        # Use a smarter ordering - put test_cycles last, workflow tables before it
        ordered_tables = []
        for table in all_tables:
            if table == 'test_cycles':
                continue
            elif 'workflow' in table:
                ordered_tables.append(table)
            else:
                ordered_tables.insert(0, table)  # Put other tables first
        
        # Add test_cycles at the end
        ordered_tables.append('test_cycles')
        
        for table_name in ordered_tables:
            try:
                if not dry_run:
                    delete_query = f"DELETE FROM {table_name} WHERE cycle_id = %s;"
                    self.cursor.execute(delete_query, (cycle_id,))
                    deleted_count = self.cursor.rowcount
                else:
                    # For dry run, count what would be deleted
                    count_query = f"SELECT COUNT(*) as count FROM {table_name} WHERE cycle_id = %s;"
                    self.cursor.execute(count_query, (cycle_id,))
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
        
        # Get all tables with cycle_id except test_cycles
        tables = [t for t in self.discover_cycle_tables() if t != 'test_cycles']
        
        for table_name in tables:
            try:
                # Find orphaned records
                orphan_query = f"""
                    SELECT COUNT(*) as count 
                    FROM {table_name} t 
                    WHERE t.cycle_id NOT IN (SELECT cycle_id FROM test_cycles);
                """
                
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
    parser = argparse.ArgumentParser(description='Improved Test Cycle Cleanup Script')
    parser.add_argument('--cycle-id', type=int, help='Specific cycle ID to clean up')
    parser.add_argument('--all-cycles', action='store_true', help='Clean up all test cycles')
    parser.add_argument('--orphaned-only', action='store_true', help='Clean up only orphaned records')
    parser.add_argument('--dry-run', action='store_true', help='Simulate cleanup without making changes')
    parser.add_argument('--confirm', action='store_true', help='Confirm destructive operations')
    parser.add_argument('--discover-tables', action='store_true', help='Just discover and list tables with cycle_id')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.cycle_id and not args.all_cycles and not args.orphaned_only and not args.discover_tables:
        parser.error("Must specify --cycle-id, --all-cycles, --orphaned-only, or --discover-tables")
    
    if (args.all_cycles or args.orphaned_only) and not args.confirm and not args.dry_run:
        parser.error("Must specify --confirm for destructive operations or use --dry-run")
    
    # Database configuration from .env
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'synapse_dt',
        'user': 'synapse_user',
        'password': 'synapse_password'
    }
    
    cleanup = ImprovedTestCycleCleanup(db_config)
    
    try:
        cleanup.connect()
        
        if args.discover_tables:
            # Just discover tables and exit
            tables = cleanup.discover_cycle_tables()
            print(f"Found {len(tables)} tables with cycle_id column:")
            for table in tables:
                print(f"  - {table}")
            return
        
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
            logger.info(f"Reports: {cycle_info['report_count']}")
            
            # Count related records
            counts = cleanup.count_related_records(args.cycle_id)
            total_records = sum(counts.values())
            logger.info(f"Total related records to {'simulate deletion' if args.dry_run else 'delete'}: {total_records}")
            
            # Show breakdown
            for table, count in counts.items():
                if count > 0:
                    logger.info(f"  {table}: {count} records")
            
            # Perform cleanup
            deleted_counts = cleanup.delete_cycle_data(args.cycle_id, dry_run=args.dry_run)
            
            # Generate report
            report = cleanup.generate_cleanup_report(args.cycle_id, deleted_counts)
            print(report)
            
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