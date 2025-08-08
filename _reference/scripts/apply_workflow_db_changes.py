"""Apply workflow database changes directly"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def apply_changes():
    """Apply database schema changes for dynamic workflows"""
    
    # Create async engine with proper driver
    database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(database_url)
    
    async with engine.begin() as conn:
        # Add new columns to workflow_activity_templates
        try:
            await conn.execute(text('''
                ALTER TABLE workflow_activity_templates 
                ADD COLUMN IF NOT EXISTS handler_name VARCHAR(255),
                ADD COLUMN IF NOT EXISTS timeout_seconds INTEGER DEFAULT 300,
                ADD COLUMN IF NOT EXISTS retry_policy JSON,
                ADD COLUMN IF NOT EXISTS conditional_expression TEXT,
                ADD COLUMN IF NOT EXISTS execution_mode VARCHAR(50) DEFAULT 'sequential'
            '''))
            logger.info('✓ Added columns to workflow_activity_templates')
        except Exception as e:
            logger.error(f'Error adding columns to workflow_activity_templates: {e}')
        
        # Add new columns to workflow_activities
        try:
            await conn.execute(text('''
                ALTER TABLE workflow_activities 
                ADD COLUMN IF NOT EXISTS instance_id VARCHAR(255),
                ADD COLUMN IF NOT EXISTS parent_activity_id INTEGER,
                ADD COLUMN IF NOT EXISTS execution_mode VARCHAR(50),
                ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS last_error TEXT
            '''))
            logger.info('✓ Added columns to workflow_activities')
        except Exception as e:
            logger.error(f'Error adding columns to workflow_activities: {e}')
        
        # Add foreign key constraint
        try:
            await conn.execute(text('''
                ALTER TABLE workflow_activities 
                ADD CONSTRAINT fk_workflow_activities_parent 
                FOREIGN KEY (parent_activity_id) 
                REFERENCES workflow_activities(activity_id) 
                ON DELETE SET NULL
            '''))
            logger.info('✓ Added foreign key constraint')
        except Exception as e:
            if 'already exists' in str(e):
                logger.info('✓ Foreign key constraint already exists')
            else:
                logger.error(f'Error adding foreign key: {e}')
        
        # Create index
        try:
            await conn.execute(text('''
                CREATE INDEX IF NOT EXISTS ix_workflow_activities_instance_id 
                ON workflow_activities(cycle_id, report_id, instance_id)
            '''))
            logger.info('✓ Created index on instance_id')
        except Exception as e:
            logger.error(f'Error creating index: {e}')
        
        # Update existing templates with handler names
        try:
            await conn.execute(text('''
                UPDATE workflow_activity_templates 
                SET handler_name = CASE
                    WHEN activity_name = 'Generate Attributes' THEN 'GenerateAttributesHandler'
                    WHEN activity_name = 'Execute Scoping' THEN 'ExecuteScopingHandler'
                    WHEN activity_name = 'Generate Samples' THEN 'GenerateSamplesHandler'
                    WHEN activity_name = 'Send Data Request' THEN 'SendDataRequestHandler'
                    WHEN activity_name = 'Execute Tests' THEN 'ExecuteTestsHandler'
                    WHEN activity_type = 'MANUAL' THEN 'ManualActivityHandler'
                    ELSE 'AutomatedActivityHandler'
                END
                WHERE handler_name IS NULL
            '''))
            logger.info('✓ Updated handler names for existing templates')
        except Exception as e:
            logger.error(f'Error updating handler names: {e}')
        
        # Set execution modes for parallel phases
        try:
            await conn.execute(text('''
                UPDATE workflow_activity_templates
                SET execution_mode = 'parallel'
                WHERE phase_name IN ('Request for Information', 'Test Execution', 'Observation Management')
                AND activity_type = 'TASK'
            '''))
            logger.info('✓ Set execution modes for parallel phases')
        except Exception as e:
            logger.error(f'Error setting execution modes: {e}')
        
        # Set retry policies for critical activities
        try:
            await conn.execute(text('''
                UPDATE workflow_activity_templates
                SET retry_policy = '{"max_attempts": 3, "initial_interval": 2, "max_interval": 60, "backoff": 2}'::json
                WHERE activity_type IN ('TASK', 'AUTOMATED')
                AND retry_policy IS NULL
            '''))
            logger.info('✓ Set retry policies for critical activities')
        except Exception as e:
            logger.error(f'Error setting retry policies: {e}')
    
    await engine.dispose()
    logger.info('\n✅ Database changes applied successfully!')


if __name__ == '__main__':
    asyncio.run(apply_changes())