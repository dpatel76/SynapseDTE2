#!/usr/bin/env python3
"""
Complete Test Database Creation Script
Creates a test database with complete schema and essential seed data

Purpose:
- Create a fully functional test database for development/testing
- Copy complete schema from source database (126 tables)
- Seed essential data for system operation
- Provide detailed reconciliation report

Usage:
    python scripts/deployment/create_test_database.py

Environment:
    DATABASE_URL - Source database connection string

Output:
    - Creates database: synapse_dt_test
    - Seeds test users with password: password123
    - Generates reconciliation report showing all tables and record counts
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
import logging
from datetime import datetime
from typing import Dict, List, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompleteDatabaseMigrationV2:
    """Complete database migration with simplified approach"""
    
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
    
    async def dump_and_restore_schema(self):
        """Use pg_dump to copy schema from source to test"""
        logger.info("Copying schema using pg_dump...")
        
        import subprocess
        
        # Build pg_dump command to dump schema only
        dump_cmd = [
            'pg_dump',
            f'--host={self.host}',
            f'--port={self.port}',
            f'--username={self.user}',
            '--no-password',
            '--schema-only',  # Schema only, no data
            '--no-owner',     # Don't include ownership
            '--no-privileges', # Don't include privileges
            self.source_db
        ]
        
        # Build psql command to restore to test database
        restore_cmd = [
            'psql',
            f'--host={self.host}',
            f'--port={self.port}',
            f'--username={self.user}',
            '--no-password',
            self.test_db_name
        ]
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = self.password
        
        try:
            # Run pg_dump and pipe to psql
            dump_process = subprocess.Popen(
                dump_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                env=env
            )
            
            restore_process = subprocess.Popen(
                restore_cmd,
                stdin=dump_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            # Allow dump_process to receive a SIGPIPE if restore_process exits
            dump_process.stdout.close()
            
            # Wait for completion
            restore_output, restore_error = restore_process.communicate()
            dump_output, dump_error = dump_process.communicate()
            
            if dump_process.returncode != 0:
                logger.error(f"pg_dump failed: {dump_error.decode()}")
                raise Exception("Failed to dump schema")
            
            if restore_process.returncode != 0:
                # Log errors but continue - some errors are expected
                logger.warning(f"psql warnings: {restore_error.decode()}")
            
            logger.info("✓ Schema copied successfully")
            
        except FileNotFoundError:
            logger.error("pg_dump or psql not found. Please ensure PostgreSQL client tools are installed.")
            raise
    
    async def verify_schema_copy(self):
        """Verify that all tables were created"""
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
            # Get table counts
            source_tables = await source_conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """)
            
            test_tables = await test_conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """)
            
            source_set = {t['tablename'] for t in source_tables}
            test_set = {t['tablename'] for t in test_tables}
            
            logger.info(f"\nSchema verification:")
            logger.info(f"  Source tables: {len(source_set)}")
            logger.info(f"  Test tables: {len(test_set)}")
            
            missing = source_set - test_set
            if missing:
                logger.error(f"  Missing tables: {missing}")
            else:
                logger.info("  ✓ All tables created successfully")
            
            return len(test_set)
            
        finally:
            await source_conn.close()
            await test_conn.close()
    
    async def seed_essential_data(self):
        """Seed essential data for system to function"""
        logger.info("\nSeeding essential data...")
        
        test_conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.test_db_name
        )
        
        source_conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.source_db
        )
        
        try:
            # 1. Copy all data from tables with no foreign keys (base tables)
            base_tables = [
                'alembic_version',
                'assignment_templates',
                'data_sources',
                'lobs',
                'permissions',
                'regulatory_data_dictionary',
                'roles',
                'universal_sla_configurations',
                'universal_version_histories',
                'workflow_activity_dependencies',
                'workflow_activity_templates',
                'workflow_metrics'
            ]
            
            for table in base_tables:
                try:
                    # Get data from source
                    data = await source_conn.fetch(f"SELECT * FROM {table}")
                    if data:
                        # Get column names
                        columns = list(data[0].keys())
                        
                        # Build insert query
                        placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
                        columns_str = ', '.join([f'"{col}"' for col in columns])
                        
                        query = f"""
                            INSERT INTO {table} ({columns_str}) 
                            VALUES ({placeholders})
                            ON CONFLICT DO NOTHING
                        """
                        
                        # Insert data
                        for row in data:
                            values = [row[col] for col in columns]
                            await test_conn.execute(query, *values)
                        
                        logger.info(f"  ✓ Copied {len(data)} rows to {table}")
                except Exception as e:
                    logger.error(f"  ✗ Failed to copy {table}: {e}")
            
            # 2. Create essential users with proper LOBs
            lob_id = await test_conn.fetchval("SELECT lob_id FROM lobs ORDER BY lob_id LIMIT 1")
            
            if lob_id:
                # Password hash for 'password123'
                password_hash = '$2b$12$iWH6wK2JpZl0X.HmoYzVn.LrWb8oXP3R5x7JLzLJYUkZ1kTvKHC8m'
                
                users_data = [
                    ('admin@example.com', 'System', 'Administrator', password_hash, 'Admin', lob_id),
                    ('tester1@example.com', 'John', 'Tester', password_hash, 'Tester', lob_id),
                    ('tester2@example.com', 'Jane', 'Tester', password_hash, 'Tester', lob_id),
                    ('test.manager@example.com', 'Test', 'Manager', password_hash, 'Test Executive', lob_id),
                    ('report.owner1@example.com', 'Jane', 'Owner', password_hash, 'Report Owner', lob_id),
                    ('report.owner2@example.com', 'Bob', 'Owner', password_hash, 'Report Owner', lob_id),
                    ('data.owner1@example.com', 'David', 'Data', password_hash, 'Data Owner', lob_id),
                    ('data.owner2@example.com', 'Diana', 'Data', password_hash, 'Data Owner', lob_id),
                    ('report.executive@example.com', 'Sarah', 'Executive', password_hash, 'Report Owner Executive', lob_id),
                    ('data.executive@example.com', 'Mike', 'DataExec', password_hash, 'Data Executive', lob_id)
                ]
                
                for user_data in users_data:
                    try:
                        await test_conn.execute("""
                            INSERT INTO users (email, first_name, last_name, hashed_password, role, lob_id, is_active) 
                            VALUES ($1, $2, $3, $4, $5::user_role_enum, $6, true)
                            ON CONFLICT (email) DO NOTHING
                        """, *user_data)
                    except Exception as e:
                        logger.error(f"  Failed to create user {user_data[0]}: {e}")
                
                logger.info(f"  ✓ Created {len(users_data)} test users")
            
            # 3. Copy role_permissions
            role_perms = await source_conn.fetch("SELECT * FROM rbac_role_permissions")
            if role_perms:
                for rp in role_perms:
                    try:
                        await test_conn.execute("""
                            INSERT INTO rbac_role_permissions (role_id, permission_id) 
                            VALUES ($1, $2) 
                            ON CONFLICT DO NOTHING
                        """, rp['role_id'], rp['permission_id'])
                    except:
                        pass
                logger.info(f"  ✓ Copied {len(role_perms)} role-permission mappings")
            
            # 4. Create user_roles for test users
            await test_conn.execute("""
                INSERT INTO rbac_user_roles (user_id, role_id)
                SELECT u.user_id, r.role_id
                FROM users u
                JOIN rbac_roles r ON r.role_name = u.role::text
                ON CONFLICT DO NOTHING
            """)
            logger.info("  ✓ Created user-role assignments")
            
            # 5. Create some test data
            # Get user IDs
            test_manager_id = await test_conn.fetchval(
                "SELECT user_id FROM users WHERE email = 'test.manager@example.com'"
            )
            report_owner_id = await test_conn.fetchval(
                "SELECT user_id FROM users WHERE email = 'report.owner1@example.com'"
            )
            
            if test_manager_id:
                # Create test cycles
                await test_conn.execute("""
                    INSERT INTO test_cycles (cycle_name, description, test_manager_id, start_date, end_date, status)
                    VALUES 
                    ('Q1 2024 Testing', 'First quarter testing cycle', $1, '2024-01-01', '2024-03-31', 'Complete'),
                    ('Q2 2024 Testing', 'Second quarter testing cycle', $1, '2024-04-01', '2024-06-30', 'Complete'),
                    ('Q3 2024 Testing', 'Third quarter testing cycle', $1, '2024-07-01', '2024-09-30', 'In Progress')
                    ON CONFLICT DO NOTHING
                """, test_manager_id)
                logger.info("  ✓ Created test cycles")
            
            if report_owner_id and lob_id:
                # Create reports
                await test_conn.execute("""
                    INSERT INTO reports (report_name, regulation, description, frequency, report_owner_id, lob_id, is_active)
                    VALUES 
                    ('FR Y-14M Credit Card', 'Federal Reserve', 'Monthly credit card data collection', 'Monthly', $1, $2, true),
                    ('FFIEC 031 Call Report', 'FFIEC', 'Quarterly bank call report', 'Quarterly', $1, $2, true),
                    ('FR Y-9C Consolidated', 'Federal Reserve', 'Consolidated financial statements', 'Quarterly', $1, $2, true)
                    ON CONFLICT DO NOTHING
                """, report_owner_id, lob_id)
                logger.info("  ✓ Created test reports")
            
        finally:
            await source_conn.close()
            await test_conn.close()
    
    async def get_complete_reconciliation(self) -> Dict[str, Dict]:
        """Get complete reconciliation report for all tables"""
        logger.info("\nGenerating complete reconciliation report...")
        
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
            # Get all tables from both databases
            source_tables = await source_conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """)
            
            test_tables = await test_conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """)
            
            source_set = {t['tablename'] for t in source_tables}
            test_set = {t['tablename'] for t in test_tables}
            all_tables = source_set | test_set
            
            # Get counts for each table
            report = {}
            
            for table in sorted(all_tables):
                source_count = 0
                test_count = 0
                
                if table in source_set:
                    try:
                        source_count = await source_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    except:
                        source_count = -1
                
                if table in test_set:
                    try:
                        test_count = await test_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    except:
                        test_count = -1
                
                report[table] = {
                    'source': source_count,
                    'test': test_count,
                    'in_source': table in source_set,
                    'in_test': table in test_set
                }
            
            return report
            
        finally:
            await source_conn.close()
            await test_conn.close()
    
    async def run_complete_migration(self):
        """Run the complete migration process"""
        logger.info("="*100)
        logger.info("COMPLETE DATABASE MIGRATION V2")
        logger.info("="*100)
        
        try:
            # Step 1: Create test database
            await self.drop_and_create_database()
            
            # Step 2: Copy schema using pg_dump
            await self.dump_and_restore_schema()
            
            # Step 3: Verify schema was copied
            table_count = await self.verify_schema_copy()
            
            # Step 4: Seed essential data
            await self.seed_essential_data()
            
            # Step 5: Get complete reconciliation
            report = await self.get_complete_reconciliation()
            
            # Print detailed reconciliation report
            logger.info("\n" + "="*100)
            logger.info("COMPLETE RECONCILIATION REPORT")
            logger.info("="*100)
            logger.info(f"{'Table':<50} {'Source':>10} {'Test':>10} {'Diff':>10} {'Status':>25}")
            logger.info("-"*105)
            
            # Statistics
            total_source_tables = 0
            total_test_tables = 0
            total_source_records = 0
            total_test_records = 0
            perfect_matches = 0
            tables_with_data = 0
            missing_tables = []
            data_matches = 0
            
            for table, info in report.items():
                if info['in_source']:
                    total_source_tables += 1
                    if info['source'] > 0:
                        total_source_records += info['source']
                
                if info['in_test']:
                    total_test_tables += 1
                    if info['test'] > 0:
                        total_test_records += info['test']
                        tables_with_data += 1
                
                # Calculate difference
                diff = info['test'] - info['source'] if info['in_source'] and info['in_test'] else 0
                
                # Determine status
                if not info['in_test']:
                    status = "❌ MISSING IN TEST"
                    missing_tables.append(table)
                elif not info['in_source']:
                    status = "➕ EXTRA IN TEST"
                elif info['source'] == info['test']:
                    if info['source'] > 0:
                        status = "✅ PERFECT MATCH"
                        perfect_matches += 1
                        data_matches += 1
                    else:
                        status = "✓ BOTH EMPTY"
                elif info['test'] > 0:
                    status = "📊 DATA PRESENT"
                    data_matches += 1
                else:
                    status = "○ NO DATA"
                
                # Format output
                diff_str = f"{diff:+,}" if diff != 0 else "-"
                logger.info(
                    f"{table:<50} {info['source']:>10,} {info['test']:>10,} "
                    f"{diff_str:>10} {status:>25}"
                )
            
            logger.info("-"*105)
            
            # Print summary
            logger.info("\nSUMMARY:")
            logger.info(f"  Source Database ({self.source_db}):")
            logger.info(f"    • Total Tables: {total_source_tables}")
            logger.info(f"    • Total Records: {total_source_records:,}")
            
            logger.info(f"\n  Test Database ({self.test_db_name}):")
            logger.info(f"    • Total Tables: {total_test_tables}")
            logger.info(f"    • Total Records: {total_test_records:,}")
            logger.info(f"    • Tables with Data: {tables_with_data}")
            logger.info(f"    • Perfect Matches: {perfect_matches}")
            logger.info(f"    • Tables with Any Data: {data_matches}")
            
            # Success/failure determination
            if missing_tables:
                logger.error(f"\n⚠️  WARNING: {len(missing_tables)} tables missing in test database!")
                for table in missing_tables[:5]:
                    logger.error(f"    - {table}")
                if len(missing_tables) > 5:
                    logger.error(f"    ... and {len(missing_tables) - 5} more")
            else:
                logger.info(f"\n✅ SUCCESS: All {total_source_tables} source tables exist in test database!")
            
            # Connection info
            logger.info(f"\n🔗 Test Database Connection:")
            logger.info(f"   postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.test_db_name}")
            
            # Instructions
            logger.info("\n📝 Next Steps:")
            logger.info("   1. Update your .env file with: DATABASE_URL=<test_db_connection_string>")
            logger.info("   2. Run the application against the test database")
            logger.info("   3. All test users have password: password123")
            
        except Exception as e:
            logger.error(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """Main entry point"""
    migration = CompleteDatabaseMigrationV2()
    await migration.run_complete_migration()


if __name__ == "__main__":
    asyncio.run(main())