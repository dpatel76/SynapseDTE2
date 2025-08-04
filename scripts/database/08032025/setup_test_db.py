#!/usr/bin/env python3
"""
Setup Test Database
This script creates a test database to validate schema and seed data
without affecting the production database.
"""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path
from datetime import datetime

# Test database configuration
TEST_DB_CONFIG = {
    'host': 'localhost',
    'database': 'synapse_dt_test_new',
    'user': 'synapse_user',
    'password': 'synapse_password',
    'port': 5432
}

class TestDatabaseSetup:
    """Setup and validate test database"""
    
    def __init__(self):
        self.test_db_name = TEST_DB_CONFIG['database']
        self.scripts_dir = Path(__file__).parent
        
    async def create_test_database(self):
        """Create test database"""
        # Connect to postgres database to create new database
        conn = await asyncpg.connect(
            host=TEST_DB_CONFIG['host'],
            port=TEST_DB_CONFIG['port'],
            user=TEST_DB_CONFIG['user'],
            password=TEST_DB_CONFIG['password'],
            database='postgres'
        )
        
        try:
            # Drop existing test database if exists
            await conn.execute(f'DROP DATABASE IF EXISTS {self.test_db_name}')
            print(f"Dropped existing test database: {self.test_db_name}")
            
            # Create new test database
            await conn.execute(f'CREATE DATABASE {self.test_db_name}')
            print(f"Created test database: {self.test_db_name}")
            
        finally:
            await conn.close()
            
    async def execute_sql_file(self, conn, sql_file: Path):
        """Execute SQL file"""
        print(f"Executing: {sql_file.name}")
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
            
        # Split by semicolons but be careful with functions/procedures
        statements = []
        current_statement = []
        in_function = False
        
        for line in sql_content.split('\n'):
            line_upper = line.upper().strip()
            
            # Check for function/procedure start
            if 'CREATE FUNCTION' in line_upper or 'CREATE PROCEDURE' in line_upper:
                in_function = True
                
            current_statement.append(line)
            
            # Check for statement end
            if line.strip().endswith(';'):
                if not in_function:
                    statements.append('\n'.join(current_statement))
                    current_statement = []
                elif '$$' in line or 'END;' in line_upper:
                    statements.append('\n'.join(current_statement))
                    current_statement = []
                    in_function = False
                    
        # Execute each statement
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    await conn.execute(statement)
                except Exception as e:
                    print(f"  Error in statement {i+1}: {str(e)[:100]}")
                    # Continue with next statement
                    
    async def setup_schema(self):
        """Setup database schema"""
        conn = await asyncpg.connect(**TEST_DB_CONFIG)
        
        try:
            # Enable extensions
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
            print("Enabled required extensions")
            
            # Execute schema file
            schema_file = self.scripts_dir / "01_schema_simple.sql"
            if schema_file.exists():
                await self.execute_sql_file(conn, schema_file)
            else:
                # Try alternative names
                schema_file = self.scripts_dir / "01_schema.sql"
                if schema_file.exists():
                    await self.execute_sql_file(conn, schema_file)
                else:
                    print(f"Warning: Schema file not found")
                
        finally:
            await conn.close()
            
    async def load_seed_data(self):
        """Load seed data"""
        conn = await asyncpg.connect(**TEST_DB_CONFIG)
        
        try:
            sql_seeds_dir = self.scripts_dir / "sql_seeds"
            if not sql_seeds_dir.exists():
                print("No seed data found")
                return
                
            # Load seed files in order
            seed_files = sorted(sql_seeds_dir.glob("*.sql"))
            
            # Define load order based on dependencies
            load_order = [
                'users.sql',
                'roles.sql',
                'permissions.sql',
                'role_permissions.sql',
                'user_roles.sql',
                'lobs.sql',
                'data_owners.sql',
                'reports.sql',
                'report_attributes.sql',
                'test_cycles.sql',
                'cycle_reports.sql',
                'workflow_phases.sql',
            ]
            
            # Load in order first
            for file_name in load_order:
                sql_file = sql_seeds_dir / file_name
                if sql_file.exists():
                    await self.execute_sql_file(conn, sql_file)
                    seed_files.remove(sql_file)
                    
            # Load remaining files
            for sql_file in seed_files:
                await self.execute_sql_file(conn, sql_file)
                
        finally:
            await conn.close()
            
    async def validate_setup(self):
        """Validate database setup"""
        conn = await asyncpg.connect(**TEST_DB_CONFIG)
        
        try:
            print("\nValidating database setup...")
            
            # Check tables
            table_query = """
                SELECT table_name 
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """
            
            tables = await conn.fetch(table_query)
            print(f"\nTables created: {len(tables)}")
            
            # Check row counts for key tables
            key_tables = ['users', 'roles', 'permissions', 'reports', 'test_cycles']
            
            print("\nRow counts:")
            for table in key_tables:
                try:
                    count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                    print(f"  {table}: {count}")
                except:
                    print(f"  {table}: ERROR")
                    
            # Test a few queries
            print("\nTesting queries:")
            
            # Test user query
            user_count = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE email LIKE '%@example.com'"
            )
            print(f"  Users with @example.com email: {user_count}")
            
            # Test joins
            role_user_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN roles r ON ur.role_id = r.role_id
            """)
            print(f"  User-role assignments: {role_user_count}")
            
        finally:
            await conn.close()
            
    async def generate_docker_compose(self):
        """Generate docker-compose configuration"""
        compose_file = self.scripts_dir / "docker-compose.yml"
        
        compose_content = f"""version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: synapse_dte_db
    environment:
      POSTGRES_USER: {TEST_DB_CONFIG['user']}
      POSTGRES_PASSWORD: {TEST_DB_CONFIG['password']}
      POSTGRES_DB: {self.test_db_name}
    ports:
      - "5432:5432"
    volumes:
      - ./01_schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
      - ./02_seed_data.sql:/docker-entrypoint-initdb.d/02_seed_data.sql
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {TEST_DB_CONFIG['user']}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
    driver: local
"""
        
        with open(compose_file, 'w') as f:
            f.write(compose_content)
            
        print(f"\nDocker compose file generated: {compose_file}")
        
        # Generate combined seed data file
        combined_seed = self.scripts_dir / "02_seed_data.sql"
        with open(combined_seed, 'w') as f:
            f.write("-- Combined seed data for Docker deployment\n")
            f.write(f"-- Generated: {datetime.now()}\n\n")
            
            sql_seeds_dir = self.scripts_dir / "sql_seeds"
            if sql_seeds_dir.exists():
                for sql_file in sorted(sql_seeds_dir.glob("*.sql")):
                    f.write(f"\n-- From {sql_file.name}\n")
                    with open(sql_file, 'r') as seed_f:
                        f.write(seed_f.read())
                    f.write("\n")
                    
        print(f"Combined seed data generated: {combined_seed}")
        
async def main():
    """Main execution"""
    setup = TestDatabaseSetup()
    
    try:
        # Create test database
        await setup.create_test_database()
        
        # Setup schema
        await setup.setup_schema()
        
        # Load seed data
        await setup.load_seed_data()
        
        # Validate setup
        await setup.validate_setup()
        
        # Generate Docker files
        await setup.generate_docker_compose()
        
        print("\nTest database setup complete!")
        print(f"Database: {TEST_DB_CONFIG['database']}")
        print("\nYou can now test the application with this database")
        
    except Exception as e:
        print(f"\nError during setup: {str(e)}")
        raise
        
if __name__ == "__main__":
    asyncio.run(main())