#!/usr/bin/env python3
"""
Comprehensive Database Migration Script for SynapseDTE Test Database
Creates a complete test database with all tables, seed data, and configurations
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import asyncpg
import logging
from sqlalchemy import create_engine, text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Any, Optional
import json

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import Base
from app.core.auth import get_password_hash
from app.models import *  # Import all models to ensure they're registered

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestDatabaseMigration:
    """Handles creation and setup of test database with all required data"""
    
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
    
    async def create_schema(self):
        """Create all tables in test database"""
        logger.info("Creating database schema...")
        
        # Create engine for test database
        engine = create_async_engine(self.test_db_url, echo=False)
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
            # Create ENUMs explicitly
            await self._create_enums(conn)
            
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
            ("activitystate", ["Not Started", "In Progress", "Completed", "Revision Requested"])
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
    
    async def seed_rbac_data(self, session: AsyncSession):
        """Seed RBAC roles and permissions"""
        logger.info("Seeding RBAC data...")
        
        # Create roles
        roles_data = [
            {"name": "Tester", "description": "Executes testing activities across all phases"},
            {"name": "Test Executive", "description": "Oversees testing operations and teams"},
            {"name": "Report Owner", "description": "Owns specific regulatory reports"},
            {"name": "Report Owner Executive", "description": "Executive oversight for report owners"},
            {"name": "Data Owner", "description": "Provides data for testing"},
            {"name": "Data Executive", "description": "Executive oversight for data operations"},
            {"name": "Admin", "description": "System administrator"}
        ]
        
        for role_data in roles_data:
            role = Role(**role_data)
            session.add(role)
        
        await session.flush()
        
        # Create permissions (simplified list - add all 50+ as needed)
        permissions_data = [
            # Planning Phase
            {"operation": "planning.view", "description": "View planning phase"},
            {"operation": "planning.execute", "description": "Execute planning activities"},
            {"operation": "planning.approve", "description": "Approve planning submissions"},
            
            # Data Profiling
            {"operation": "profiling.view", "description": "View data profiling"},
            {"operation": "profiling.execute", "description": "Execute profiling"},
            {"operation": "profiling.approve", "description": "Approve profiling rules"},
            
            # Scoping
            {"operation": "scoping.view", "description": "View scoping phase"},
            {"operation": "scoping.submit", "description": "Submit scope"},
            {"operation": "scoping.approve", "description": "Approve scope"},
            
            # Sample Selection
            {"operation": "samples.view", "description": "View samples"},
            {"operation": "samples.create", "description": "Create sample sets"},
            {"operation": "samples.approve", "description": "Approve samples"},
            
            # Request Info
            {"operation": "requests.view", "description": "View data requests"},
            {"operation": "requests.create", "description": "Create data requests"},
            {"operation": "requests.respond", "description": "Respond to data requests"},
            
            # Testing
            {"operation": "testing.view", "description": "View test execution"},
            {"operation": "testing.execute", "description": "Execute tests"},
            {"operation": "testing.review", "description": "Review test results"},
            
            # Observations
            {"operation": "observations.view", "description": "View observations"},
            {"operation": "observations.create", "description": "Create observations"},
            {"operation": "observations.approve", "description": "Approve observations"},
            
            # Reports
            {"operation": "reports.view", "description": "View reports"},
            {"operation": "reports.generate", "description": "Generate reports"},
            {"operation": "reports.approve", "description": "Approve reports"},
            
            # Admin
            {"operation": "admin.users", "description": "Manage users"},
            {"operation": "admin.system", "description": "System administration"}
        ]
        
        for perm_data in permissions_data:
            perm = Permission(**perm_data)
            session.add(perm)
        
        await session.flush()
        
        # Create role-permission mappings
        role_permissions = {
            "Tester": [
                "planning.view", "planning.execute",
                "profiling.view", "profiling.execute",
                "scoping.view", "scoping.submit",
                "samples.view", "samples.create",
                "requests.view", "requests.create",
                "testing.view", "testing.execute",
                "observations.view", "observations.create",
                "reports.view"
            ],
            "Test Executive": [
                "planning.view", "planning.approve",
                "profiling.view", "profiling.approve",
                "scoping.view", "scoping.approve",
                "samples.view", "samples.approve",
                "requests.view",
                "testing.view", "testing.review",
                "observations.view", "observations.approve",
                "reports.view", "reports.generate", "reports.approve"
            ],
            "Report Owner": [
                "planning.view", "planning.approve",
                "profiling.view", "profiling.approve",
                "scoping.view", "scoping.approve",
                "samples.view", "samples.approve",
                "testing.view",
                "observations.view", "observations.approve",
                "reports.view", "reports.approve"
            ],
            "Data Owner": [
                "requests.view", "requests.respond",
                "testing.view",
                "observations.view"
            ],
            "Admin": ["admin.users", "admin.system"]
        }
        
        # Get all roles and permissions
        roles = await session.execute(select(Role))
        roles_dict = {r.name: r for r in roles.scalars().all()}
        
        perms = await session.execute(select(Permission))
        perms_dict = {p.operation: p for p in perms.scalars().all()}
        
        # Create mappings
        for role_name, perm_ops in role_permissions.items():
            role = roles_dict.get(role_name)
            if role:
                for op in perm_ops:
                    perm = perms_dict.get(op)
                    if perm:
                        role_perm = RolePermission(
                            role_id=role.role_id,
                            permission_id=perm.permission_id
                        )
                        session.add(role_perm)
        
        logger.info("✓ RBAC data seeded successfully")
    
    async def seed_test_users(self, session: AsyncSession):
        """Create test users for each role"""
        logger.info("Creating test users...")
        
        test_users = [
            {
                "email": "admin@example.com",
                "username": "admin",
                "first_name": "System",
                "last_name": "Administrator",
                "role": "Admin",
                "password": "admin123"
            },
            {
                "email": "test.manager@example.com",
                "username": "testmanager",
                "first_name": "Test",
                "last_name": "Manager",
                "role": "Test Executive",
                "password": "password123"
            },
            {
                "email": "tester1@example.com",
                "username": "tester1",
                "first_name": "John",
                "last_name": "Tester",
                "role": "Tester",
                "password": "password123"
            },
            {
                "email": "report.owner1@example.com",
                "username": "reportowner1",
                "first_name": "Jane",
                "last_name": "Owner",
                "role": "Report Owner",
                "password": "password123"
            },
            {
                "email": "data.owner1@example.com",
                "username": "dataowner1",
                "first_name": "Bob",
                "last_name": "Data",
                "role": "Data Owner",
                "password": "password123"
            },
            {
                "email": "report.executive@example.com",
                "username": "reportexec",
                "first_name": "Sarah",
                "last_name": "Executive",
                "role": "Report Owner Executive",
                "password": "password123"
            },
            {
                "email": "data.executive@example.com",
                "username": "dataexec",
                "first_name": "Mike",
                "last_name": "DataExec",
                "role": "Data Executive",
                "password": "password123"
            }
        ]
        
        for user_data in test_users:
            password = user_data.pop("password")
            user = User(**user_data)
            user.hashed_password = get_password_hash(password)
            user.is_active = True
            session.add(user)
        
        logger.info(f"✓ Created {len(test_users)} test users")
    
    async def seed_business_data(self, session: AsyncSession):
        """Seed LOBs, Reports, and other business entities"""
        logger.info("Seeding business data...")
        
        # Create LOBs
        lobs = [
            {"lob_name": "Retail Banking", "lob_code": "RB", "description": "Retail banking operations"},
            {"lob_name": "Commercial Banking", "lob_code": "CB", "description": "Commercial banking operations"},
            {"lob_name": "Investment Banking", "lob_code": "IB", "description": "Investment banking operations"},
            {"lob_name": "Wealth Management", "lob_code": "WM", "description": "Wealth management services"}
        ]
        
        for lob_data in lobs:
            lob = LOB(**lob_data)
            session.add(lob)
        
        await session.flush()
        
        # Get users for assignments
        users = await session.execute(select(User))
        users_dict = {u.email: u for u in users.scalars().all()}
        
        # Get LOBs
        lobs = await session.execute(select(LOB))
        lobs_list = lobs.scalars().all()
        
        # Create Reports
        reports = [
            {
                "report_name": "FR Y-14M Credit Card",
                "regulation": "Federal Reserve",
                "description": "Monthly credit card data collection",
                "frequency": "Monthly",
                "report_owner_id": users_dict["report.owner1@example.com"].user_id,
                "lob_id": lobs_list[0].lob_id
            },
            {
                "report_name": "FFIEC 031 Call Report",
                "regulation": "FFIEC",
                "description": "Quarterly bank call report",
                "frequency": "Quarterly",
                "report_owner_id": users_dict["report.owner1@example.com"].user_id,
                "lob_id": lobs_list[1].lob_id
            },
            {
                "report_name": "FR Y-9C Consolidated",
                "regulation": "Federal Reserve",
                "description": "Consolidated financial statements",
                "frequency": "Quarterly",
                "report_owner_id": users_dict["report.owner1@example.com"].user_id,
                "lob_id": lobs_list[2].lob_id
            }
        ]
        
        for report_data in reports:
            report = Report(**report_data)
            session.add(report)
        
        logger.info("✓ Business data seeded successfully")
    
    async def seed_workflow_config(self, session: AsyncSession):
        """Seed workflow configurations"""
        logger.info("Seeding workflow configurations...")
        
        # Create workflow definition
        workflow = WorkflowDefinition(
            workflow_name="Standard Testing Workflow",
            description="7-phase testing workflow for regulatory reports",
            version="1.0",
            is_active=True
        )
        session.add(workflow)
        await session.flush()
        
        # Define phases with dependencies
        phases = [
            {
                "phase_name": "Planning",
                "phase_order": 1,
                "description": "Initial planning and attribute identification",
                "required_role": "Tester",
                "sla_days": 5,
                "dependencies": []
            },
            {
                "phase_name": "Data Profiling",
                "phase_order": 2,
                "description": "Profile data and generate quality rules",
                "required_role": "Tester",
                "sla_days": 3,
                "dependencies": ["Planning"]
            },
            {
                "phase_name": "Scoping",
                "phase_order": 3,
                "description": "Define testing scope",
                "required_role": "Tester",
                "sla_days": 2,
                "dependencies": ["Data Profiling"]
            },
            {
                "phase_name": "Sample Selection",
                "phase_order": 4,
                "description": "Select data samples for testing",
                "required_role": "Tester",
                "sla_days": 2,
                "dependencies": ["Scoping"]
            },
            {
                "phase_name": "Data Provider ID",
                "phase_order": 5,
                "description": "Identify data providers",
                "required_role": "Data Executive",
                "sla_days": 1,
                "dependencies": ["Scoping"]
            },
            {
                "phase_name": "Request Info",
                "phase_order": 6,
                "description": "Request information from data providers",
                "required_role": "Tester",
                "sla_days": 3,
                "dependencies": ["Sample Selection", "Data Provider ID"]
            },
            {
                "phase_name": "Testing",
                "phase_order": 7,
                "description": "Execute test cases",
                "required_role": "Tester",
                "sla_days": 5,
                "dependencies": ["Request Info"]
            },
            {
                "phase_name": "Observations",
                "phase_order": 8,
                "description": "Document and manage observations",
                "required_role": "Tester",
                "sla_days": 3,
                "dependencies": ["Testing"]
            },
            {
                "phase_name": "Finalize Test Report",
                "phase_order": 9,
                "description": "Generate and finalize test report",
                "required_role": "Test Executive",
                "sla_days": 2,
                "dependencies": ["Observations"]
            }
        ]
        
        phase_objects = {}
        for phase_data in phases:
            deps = phase_data.pop("dependencies")
            phase = WorkflowPhaseDefinition(
                workflow_id=workflow.workflow_id,
                **phase_data
            )
            session.add(phase)
            await session.flush()
            phase_objects[phase.phase_name] = phase
        
        # Create phase dependencies
        for phase_data in phases:
            phase = phase_objects[phase_data["phase_name"]]
            for dep_name in phase_data.get("dependencies", []):
                dep_phase = phase_objects.get(dep_name)
                if dep_phase:
                    dependency = WorkflowPhaseDependency(
                        workflow_id=workflow.workflow_id,
                        phase_id=phase.phase_definition_id,
                        depends_on_phase_id=dep_phase.phase_definition_id
                    )
                    session.add(dependency)
        
        logger.info("✓ Workflow configurations seeded successfully")
    
    async def seed_data_dictionary(self, session: AsyncSession):
        """Seed regulatory data dictionary entries"""
        logger.info("Seeding data dictionary...")
        
        # Sample data dictionary entries
        entries = [
            {
                "line_item_number": "1",
                "field_name": "Reference Number",
                "description": "Unique identifier for credit card account",
                "data_type": "VARCHAR(50)",
                "is_mandatory": True,
                "mdrm_code": "M214",
                "regulatory_report": "FR Y-14M",
                "section": "Credit Card",
                "is_primary_key": True,
                "has_cde": False,
                "has_historical_issues": False
            },
            {
                "line_item_number": "2",
                "field_name": "Account Number",
                "description": "Credit card account number",
                "data_type": "VARCHAR(20)",
                "is_mandatory": True,
                "mdrm_code": "M215",
                "regulatory_report": "FR Y-14M",
                "section": "Credit Card",
                "is_primary_key": False,
                "has_cde": True,
                "has_historical_issues": False
            },
            {
                "line_item_number": "3",
                "field_name": "Current Credit Limit",
                "description": "Current credit limit on the account",
                "data_type": "DECIMAL(15,2)",
                "is_mandatory": True,
                "mdrm_code": "M216",
                "regulatory_report": "FR Y-14M",
                "section": "Credit Card",
                "is_primary_key": False,
                "has_cde": False,
                "has_historical_issues": True
            }
        ]
        
        # Add more entries as needed (total 118 for FR Y-14M)
        for i in range(4, 119):
            entries.append({
                "line_item_number": str(i),
                "field_name": f"Attribute_{i}",
                "description": f"Test attribute {i}",
                "data_type": "VARCHAR(100)",
                "is_mandatory": i % 3 != 0,  # Some optional
                "mdrm_code": f"M{213+i}",
                "regulatory_report": "FR Y-14M",
                "section": "Credit Card",
                "is_primary_key": False,
                "has_cde": i % 10 == 0,  # Every 10th is CDE
                "has_historical_issues": i % 7 == 0  # Every 7th has issues
            })
        
        for entry_data in entries:
            entry = RegulatoryDataDictionary(**entry_data)
            session.add(entry)
        
        logger.info(f"✓ Added {len(entries)} data dictionary entries")
    
    async def seed_test_cycle(self, session: AsyncSession):
        """Create a test cycle with sample data"""
        logger.info("Creating test cycle...")
        
        # Get users and reports
        tester = await session.execute(
            select(User).where(User.email == "tester1@example.com")
        )
        tester = tester.scalar_one()
        
        test_manager = await session.execute(
            select(User).where(User.email == "test.manager@example.com")
        )
        test_manager = test_manager.scalar_one()
        
        reports = await session.execute(select(Report))
        report = reports.scalars().first()
        
        # Create test cycle
        cycle = TestCycle(
            cycle_name="Q4 2024 Testing Cycle",
            description="Fourth quarter 2024 regulatory testing",
            test_manager_id=test_manager.user_id,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now() + timedelta(days=60),
            status="Active",
            workflow_id=1  # Assuming workflow created above
        )
        session.add(cycle)
        await session.flush()
        
        # Create workflow phases for the cycle
        phase_names = ["Planning", "Data Profiling", "Scoping", "Sample Selection",
                      "Data Provider ID", "Request Info", "Testing", "Observations", 
                      "Finalize Test Report"]
        
        for i, phase_name in enumerate(phase_names):
            # Determine state based on order
            if i < 2:  # First 2 phases complete
                state = "Complete"
                status = "Completed"
                start_date = datetime.now() - timedelta(days=30-i*3)
                end_date = start_date + timedelta(days=2)
            elif i == 2:  # Current phase
                state = "In Progress"
                status = "Active"
                start_date = datetime.now() - timedelta(days=15)
                end_date = None
            else:  # Future phases
                state = "Not Started"
                status = "Not Started"
                start_date = None
                end_date = None
            
            phase = WorkflowPhase(
                cycle_id=cycle.cycle_id,
                report_id=report.report_id,
                phase_name=phase_name,
                state=state,
                status=status,
                schedule_status="On Schedule",
                planned_start_date=datetime.now() - timedelta(days=25-i*3),
                planned_end_date=datetime.now() - timedelta(days=23-i*3),
                actual_start_date=start_date,
                actual_end_date=end_date,
                started_by=tester.user_id if start_date else None,
                completed_by=tester.user_id if end_date else None
            )
            session.add(phase)
        
        # Create report attributes from data dictionary
        dict_entries = await session.execute(
            select(RegulatoryDataDictionary).where(
                RegulatoryDataDictionary.regulatory_report == "FR Y-14M"
            )
        )
        
        for entry in dict_entries.scalars().all():
            attr = ReportAttribute(
                cycle_id=cycle.cycle_id,
                report_id=report.report_id,
                attribute_id=entry.dictionary_id,
                line_item_number=entry.line_item_number,
                attribute_name=entry.field_name,
                description=entry.description,
                data_type=entry.data_type,
                mdrm=entry.mdrm_code,
                mandatory_flag="Mandatory" if entry.is_mandatory else "Optional",
                cde_flag=entry.has_cde,
                is_primary_key=entry.is_primary_key,
                historical_issues_flag=entry.has_historical_issues,
                approval_status="approved" if i < 20 else "pending",
                is_scoped=not entry.is_primary_key and i < 10,  # First 10 non-PK scoped
                risk_score=8 if entry.has_historical_issues else 5,
                llm_risk_rationale="Historical issues require additional testing" if entry.has_historical_issues else "Standard risk attribute",
                is_latest_version=True,
                version_number=1
            )
            session.add(attr)
        
        logger.info("✓ Test cycle created with sample data")
    
    async def copy_data_from_source(self):
        """Copy data from source database (read-only)"""
        logger.info("Analyzing source database...")
        
        # Create read-only connection to source
        source_engine = create_async_engine(
            self.source_db_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"server_settings": {"jit": "off"}}
        )
        
        async with source_engine.begin() as conn:
            # Get table counts
            table_counts = {}
            
            tables = [
                "users", "roles", "permissions", "role_permissions",
                "lobs", "reports", "test_cycles", "workflow_phases",
                "report_attributes", "cycle_report_data_profiling_rules", "sample_sets",
                "test_cases", "testing_test_executions", "observation_groups",
                "regulatory_data_dictionary", "universal_assignments",
                "audit_logs", "universal_sla_configurations"
            ]
            
            for table in tables:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    table_counts[table] = count
                    logger.info(f"  {table}: {count} records")
                except Exception as e:
                    logger.warning(f"  {table}: Unable to count - {str(e)}")
                    table_counts[table] = 0
        
        await source_engine.dispose()
        return table_counts
    
    async def verify_test_database(self):
        """Verify test database and compare with source"""
        logger.info("\nVerifying test database...")
        
        # Get counts from test database
        test_engine = create_async_engine(self.test_db_url, echo=False)
        
        async with test_engine.begin() as conn:
            test_counts = {}
            
            tables = [
                "users", "roles", "permissions", "role_permissions",
                "lobs", "reports", "test_cycles", "workflow_phases",
                "report_attributes", "cycle_report_data_profiling_rules", "regulatory_data_dictionary"
            ]
            
            for table in tables:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    test_counts[table] = count
                except Exception as e:
                    test_counts[table] = 0
        
        await test_engine.dispose()
        
        logger.info("\nTest database record counts:")
        for table, count in test_counts.items():
            logger.info(f"  {table}: {count} records")
        
        return test_counts
    
    async def run_migration(self):
        """Run the complete migration process"""
        logger.info("Starting test database migration...")
        logger.info("="*60)
        
        try:
            # Step 1: Create test database
            await self.create_test_database()
            
            # Step 2: Create schema
            await self.create_schema()
            
            # Step 3: Seed data
            engine = create_async_engine(self.test_db_url, echo=False)
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            
            async with async_session() as session:
                try:
                    # Seed all data
                    await self.seed_rbac_data(session)
                    await self.seed_test_users(session)
                    await self.seed_business_data(session)
                    await self.seed_workflow_config(session)
                    await self.seed_data_dictionary(session)
                    await self.seed_test_cycle(session)
                    
                    await session.commit()
                    logger.info("✓ All data seeded successfully")
                    
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error seeding data: {e}")
                    raise
            
            await engine.dispose()
            
            # Step 4: Get source database counts (read-only)
            logger.info("\n" + "="*60)
            logger.info("Source database analysis:")
            source_counts = await self.copy_data_from_source()
            
            # Step 5: Verify test database
            logger.info("\n" + "="*60)
            test_counts = await self.verify_test_database()
            
            # Step 6: Generate reconciliation report
            logger.info("\n" + "="*60)
            logger.info("RECONCILIATION REPORT")
            logger.info("="*60)
            logger.info(f"{'Table':<30} {'Source DB':>12} {'Test DB':>12} {'Status':>10}")
            logger.info("-"*64)
            
            for table in source_counts.keys():
                source_count = source_counts.get(table, 0)
                test_count = test_counts.get(table, 0)
                
                if table in test_counts:
                    if test_count > 0:
                        status = "✓ Seeded"
                    else:
                        status = "⚠ Empty"
                else:
                    status = "✗ Missing"
                
                logger.info(f"{table:<30} {source_count:>12,} {test_count:>12,} {status:>10}")
            
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
    migration = TestDatabaseMigration(
        source_db_url=source_db_url,
        test_db_name="synapse_dt_test"
    )
    
    # Run migration
    await migration.run_migration()


if __name__ == "__main__":
    asyncio.run(main())