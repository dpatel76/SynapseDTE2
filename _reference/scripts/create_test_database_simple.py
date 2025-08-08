#!/usr/bin/env python3
"""
Simplified Database Migration Script for SynapseDTE Test Database
Creates a test database with basic seed data to verify setup
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import asyncpg
import logging
from sqlalchemy import create_engine, text, select, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Any, Optional
import json

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import Base
from app.core.auth import get_password_hash

# Import specific models to control order
from app.models.user import User
from app.models.lob import LOB
from app.models.rbac import Role, Permission, RolePermission
from app.models.report import Report
from app.models.test_cycle import TestCycle
from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.models.data_dictionary import RegulatoryDataDictionary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDatabaseMigration:
    """Simplified database migration focusing on core tables"""
    
    def __init__(self, source_db_url: str, test_db_name: str = "synapse_dt_test"):
        self.source_db_url = source_db_url
        self.test_db_name = test_db_name
        
        # Parse source DB URL to get connection params
        self.source_parts = self._parse_db_url(source_db_url)
        
        # Create test DB URL
        self.test_db_url = source_db_url.replace(
            self.source_parts['database'], 
            test_db_name
        )
        
        # Admin connection URL (to postgres database for creating test DB)
        self.admin_db_url = source_db_url.replace(
            self.source_parts['database'],
            'postgres'
        )
        
        logger.info(f"Source DB: {self.source_parts['database']}")
        logger.info(f"Test DB: {test_db_name}")
    
    def _parse_db_url(self, db_url: str) -> Dict[str, str]:
        """Parse database URL into components"""
        # Handle both postgresql and postgresql+asyncpg URLs
        if '+asyncpg' in db_url:
            db_url = db_url.replace('+asyncpg', '')
        
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        
        return {
            'scheme': parsed.scheme,
            'username': parsed.username,
            'password': parsed.password,
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/')
        }
    
    async def create_test_database(self):
        """Create the test database"""
        logger.info(f"Creating test database: {self.test_db_name}")
        
        # Connect to postgres database to create test DB
        admin_parts = self._parse_db_url(self.admin_db_url)
        conn = await asyncpg.connect(
            host=admin_parts['host'],
            port=admin_parts['port'],
            user=admin_parts['username'],
            password=admin_parts['password'],
            database='postgres'
        )
        
        try:
            # Drop test database if exists
            await conn.execute(f'DROP DATABASE IF EXISTS {self.test_db_name}')
            
            # Create test database
            await conn.execute(f'CREATE DATABASE {self.test_db_name}')
            logger.info(f"✓ Test database '{self.test_db_name}' created successfully")
            
        finally:
            await conn.close()
    
    async def create_schema_ordered(self):
        """Create tables in specific order to avoid foreign key issues"""
        logger.info("Creating database schema in ordered fashion...")
        
        # Create engine for test database
        engine = create_async_engine(self.test_db_url, echo=False)
        
        async with engine.begin() as conn:
            # First create ENUM types
            await self._create_enums(conn)
            
            # Create tables in dependency order
            # Group 1: No dependencies
            tables_group1 = [
                Base.metadata.tables.get('lobs'),
                Base.metadata.tables.get('rbac_roles'),
                Base.metadata.tables.get('rbac_permissions'),
                Base.metadata.tables.get('regulatory_data_dictionary'),
                Base.metadata.tables.get('workflow_definitions'),
                Base.metadata.tables.get('workflow_phase_definitions'),
                Base.metadata.tables.get('universal_sla_configurations'),
            ]
            
            for table in tables_group1:
                if table is not None:
                    await conn.run_sync(table.create, checkfirst=True)
                    logger.info(f"  Created table: {table.name}")
            
            # Group 2: Depend on Group 1
            tables_group2 = [
                Base.metadata.tables.get('users'),
                Base.metadata.tables.get('rbac_role_permissions'),
                Base.metadata.tables.get('workflow_phase_dependencies'),
            ]
            
            for table in tables_group2:
                if table is not None:
                    await conn.run_sync(table.create, checkfirst=True)
                    logger.info(f"  Created table: {table.name}")
            
            # Group 3: Depend on users and lobs
            tables_group3 = [
                Base.metadata.tables.get('reports'),
                Base.metadata.tables.get('test_cycles'),
                Base.metadata.tables.get('rbac_user_roles'),
                Base.metadata.tables.get('rbac_user_permissions'),
                Base.metadata.tables.get('audit_logs'),
                Base.metadata.tables.get('llm_audit_logs'),
            ]
            
            for table in tables_group3:
                if table is not None:
                    await conn.run_sync(table.create, checkfirst=True)
                    logger.info(f"  Created table: {table.name}")
            
            # Group 4: Depend on test_cycles and reports
            tables_group4 = [
                Base.metadata.tables.get('cycle_reports'),
                Base.metadata.tables.get('workflow_phases'),
                Base.metadata.tables.get('documents'),
                Base.metadata.tables.get('report_attributes'),
                Base.metadata.tables.get('universal_assignments'),
            ]
            
            for table in tables_group4:
                if table is not None:
                    await conn.run_sync(table.create, checkfirst=True)
                    logger.info(f"  Created table: {table.name}")
            
            # Group 5: Complex dependencies - create remaining tables
            # Get all remaining tables
            all_tables = set(Base.metadata.tables.keys())
            created_tables = set()
            for group in [tables_group1, tables_group2, tables_group3, tables_group4]:
                for table in group:
                    if table is not None:
                        created_tables.add(table.name)
            
            remaining_tables = all_tables - created_tables
            
            # Create remaining tables without strict ordering
            for table_name in remaining_tables:
                table = Base.metadata.tables.get(table_name)
                if table is not None:
                    try:
                        await conn.run_sync(table.create, checkfirst=True)
                        logger.info(f"  Created table: {table_name}")
                    except Exception as e:
                        logger.warning(f"  Skipped table {table_name}: {str(e)}")
            
        await engine.dispose()
        logger.info("✓ Database schema created successfully")
    
    async def _create_enums(self, conn):
        """Create PostgreSQL ENUM types"""
        enums = [
            ("userrole", ["Tester", "Test Executive", "Report Owner", 
                         "Report Owner Executive", "Data Owner", "Data Executive", "Admin"]),
            ("workflowstate", ["Not Started", "In Progress", "Complete", "On Hold"]),
            ("workflowstatus", ["Active", "Paused", "Cancelled", "Completed"]),
            ("schedulestatus", ["On Schedule", "At Risk", "Delayed", "Not Applicable"]),
            ("testresult", ["Pass", "Fail", "Not Tested", "In Progress"]),
            ("observationrating", ["HIGH", "MEDIUM", "LOW"]),
            ("documenttype", ["Evidence", "Report", "Test Case", "Supporting"]),
            ("escalationstatus", ["None", "Warning", "Escalated", "Resolved"]),
            ("assignmentstatus", ["Pending", "Acknowledged", "In Progress", "Completed", "Cancelled"]),
            ("activitystate", ["Not Started", "In Progress", "Completed", "Revision Requested"]),
            ("activitystatus", ["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "REVISION_REQUESTED", "BLOCKED", "SKIPPED"]),
            ("activitytype", ["START", "TASK", "REVIEW", "APPROVAL", "COMPLETE", "CUSTOM"]),
            ("workflow_phase_enum", ["Planning", "Data Profiling", "Scoping", "Sample Selection", 
                                   "Data Provider ID", "Request Info", "Testing", "Test Execution", 
                                   "Observations", "Finalize Test Report"]),
            ("workflow_phase_state_enum", ["Not Started", "In Progress", "Complete"]),
            ("workflow_phase_status_enum", ["On Track", "At Risk", "Past Due"]),
            ("phase_status_enum", ["Not Started", "In Progress", "Complete", "Pending Approval"]),
            ("cycle_report_status_enum", ["Not Started", "In Progress", "Complete"]),
            ("mandatory_flag_enum", ["Mandatory", "Conditional", "Optional"]),
        ]
        
        for enum_name, values in enums:
            try:
                # Create ENUM type if not exists
                values_str = ", ".join([f"'{v}'" for v in values])
                await conn.execute(text(f"""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN
                            CREATE TYPE {enum_name} AS ENUM ({values_str});
                        END IF;
                    END $$;
                """))
            except Exception as e:
                logger.warning(f"ENUM {enum_name} might already exist: {e}")
    
    async def seed_minimal_data(self, session: AsyncSession):
        """Seed minimal data for testing"""
        logger.info("Seeding minimal test data...")
        
        # Create roles
        roles_data = [
            {"role_name": "Admin", "description": "System administrator"},
            {"role_name": "Tester", "description": "Executes testing activities"},
            {"role_name": "Test Executive", "description": "Oversees testing operations"},
            {"role_name": "Report Owner", "description": "Owns specific regulatory reports"},
            {"role_name": "Data Owner", "description": "Provides data for testing"},
        ]
        
        for role_data in roles_data:
            role = Role(**role_data)
            session.add(role)
        
        await session.flush()
        
        # Create LOBs
        lobs = [
            {"lob_name": "Retail Banking"},
            {"lob_name": "Commercial Banking"},
        ]
        
        for lob_data in lobs:
            lob = LOB(**lob_data)
            session.add(lob)
        
        await session.flush()
        
        # Get LOB for user assignment
        lobs = await session.execute(select(LOB))
        first_lob = lobs.scalars().first()
        
        # Create test users
        test_users = [
            {
                "email": "admin@example.com",
                "username": "admin",
                "first_name": "System",
                "last_name": "Administrator",
                "role": "Admin",
                "password": "admin123",
                "lob_id": first_lob.lob_id if first_lob else None
            },
            {
                "email": "tester1@example.com",
                "username": "tester1",
                "first_name": "John",
                "last_name": "Tester",
                "role": "Tester",
                "password": "password123",
                "lob_id": first_lob.lob_id if first_lob else None
            },
        ]
        
        for user_data in test_users:
            password = user_data.pop("password")
            user = User(**user_data)
            user.hashed_password = get_password_hash(password)
            user.is_active = True
            session.add(user)
        
        logger.info(f"✓ Created {len(test_users)} test users")
    
    async def get_table_counts(self, db_url: str, db_name: str) -> Dict[str, int]:
        """Get record counts from database"""
        logger.info(f"Getting table counts from {db_name}...")
        
        engine = create_async_engine(db_url, echo=False)
        counts = {}
        
        async with engine.begin() as conn:
            # Get list of tables
            result = await conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """))
            tables = [row[0] for row in result]
            
            for table in tables:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    counts[table] = count
                except Exception as e:
                    counts[table] = -1  # Error indicator
        
        await engine.dispose()
        return counts
    
    async def run_migration(self):
        """Run the complete migration process"""
        logger.info("Starting test database migration...")
        logger.info("="*60)
        
        try:
            # Step 1: Create test database
            await self.create_test_database()
            
            # Step 2: Create schema with ordered approach
            await self.create_schema_ordered()
            
            # Step 3: Seed minimal data
            engine = create_async_engine(self.test_db_url, echo=False)
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            
            async with async_session() as session:
                try:
                    await self.seed_minimal_data(session)
                    await session.commit()
                    logger.info("✓ Minimal data seeded successfully")
                    
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error seeding data: {e}")
                    raise
            
            await engine.dispose()
            
            # Step 4: Get counts from both databases
            logger.info("\n" + "="*60)
            source_counts = await self.get_table_counts(self.source_db_url, "source")
            test_counts = await self.get_table_counts(self.test_db_url, "test")
            
            # Step 5: Generate reconciliation report
            logger.info("\n" + "="*60)
            logger.info("RECONCILIATION REPORT")
            logger.info("="*60)
            logger.info(f"{'Table':<35} {'Source DB':>12} {'Test DB':>12} {'Status':>15}")
            logger.info("-"*74)
            
            all_tables = sorted(set(source_counts.keys()) | set(test_counts.keys()))
            
            for table in all_tables:
                source_count = source_counts.get(table, 0)
                test_count = test_counts.get(table, 0)
                
                if table not in test_counts:
                    status = "✗ Missing"
                elif test_count == -1:
                    status = "⚠ Error"
                elif test_count > 0:
                    status = "✓ Created"
                else:
                    status = "○ Empty"
                
                logger.info(f"{table:<35} {source_count:>12,} {test_count:>12,} {status:>15}")
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info("SUMMARY")
            logger.info("="*60)
            logger.info(f"Total tables in source DB: {len(source_counts)}")
            logger.info(f"Total tables in test DB: {len(test_counts)}")
            logger.info(f"Tables with data in test DB: {sum(1 for c in test_counts.values() if c > 0)}")
            
            logger.info("\n" + "="*60)
            logger.info("✅ Test database migration completed successfully!")
            logger.info(f"Test database '{self.test_db_name}' is ready for use")
            logger.info(f"Connection string: {self.test_db_url}")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise


async def main():
    """Main entry point"""
    # Get database URL from environment or use default
    source_db_url = os.getenv(
        'DATABASE_URL',
        'postgresql+asyncpg://postgres:postgres@localhost:5432/synapse_dt'
    )
    
    # Ensure we use asyncpg driver
    if 'postgresql://' in source_db_url and '+asyncpg' not in source_db_url:
        source_db_url = source_db_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    # Create migration instance
    migration = SimpleDatabaseMigration(
        source_db_url=source_db_url,
        test_db_name="synapse_dt_test"
    )
    
    # Run migration
    await migration.run_migration()


if __name__ == "__main__":
    asyncio.run(main())