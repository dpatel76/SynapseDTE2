#!/usr/bin/env python3
"""
Complete Test Database Migration Script
Creates ALL 126 tables from source database with proper seed data
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompleteDatabaseMigration:
    """Complete database migration with all tables and seed data"""
    
    def __init__(self, test_db_name: str = "synapse_dt_test"):
        self.test_db_name = test_db_name
        
        # Get database URL
        db_url = os.getenv('DATABASE_URL', 'postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
        
        # Parse connection info
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        
        self.host = parsed.hostname
        self.port = parsed.port or 5432
        self.user = parsed.username
        self.password = parsed.password
        self.source_db = parsed.path.lstrip('/')
        
    async def drop_and_create_database(self):
        """Drop existing test database and create new one"""
        logger.info(f"Creating test database: {self.test_db_name}")
        
        # Connect to postgres database
        conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database='postgres'
        )
        
        try:
            # Drop test database if exists
            await conn.execute(f'DROP DATABASE IF EXISTS {self.test_db_name}')
            logger.info("Dropped existing test database if it existed")
            
            # Create test database
            await conn.execute(f'CREATE DATABASE {self.test_db_name}')
            logger.info(f"✓ Created test database: {self.test_db_name}")
            
        finally:
            await conn.close()
    
    async def copy_schema_from_source(self):
        """Copy complete schema from source database"""
        logger.info("Copying schema from source database...")
        
        # Connect to source database
        source_conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.source_db
        )
        
        # Connect to test database
        test_conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.test_db_name
        )
        
        try:
            # Step 1: Create all ENUM types first
            logger.info("Creating ENUM types...")
            enum_query = """
            SELECT 
                t.typname as enum_name,
                pg_catalog.format_type(t.oid, NULL) AS sql_definition
            FROM pg_type t 
            JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typtype = 'e' 
            AND n.nspname = 'public'
            ORDER BY t.typname;
            """
            
            enums = await source_conn.fetch(enum_query)
            
            # Get enum values for each type
            for enum in enums:
                enum_name = enum['enum_name']
                
                # Get enum values
                values_query = f"""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = '{enum_name}'::regtype
                ORDER BY enumsortorder
                """
                
                values = await source_conn.fetch(values_query)
                enum_values = [v['enumlabel'] for v in values]
                
                if enum_values:
                    values_str = ", ".join([f"'{v}'" for v in enum_values])
                    create_enum = f"CREATE TYPE {enum_name} AS ENUM ({values_str})"
                    
                    try:
                        await test_conn.execute(create_enum)
                        logger.info(f"  Created ENUM: {enum_name}")
                    except asyncpg.exceptions.DuplicateObjectError:
                        logger.info(f"  ENUM already exists: {enum_name}")
                    except Exception as e:
                        logger.error(f"  Failed to create ENUM {enum_name}: {e}")
            
            # Step 2: Get table creation order based on dependencies
            tables_query = """
            WITH RECURSIVE fk_tree AS (
                -- Start with tables that have no foreign keys
                SELECT 
                    c.oid,
                    c.relname as table_name,
                    0 as level
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                LEFT JOIN pg_constraint con ON con.conrelid = c.oid AND con.contype = 'f'
                WHERE c.relkind = 'r'
                AND n.nspname = 'public'
                GROUP BY c.oid, c.relname
                HAVING COUNT(con.oid) = 0
                
                UNION ALL
                
                -- Recursively find tables that depend on tables already in the list
                SELECT 
                    c.oid,
                    c.relname as table_name,
                    ft.level + 1
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_constraint con ON con.conrelid = c.oid AND con.contype = 'f'
                JOIN pg_class ref ON ref.oid = con.confrelid
                JOIN fk_tree ft ON ft.oid = ref.oid
                WHERE c.relkind = 'r'
                AND n.nspname = 'public'
                AND c.oid NOT IN (SELECT oid FROM fk_tree)
            )
            SELECT DISTINCT table_name, MIN(level) as dep_level
            FROM fk_tree
            GROUP BY table_name
            ORDER BY dep_level, table_name;
            """
            
            ordered_tables = await source_conn.fetch(tables_query)
            
            # If some tables weren't captured (circular dependencies), get remaining
            all_tables_query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
            all_tables = await source_conn.fetch(all_tables_query)
            all_table_names = {t['tablename'] for t in all_tables}
            ordered_table_names = {t['table_name'] for t in ordered_tables}
            remaining_tables = all_table_names - ordered_table_names
            
            # Step 3: Create tables in order
            logger.info(f"Creating {len(all_table_names)} tables...")
            
            # Create tables captured by dependency query first
            for table in ordered_tables:
                table_name = table['table_name']
                await self.copy_table_structure(source_conn, test_conn, table_name)
            
            # Create remaining tables
            for table_name in sorted(remaining_tables):
                await self.copy_table_structure(source_conn, test_conn, table_name)
            
            # Step 4: Create indexes
            logger.info("Creating indexes...")
            await self.copy_indexes(source_conn, test_conn)
            
            # Step 5: Create constraints (after all tables exist)
            logger.info("Creating constraints...")
            await self.copy_constraints(source_conn, test_conn)
            
        finally:
            await source_conn.close()
            await test_conn.close()
    
    async def copy_table_structure(self, source_conn, test_conn, table_name):
        """Copy a single table structure"""
        try:
            # Get table definition
            table_def_query = f"""
            SELECT 
                'CREATE TABLE ' || quote_ident(c.relname) || ' (' || 
                string_agg(
                    quote_ident(a.attname) || ' ' || 
                    pg_catalog.format_type(a.atttypid, a.atttypmod) ||
                    CASE 
                        WHEN a.attnotnull THEN ' NOT NULL'
                        ELSE ''
                    END ||
                    CASE 
                        WHEN a.atthasdef THEN ' DEFAULT ' || (
                            SELECT pg_catalog.pg_get_expr(d.adbin, d.adrelid)
                            FROM pg_catalog.pg_attrdef d
                            WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum
                        )
                        ELSE ''
                    END,
                    ', '
                    ORDER BY a.attnum
                ) || ');' as create_sql
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
            WHERE c.relname = '{table_name}'
            AND n.nspname = 'public'
            AND a.attnum > 0
            AND NOT a.attisdropped
            GROUP BY c.relname;
            """
            
            result = await source_conn.fetchrow(table_def_query)
            if result and result['create_sql']:
                # Execute create table
                await test_conn.execute(result['create_sql'])
                logger.info(f"  Created table: {table_name}")
            
        except Exception as e:
            logger.error(f"  Failed to create table {table_name}: {e}")
    
    async def copy_indexes(self, source_conn, test_conn):
        """Copy all indexes"""
        index_query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND indexname NOT LIKE '%_pkey'  -- Skip primary keys
        ORDER BY tablename, indexname;
        """
        
        indexes = await source_conn.fetch(index_query)
        
        for idx in indexes:
            try:
                await test_conn.execute(idx['indexdef'])
                logger.info(f"  Created index: {idx['indexname']}")
            except asyncpg.exceptions.DuplicateObjectError:
                pass  # Index already exists
            except Exception as e:
                logger.error(f"  Failed to create index {idx['indexname']}: {e}")
    
    async def copy_constraints(self, source_conn, test_conn):
        """Copy all constraints"""
        # Primary keys
        pk_query = """
        SELECT 
            'ALTER TABLE ' || quote_ident(n.nspname) || '.' || quote_ident(c.relname) || 
            ' ADD CONSTRAINT ' || quote_ident(con.conname) || ' PRIMARY KEY (' ||
            string_agg(quote_ident(a.attname), ', ' ORDER BY u.pos) || ');' as sql
        FROM pg_constraint con
        JOIN pg_class c ON c.oid = con.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN LATERAL unnest(con.conkey) WITH ORDINALITY u(attnum, pos) ON TRUE
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = u.attnum
        WHERE con.contype = 'p'
        AND n.nspname = 'public'
        GROUP BY n.nspname, c.relname, con.conname;
        """
        
        pks = await source_conn.fetch(pk_query)
        for pk in pks:
            try:
                await test_conn.execute(pk['sql'])
            except Exception as e:
                logger.error(f"  Failed to create primary key: {e}")
        
        # Foreign keys - try multiple times due to dependencies
        fk_query = """
        SELECT 
            'ALTER TABLE ' || quote_ident(n1.nspname) || '.' || quote_ident(c1.relname) || 
            ' ADD CONSTRAINT ' || quote_ident(con.conname) || 
            ' FOREIGN KEY (' || string_agg(quote_ident(a1.attname), ', ') || ')' ||
            ' REFERENCES ' || quote_ident(n2.nspname) || '.' || quote_ident(c2.relname) || 
            ' (' || string_agg(quote_ident(a2.attname), ', ') || ')' ||
            CASE 
                WHEN con.confupdtype = 'c' THEN ' ON UPDATE CASCADE'
                WHEN con.confupdtype = 'r' THEN ' ON UPDATE RESTRICT'
                ELSE ''
            END ||
            CASE 
                WHEN con.confdeltype = 'c' THEN ' ON DELETE CASCADE'
                WHEN con.confdeltype = 'r' THEN ' ON DELETE RESTRICT'
                ELSE ''
            END || ';' as sql
        FROM pg_constraint con
        JOIN pg_class c1 ON c1.oid = con.conrelid
        JOIN pg_namespace n1 ON n1.oid = c1.relnamespace
        JOIN pg_class c2 ON c2.oid = con.confrelid
        JOIN pg_namespace n2 ON n2.oid = c2.relnamespace
        JOIN LATERAL (
            SELECT a.attname, u.pos
            FROM unnest(con.conkey) WITH ORDINALITY u(attnum, pos)
            JOIN pg_attribute a ON a.attrelid = c1.oid AND a.attnum = u.attnum
        ) a1 ON TRUE
        JOIN LATERAL (
            SELECT a.attname, u.pos
            FROM unnest(con.confkey) WITH ORDINALITY u(attnum, pos)
            JOIN pg_attribute a ON a.attrelid = c2.oid AND a.attnum = u.attnum
        ) a2 ON TRUE
        WHERE con.contype = 'f'
        AND n1.nspname = 'public'
        AND a1.pos = a2.pos
        GROUP BY n1.nspname, c1.relname, con.conname, n2.nspname, c2.relname, 
                 con.confupdtype, con.confdeltype;
        """
        
        fks = await source_conn.fetch(fk_query)
        
        # Try creating FKs multiple times
        for attempt in range(3):
            failed_fks = []
            for fk in fks:
                try:
                    await test_conn.execute(fk['sql'])
                except Exception as e:
                    failed_fks.append(fk)
            
            fks = failed_fks
            if not fks:
                break
            
            if attempt < 2:
                logger.info(f"  Retrying {len(fks)} failed foreign keys...")
    
    async def seed_essential_data(self):
        """Seed essential data for system to function"""
        logger.info("Seeding essential data...")
        
        test_conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.test_db_name
        )
        
        try:
            # Seed in order of dependencies
            
            # 1. Roles
            await test_conn.execute("""
                INSERT INTO rbac_roles (role_name, description, is_system, is_active) VALUES 
                ('Admin', 'System administrator', true, true),
                ('Tester', 'Executes testing activities', true, true),
                ('Test Executive', 'Oversees testing operations', true, true),
                ('Report Owner', 'Owns specific regulatory reports', true, true),
                ('Report Owner Executive', 'Executive oversight for report owners', true, true),
                ('Data Owner', 'Provides data for testing', true, true),
                ('Data Executive', 'Executive oversight for data operations', true, true)
                ON CONFLICT (role_name) DO NOTHING;
            """)
            logger.info("  ✓ Seeded roles")
            
            # 2. LOBs
            await test_conn.execute("""
                INSERT INTO lobs (lob_name) VALUES 
                ('Retail Banking'),
                ('Commercial Banking'),
                ('Investment Banking'),
                ('Wealth Management'),
                ('Corporate Banking'),
                ('Private Banking'),
                ('Asset Management'),
                ('Capital Markets')
                ON CONFLICT (lob_name) DO NOTHING;
            """)
            logger.info("  ✓ Seeded LOBs")
            
            # 3. Users (with bcrypt hash for 'password123')
            password_hash = '$2b$12$iWH6wK2JpZl0X.HmoYzVn.LrWb8oXP3R5x7JLzLJYUkZ1kTvKHC8m'
            
            await test_conn.execute(f"""
                INSERT INTO users (username, email, first_name, last_name, hashed_password, role, lob_id, is_active) VALUES
                ('admin', 'admin@example.com', 'System', 'Administrator', '{password_hash}', 'Admin', 1, true),
                ('tester1', 'tester1@example.com', 'John', 'Tester', '{password_hash}', 'Tester', 1, true),
                ('tester2', 'tester2@example.com', 'Jane', 'Tester', '{password_hash}', 'Tester', 2, true),
                ('testmanager', 'test.manager@example.com', 'Test', 'Manager', '{password_hash}', 'Test Executive', 1, true),
                ('reportowner1', 'report.owner1@example.com', 'Jane', 'Owner', '{password_hash}', 'Report Owner', 1, true),
                ('reportowner2', 'report.owner2@example.com', 'Bob', 'Owner', '{password_hash}', 'Report Owner', 2, true),
                ('dataowner1', 'data.owner1@example.com', 'David', 'Data', '{password_hash}', 'Data Owner', 1, true),
                ('dataowner2', 'data.owner2@example.com', 'Diana', 'Data', '{password_hash}', 'Data Owner', 2, true),
                ('reportexec', 'report.executive@example.com', 'Sarah', 'Executive', '{password_hash}', 'Report Owner Executive', 1, true),
                ('dataexec', 'data.executive@example.com', 'Mike', 'DataExec', '{password_hash}', 'Data Executive', 1, true)
                ON CONFLICT (email) DO NOTHING;
            """)
            logger.info("  ✓ Seeded users")
            
            # 4. Permissions (copy from source if exists)
            source_conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.source_db
            )
            
            try:
                # Copy permissions
                permissions = await source_conn.fetch("SELECT * FROM rbac_permissions")
                if permissions:
                    for perm in permissions:
                        await test_conn.execute("""
                            INSERT INTO rbac_permissions (resource, action, description) 
                            VALUES ($1, $2, $3) 
                            ON CONFLICT (resource, action) DO NOTHING
                        """, perm['resource'], perm['action'], perm['description'])
                    logger.info(f"  ✓ Copied {len(permissions)} permissions")
                
                # Copy role_permissions
                role_perms = await source_conn.fetch("SELECT * FROM rbac_role_permissions")
                if role_perms:
                    for rp in role_perms:
                        await test_conn.execute("""
                            INSERT INTO rbac_role_permissions (role_id, permission_id) 
                            VALUES ($1, $2) 
                            ON CONFLICT DO NOTHING
                        """, rp['role_id'], rp['permission_id'])
                    logger.info(f"  ✓ Copied {len(role_perms)} role-permission mappings")
                
                # Copy user_roles
                user_roles = await source_conn.fetch("""
                    SELECT DISTINCT u.email, r.role_name
                    FROM rbac_user_roles ur
                    JOIN users u ON u.user_id = ur.user_id
                    JOIN rbac_roles r ON r.role_id = ur.role_id
                """)
                
                if user_roles:
                    for ur in user_roles:
                        await test_conn.execute("""
                            INSERT INTO rbac_user_roles (user_id, role_id)
                            SELECT u.user_id, r.role_id
                            FROM users u, rbac_roles r
                            WHERE u.email = $1 AND r.role_name = $2
                            ON CONFLICT DO NOTHING
                        """, ur['email'], ur['role_name'])
                    logger.info(f"  ✓ Created {len(user_roles)} user-role assignments")
                
            finally:
                await source_conn.close()
            
            # 5. Workflow activity templates
            await test_conn.execute("""
                INSERT INTO workflow_activity_templates (phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, is_active)
                SELECT phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, is_active
                FROM (VALUES 
                    ('Planning', 'Start Planning', 'START', 1, 'Begin planning phase', true, false, true),
                    ('Planning', 'Generate Attributes', 'TASK', 2, 'Generate test attributes using LLM', true, false, true),
                    ('Planning', 'Review Attributes', 'REVIEW', 3, 'Review generated attributes', true, false, true),
                    ('Planning', 'Complete Planning', 'COMPLETE', 4, 'Complete planning phase', true, false, true)
                ) AS v(phase_name, activity_name, activity_type, activity_order, description, is_manual, is_optional, is_active)
                ON CONFLICT DO NOTHING;
            """)
            logger.info("  ✓ Seeded workflow templates")
            
        finally:
            await test_conn.close()
    
    async def get_reconciliation_report(self) -> Dict[str, Dict[str, int]]:
        """Get complete reconciliation report"""
        logger.info("\nGenerating reconciliation report...")
        
        source_conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.source_db
        )
        
        test_conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.test_db_name
        )
        
        try:
            # Get all tables
            tables_query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
            """
            
            source_tables = await source_conn.fetch(tables_query)
            test_tables = await test_conn.fetch(tables_query)
            
            source_table_names = {t['tablename'] for t in source_tables}
            test_table_names = {t['tablename'] for t in test_tables}
            
            all_tables = source_table_names | test_table_names
            
            report = {}
            
            for table in sorted(all_tables):
                source_count = 0
                test_count = 0
                
                if table in source_table_names:
                    try:
                        source_count = await source_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    except:
                        source_count = -1
                
                if table in test_table_names:
                    try:
                        test_count = await test_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    except:
                        test_count = -1
                
                report[table] = {
                    'source': source_count,
                    'test': test_count,
                    'exists_in_source': table in source_table_names,
                    'exists_in_test': table in test_table_names
                }
            
            return report
            
        finally:
            await source_conn.close()
            await test_conn.close()
    
    async def run_complete_migration(self):
        """Run the complete migration process"""
        logger.info("="*80)
        logger.info("COMPLETE DATABASE MIGRATION")
        logger.info("="*80)
        
        try:
            # Step 1: Create test database
            await self.drop_and_create_database()
            
            # Step 2: Copy complete schema
            await self.copy_schema_from_source()
            
            # Step 3: Seed essential data
            await self.seed_essential_data()
            
            # Step 4: Get reconciliation report
            report = await self.get_reconciliation_report()
            
            # Print detailed report
            logger.info("\n" + "="*80)
            logger.info("RECONCILIATION REPORT")
            logger.info("="*80)
            logger.info(f"{'Table':<50} {'Source':>10} {'Test':>10} {'Status':>20}")
            logger.info("-"*90)
            
            total_source_tables = 0
            total_test_tables = 0
            total_source_records = 0
            total_test_records = 0
            tables_with_data = 0
            perfect_matches = 0
            
            for table, counts in report.items():
                if counts['exists_in_source']:
                    total_source_tables += 1
                    if counts['source'] > 0:
                        total_source_records += counts['source']
                
                if counts['exists_in_test']:
                    total_test_tables += 1
                    if counts['test'] > 0:
                        total_test_records += counts['test']
                        tables_with_data += 1
                
                # Determine status
                if not counts['exists_in_test']:
                    status = "❌ MISSING IN TEST"
                elif not counts['exists_in_source']:
                    status = "➕ EXTRA IN TEST"
                elif counts['test'] == counts['source']:
                    if counts['test'] > 0:
                        status = "✅ PERFECT MATCH"
                        perfect_matches += 1
                    else:
                        status = "✓ BOTH EMPTY"
                elif counts['test'] > 0:
                    status = "⚠️ DATA SEEDED"
                else:
                    status = "○ NO DATA"
                
                logger.info(f"{table:<50} {counts['source']:>10,} {counts['test']:>10,} {status:>20}")
            
            logger.info("-"*90)
            logger.info(f"\nSUMMARY:")
            logger.info(f"  Source Database:")
            logger.info(f"    - Tables: {total_source_tables}")
            logger.info(f"    - Total Records: {total_source_records:,}")
            logger.info(f"  Test Database:")
            logger.info(f"    - Tables: {total_test_tables}")
            logger.info(f"    - Total Records: {total_test_records:,}")
            logger.info(f"    - Tables with Data: {tables_with_data}")
            logger.info(f"    - Perfect Matches: {perfect_matches}")
            
            # Check if all source tables exist in test
            missing_tables = []
            for table, counts in report.items():
                if counts['exists_in_source'] and not counts['exists_in_test']:
                    missing_tables.append(table)
            
            if missing_tables:
                logger.error(f"\n⚠️ WARNING: {len(missing_tables)} tables missing in test database:")
                for table in missing_tables[:10]:  # Show first 10
                    logger.error(f"  - {table}")
                if len(missing_tables) > 10:
                    logger.error(f"  ... and {len(missing_tables) - 10} more")
            else:
                logger.info(f"\n✅ SUCCESS: All {total_source_tables} source tables exist in test database!")
            
            logger.info(f"\n🔗 Test Database Connection:")
            logger.info(f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.test_db_name}")
            
        except Exception as e:
            logger.error(f"\n❌ Migration failed: {e}")
            raise


async def main():
    """Main entry point"""
    migration = CompleteDatabaseMigration()
    await migration.run_complete_migration()


if __name__ == "__main__":
    asyncio.run(main())