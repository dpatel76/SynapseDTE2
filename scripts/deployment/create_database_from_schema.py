#!/usr/bin/env python3
"""
Create Database from Schema Files
Creates a new database using SQL schema files (no source database required)

Purpose:
- Create a fully functional database without access to source database
- Use SQL schema dumps and seed data files
- Suitable for deployment on new machines

Usage:
    python scripts/deployment/create_database_from_schema.py

Requirements:
    - PostgreSQL database server
    - SQL schema file (schema.sql)
    - Seed data file (seed_data.sql)
"""

import asyncio
import os
import sys
import asyncpg
import logging
from pathlib import Path
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseFromSchema:
    """Create database from SQL schema files"""
    
    def __init__(self, db_name: str = "synapse_dt_new"):
        self.db_name = db_name
        
        # Get connection parameters from environment or defaults
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
        
        # Paths to schema files
        self.base_path = Path(__file__).parent.parent.parent
        self.schema_file = self.base_path / 'migrations' / 'schema' / 'complete_schema.sql'
        self.seed_file = self.base_path / 'migrations' / 'schema' / 'seed_data.sql'
        
    async def create_database(self):
        """Create the database"""
        logger.info(f"Creating database: {self.db_name}")
        
        conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database='postgres'
        )
        
        try:
            # Drop if exists
            await conn.execute(f'DROP DATABASE IF EXISTS {self.db_name}')
            logger.info("Dropped existing database if it existed")
            
            # Create database
            await conn.execute(f'CREATE DATABASE {self.db_name}')
            logger.info(f"✓ Created database: {self.db_name}")
            
        finally:
            await conn.close()
    
    async def load_schema(self):
        """Load schema from SQL file"""
        if not self.schema_file.exists():
            logger.error(f"Schema file not found: {self.schema_file}")
            logger.info("Please run export_schema.py first to generate schema file")
            return False
        
        logger.info("Loading schema from file...")
        
        # Use psql to load schema
        env = os.environ.copy()
        env['PGPASSWORD'] = self.password
        
        cmd = [
            'psql',
            f'--host={self.host}',
            f'--port={self.port}',
            f'--username={self.user}',
            '--no-password',
            f'--dbname={self.db_name}',
            f'--file={self.schema_file}'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("✓ Schema loaded successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to load schema: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("psql command not found. Please install PostgreSQL client tools.")
            return False
    
    async def load_seed_data(self):
        """Load seed data from SQL file"""
        if not self.seed_file.exists():
            logger.warning(f"Seed data file not found: {self.seed_file}")
            logger.info("Creating minimal seed data...")
            await self.create_minimal_seed_data()
            return
        
        logger.info("Loading seed data from file...")
        
        # Use psql to load seed data
        env = os.environ.copy()
        env['PGPASSWORD'] = self.password
        
        cmd = [
            'psql',
            f'--host={self.host}',
            f'--port={self.port}',
            f'--username={self.user}',
            '--no-password',
            f'--dbname={self.db_name}',
            f'--file={self.seed_file}'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("✓ Seed data loaded successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to load seed data: {e.stderr}")
            logger.info("Creating minimal seed data...")
            await self.create_minimal_seed_data()
    
    async def create_minimal_seed_data(self):
        """Create minimal seed data programmatically"""
        conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db_name
        )
        
        try:
            # Essential data for system to function
            
            # 1. Roles
            await conn.execute("""
                INSERT INTO rbac_roles (role_name, description, is_system, is_active) VALUES 
                ('Admin', 'System administrator', true, true),
                ('Tester', 'Executes testing activities', true, true),
                ('Test Executive', 'Oversees testing operations', true, true),
                ('Report Owner', 'Owns specific regulatory reports', true, true),
                ('Report Owner Executive', 'Executive oversight', true, true),
                ('Data Owner', 'Provides data for testing', true, true),
                ('Data Executive', 'Data operations oversight', true, true)
                ON CONFLICT (role_name) DO NOTHING;
            """)
            
            # 2. LOBs
            await conn.execute("""
                INSERT INTO lobs (lob_name) VALUES 
                ('Retail Banking'),
                ('Commercial Banking'),
                ('Investment Banking'),
                ('Wealth Management')
                ON CONFLICT (lob_name) DO NOTHING;
            """)
            
            # 3. Basic permissions
            await conn.execute("""
                INSERT INTO rbac_permissions (resource, action, description) VALUES
                ('test_cycle', 'create', 'Create test cycles'),
                ('test_cycle', 'read', 'View test cycles'),
                ('test_cycle', 'update', 'Update test cycles'),
                ('test_cycle', 'delete', 'Delete test cycles'),
                ('report', 'read', 'View reports'),
                ('report', 'assign', 'Assign reports'),
                ('workflow', 'execute', 'Execute workflow phases'),
                ('workflow', 'approve', 'Approve workflow submissions')
                ON CONFLICT (resource, action) DO NOTHING;
            """)
            
            # 4. Test users (password: password123)
            password_hash = '$2b$12$iWH6wK2JpZl0X.HmoYzVn.LrWb8oXP3R5x7JLzLJYUkZ1kTvKHC8m'
            
            await conn.execute(f"""
                INSERT INTO users (email, first_name, last_name, hashed_password, role, lob_id, is_active)
                SELECT 
                    vals.email,
                    vals.first_name,
                    vals.last_name,
                    vals.password_hash,
                    vals.role::user_role_enum,
                    (SELECT lob_id FROM lobs ORDER BY lob_id LIMIT 1),
                    true
                FROM (VALUES
                    ('admin@example.com', 'System', 'Admin', '{password_hash}', 'Admin'),
                    ('tester@example.com', 'Test', 'User', '{password_hash}', 'Tester'),
                    ('manager@example.com', 'Test', 'Manager', '{password_hash}', 'Test Executive')
                ) AS vals(email, first_name, last_name, password_hash, role)
                ON CONFLICT (email) DO NOTHING;
            """)
            
            logger.info("✓ Created minimal seed data")
            
        finally:
            await conn.close()
    
    async def verify_database(self):
        """Verify database was created successfully"""
        conn = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db_name
        )
        
        try:
            # Count tables
            table_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            # Count key records
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            role_count = await conn.fetchval("SELECT COUNT(*) FROM roles")
            
            logger.info("\nDatabase Verification:")
            logger.info(f"  Tables created: {table_count}")
            logger.info(f"  Users created: {user_count}")
            logger.info(f"  Roles created: {role_count}")
            
            if table_count > 0:
                logger.info("\n✅ Database created successfully!")
                logger.info(f"Connection string: postgresql://{self.user}:****@{self.host}:{self.port}/{self.db_name}")
            else:
                logger.error("❌ No tables found in database")
            
        finally:
            await conn.close()
    
    async def run(self):
        """Run the complete database creation process"""
        logger.info("="*80)
        logger.info("DATABASE CREATION FROM SCHEMA")
        logger.info("="*80)
        
        try:
            # Step 1: Create database
            await self.create_database()
            
            # Step 2: Load schema
            if not await self.load_schema():
                logger.error("Failed to load schema. Please ensure schema file exists.")
                return
            
            # Step 3: Load seed data
            await self.load_seed_data()
            
            # Step 4: Verify
            await self.verify_database()
            
            logger.info("\n📝 Next Steps:")
            logger.info("1. Update DATABASE_URL in your .env file")
            logger.info("2. Test users: admin@example.com, tester@example.com (password: password123)")
            
        except Exception as e:
            logger.error(f"❌ Database creation failed: {e}")
            raise


async def main():
    """Main entry point"""
    db_creator = DatabaseFromSchema()
    await db_creator.run()


if __name__ == "__main__":
    asyncio.run(main())