#!/usr/bin/env python3
"""
Migration script to move data from workflow_activities tables to activity_definitions and activity_states tables
This unifies the two activity management systems into one
"""

import asyncio
import logging
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.activity_definition import ActivityDefinition, ActivityState
from app.models.workflow_activity import WorkflowActivity, WorkflowActivityTemplate, ActivityStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActivityMigrator:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def migrate_templates_to_definitions(self):
        """Migrate workflow_activity_templates to activity_definitions"""
        async with self.async_session() as session:
            # Get all templates
            templates = await session.execute(
                select(WorkflowActivityTemplate).where(
                    WorkflowActivityTemplate.is_active == True
                )
            )
            templates = templates.scalars().all()
            
            logger.info(f"Found {len(templates)} templates to migrate")
            
            for template in templates:
                # Check if definition already exists
                existing = await session.execute(
                    select(ActivityDefinition).where(
                        ActivityDefinition.activity_code == template.activity_name.lower().replace(' ', '_')
                    )
                )
                existing = existing.scalar_one_or_none()
                
                if existing:
                    logger.info(f"Definition already exists for {template.activity_name}, skipping")
                    continue
                
                # Map activity type
                activity_type_mapping = {
                    'START': 'phase_start',
                    'TASK': 'manual',
                    'REVIEW': 'manual',
                    'APPROVAL': 'manual',
                    'COMPLETE': 'phase_complete',
                    'CUSTOM': 'manual'
                }
                
                activity_type = activity_type_mapping.get(
                    template.activity_type.value if hasattr(template.activity_type, 'value') else template.activity_type,
                    'manual'
                )
                
                # Create new definition
                definition = ActivityDefinition(
                    phase_name=template.phase_name,
                    activity_name=template.activity_name,
                    activity_code=template.activity_name.lower().replace(' ', '_'),
                    description=template.description or f"{template.activity_name} for {template.phase_name}",
                    activity_type=activity_type,
                    requires_backend_action=not template.is_manual,
                    sequence_order=template.activity_order,
                    can_skip=template.is_optional,
                    can_reset=True,
                    is_active=template.is_active,
                    button_text=template.activity_name,
                    success_message=f"{template.activity_name} completed successfully",
                    instructions=template.description
                )
                
                session.add(definition)
                logger.info(f"Created definition for {template.activity_name}")
            
            await session.commit()
            logger.info("Template migration completed")
    
    async def migrate_activity_instances(self):
        """Migrate workflow_activities to activity_states"""
        async with self.async_session() as session:
            # Get all workflow activities
            activities = await session.execute(
                select(WorkflowActivity)
            )
            activities = activities.scalars().all()
            
            logger.info(f"Found {len(activities)} activities to migrate")
            
            for activity in activities:
                # Find corresponding definition
                definition = await session.execute(
                    select(ActivityDefinition).where(
                        ActivityDefinition.activity_code == activity.activity_name.lower().replace(' ', '_')
                    )
                )
                definition = definition.scalar_one_or_none()
                
                if not definition:
                    logger.warning(f"No definition found for {activity.activity_name}, creating one")
                    
                    # Create definition on the fly
                    activity_type = 'manual'
                    if activity.activity_type:
                        type_value = activity.activity_type.value if hasattr(activity.activity_type, 'value') else activity.activity_type
                        if type_value == 'START':
                            activity_type = 'phase_start'
                        elif type_value == 'COMPLETE':
                            activity_type = 'phase_complete'
                    
                    definition = ActivityDefinition(
                        phase_name=activity.phase_name,
                        activity_name=activity.activity_name,
                        activity_code=activity.activity_name.lower().replace(' ', '_'),
                        description=f"{activity.activity_name} for {activity.phase_name}",
                        activity_type=activity_type,
                        requires_backend_action=not activity.is_manual,
                        sequence_order=activity.activity_order,
                        can_skip=activity.is_optional,
                        can_reset=True,
                        is_active=True,
                        button_text=activity.activity_name,
                        success_message=f"{activity.activity_name} completed successfully"
                    )
                    session.add(definition)
                    await session.flush()
                
                # Check if state already exists
                existing_state = await session.execute(
                    select(ActivityState).where(
                        ActivityState.cycle_id == activity.cycle_id,
                        ActivityState.report_id == activity.report_id,
                        ActivityState.activity_definition_id == definition.id
                    )
                )
                existing_state = existing_state.scalar_one_or_none()
                
                if existing_state:
                    logger.info(f"State already exists for {activity.activity_name} in cycle {activity.cycle_id}, report {activity.report_id}")
                    continue
                
                # Map status
                status_mapping = {
                    ActivityStatus.NOT_STARTED: 'pending',
                    ActivityStatus.IN_PROGRESS: 'active',
                    ActivityStatus.COMPLETED: 'completed',
                    ActivityStatus.REVISION_REQUESTED: 'blocked',
                    ActivityStatus.BLOCKED: 'blocked',
                    ActivityStatus.SKIPPED: 'skipped'
                }
                
                status = status_mapping.get(activity.status, 'pending')
                
                # Create activity state
                state = ActivityState(
                    cycle_id=activity.cycle_id,
                    report_id=activity.report_id,
                    phase_name=activity.phase_name,
                    activity_definition_id=definition.id,
                    status=status,
                    started_at=activity.started_at,
                    started_by=activity.started_by,
                    completed_at=activity.completed_at,
                    completed_by=activity.completed_by,
                    is_blocked=activity.status == ActivityStatus.BLOCKED,
                    blocking_reason=activity.blocked_reason or activity.revision_reason,
                    completion_notes=activity.revision_reason
                )
                
                session.add(state)
                logger.info(f"Created state for {activity.activity_name} in cycle {activity.cycle_id}, report {activity.report_id}")
            
            await session.commit()
            logger.info("Activity instance migration completed")
    
    async def migrate_dependencies(self):
        """Migrate workflow_activity_dependencies to activity_definitions.depends_on_activity_codes"""
        async with self.async_session() as session:
            # Get all dependencies
            result = await session.execute(
                text("""
                    SELECT phase_name, activity_name, depends_on_activity 
                    FROM workflow_activity_dependencies 
                    WHERE is_active = true
                """)
            )
            dependencies = result.fetchall()
            
            logger.info(f"Found {len(dependencies)} dependencies to migrate")
            
            # Group dependencies by activity
            activity_deps = {}
            for dep in dependencies:
                key = (dep.phase_name, dep.activity_name)
                if key not in activity_deps:
                    activity_deps[key] = []
                activity_deps[key].append(dep.depends_on_activity.lower().replace(' ', '_'))
            
            # Update definitions
            for (phase_name, activity_name), deps in activity_deps.items():
                definition = await session.execute(
                    select(ActivityDefinition).where(
                        ActivityDefinition.activity_code == activity_name.lower().replace(' ', '_')
                    )
                )
                definition = definition.scalar_one_or_none()
                
                if definition:
                    definition.depends_on_activity_codes = deps
                    logger.info(f"Updated dependencies for {activity_name}: {deps}")
                else:
                    logger.warning(f"Definition not found for {activity_name}")
            
            await session.commit()
            logger.info("Dependency migration completed")
    
    async def close(self):
        await self.engine.dispose()
    
    async def run_migration(self):
        """Run the complete migration"""
        try:
            logger.info("Starting migration from workflow_activities to activity_states...")
            
            # Step 1: Migrate templates
            logger.info("Step 1: Migrating templates to definitions...")
            await self.migrate_templates_to_definitions()
            
            # Step 2: Migrate activity instances
            logger.info("Step 2: Migrating activity instances to states...")
            await self.migrate_activity_instances()
            
            # Step 3: Migrate dependencies
            logger.info("Step 3: Migrating activity dependencies...")
            await self.migrate_dependencies()
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            raise
        finally:
            await self.close()


async def main():
    # Use the database URL from settings
    db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    migrator = ActivityMigrator(db_url)
    await migrator.run_migration()


if __name__ == "__main__":
    asyncio.run(main())