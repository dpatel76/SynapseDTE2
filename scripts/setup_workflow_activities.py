#!/usr/bin/env python3
"""
Setup workflow activities tables and migrate existing data
This script handles the complete setup in the correct order
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowActivitySetup:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def create_enums(self, session: AsyncSession):
        """Create enum types if they don't exist"""
        logger.info("Creating enum types...")
        
        try:
            # Check if enums exist
            enum_check = await session.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'activity_status_enum'
                )
            """))
            
            if not enum_check.scalar():
                await session.execute(text("""
                    CREATE TYPE activity_status_enum AS ENUM (
                        'not_started', 'in_progress', 'completed', 
                        'revision_requested', 'blocked', 'skipped'
                    )
                """))
                
                await session.execute(text("""
                    CREATE TYPE activity_type_enum AS ENUM (
                        'start', 'task', 'review', 'approval', 'complete', 'custom'
                    )
                """))
                
                await session.commit()
                logger.info("Enum types created successfully")
            else:
                logger.info("Enum types already exist")
                
        except Exception as e:
            logger.error(f"Error creating enums: {e}")
            await session.rollback()
            raise
    
    async def create_tables(self, session: AsyncSession):
        """Create workflow activity tables"""
        logger.info("Creating workflow activity tables...")
        
        try:
            # Create workflow_activities table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS workflow_activities (
                    activity_id SERIAL PRIMARY KEY,
                    cycle_id INTEGER NOT NULL,
                    report_id INTEGER NOT NULL,
                    phase_name VARCHAR(100) NOT NULL,
                    activity_name VARCHAR(255) NOT NULL,
                    activity_type activity_type_enum NOT NULL,
                    activity_order INTEGER NOT NULL,
                    status activity_status_enum NOT NULL DEFAULT 'not_started',
                    can_start BOOLEAN NOT NULL DEFAULT FALSE,
                    can_complete BOOLEAN NOT NULL DEFAULT FALSE,
                    is_manual BOOLEAN NOT NULL DEFAULT TRUE,
                    is_optional BOOLEAN NOT NULL DEFAULT FALSE,
                    started_at TIMESTAMP WITH TIME ZONE,
                    started_by INTEGER REFERENCES users(user_id),
                    completed_at TIMESTAMP WITH TIME ZONE,
                    completed_by INTEGER REFERENCES users(user_id),
                    revision_requested_at TIMESTAMP WITH TIME ZONE,
                    revision_requested_by INTEGER REFERENCES users(user_id),
                    revision_reason TEXT,
                    blocked_at TIMESTAMP WITH TIME ZONE,
                    blocked_reason TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_workflow_activities_unique_activity 
                        UNIQUE (cycle_id, report_id, phase_name, activity_name)
                )
            """))
            
            # Create indexes
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_workflow_activities_cycle_report 
                ON workflow_activities(cycle_id, report_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_workflow_activities_phase 
                ON workflow_activities(cycle_id, report_id, phase_name)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_workflow_activities_status 
                ON workflow_activities(status)
            """))
            
            # Create workflow_activity_history table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS workflow_activity_history (
                    history_id SERIAL PRIMARY KEY,
                    activity_id INTEGER NOT NULL REFERENCES workflow_activities(activity_id),
                    cycle_id INTEGER NOT NULL,
                    report_id INTEGER NOT NULL,
                    phase_name VARCHAR(100) NOT NULL,
                    activity_name VARCHAR(255) NOT NULL,
                    from_status VARCHAR(50),
                    to_status VARCHAR(50) NOT NULL,
                    changed_by INTEGER NOT NULL REFERENCES users(user_id),
                    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    change_reason TEXT,
                    metadata JSONB
                )
            """))
            
            # Create workflow_activity_dependencies table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS workflow_activity_dependencies (
                    dependency_id SERIAL PRIMARY KEY,
                    phase_name VARCHAR(100) NOT NULL,
                    activity_name VARCHAR(255) NOT NULL,
                    depends_on_activity VARCHAR(255) NOT NULL,
                    dependency_type VARCHAR(50) NOT NULL DEFAULT 'completion',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_activity_dependencies_unique 
                        UNIQUE (phase_name, activity_name, depends_on_activity)
                )
            """))
            
            # Create workflow_activity_templates table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS workflow_activity_templates (
                    template_id SERIAL PRIMARY KEY,
                    phase_name VARCHAR(100) NOT NULL,
                    activity_name VARCHAR(255) NOT NULL,
                    activity_type activity_type_enum NOT NULL,
                    activity_order INTEGER NOT NULL,
                    description TEXT,
                    is_manual BOOLEAN NOT NULL DEFAULT TRUE,
                    is_optional BOOLEAN NOT NULL DEFAULT FALSE,
                    required_role VARCHAR(100),
                    auto_complete_on_event VARCHAR(100),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_activity_templates_unique 
                        UNIQUE (phase_name, activity_name)
                )
            """))
            
            await session.commit()
            logger.info("Tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            await session.rollback()
            raise
    
    async def populate_templates(self, session: AsyncSession):
        """Populate activity templates"""
        logger.info("Populating activity templates...")
        
        templates = [
            # Planning Phase
            ('Planning', 'Start Planning Phase', 'start', 1, 'Initialize planning phase', True, False, 'Tester', None),
            ('Planning', 'Generate Attributes', 'task', 2, 'Generate test attributes using LLM', False, False, 'Tester', None),
            ('Planning', 'Review Attributes', 'task', 3, 'Review and edit generated attributes', True, False, 'Tester', None),
            ('Planning', 'Tester Review', 'review', 4, 'Submit for report owner review', True, False, 'Tester', None),
            ('Planning', 'Report Owner Approval', 'approval', 5, 'Report owner approves attributes', True, False, 'Report Owner', None),
            ('Planning', 'Complete Planning Phase', 'complete', 6, 'Finalize planning phase', False, False, None, None),
            
            # Data Profiling Phase
            ('Data Profiling', 'Start Data Profiling', 'start', 1, 'Initialize data profiling', True, False, 'Tester', None),
            ('Data Profiling', 'Profile Data Sources', 'task', 2, 'Analyze data sources and patterns', True, False, 'Tester', None),
            ('Data Profiling', 'Document Findings', 'task', 3, 'Document profiling results', True, False, 'Tester', None),
            ('Data Profiling', 'Complete Data Profiling', 'complete', 4, 'Finalize data profiling', True, False, 'Tester', None),
            
            # Scoping Phase
            ('Scoping', 'Start Scoping Phase', 'start', 1, 'Initialize scoping phase', True, False, 'Tester', None),
            ('Scoping', 'Define Scope', 'task', 2, 'Define testing scope and boundaries', True, False, 'Tester', None),
            ('Scoping', 'Tester Review', 'review', 3, 'Submit scope for approval', True, False, 'Tester', None),
            ('Scoping', 'Report Owner Approval', 'approval', 4, 'Report owner approves scope', True, False, 'Report Owner', None),
            ('Scoping', 'Complete Scoping Phase', 'complete', 5, 'Finalize scoping phase', False, False, None, None),
            
            # Sample Selection Phase
            ('Sample Selection', 'Start Sample Selection', 'start', 1, 'Initialize sample selection', True, False, 'Tester', None),
            ('Sample Selection', 'Generate Samples', 'task', 2, 'Generate test samples', True, False, 'Tester', None),
            ('Sample Selection', 'Review Samples', 'task', 3, 'Review and adjust samples', True, False, 'Tester', None),
            ('Sample Selection', 'Complete Sample Selection', 'complete', 4, 'Finalize sample selection', True, False, 'Tester', None),
            
            # Data Provider ID Phase
            ('Data Provider ID', 'Start Data Provider ID', 'start', 1, 'Initialize data provider identification', True, False, 'CDO', None),
            ('Data Provider ID', 'LOB Executive Assignment', 'task', 2, 'Assign LOB executives', True, False, 'CDO', None),
            ('Data Provider ID', 'Data Owner Assignment', 'task', 3, 'Assign data owners', True, False, 'Report Owner Executive', None),
            ('Data Provider ID', 'Data Provider Assignment', 'task', 4, 'Assign data providers', True, False, 'Data Owner', None),
            ('Data Provider ID', 'Complete Provider ID', 'complete', 5, 'Complete provider identification', False, False, None, None),
            
            # Data Owner ID Phase
            ('Data Owner ID', 'Start Data Owner ID', 'start', 1, 'Initialize data owner identification', True, False, 'CDO', None),
            ('Data Owner ID', 'Assign LOB Executives', 'task', 2, 'CDO assigns LOB executives', True, False, 'CDO', None),
            ('Data Owner ID', 'Assign Data Owners', 'task', 3, 'Executives assign data owners', True, False, 'Report Owner Executive', None),
            ('Data Owner ID', 'Complete Data Owner ID', 'complete', 4, 'Complete data owner identification', False, False, None, None),
            
            # Request Info Phase
            ('Request Info', 'Start Request Info', 'start', 1, 'Initialize request info phase', False, False, None, 'sample_selection_complete'),
            ('Request Info', 'Generate Test Cases', 'task', 2, 'Generate test cases FROM cycle_report_sample_selection_samples', False, False, None, None),
            ('Request Info', 'Data Provider Upload', 'task', 3, 'Data providers upload documents', True, False, 'Data Provider', None),
            ('Request Info', 'Complete Request Info', 'complete', 4, 'Complete request info phase', False, False, None, None),
            
            # Test Execution Phase
            ('Test Execution', 'Start Test Execution', 'start', 1, 'Initialize test execution', True, False, 'Tester', None),
            ('Test Execution', 'Execute Tests', 'task', 2, 'Execute test cases', True, False, 'Tester', None),
            ('Test Execution', 'Document Results', 'task', 3, 'Document test results', True, False, 'Tester', None),
            ('Test Execution', 'Complete Test Execution', 'complete', 4, 'Complete test execution', True, False, 'Tester', None),
            
            # Observation Management Phase
            ('Observation Management', 'Start Observations', 'start', 1, 'Initialize observation management', True, False, 'Tester', None),
            ('Observation Management', 'Create Observations', 'task', 2, 'Create and document observations', True, False, 'Tester', None),
            ('Observation Management', 'Data Provider Response', 'task', 3, 'Data providers respond to observations', True, True, 'Data Provider', None),
            ('Observation Management', 'Finalize Observations', 'task', 4, 'Finalize all observations', True, False, 'Tester', None),
            ('Observation Management', 'Complete Observations', 'complete', 5, 'Complete observation management', True, False, 'Tester', None),
            
            # Test Report Phase
            ('Test Report', 'Start Test Report', 'start', 1, 'Initialize test report generation', True, False, 'Tester', None),
            ('Test Report', 'Generate Report', 'task', 2, 'Generate test report', True, False, 'Tester', None),
            ('Test Report', 'Review Report', 'review', 3, 'Review generated report', True, False, 'Test Manager', None),
            ('Test Report', 'Approve Report', 'approval', 4, 'Approve final report', True, False, 'Report Owner', None),
            ('Test Report', 'Complete Test Report', 'complete', 5, 'Complete test report phase', False, False, None, None),
        ]
        
        try:
            for template in templates:
                await session.execute(text("""
                    INSERT INTO workflow_activity_templates 
                    (phase_name, activity_name, activity_type, activity_order, description, 
                     is_manual, is_optional, required_role, auto_complete_on_event)
                    VALUES (:phase_name, :activity_name, :activity_type, :activity_order, 
                            :description, :is_manual, :is_optional, :required_role, :auto_complete_on_event)
                    ON CONFLICT (phase_name, activity_name) DO NOTHING
                """), {
                    'phase_name': template[0],
                    'activity_name': template[1],
                    'activity_type': template[2],
                    'activity_order': template[3],
                    'description': template[4],
                    'is_manual': template[5],
                    'is_optional': template[6],
                    'required_role': template[7],
                    'auto_complete_on_event': template[8]
                })
            
            await session.commit()
            logger.info("Activity templates populated successfully")
            
        except Exception as e:
            logger.error(f"Error populating templates: {e}")
            await session.rollback()
            raise
    
    async def populate_dependencies(self, session: AsyncSession):
        """Populate activity dependencies"""
        logger.info("Populating activity dependencies...")
        
        dependencies = [
            # Planning Phase
            ('Planning', 'Generate Attributes', 'Start Planning Phase', 'completion'),
            ('Planning', 'Review Attributes', 'Generate Attributes', 'completion'),
            ('Planning', 'Tester Review', 'Review Attributes', 'completion'),
            ('Planning', 'Report Owner Approval', 'Tester Review', 'completion'),
            ('Planning', 'Complete Planning Phase', 'Report Owner Approval', 'approval'),
            
            # Data Profiling
            ('Data Profiling', 'Profile Data Sources', 'Start Data Profiling', 'completion'),
            ('Data Profiling', 'Document Findings', 'Profile Data Sources', 'completion'),
            ('Data Profiling', 'Complete Data Profiling', 'Document Findings', 'completion'),
            
            # Scoping
            ('Scoping', 'Define Scope', 'Start Scoping Phase', 'completion'),
            ('Scoping', 'Tester Review', 'Define Scope', 'completion'),
            ('Scoping', 'Report Owner Approval', 'Tester Review', 'completion'),
            ('Scoping', 'Complete Scoping Phase', 'Report Owner Approval', 'approval'),
            
            # Sample Selection
            ('Sample Selection', 'Generate Samples', 'Start Sample Selection', 'completion'),
            ('Sample Selection', 'Review Samples', 'Generate Samples', 'completion'),
            ('Sample Selection', 'Complete Sample Selection', 'Review Samples', 'completion'),
            
            # Data Provider ID
            ('Data Provider ID', 'LOB Executive Assignment', 'Start Data Provider ID', 'completion'),
            ('Data Provider ID', 'Data Owner Assignment', 'LOB Executive Assignment', 'completion'),
            ('Data Provider ID', 'Data Provider Assignment', 'Data Owner Assignment', 'completion'),
            ('Data Provider ID', 'Complete Provider ID', 'Data Provider Assignment', 'completion'),
            
            # Data Owner ID
            ('Data Owner ID', 'Assign LOB Executives', 'Start Data Owner ID', 'completion'),
            ('Data Owner ID', 'Assign Data Owners', 'Assign LOB Executives', 'completion'),
            ('Data Owner ID', 'Complete Data Owner ID', 'Assign Data Owners', 'completion'),
            
            # Request Info
            ('Request Info', 'Generate Test Cases', 'Start Request Info', 'completion'),
            ('Request Info', 'Data Provider Upload', 'Generate Test Cases', 'completion'),
            ('Request Info', 'Complete Request Info', 'Data Provider Upload', 'any'),
            
            # Test Execution
            ('Test Execution', 'Execute Tests', 'Start Test Execution', 'completion'),
            ('Test Execution', 'Document Results', 'Execute Tests', 'any'),
            ('Test Execution', 'Complete Test Execution', 'Document Results', 'completion'),
            
            # Observation Management
            ('Observation Management', 'Create Observations', 'Start Observations', 'completion'),
            ('Observation Management', 'Data Provider Response', 'Create Observations', 'any'),
            ('Observation Management', 'Finalize Observations', 'Create Observations', 'any'),
            ('Observation Management', 'Complete Observations', 'Finalize Observations', 'completion'),
            
            # Test Report
            ('Test Report', 'Generate Report', 'Start Test Report', 'completion'),
            ('Test Report', 'Review Report', 'Generate Report', 'completion'),
            ('Test Report', 'Approve Report', 'Review Report', 'completion'),
            ('Test Report', 'Complete Test Report', 'Approve Report', 'approval'),
        ]
        
        try:
            for dep in dependencies:
                await session.execute(text("""
                    INSERT INTO workflow_activity_dependencies 
                    (phase_name, activity_name, depends_on_activity, dependency_type)
                    VALUES (:phase_name, :activity_name, :depends_on_activity, :dependency_type)
                    ON CONFLICT (phase_name, activity_name, depends_on_activity) DO NOTHING
                """), {
                    'phase_name': dep[0],
                    'activity_name': dep[1],
                    'depends_on_activity': dep[2],
                    'dependency_type': dep[3]
                })
            
            await session.commit()
            logger.info("Activity dependencies populated successfully")
            
        except Exception as e:
            logger.error(f"Error populating dependencies: {e}")
            await session.rollback()
            raise
    
    async def migrate_existing_data(self, session: AsyncSession):
        """Migrate existing phase_data to workflow_activities table"""
        logger.info("Migrating existing phase data...")
        
        try:
            # Get all workflow phases with phase_data
            result = await session.execute(text("""
                SELECT phase_id, cycle_id, report_id, phase_name, phase_data, 
                       actual_start_date, actual_end_date, started_by, completed_by
                FROM workflow_phases 
                WHERE phase_data IS NOT NULL AND phase_data != '{}'::jsonb
            """))
            
            migrated_count = 0
            for row in result:
                phase_id, cycle_id, report_id, phase_name, phase_data, start_date, end_date, started_by, completed_by = row
                
                if not phase_data:
                    continue
                
                # Parse activities from phase_data
                activities = phase_data.get('activities', {})
                
                if not activities:
                    continue
                
                logger.info(f"Migrating activities for cycle {cycle_id}, report {report_id}, phase {phase_name}")
                
                # Get templates for this phase
                templates_result = await session.execute(text("""
                    SELECT activity_name, activity_type, activity_order, is_manual, is_optional, required_role
                    FROM workflow_activity_templates
                    WHERE phase_name = :phase_name AND is_active = true
                    ORDER BY activity_order
                """), {'phase_name': phase_name})
                
                template_map = {
                    row[0]: {
                        'type': row[1], 
                        'order': row[2], 
                        'is_manual': row[3], 
                        'is_optional': row[4], 
                        'required_role': row[5]
                    } 
                    for row in templates_result
                }
                
                # Process each activity
                for activity_name, activity_data in activities.items():
                    template = template_map.get(activity_name)
                    if not template:
                        logger.warning(f"Activity '{activity_name}' not found in templates for phase '{phase_name}'")
                        continue
                    
                    # Map old state to new status
                    old_state = activity_data.get('state', 'NOT_STARTED')
                    status_map = {
                        'NOT_STARTED': 'not_started',
                        'IN_PROGRESS': 'in_progress',
                        'COMPLETED': 'completed',
                        'REVISION_REQUESTED': 'revision_requested'
                    }
                    status = status_map.get(old_state, 'not_started')
                    
                    # Extract timestamps
                    started_at = activity_data.get('started_at')
                    completed_at = activity_data.get('completed_at')
                    
                    # Convert string timestamps
                    if started_at and isinstance(started_at, str):
                        started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                    if completed_at and isinstance(completed_at, str):
                        completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    
                    # Insert activity
                    await session.execute(text("""
                        INSERT INTO workflow_activities (
                            cycle_id, report_id, phase_name, activity_name, activity_type, 
                            activity_order, status, can_start, can_complete, is_manual, is_optional,
                            started_at, started_by, completed_at, completed_by, metadata
                        ) VALUES (
                            :cycle_id, :report_id, :phase_name, :activity_name, :activity_type,
                            :activity_order, :status, :can_start, :can_complete, :is_manual, :is_optional,
                            :started_at, :started_by, :completed_at, :completed_by, :metadata
                        )
                        ON CONFLICT (cycle_id, report_id, phase_name, activity_name) DO UPDATE SET
                            status = EXCLUDED.status,
                            started_at = EXCLUDED.started_at,
                            started_by = EXCLUDED.started_by,
                            completed_at = EXCLUDED.completed_at,
                            completed_by = EXCLUDED.completed_by,
                            updated_at = NOW()
                    """), {
                        'cycle_id': cycle_id,
                        'report_id': report_id,
                        'phase_name': phase_name,
                        'activity_name': activity_name,
                        'activity_type': template['type'],
                        'activity_order': template['order'],
                        'status': status,
                        'can_start': status == 'not_started',
                        'can_complete': status == 'in_progress',
                        'is_manual': template['is_manual'],
                        'is_optional': template['is_optional'],
                        'started_at': started_at,
                        'started_by': activity_data.get('started_by'),
                        'completed_at': completed_at,
                        'completed_by': activity_data.get('completed_by'),
                        'metadata': json.dumps(activity_data.get('metadata', {})) if activity_data.get('metadata') else None
                    })
                    
                    migrated_count += 1
            
            await session.commit()
            logger.info(f"Migrated {migrated_count} activities successfully")
            
        except Exception as e:
            logger.error(f"Error migrating data: {e}")
            await session.rollback()
            raise
    
    async def update_activity_flags(self, session: AsyncSession):
        """Update can_start and can_complete flags based on dependencies"""
        logger.info("Updating activity flags based on dependencies...")
        
        try:
            await session.execute(text("""
                WITH activity_deps AS (
                    SELECT 
                        wa.activity_id,
                        wa.cycle_id,
                        wa.report_id,
                        wa.phase_name,
                        wa.activity_name,
                        wa.status,
                        dep.depends_on_activity,
                        dep_wa.status as dep_status
                    FROM workflow_activities wa
                    LEFT JOIN workflow_activity_dependencies dep 
                        ON wa.phase_name = dep.phase_name 
                        AND wa.activity_name = dep.activity_name
                        AND dep.is_active = true
                    LEFT JOIN workflow_activities dep_wa
                        ON wa.cycle_id = dep_wa.cycle_id
                        AND wa.report_id = dep_wa.report_id
                        AND wa.phase_name = dep_wa.phase_name
                        AND dep.depends_on_activity = dep_wa.activity_name
                )
                UPDATE workflow_activities wa
                SET 
                    can_start = CASE 
                        WHEN wa.status != 'not_started' THEN false
                        WHEN NOT EXISTS (
                            SELECT 1 FROM activity_deps ad 
                            WHERE ad.activity_id = wa.activity_id 
                            AND (ad.dep_status IS NULL OR ad.dep_status != 'completed')
                        ) THEN true
                        ELSE false
                    END,
                    can_complete = CASE
                        WHEN wa.status = 'in_progress' THEN true
                        ELSE false
                    END,
                    updated_at = NOW()
                WHERE wa.status IN ('not_started', 'in_progress')
            """))
            
            await session.commit()
            logger.info("Activity flags updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating flags: {e}")
            await session.rollback()
            raise
    
    async def run(self):
        """Run the complete setup"""
        async with self.async_session() as session:
            try:
                # Step 1: Create enums
                await self.create_enums(session)
                
                # Step 2: Create tables
                await self.create_tables(session)
                
                # Step 3: Populate templates
                await self.populate_templates(session)
                
                # Step 4: Populate dependencies
                await self.populate_dependencies(session)
                
                # Step 5: Migrate existing data
                await self.migrate_existing_data(session)
                
                # Step 6: Update activity flags
                await self.update_activity_flags(session)
                
                logger.info("Workflow activities setup completed successfully!")
                
            except Exception as e:
                logger.error(f"Setup failed: {e}")
                raise
            finally:
                await self.engine.dispose()


async def main():
    """Main entry point"""
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Convert to async URL
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    setup = WorkflowActivitySetup(db_url)
    await setup.run()


if __name__ == "__main__":
    asyncio.run(main())