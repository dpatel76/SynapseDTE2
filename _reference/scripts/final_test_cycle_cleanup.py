#!/usr/bin/env python3
"""
Final Test Cycle Cleanup Script
Handles mixed data types and provides comprehensive cleanup
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


class FinalTestCycleCleanup:
    """Handles comprehensive test cycle cleanup with proper data type handling"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.cursor = None
    
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
    
    def get_cycle_id_column_info(self, table_name: str) -> Optional[Dict[str, str]]:
        """Get information about the cycle_id column in a table"""
        query = """
            SELECT data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = 'cycle_id'
            AND table_schema = 'public';
        """
        try:
            self.cursor.execute(query, (table_name,))
            result = self.cursor.fetchone()
            return dict(result) if result else None
        except Exception:
            return None
    
    def get_tables_with_cycle_id(self) -> Dict[str, Dict[str, str]]:
        """Get all tables with cycle_id and their column info"""
        query = """
            SELECT t.table_name, c.data_type, c.is_nullable
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public' 
            AND c.column_name = 'cycle_id'
            AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name;
        """
        self.cursor.execute(query)
        tables = {}
        for row in self.cursor.fetchall():
            tables[row['table_name']] = {
                'data_type': row['data_type'],
                'is_nullable': row['is_nullable']
            }
        return tables
    
    def get_all_cycles(self) -> List[Dict[str, Any]]:
        """Get information about all test cycles"""
        query = """
            SELECT 
                tc.cycle_id,
                tc.cycle_name,
                tc.description,
                tc.status,
                tc.start_date,
                tc.end_date
            FROM test_cycles tc
            ORDER BY tc.cycle_id;
        """
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def count_records_in_table(self, table_name: str, cycle_id: int, data_type: str) -> int:
        """Count records in a specific table for a cycle, handling data type conversion"""
        try:
            if data_type == 'uuid':
                # For UUID fields, we need to convert the integer to string format
                count_query = f"SELECT COUNT(*) as count FROM {table_name} WHERE cycle_id::text = %s;"
                self.cursor.execute(count_query, (str(cycle_id),))
            else:
                # For integer fields
                count_query = f"SELECT COUNT(*) as count FROM {table_name} WHERE cycle_id = %s;"
                self.cursor.execute(count_query, (cycle_id,))
            
            result = self.cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            logger.warning(f"Could not count records in {table_name}: {e}")
            return 0
    
    def delete_records_from_table(self, table_name: str, cycle_id: int, data_type: str, dry_run: bool = False) -> int:
        """Delete records from a specific table for a cycle"""
        try:
            if dry_run:
                return self.count_records_in_table(table_name, cycle_id, data_type)
            
            if data_type == 'uuid':
                # For UUID fields
                delete_query = f"DELETE FROM {table_name} WHERE cycle_id::text = %s;"
                self.cursor.execute(delete_query, (str(cycle_id),))
            else:
                # For integer fields
                delete_query = f"DELETE FROM {table_name} WHERE cycle_id = %s;"
                self.cursor.execute(delete_query, (cycle_id,))
            
            return self.cursor.rowcount
        except Exception as e:
            logger.error(f"Error deleting from {table_name}: {e}")
            return 0
    
    def cleanup_cycle(self, cycle_id: int, dry_run: bool = False) -> Dict[str, int]:
        """Clean up a single test cycle"""
        deleted_counts = {}
        
        logger.info(f"{'DRY RUN: ' if dry_run else ''}Starting cleanup for cycle {cycle_id}")
        
        # Get all tables with cycle_id
        tables = self.get_tables_with_cycle_id()
        logger.info(f"Found {len(tables)} tables with cycle_id column")
        
        # Sort tables to delete in safe order (test_cycles last)
        table_order = []
        for table_name in tables.keys():
            if table_name == 'test_cycles':
                continue
            table_order.append(table_name)
        table_order.append('test_cycles')  # Always delete this last
        
        total_to_delete = 0
        
        # First, count everything that would be deleted
        for table_name in table_order:
            data_type = tables[table_name]['data_type']
            count = self.count_records_in_table(table_name, cycle_id, data_type)
            deleted_counts[table_name] = count
            total_to_delete += count
            if count > 0:
                logger.info(f"{'Would delete' if dry_run else 'Will delete'} {count} records from {table_name}")
        
        logger.info(f"Total records to {'simulate deletion' if dry_run else 'delete'}: {total_to_delete}")
        
        if not dry_run and total_to_delete > 0:
            # Actually delete the records
            try:
                for table_name in table_order:
                    data_type = tables[table_name]['data_type']
                    deleted_count = self.delete_records_from_table(table_name, cycle_id, data_type, dry_run=False)
                    if deleted_count > 0:
                        logger.info(f"Deleted {deleted_count} records from {table_name}")
                
                self.connection.commit()
                logger.info(f"Successfully cleaned up test cycle {cycle_id}")
                
            except Exception as e:
                self.connection.rollback()
                logger.error(f"Error during cleanup, rolled back: {e}")
                raise
        
        return deleted_counts
    
    def cleanup_all_cycles(self, dry_run: bool = False) -> Dict[int, Dict[str, int]]:
        """Clean up all test cycles"""
        all_results = {}
        
        cycles = self.get_all_cycles()
        logger.info(f"Found {len(cycles)} test cycles to clean up")
        
        for cycle in cycles:
            cycle_id = cycle['cycle_id']
            logger.info(f"Processing cycle {cycle_id}: {cycle['cycle_name']}")
            
            results = self.cleanup_cycle(cycle_id, dry_run)
            all_results[cycle_id] = results
            
            total_deleted = sum(results.values())
            logger.info(f"Cycle {cycle_id}: {total_deleted} records {'would be ' if dry_run else ''}deleted")
        
        return all_results
    
    def cleanup_orphaned_records(self, dry_run: bool = False) -> Dict[str, int]:
        """Clean up orphaned records that reference non-existent cycles"""
        orphaned_counts = {}
        
        logger.info(f"{'DRY RUN: ' if dry_run else ''}Starting orphaned records cleanup")
        
        tables = self.get_tables_with_cycle_id()
        
        for table_name, table_info in tables.items():
            if table_name == 'test_cycles':
                continue  # Skip the main table
                
            try:
                data_type = table_info['data_type']
                
                if data_type == 'uuid':
                    # For UUID fields
                    orphan_query = f"""
                        SELECT COUNT(*) as count 
                        FROM {table_name} t 
                        WHERE t.cycle_id::text NOT IN (SELECT cycle_id::text FROM test_cycles);
                    """
                else:
                    # For integer fields
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
                        if data_type == 'uuid':
                            delete_query = f"""
                                DELETE FROM {table_name} 
                                WHERE cycle_id::text NOT IN (SELECT cycle_id::text FROM test_cycles);
                            """
                        else:
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
            self.connection.commit()
            logger.info("Successfully cleaned up orphaned records")
        
        return orphaned_counts


def main():
    parser = argparse.ArgumentParser(description='Final Test Cycle Cleanup Script')
    parser.add_argument('--cycle-id', type=int, help='Specific cycle ID to clean up')
    parser.add_argument('--all-cycles', action='store_true', help='Clean up all test cycles')
    parser.add_argument('--orphaned-only', action='store_true', help='Clean up only orphaned records')
    parser.add_argument('--dry-run', action='store_true', help='Simulate cleanup without making changes')
    parser.add_argument('--confirm', action='store_true', help='Confirm destructive operations')
    parser.add_argument('--list-cycles', action='store_true', help='Just list all cycles and exit')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.cycle_id and not args.all_cycles and not args.orphaned_only and not args.list_cycles:
        parser.error("Must specify --cycle-id, --all-cycles, --orphaned-only, or --list-cycles")
    
    if (args.all_cycles or args.orphaned_only) and not args.confirm and not args.dry_run:
        parser.error("Must specify --confirm for destructive operations or use --dry-run")
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'synapse_dt',
        'user': 'synapse_user',
        'password': 'synapse_password'
    }
    
    cleanup = FinalTestCycleCleanup(db_config)
    
    try:
        cleanup.connect()
        
        if args.list_cycles:
            cycles = cleanup.get_all_cycles()
            print(f"Found {len(cycles)} test cycles:")
            for cycle in cycles:
                print(f"  Cycle {cycle['cycle_id']}: {cycle['cycle_name']} ({cycle['status']})")
            return
        
        if args.orphaned_only:
            deleted_counts = cleanup.cleanup_orphaned_records(dry_run=args.dry_run)
            total_deleted = sum(deleted_counts.values())
            logger.info(f"Orphaned records cleanup completed. Total records {'would be ' if args.dry_run else ''}deleted: {total_deleted}")
            
        elif args.cycle_id:
            deleted_counts = cleanup.cleanup_cycle(args.cycle_id, dry_run=args.dry_run)
            total_deleted = sum(deleted_counts.values())
            logger.info(f"Cycle {args.cycle_id} cleanup completed. Total records {'would be ' if args.dry_run else ''}deleted: {total_deleted}")
            
        elif args.all_cycles:
            all_results = cleanup.cleanup_all_cycles(dry_run=args.dry_run)
            grand_total = sum(sum(results.values()) for results in all_results.values())
            logger.info(f"All cycles cleanup completed. Grand total records {'would be ' if args.dry_run else ''}deleted: {grand_total}")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        sys.exit(1)
    finally:
        cleanup.disconnect()


if __name__ == '__main__':
    main()