#!/usr/bin/env python3
"""
Simple test database creation script
Creates a test database with basic structure and seed data
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
import logging

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_test_database():
    """Create test database and basic structure"""
    
    # Get database URL from environment or use default
    db_url = os.getenv('DATABASE_URL', 'postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
    
    # Parse connection info
    from urllib.parse import urlparse
    parsed = urlparse(db_url)
    
    host = parsed.hostname
    port = parsed.port or 5432
    user = parsed.username
    password = parsed.password
    
    logger.info("Creating test database...")
    
    # Connect to postgres database
    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database='postgres'
    )
    
    try:
        # Drop test database if exists
        await conn.execute('DROP DATABASE IF EXISTS synapse_dt_test')
        logger.info("Dropped existing test database if it existed")
        
        # Create test database
        await conn.execute('CREATE DATABASE synapse_dt_test')
        logger.info("✓ Created test database: synapse_dt_test")
        
    finally:
        await conn.close()
    
    # Connect to the new test database
    test_conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database='synapse_dt_test'
    )
    
    try:
        # Create basic ENUMs
        logger.info("Creating ENUM types...")
        
        enum_queries = [
            """CREATE TYPE userrole AS ENUM ('Tester', 'Test Executive', 'Report Owner', 
               'Report Owner Executive', 'Data Owner', 'Data Executive', 'Admin')""",
            """CREATE TYPE workflowstate AS ENUM ('Not Started', 'In Progress', 'Complete', 'On Hold')""",
            """CREATE TYPE workflow_phase_enum AS ENUM ('Planning', 'Data Profiling', 'Scoping', 
               'Sample Selection', 'Data Provider ID', 'Request Info', 'Testing', 
               'Test Execution', 'Observations', 'Finalize Test Report')""",
            """CREATE TYPE workflow_phase_state_enum AS ENUM ('Not Started', 'In Progress', 'Complete')""",
            """CREATE TYPE workflow_phase_status_enum AS ENUM ('On Track', 'At Risk', 'Past Due')""",
        ]
        
        for enum_query in enum_queries:
            try:
                await test_conn.execute(enum_query)
            except asyncpg.exceptions.DuplicateObjectError:
                pass  # Enum already exists
        
        logger.info("✓ Created ENUM types")
        
        # Create basic tables
        logger.info("Creating tables...")
        
        # Create LOBs table
        await test_conn.execute("""
            CREATE TABLE IF NOT EXISTS lobs (
                lob_id SERIAL PRIMARY KEY,
                lob_name VARCHAR(255) NOT NULL UNIQUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create roles table
        await test_conn.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                role_id SERIAL PRIMARY KEY,
                role_name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                is_system BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create users table
        await test_conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                hashed_password VARCHAR(255) NOT NULL,
                role userrole NOT NULL,
                lob_id INTEGER REFERENCES lobs(lob_id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create test_cycles table
        await test_conn.execute("""
            CREATE TABLE IF NOT EXISTS test_cycles (
                cycle_id SERIAL PRIMARY KEY,
                cycle_name VARCHAR(255) NOT NULL,
                description TEXT,
                test_manager_id INTEGER REFERENCES users(user_id),
                start_date DATE,
                end_date DATE,
                status VARCHAR(50),
                workflow_id INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create reports table
        await test_conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                report_id SERIAL PRIMARY KEY,
                report_name VARCHAR(255) NOT NULL,
                regulation VARCHAR(100),
                description TEXT,
                frequency VARCHAR(50),
                report_owner_id INTEGER REFERENCES users(user_id),
                lob_id INTEGER REFERENCES lobs(lob_id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create workflow_phases table
        await test_conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_phases (
                phase_id SERIAL PRIMARY KEY,
                cycle_id INTEGER REFERENCES test_cycles(cycle_id) NOT NULL,
                report_id INTEGER REFERENCES reports(report_id) NOT NULL,
                phase_name workflow_phase_enum NOT NULL,
                state workflow_phase_state_enum DEFAULT 'Not Started',
                schedule_status workflow_phase_status_enum DEFAULT 'On Track',
                started_by INTEGER REFERENCES users(user_id),
                completed_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        logger.info("✓ Created basic tables")
        
        # Seed basic data
        logger.info("Seeding basic data...")
        
        # Insert LOBs
        await test_conn.execute("""
            INSERT INTO lobs (lob_name) VALUES 
            ('Retail Banking'),
            ('Commercial Banking'),
            ('Investment Banking'),
            ('Wealth Management')
        """)
        
        # Insert roles
        await test_conn.execute("""
            INSERT INTO roles (role_name, description) VALUES 
            ('Admin', 'System administrator'),
            ('Tester', 'Executes testing activities'),
            ('Test Executive', 'Oversees testing operations'),
            ('Report Owner', 'Owns specific regulatory reports'),
            ('Data Owner', 'Provides data for testing')
        """)
        
        # Insert test users (with bcrypt hash for 'password123')
        # Note: This is a pre-computed hash for demonstration
        password_hash = '$2b$12$iWH6wK2JpZl0X.HmoYzVn.LrWb8oXP3R5x7JLzLJYUkZ1kTvKHC8m'
        
        await test_conn.execute(f"""
            INSERT INTO users (username, email, first_name, last_name, hashed_password, role, lob_id) VALUES
            ('admin', 'admin@example.com', 'System', 'Administrator', '{password_hash}', 'Admin', 1),
            ('tester1', 'tester1@example.com', 'John', 'Tester', '{password_hash}', 'Tester', 1),
            ('testmanager', 'test.manager@example.com', 'Test', 'Manager', '{password_hash}', 'Test Executive', 1),
            ('reportowner1', 'report.owner1@example.com', 'Jane', 'Owner', '{password_hash}', 'Report Owner', 2)
        """)
        
        logger.info("✓ Seeded basic data")
        
        # Get record counts
        logger.info("\nRecord counts in test database:")
        tables = ['lobs', 'roles', 'users', 'test_cycles', 'reports', 'workflow_phases']
        
        for table in tables:
            count = await test_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            logger.info(f"  {table}: {count} records")
        
        # Get source database counts for comparison
        logger.info("\n" + "="*60)
        logger.info("RECONCILIATION REPORT")
        logger.info("="*60)
        logger.info(f"{'Table':<20} {'Source DB':>15} {'Test DB':>15}")
        logger.info("-"*50)
        
        # Create new connection for source database
        source_conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=parsed.path.lstrip('/')
        )
        
        try:
            for table in tables:
                try:
                    source_count = await source_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                except:
                    source_count = "N/A"
                
                test_count = await test_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                logger.info(f"{table:<20} {str(source_count):>15} {test_count:>15}")
        finally:
            await source_conn.close()
            
    finally:
        await test_conn.close()
    
    logger.info("\n" + "="*60)
    logger.info("✅ Test database created successfully!")
    logger.info(f"Connection: postgresql://{user}:{password}@{host}:{port}/synapse_dt_test")


if __name__ == "__main__":
    asyncio.run(create_test_database())