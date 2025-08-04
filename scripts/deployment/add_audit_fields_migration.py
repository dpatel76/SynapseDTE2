#!/usr/bin/env python3
"""
Migration: Add created_by and updated_by fields to all tables
Date: 2025-01-09
Author: System

Purpose:
- Add created_by_id and updated_by_id columns to all tables
- These fields track which user created or last updated each record
- Fields are nullable to avoid breaking existing records

Prerequisites:
- PostgreSQL database with existing schema
- Users table must exist

Rollback:
- Run with --rollback flag to remove the added columns
"""

import asyncio
import os
import asyncpg
import logging
from datetime import datetime
from typing import List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditFieldsMigration:
    """Add audit fields to all database tables"""
    
    # Tables to exclude from audit fields
    EXCLUDED_TABLES = {
        'alembic_version',  # Alembic migration tracking
        'users',  # Users table itself
        'pg_stat_statements',  # PostgreSQL system table
    }
    
    # Tables that already have some form of user tracking
    TABLES_WITH_EXISTING_TRACKING = {
        'profiling_rules': ('created_by', 'updated_by'),
        'sample_selection_phases': ('created_by', 'updated_by'),
        'observations': ('created_by',),
        'observation_resolutions': ('created_by',),
        'sample_sets': ('created_by',),
    }
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
        
    async def get_all_tables(self, conn) -> List[str]:
        """Get all tables in the database"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        rows = await conn.fetch(query)
        return [row['table_name'] for row in rows]
    
    async def check_column_exists(self, conn, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        query = """
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = $1 
            AND column_name = $2
        );
        """
        
        result = await conn.fetchval(query, table_name, column_name)
        return result
    
    async def add_audit_columns(self, conn, table_name: str) -> Tuple[bool, str]:
        """Add created_by_id and updated_by_id columns to a table"""
        try:
            # Check what columns need to be added
            has_created_by = await self.check_column_exists(conn, table_name, 'created_by_id')
            has_updated_by = await self.check_column_exists(conn, table_name, 'updated_by_id')
            
            if has_created_by and has_updated_by:
                return True, "Already has audit columns"
            
            # Add missing columns
            if not has_created_by:
                await conn.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN created_by_id INTEGER 
                    REFERENCES users(user_id) ON DELETE SET NULL;
                """)
                
                # Add index for performance
                await conn.execute(f"""
                    CREATE INDEX idx_{table_name}_created_by 
                    ON {table_name}(created_by_id);
                """)
                
            if not has_updated_by:
                await conn.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN updated_by_id INTEGER 
                    REFERENCES users(user_id) ON DELETE SET NULL;
                """)
                
                # Add index for performance
                await conn.execute(f"""
                    CREATE INDEX idx_{table_name}_updated_by 
                    ON {table_name}(updated_by_id);
                """)
            
            # Add comments to columns
            await conn.execute(f"""
                COMMENT ON COLUMN {table_name}.created_by_id 
                IS 'ID of user who created this record';
            """)
            
            await conn.execute(f"""
                COMMENT ON COLUMN {table_name}.updated_by_id 
                IS 'ID of user who last updated this record';
            """)
            
            return True, "Audit columns added successfully"
            
        except Exception as e:
            return False, str(e)
    
    async def remove_audit_columns(self, conn, table_name: str) -> Tuple[bool, str]:
        """Remove audit columns from a table (for rollback)"""
        try:
            # Drop indexes first
            await conn.execute(f"DROP INDEX IF EXISTS idx_{table_name}_created_by;")
            await conn.execute(f"DROP INDEX IF EXISTS idx_{table_name}_updated_by;")
            
            # Drop columns
            await conn.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS created_by_id;")
            await conn.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS updated_by_id;")
            
            return True, "Audit columns removed successfully"
            
        except Exception as e:
            return False, str(e)
    
    async def run_migration(self):
        """Run the migration to add audit fields"""
        logger.info("="*80)
        logger.info("AUDIT FIELDS MIGRATION - ADD")
        logger.info("="*80)
        
        conn = await asyncpg.connect(self.db_url)
        
        try:
            # Get all tables
            tables = await self.get_all_tables(conn)
            logger.info(f"Found {len(tables)} tables in database")
            
            # Filter out excluded tables
            tables_to_update = [t for t in tables if t not in self.EXCLUDED_TABLES]
            logger.info(f"Will process {len(tables_to_update)} tables")
            
            # Process each table
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for table in tables_to_update:
                # Check if table already has existing tracking
                if table in self.TABLES_WITH_EXISTING_TRACKING:
                    existing_cols = self.TABLES_WITH_EXISTING_TRACKING[table]
                    logger.info(f"⚠️  {table}: Has existing tracking columns {existing_cols}, adding standard audit fields")
                
                success, message = await self.add_audit_columns(conn, table)
                
                if success:
                    if "Already has" in message:
                        logger.info(f"✓ {table}: {message}")
                        skip_count += 1
                    else:
                        logger.info(f"✓ {table}: {message}")
                        success_count += 1
                else:
                    logger.error(f"✗ {table}: {message}")
                    error_count += 1
            
            # Summary
            logger.info("\n" + "="*80)
            logger.info("MIGRATION SUMMARY")
            logger.info("="*80)
            logger.info(f"Total tables processed: {len(tables_to_update)}")
            logger.info(f"Successfully updated: {success_count}")
            logger.info(f"Already had audit fields: {skip_count}")
            logger.info(f"Errors: {error_count}")
            
            if error_count == 0:
                logger.info("\n✅ Migration completed successfully!")
            else:
                logger.warning(f"\n⚠️  Migration completed with {error_count} errors")
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            await conn.close()
    
    async def run_rollback(self):
        """Rollback the migration by removing audit fields"""
        logger.info("="*80)
        logger.info("AUDIT FIELDS MIGRATION - ROLLBACK")
        logger.info("="*80)
        
        conn = await asyncpg.connect(self.db_url)
        
        try:
            # Get all tables
            tables = await self.get_all_tables(conn)
            tables_to_update = [t for t in tables if t not in self.EXCLUDED_TABLES]
            
            # Process each table
            success_count = 0
            error_count = 0
            
            for table in tables_to_update:
                success, message = await self.remove_audit_columns(conn, table)
                
                if success:
                    logger.info(f"✓ {table}: {message}")
                    success_count += 1
                else:
                    logger.error(f"✗ {table}: {message}")
                    error_count += 1
            
            # Summary
            logger.info("\n" + "="*80)
            logger.info(f"Rollback completed: {success_count} tables processed, {error_count} errors")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise
        finally:
            await conn.close()


def main():
    """Main entry point"""
    import sys
    
    migration = AuditFieldsMigration()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        logger.info("Running rollback...")
        asyncio.run(migration.run_rollback())
    else:
        asyncio.run(migration.run_migration())


if __name__ == "__main__":
    main()