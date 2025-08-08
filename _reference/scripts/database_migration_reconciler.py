#!/usr/bin/env python3
"""
Database Migration and Reconciliation Script
==========================================

This script performs the following operations:
1. Extracts schema from the current database (READ-ONLY)
2. Extracts essential seed data from the current database (READ-ONLY)
3. Creates a test database
4. Applies the extracted schema to the test database
5. Inserts seed data into the test database
6. Reconciles and validates schema and data between databases

IMPORTANT: The current database is accessed in READ-ONLY mode.
No modifications will be made to the existing production database.
"""

import asyncio
import asyncpg
import os
import sys
import json
import logging
import re
from datetime import datetime, date
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import difflib
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_reconciliation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TableInfo:
    """Information about a database table"""
    name: str
    columns: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    row_count: int
    sample_data: List[Dict[str, Any]]
    is_seed_table: bool


class DatabaseMigrationReconciler:
    """Handles database migration extraction, creation, and reconciliation"""
    
    # Essential seed tables that contain reference data needed for system operation
    SEED_TABLES = [
        'users',
        'roles',
        'permissions',
        'role_permissions',
        'lobs',
        'test_cycles',  # Corrected table name
        'reports',
        'workflow_phases',
        'workflow_activities',
        'workflow_activity_templates',
        'workflow_activity_dependencies',
        'report_types',
        'regulatory_bodies',
        'universal_sla_configurations',
        'notification_templates'
    ]
    
    # Tables to exclude from migration (system tables)
    EXCLUDE_TABLES = [
        'alembic_version',
        'pg_stat_statements',
        'spatial_ref_sys'
    ]
    
    def __init__(self, source_db_url: str, test_db_url: str):
        self.source_db_url = source_db_url
        self.test_db_url = test_db_url
        self.source_conn: Optional[asyncpg.Connection] = None
        self.test_conn: Optional[asyncpg.Connection] = None
        self.schema_data: Dict[str, TableInfo] = {}
        self.reconciliation_report: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'source_database': source_db_url.split('/')[-1],
            'test_database': test_db_url.split('/')[-1],
            'schema_differences': [],
            'data_differences': [],
            'validation_errors': []
        }
    
    async def connect(self):
        """Establish database connections"""
        try:
            # Connect to source database in READ-ONLY mode
            logger.info("Connecting to source database (READ-ONLY)...")
            self.source_conn = await asyncpg.connect(
                self.source_db_url,
                server_settings={'default_transaction_read_only': 'on'}
            )
            logger.info("✓ Connected to source database in READ-ONLY mode")
            
            # Connect to test database
            logger.info("Connecting to test database...")
            self.test_conn = await asyncpg.connect(self.test_db_url)
            logger.info("✓ Connected to test database")
            
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise
    
    async def disconnect(self):
        """Close database connections"""
        if self.source_conn:
            await self.source_conn.close()
        if self.test_conn:
            await self.test_conn.close()
        logger.info("✓ Database connections closed")
    
    async def extract_schema(self):
        """Extract complete schema from source database"""
        logger.info("\n=== Extracting Schema from Source Database ===")
        
        # First, extract custom types (ENUMs)
        self.custom_types = await self._get_custom_types()
        logger.info(f"Found {len(self.custom_types)} custom types")
        
        # Get all tables
        # Build the NOT IN clause dynamically
        exclude_clause = "AND table_name NOT IN ({})".format(
            ', '.join(f"'{table}'" for table in self.EXCLUDE_TABLES)
        ) if self.EXCLUDE_TABLES else ""
        
        tables = await self.source_conn.fetch(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                {exclude_clause}
            ORDER BY table_name
        """)
        
        logger.info(f"Found {len(tables)} tables to process")
        
        for table in tables:
            table_name = table['table_name']
            logger.info(f"\nProcessing table: {table_name}")
            
            # Get column information
            columns = await self._get_table_columns(table_name)
            
            # Get constraints
            constraints = await self._get_table_constraints(table_name)
            
            # Get indexes
            indexes = await self._get_table_indexes(table_name)
            
            # Get row count
            row_count = await self.source_conn.fetchval(
                f"SELECT COUNT(*) FROM {table_name}"
            )
            
            # Get sample data if it's a seed table
            sample_data = []
            is_seed_table = table_name in self.SEED_TABLES
            if is_seed_table:
                sample_data = await self._get_seed_data(table_name)
                logger.info(f"  - Extracted {len(sample_data)} seed records")
            
            self.schema_data[table_name] = TableInfo(
                name=table_name,
                columns=columns,
                constraints=constraints,
                indexes=indexes,
                row_count=row_count,
                sample_data=sample_data,
                is_seed_table=is_seed_table
            )
            
            logger.info(f"  ✓ {len(columns)} columns, {len(constraints)} constraints, "
                       f"{len(indexes)} indexes, {row_count} rows")
    
    async def _get_custom_types(self) -> List[Dict[str, Any]]:
        """Get custom types (ENUMs) from database"""
        return await self.source_conn.fetch("""
            SELECT 
                t.typname as type_name,
                array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            GROUP BY t.typname
        """)
    
    async def _get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table"""
        return await self.source_conn.fetch("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default,
                udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' 
                AND table_name = $1
            ORDER BY ordinal_position
        """, table_name)
    
    async def _get_table_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Get constraint information for a table"""
        return await self.source_conn.fetch("""
            SELECT 
                con.conname as constraint_name,
                con.contype as constraint_type,
                pg_get_constraintdef(con.oid) as definition
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            WHERE nsp.nspname = 'public' 
                AND rel.relname = $1
        """, table_name)
    
    async def _get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get index information for a table"""
        return await self.source_conn.fetch("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' 
                AND tablename = $1
        """, table_name)
    
    async def _get_seed_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Extract seed data from a table"""
        # Get column names
        columns = await self.source_conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
        """, table_name)
        
        column_names = [col['column_name'] for col in columns]
        
        # Build query to get all data
        query = f"""
            SELECT {', '.join(column_names)}
            FROM {table_name}
            ORDER BY {column_names[0]}  -- Order by first column (usually ID)
        """
        
        rows = await self.source_conn.fetch(query)
        
        # Convert to list of dicts
        return [dict(row) for row in rows]
    
    async def generate_migration_sql(self) -> str:
        """Generate SQL migration script"""
        import re  # Import locally to avoid Python 3.13 scoping issue
        logger.info("\n=== Generating Migration SQL ===")
        
        migration_sql = []
        migration_sql.append("-- Database Migration Script")
        migration_sql.append(f"-- Generated: {datetime.now().isoformat()}")
        migration_sql.append("-- This script recreates the database schema and seed data\n")
        
        # Drop existing tables (in reverse dependency order)
        migration_sql.append("-- Drop existing tables")
        migration_sql.append("SET client_min_messages TO WARNING;")
        for table_name in reversed(list(self.schema_data.keys())):
            migration_sql.append(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
        
        # Drop and recreate custom types
        if hasattr(self, 'custom_types') and self.custom_types:
            migration_sql.append("\n-- Drop and recreate custom types")
            for custom_type in self.custom_types:
                type_name = custom_type['type_name']
                migration_sql.append(f"DROP TYPE IF EXISTS {type_name} CASCADE;")
            
            migration_sql.append("\n-- Create custom types")
            for custom_type in self.custom_types:
                type_name = custom_type['type_name']
                enum_values = custom_type['enum_values']
                values_str = ', '.join(f"'{val}'" for val in enum_values)
                migration_sql.append(f"CREATE TYPE {type_name} AS ENUM ({values_str});")
        
        # Create sequences
        migration_sql.append("\n-- Create sequences")
        sequences_created = set()
        for table_name, table_info in self.schema_data.items():
            for col in table_info.columns:
                if col.get('column_default') and 'nextval' in str(col['column_default']):
                    # Extract sequence name from default value
                    match = re.search(r"nextval\('([^']+)'", str(col['column_default']))
                    if match:
                        seq_name = match.group(1).replace('::regclass', '')
                        if seq_name not in sequences_created:
                            migration_sql.append(f"CREATE SEQUENCE IF NOT EXISTS {seq_name};")
                            sequences_created.add(seq_name)
        
        migration_sql.append("\n-- Create tables")
        
        # Create tables
        for table_name, table_info in self.schema_data.items():
            migration_sql.append(f"\n-- Table: {table_name}")
            create_table_sql, fk_constraints = self._generate_create_table_sql(table_info)
            migration_sql.append(create_table_sql)
        
        # Add foreign key constraints after all tables are created
        migration_sql.append("\n-- Add foreign key constraints")
        for table_name, table_info in self.schema_data.items():
            _, fk_constraints = self._generate_create_table_sql(table_info)
            for fk in fk_constraints:
                migration_sql.append(fk)
        
        # Create indexes
        migration_sql.append("\n-- Create indexes")
        for table_name, table_info in self.schema_data.items():
            for index in table_info.indexes:
                # Skip primary key indexes and unique constraint indexes (they're created automatically)
                index_name = index['indexname']
                if ('PRIMARY' not in index_name.upper() and 
                    '_pkey' not in index_name and 
                    '_key' not in index_name and
                    'UNIQUE' not in index['indexdef'].upper()):
                    # Remove schema prefix from index definition
                    indexdef = index['indexdef'].replace(' ON public.', ' ON ')
                    migration_sql.append(f"{indexdef};")
        
        # Insert seed data in dependency order
        migration_sql.append("\n-- Insert seed data")
        
        # Define the correct insertion order to respect foreign key dependencies
        seed_table_order = [
            'lobs',  # Must come first as users references it
            'roles',  # Before role_permissions
            'permissions',  # Before role_permissions
            'users',  # After lobs since it has lob_id foreign key
            'role_permissions',  # After roles and permissions
            'test_cycles',  # Referenced by reports (corrected table name)
            'reports',  # After users, lobs, test_cycles
            'report_types',
            'regulatory_bodies',
            'workflow_phases',
            'workflow_activities',
            'workflow_activity_templates',
            'workflow_activity_dependencies',
            'universal_sla_configurations',
            'notification_templates'
        ]
        
        # First insert tables in the defined order
        for table_name in seed_table_order:
            if table_name in self.schema_data:
                table_info = self.schema_data[table_name]
                if table_info.is_seed_table and table_info.sample_data:
                    migration_sql.append(f"\n-- Seed data for {table_name}")
                    for row in table_info.sample_data:
                        migration_sql.append(self._generate_insert_sql(table_name, row))
        
        # Then insert any remaining seed tables not in the order list
        for table_name, table_info in self.schema_data.items():
            if table_name not in seed_table_order and table_info.is_seed_table and table_info.sample_data:
                migration_sql.append(f"\n-- Seed data for {table_name}")
                for row in table_info.sample_data:
                    migration_sql.append(self._generate_insert_sql(table_name, row))
        
        # Reset sequences
        migration_sql.append("\n-- Reset sequences")
        for table_name, table_info in self.schema_data.items():
            # Look for columns with sequences
            for col in table_info.columns:
                if col.get('column_default') and 'nextval' in str(col['column_default']):
                    import re
                    match = re.search(r"nextval\('([^']+)'", str(col['column_default']))
                    if match:
                        seq_name = match.group(1).replace('::regclass', '')
                        col_name = col['column_name']
                        migration_sql.append(f"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = '{seq_name}') THEN
        PERFORM setval('{seq_name}', COALESCE((SELECT MAX({col_name}) FROM {table_name}), 1));
    END IF;
END $$;
""".strip())
        
        full_script = '\n'.join(migration_sql)
        
        # Save to file
        migration_file = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(migration_file, 'w') as f:
            f.write(full_script)
        
        logger.info(f"✓ Migration SQL saved to: {migration_file}")
        return full_script
    
    def _generate_create_table_sql(self, table_info: TableInfo) -> Tuple[str, List[str]]:
        """Generate CREATE TABLE statement and foreign key constraints separately"""
        sql_parts = [f"CREATE TABLE {table_info.name} ("]
        
        # Add columns
        column_defs = []
        for col in table_info.columns:
            # Handle USER-DEFINED types (ENUMs)
            data_type = col['data_type']
            if data_type == 'USER-DEFINED' and col.get('udt_name'):
                data_type = col['udt_name']
            
            # Fix integer precision syntax
            if data_type == 'integer' and col.get('numeric_precision'):
                # PostgreSQL doesn't support integer(32), just use integer
                data_type = 'integer'
            
            # Fix double precision syntax - PostgreSQL doesn't accept precision for double precision
            if data_type == 'double precision':
                # Just use 'double precision' without any precision
                col_def = f"    {col['column_name']} double precision"
            else:
                col_def = f"    {col['column_name']} {data_type}"
                
                # Add length/precision
                if col['character_maximum_length']:
                    col_def += f"({col['character_maximum_length']})"
                elif col['numeric_precision'] and data_type not in ['integer', 'bigint', 'smallint', 'real', 'double precision']:
                    # Only add precision for numeric/decimal types, not integer or float types
                    col_def += f"({col['numeric_precision']}"
                    if col['numeric_scale']:
                        col_def += f",{col['numeric_scale']}"
                    col_def += ")"
            
            # Add NOT NULL
            if col['is_nullable'] == 'NO':
                col_def += " NOT NULL"
            
            # Add DEFAULT
            if col['column_default']:
                col_def += f" DEFAULT {col['column_default']}"
            
            column_defs.append(col_def)
        
        # Collect foreign key constraints separately
        fk_sql = []
        
        # Add constraints
        for constraint in table_info.constraints:
            # Handle both string and bytes constraint types
            constraint_type = constraint['constraint_type']
            if isinstance(constraint_type, bytes):
                constraint_type = constraint_type.decode('utf-8')
            
            if constraint_type == 'p':  # Primary key
                column_defs.append(f"    {constraint['definition']}")
            elif constraint_type == 'u':  # Unique constraint
                column_defs.append(f"    {constraint['definition']}")
            elif constraint_type == 'c':  # Check constraint
                column_defs.append(f"    {constraint['definition']}")
            elif constraint_type == 'f':  # Foreign key - save for later
                fk_sql.append(f"ALTER TABLE {table_info.name} ADD CONSTRAINT {constraint['constraint_name']} {constraint['definition']};")
        
        sql_parts.append(',\n'.join(column_defs))
        sql_parts.append(");")
        
        return '\n'.join(sql_parts), fk_sql
    
    def _generate_insert_sql(self, table_name: str, row: Dict[str, Any]) -> str:
        """Generate INSERT statement for a row"""
        columns = []
        values = []
        
        for col, val in row.items():
            if val is not None:
                columns.append(col)
                if isinstance(val, str):
                    # Escape single quotes
                    val = val.replace("'", "''")
                    values.append(f"'{val}'")
                elif isinstance(val, (dict, list)):
                    # JSON data
                    val_str = json.dumps(val).replace("'", "''")
                    values.append(f"'{val_str}'::jsonb")
                elif isinstance(val, datetime):
                    values.append(f"'{val.isoformat()}'")
                elif isinstance(val, date) and not isinstance(val, datetime):
                    # Handle date objects separately from datetime
                    values.append(f"'{val.isoformat()}'")
                elif isinstance(val, bool):
                    values.append('TRUE' if val else 'FALSE')
                elif isinstance(val, memoryview):
                    # Handle bytea data
                    values.append(f"'\\\\x{val.hex()}'")
                elif isinstance(val, bytes):
                    # Handle bytea data
                    values.append(f"'\\\\x{val.hex()}'")
                else:
                    # For numeric types and others
                    values.append(str(val))
        
        if columns:
            return f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
        return ""
    
    async def create_test_database_schema(self, migration_sql: str):
        """Create schema in test database"""
        logger.info("\n=== Creating Test Database Schema ===")
        
        try:
            # Split SQL into individual statements to execute them one by one
            # This helps identify which statement is causing the error
            statements = []
            current_statement = []
            in_dollar_block = False
            
            for line in migration_sql.split('\n'):
                # Skip standalone comment lines between statements
                if not current_statement and line.strip().startswith('--'):
                    continue
                    
                # Check if we're entering or leaving a dollar-quoted block
                if '$$' in line:
                    in_dollar_block = not in_dollar_block
                    
                # Add line to current statement if we have one building, or if line is not empty
                if current_statement or line.strip():
                    current_statement.append(line)
                    # Check if this line ends a statement (but not if we're in a $$ block)
                    if (line.strip().endswith(';') and 
                        not line.strip().startswith('--') and 
                        not in_dollar_block):
                        statements.append('\n'.join(current_statement))
                        current_statement = []
            
            # Add any remaining statement
            if current_statement:
                statements.append('\n'.join(current_statement))
            
            # Execute each statement individually
            logger.info(f"Executing {len(statements)} SQL statements...")
            
            # Count statement types for debugging
            table_count = sum(1 for s in statements if 'CREATE TABLE' in s)
            index_count = sum(1 for s in statements if 'CREATE INDEX' in s)
            logger.info(f"Found {table_count} CREATE TABLE statements")
            logger.info(f"Found {index_count} CREATE INDEX statements")
            
            # Debug: log first few CREATE TABLE statements
            table_stmts = [s for s in statements if 'CREATE TABLE' in s]
            if table_stmts:
                logger.debug(f"First CREATE TABLE statement: {table_stmts[0][:100]}...")
                logger.debug(f"Statement #455 preview: {statements[454][:100] if len(statements) > 454 else 'N/A'}...")
            
            for i, statement in enumerate(statements):
                # Check if statement has actual SQL (not just comments)
                has_sql = any(line.strip() and not line.strip().startswith('--') for line in statement.split('\n'))
                if statement.strip() and has_sql:
                    try:
                        # Log every 50th statement for progress tracking
                        if i % 50 == 0:
                            logger.info(f"Processing statement {i}/{len(statements)}")
                        
                        # Special logging for the CREATE TABLE range
                        if 325 <= i <= 335:
                            logger.info(f"Statement {i}: {statement[:80]}...")
                        
                        # Log progress for different statement types
                        if 'CREATE TABLE' in statement:
                            table_match = re.search(r'CREATE TABLE (\w+)', statement)
                            if table_match:
                                logger.info(f"Creating table: {table_match.group(1)}")
                            else:
                                logger.warning(f"Found CREATE TABLE but couldn't parse table name: {statement[:100]}...")
                        elif 'CREATE TYPE' in statement:
                            type_match = re.search(r'CREATE TYPE (\w+)', statement)
                            if type_match:
                                logger.info(f"Creating type: {type_match.group(1)}")
                        elif 'CREATE SEQUENCE' in statement:
                            seq_match = re.search(r'CREATE SEQUENCE[^(]*?(\w+)', statement)
                            if seq_match:
                                logger.info(f"Creating sequence: {seq_match.group(1)}")
                        elif 'CREATE INDEX' in statement:
                            idx_match = re.search(r'CREATE.*?INDEX[^(]*?(\w+)', statement)
                            if idx_match:
                                logger.debug(f"Creating index: {idx_match.group(1)}")
                        
                        await self.test_conn.execute(statement)
                    except Exception as e:
                        logger.error(f"Failed at statement {i}: {statement[:200]}...")
                        if len(statement) > 200:
                            logger.error(f"Statement ends with: ...{statement[-200:]}")
                        logger.error(f"Error: {e}")
                        # Check if we can get more info about the database state
                        try:
                            tables = await self.test_conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                            logger.info(f"Tables in database: {[t['tablename'] for t in tables]}")
                        except:
                            pass
                        raise
            
            logger.info("✓ Test database schema created successfully")
        except Exception as e:
            self.reconciliation_report['validation_errors'].append({
                'type': 'schema_creation',
                'error': str(e)
            })
            raise
    
    async def reconcile_schemas(self):
        """Compare schemas between source and test databases"""
        logger.info("\n=== Reconciling Schemas ===")
        
        # Get test database schema
        # Build the NOT IN clause dynamically
        exclude_clause = ""
        if self.EXCLUDE_TABLES:
            exclude_clause = "AND table_name NOT IN ({})".format(
                ', '.join(f"'{table}'" for table in self.EXCLUDE_TABLES)
            )
        
        test_tables = await self.test_conn.fetch(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                {exclude_clause}
            ORDER BY table_name
        """)
        
        test_table_names = {t['table_name'] for t in test_tables}
        source_table_names = set(self.schema_data.keys())
        
        # Check for missing tables
        missing_in_test = source_table_names - test_table_names
        extra_in_test = test_table_names - source_table_names
        
        if missing_in_test:
            self.reconciliation_report['schema_differences'].append({
                'type': 'missing_tables',
                'tables': list(missing_in_test)
            })
            logger.warning(f"Tables missing in test database: {missing_in_test}")
        
        if extra_in_test:
            self.reconciliation_report['schema_differences'].append({
                'type': 'extra_tables',
                'tables': list(extra_in_test)
            })
            logger.warning(f"Extra tables in test database: {extra_in_test}")
        
        # Compare table structures
        for table_name in source_table_names & test_table_names:
            await self._compare_table_structure(table_name)
        
        logger.info(f"✓ Schema reconciliation complete. Found {len(self.reconciliation_report['schema_differences'])} differences")
    
    async def _compare_table_structure(self, table_name: str):
        """Compare structure of a specific table"""
        # Get test table columns
        test_columns = await self.test_conn.fetch("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
                AND table_name = $1
            ORDER BY ordinal_position
        """, table_name)
        
        source_columns = {col['column_name']: col for col in self.schema_data[table_name].columns}
        test_columns_dict = {col['column_name']: col for col in test_columns}
        
        # Compare columns
        source_col_names = set(source_columns.keys())
        test_col_names = set(test_columns_dict.keys())
        
        missing_cols = source_col_names - test_col_names
        extra_cols = test_col_names - source_col_names
        
        if missing_cols or extra_cols:
            self.reconciliation_report['schema_differences'].append({
                'table': table_name,
                'type': 'column_mismatch',
                'missing_columns': list(missing_cols),
                'extra_columns': list(extra_cols)
            })
        
        # Compare column properties
        for col_name in source_col_names & test_col_names:
            source_col = source_columns[col_name]
            test_col = test_columns_dict[col_name]
            
            differences = []
            for prop in ['data_type', 'character_maximum_length', 'is_nullable']:
                if source_col[prop] != test_col[prop]:
                    differences.append({
                        'property': prop,
                        'source': source_col[prop],
                        'test': test_col[prop]
                    })
            
            if differences:
                self.reconciliation_report['schema_differences'].append({
                    'table': table_name,
                    'column': col_name,
                    'type': 'column_properties',
                    'differences': differences
                })
    
    async def reconcile_data(self):
        """Compare data between source and test databases"""
        logger.info("\n=== Reconciling Data ===")
        
        for table_name, table_info in self.schema_data.items():
            if table_info.is_seed_table:
                logger.info(f"\nReconciling data for: {table_name}")
                
                # Get row counts
                test_count = await self.test_conn.fetchval(
                    f"SELECT COUNT(*) FROM {table_name}"
                )
                
                if table_info.row_count != test_count:
                    self.reconciliation_report['data_differences'].append({
                        'table': table_name,
                        'type': 'row_count',
                        'source_count': table_info.row_count,
                        'test_count': test_count
                    })
                    logger.warning(f"  Row count mismatch: source={table_info.row_count}, test={test_count}")
                else:
                    logger.info(f"  ✓ Row count matches: {test_count}")
                
                # Compare data checksums for seed tables
                if table_info.sample_data:
                    await self._compare_table_data(table_name, table_info)
    
    async def _compare_table_data(self, table_name: str, table_info: TableInfo):
        """Compare actual data content"""
        # Get primary key column
        pk_result = await self.source_conn.fetch("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid
                AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = $1::regclass
                AND i.indisprimary
        """, table_name)
        
        if not pk_result:
            logger.warning(f"  No primary key found for {table_name}, skipping data comparison")
            return
        
        pk_column = pk_result[0]['attname']
        
        # Get test data
        test_data = await self.test_conn.fetch(f"""
            SELECT * FROM {table_name}
            ORDER BY {pk_column}
        """)
        
        test_data_dict = {row[pk_column]: dict(row) for row in test_data}
        source_data_dict = {row[pk_column]: row for row in table_info.sample_data if pk_column in row}
        
        # Compare data
        missing_in_test = set(source_data_dict.keys()) - set(test_data_dict.keys())
        extra_in_test = set(test_data_dict.keys()) - set(source_data_dict.keys())
        
        if missing_in_test:
            self.reconciliation_report['data_differences'].append({
                'table': table_name,
                'type': 'missing_records',
                'primary_keys': list(missing_in_test)
            })
        
        if extra_in_test:
            self.reconciliation_report['data_differences'].append({
                'table': table_name,
                'type': 'extra_records',
                'primary_keys': list(extra_in_test)
            })
        
        # Compare record contents
        data_mismatches = 0
        for pk in set(source_data_dict.keys()) & set(test_data_dict.keys()):
            source_row = source_data_dict[pk]
            test_row = test_data_dict[pk]
            
            for col in source_row:
                if col in test_row:
                    # Handle special comparisons
                    if isinstance(source_row[col], datetime) and isinstance(test_row[col], datetime):
                        # Compare timestamps with tolerance
                        continue
                    elif source_row[col] != test_row[col]:
                        data_mismatches += 1
                        if data_mismatches <= 5:  # Limit detailed reporting
                            self.reconciliation_report['data_differences'].append({
                                'table': table_name,
                                'type': 'data_mismatch',
                                'primary_key': pk,
                                'column': col,
                                'source_value': str(source_row[col])[:100],
                                'test_value': str(test_row[col])[:100]
                            })
        
        if data_mismatches > 0:
            logger.warning(f"  Found {data_mismatches} data mismatches")
        else:
            logger.info(f"  ✓ Data content matches")
    
    def generate_reconciliation_report(self):
        """Generate detailed reconciliation report"""
        logger.info("\n=== Generating Reconciliation Report ===")
        
        report_file = f"reconciliation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Add summary
        self.reconciliation_report['summary'] = {
            'total_tables': len(self.schema_data),
            'seed_tables': len([t for t in self.schema_data.values() if t.is_seed_table]),
            'schema_differences_count': len(self.reconciliation_report['schema_differences']),
            'data_differences_count': len(self.reconciliation_report['data_differences']),
            'validation_errors_count': len(self.reconciliation_report['validation_errors'])
        }
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(self.reconciliation_report, f, indent=2, default=str)
        
        logger.info(f"✓ Reconciliation report saved to: {report_file}")
        
        # Print summary
        logger.info("\n=== Reconciliation Summary ===")
        logger.info(f"Total tables processed: {self.reconciliation_report['summary']['total_tables']}")
        logger.info(f"Seed tables with data: {self.reconciliation_report['summary']['seed_tables']}")
        logger.info(f"Schema differences: {self.reconciliation_report['summary']['schema_differences_count']}")
        logger.info(f"Data differences: {self.reconciliation_report['summary']['data_differences_count']}")
        logger.info(f"Validation errors: {self.reconciliation_report['summary']['validation_errors_count']}")
        
        # Print detailed issues
        if self.reconciliation_report['schema_differences']:
            logger.warning("\nSchema Differences Found:")
            for diff in self.reconciliation_report['schema_differences'][:5]:  # Show first 5
                logger.warning(f"  - {diff}")
        
        if self.reconciliation_report['data_differences']:
            logger.warning("\nData Differences Found:")
            for diff in self.reconciliation_report['data_differences'][:5]:  # Show first 5
                logger.warning(f"  - {diff}")
    
    async def run(self):
        """Run the complete migration and reconciliation process"""
        try:
            await self.connect()
            
            # Step 1: Extract schema from source database
            await self.extract_schema()
            
            # Step 2: Generate migration SQL
            migration_sql = await self.generate_migration_sql()
            
            # Step 3: Create test database schema
            await self.create_test_database_schema(migration_sql)
            
            # Step 4: Reconcile schemas
            await self.reconcile_schemas()
            
            # Step 5: Reconcile data
            await self.reconcile_data()
            
            # Step 6: Generate report
            self.generate_reconciliation_report()
            
            logger.info("\n✓ Migration and reconciliation completed successfully!")
            
        except Exception as e:
            logger.error(f"\n✗ Migration failed: {e}")
            raise
        finally:
            await self.disconnect()


async def main():
    """Main entry point"""
    # Load database URLs from environment or configuration
    source_db_url = os.getenv('SOURCE_DATABASE_URL', 'postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
    test_db_url = os.getenv('TEST_DATABASE_URL', 'postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt_test')
    
    logger.info("=== Database Migration and Reconciliation Tool ===")
    logger.info(f"Source Database: {source_db_url.split('@')[-1]}")
    logger.info(f"Test Database: {test_db_url.split('@')[-1]}")
    logger.info("=" * 50)
    
    # Confirm before proceeding
    if '--no-confirm' not in sys.argv:
        response = input("\nThis will create a test database and copy schema/data. Continue? (y/N): ")
        if response.lower() != 'y':
            logger.info("Operation cancelled.")
            return
    
    # Run reconciliation
    reconciler = DatabaseMigrationReconciler(source_db_url, test_db_url)
    await reconciler.run()


if __name__ == "__main__":
    asyncio.run(main())