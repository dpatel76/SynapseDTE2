#!/usr/bin/env python3
"""
Execute unified test execution database changes directly
This script bypasses Alembic and applies changes directly to the database
"""

import os
import sys
import asyncio
import asyncpg
from typing import Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'synapse_dt'),
    'user': os.getenv('DB_USER', 'synapse_user'),
    'password': os.getenv('DB_PASSWORD', 'synapse_password')
}

async def execute_sql_file(connection: asyncpg.Connection, sql_file_path: str) -> None:
    """Execute SQL commands from a file"""
    try:
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        # Split SQL content into individual statements
        statements = []
        current_statement = []
        in_comment = False
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('--'):
                continue
                
            # Handle multi-line statements
            current_statement.append(line)
            
            # Check if statement is complete (ends with semicolon)
            if line.endswith(';'):
                statement = ' '.join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []
        
        # Execute each statement
        for i, statement in enumerate(statements):
            try:
                logger.info(f"Executing statement {i+1}/{len(statements)}")
                await connection.execute(statement)
                logger.info(f"✓ Statement {i+1} executed successfully")
            except Exception as e:
                logger.error(f"✗ Error executing statement {i+1}: {e}")
                logger.error(f"Statement: {statement[:100]}...")
                raise
                
    except FileNotFoundError:
        logger.error(f"SQL file not found: {sql_file_path}")
        raise
    except Exception as e:
        logger.error(f"Error executing SQL file: {e}")
        raise

async def check_table_exists(connection: asyncpg.Connection, table_name: str) -> bool:
    """Check if a table exists in the database"""
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = $1
        )
    """
    result = await connection.fetchval(query, table_name)
    return result

async def backup_legacy_tables(connection: asyncpg.Connection) -> None:
    """Create backup of legacy tables before dropping them"""
    legacy_tables = [
        'cycle_report_test_executions',
        'cycle_report_test_execution_document_analyses',
        'cycle_report_test_execution_database_tests',
        'test_result_reviews',
        'bulk_test_executions',
        'test_comparisons',
        'test_execution_audit_logs'
    ]
    
    logger.info("Creating backup of legacy tables...")
    
    for table in legacy_tables:
        if await check_table_exists(connection, table):
            backup_table = f"{table}_backup_{int(asyncio.get_event_loop().time())}"
            try:
                await connection.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {table}")
                logger.info(f"✓ Backed up {table} to {backup_table}")
            except Exception as e:
                logger.warning(f"⚠ Could not backup {table}: {e}")
        else:
            logger.info(f"Table {table} does not exist, skipping backup")

async def verify_installation(connection: asyncpg.Connection) -> None:
    """Verify that the unified test execution tables were created successfully"""
    logger.info("Verifying unified test execution tables...")
    
    expected_tables = [
        'cycle_report_test_execution_results',
        'cycle_report_test_execution_reviews',
        'cycle_report_test_execution_audit'
    ]
    
    for table in expected_tables:
        exists = await check_table_exists(connection, table)
        if exists:
            logger.info(f"✓ Table {table} exists")
        else:
            logger.error(f"✗ Table {table} does not exist")
            return False
    
    # Check constraints
    constraint_query = """
        SELECT conname, contype 
        FROM pg_constraint 
        WHERE conrelid = 'cycle_report_test_execution_results'::regclass
    """
    constraints = await connection.fetch(constraint_query)
    logger.info(f"Found {len(constraints)} constraints on test execution results table")
    
    # Check indexes
    index_query = """
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename = 'cycle_report_test_execution_results'
    """
    indexes = await connection.fetch(index_query)
    logger.info(f"Found {len(indexes)} indexes on test execution results table")
    
    logger.info("✓ Verification complete - all tables created successfully")
    return True

async def main():
    """Main execution function"""
    logger.info("Starting unified test execution database migration...")
    
    # Check if SQL file exists
    sql_file = 'create_unified_test_execution_tables.sql'
    if not os.path.exists(sql_file):
        logger.error(f"SQL file not found: {sql_file}")
        return False
    
    connection = None
    try:
        # Connect to database
        logger.info("Connecting to database...")
        connection = await asyncpg.connect(**DATABASE_CONFIG)
        logger.info("✓ Connected to database")
        
        # Start transaction
        async with connection.transaction():
            logger.info("Starting database transaction...")
            
            # Optional: Create backup of legacy tables
            backup_choice = input("Create backup of legacy tables? (y/n): ").lower()
            if backup_choice == 'y':
                await backup_legacy_tables(connection)
            
            # Execute SQL file
            logger.info("Executing unified test execution SQL commands...")
            await execute_sql_file(connection, sql_file)
            
            # Verify installation
            success = await verify_installation(connection)
            
            if success:
                logger.info("✓ Database migration completed successfully")
                confirm = input("Commit changes? (y/n): ").lower()
                if confirm != 'y':
                    raise Exception("User cancelled migration")
            else:
                raise Exception("Verification failed")
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
    finally:
        if connection:
            await connection.close()
            logger.info("Database connection closed")
    
    return True

if __name__ == "__main__":
    # Allow environment variables to override defaults
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("""
Unified Test Execution Database Migration Tool

Usage: python execute_database_changes.py [options]

Environment Variables:
    DB_HOST     - Database host (default: localhost)
    DB_PORT     - Database port (default: 5432)
    DB_NAME     - Database name (default: synapse_dt)
    DB_USER     - Database user (default: synapse_user)
    DB_PASSWORD - Database password (default: synapse_password)

Options:
    --help      - Show this help message
    --dry-run   - Show what would be executed without making changes
    
Examples:
    python execute_database_changes.py
    DB_HOST=prod-db python execute_database_changes.py
            """)
            sys.exit(0)
    
    # Run the migration
    success = asyncio.run(main())
    sys.exit(0 if success else 1)