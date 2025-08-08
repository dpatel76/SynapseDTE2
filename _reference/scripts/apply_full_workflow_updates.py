"""Apply full workflow database updates"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def apply_full_updates():
    """Apply all database schema changes for dynamic workflows"""
    
    # Create async engine with proper driver
    database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(database_url)
    
    success_count = 0
    total_operations = 0
    
    async with engine.connect() as conn:
        # Start transaction
        trans = await conn.begin()
        
        try:
            # 1. Add columns to workflow_activity_templates
            logger.info("Adding columns to workflow_activity_templates...")
            columns_to_add = [
                ("handler_name", "VARCHAR(255)"),
                ("timeout_seconds", "INTEGER DEFAULT 300"),
                ("retry_policy", "JSON"),
                ("conditional_expression", "TEXT"),
                ("execution_mode", "VARCHAR(50) DEFAULT 'sequential'")
            ]
            
            for col_name, col_type in columns_to_add:
                total_operations += 1
                try:
                    await conn.execute(text(f"""
                        ALTER TABLE workflow_activity_templates 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """))
                    logger.info(f"  ✓ Added column {col_name}")
                    success_count += 1
                except Exception as e:
                    logger.warning(f"  ⚠ Column {col_name} may already exist: {str(e)}")
            
            # 2. Add columns to workflow_activities
            logger.info("\nAdding columns to workflow_activities...")
            activity_columns = [
                ("instance_id", "VARCHAR(255)"),
                ("parent_activity_id", "INTEGER"),
                ("execution_mode", "VARCHAR(50)"),
                ("retry_count", "INTEGER DEFAULT 0"),
                ("last_error", "TEXT")
            ]
            
            for col_name, col_type in activity_columns:
                total_operations += 1
                try:
                    await conn.execute(text(f"""
                        ALTER TABLE workflow_activities 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """))
                    logger.info(f"  ✓ Added column {col_name}")
                    success_count += 1
                except Exception as e:
                    logger.warning(f"  ⚠ Column {col_name} may already exist: {str(e)}")
            
            # 3. Add foreign key constraint
            logger.info("\nAdding foreign key constraints...")
            total_operations += 1
            try:
                # Check if constraint exists
                result = await conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.table_constraints 
                    WHERE constraint_name = 'fk_workflow_activities_parent'
                    AND table_name = 'workflow_activities'
                """))
                if result.scalar() == 0:
                    await conn.execute(text("""
                        ALTER TABLE workflow_activities 
                        ADD CONSTRAINT fk_workflow_activities_parent 
                        FOREIGN KEY (parent_activity_id) 
                        REFERENCES workflow_activities(activity_id) 
                        ON DELETE SET NULL
                    """))
                    logger.info("  ✓ Added foreign key constraint")
                    success_count += 1
                else:
                    logger.info("  ✓ Foreign key constraint already exists")
                    success_count += 1
            except Exception as e:
                logger.error(f"  ✗ Error adding foreign key: {e}")
            
            # 4. Create indexes
            logger.info("\nCreating indexes...")
            indexes = [
                ("ix_workflow_activities_instance_id", "workflow_activities(cycle_id, report_id, instance_id)"),
                ("ix_workflow_activities_parent", "workflow_activities(parent_activity_id)"),
                ("ix_workflow_activity_templates_handler", "workflow_activity_templates(handler_name)"),
                ("ix_workflow_activity_templates_phase_order", "workflow_activity_templates(phase_name, activity_order)")
            ]
            
            for idx_name, idx_def in indexes:
                total_operations += 1
                try:
                    await conn.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}
                    """))
                    logger.info(f"  ✓ Created index {idx_name}")
                    success_count += 1
                except Exception as e:
                    logger.warning(f"  ⚠ Index {idx_name} may already exist: {str(e)}")
            
            # 5. Update handler names for existing templates
            logger.info("\nUpdating handler names...")
            total_operations += 1
            try:
                await conn.execute(text("""
                    UPDATE workflow_activity_templates 
                    SET handler_name = CASE
                        WHEN activity_name = 'Generate Attributes' THEN 'GenerateAttributesHandler'
                        WHEN activity_name = 'Execute Scoping' THEN 'ExecuteScopingHandler'
                        WHEN activity_name = 'Generate Samples' THEN 'GenerateSamplesHandler'
                        WHEN activity_name = 'Send Data Request' THEN 'SendDataRequestHandler'
                        WHEN activity_name = 'Execute Tests' THEN 'ExecuteTestsHandler'
                        WHEN activity_name = 'Create Observations' THEN 'CreateObservationsHandler'
                        WHEN activity_name = 'Generate Report Sections' THEN 'GenerateReportSectionsHandler'
                        WHEN activity_name = 'Generate Final Report' THEN 'GenerateFinalReportHandler'
                        WHEN activity_name = 'Execute Data Profiling' THEN 'DataProfilingHandler'
                        WHEN activity_name = 'Validate Data Upload' THEN 'ValidateDataUploadHandler'
                        WHEN activity_name = 'Generate Test Cases' THEN 'GenerateTestCasesHandler'
                        WHEN is_manual = true THEN 'ManualActivityHandler'
                        WHEN activity_type IN ('START', 'COMPLETE') THEN 'AutomatedActivityHandler'
                        ELSE 'AutomatedActivityHandler'
                    END
                    WHERE handler_name IS NULL
                """))
                rows = conn.rowcount if hasattr(conn, 'rowcount') else 'unknown'
                logger.info(f"  ✓ Updated handler names")
                success_count += 1
            except Exception as e:
                logger.error(f"  ✗ Error updating handler names: {e}")
            
            # 6. Set execution modes for parallel phases
            logger.info("\nSetting execution modes...")
            total_operations += 1
            try:
                await conn.execute(text("""
                    UPDATE workflow_activity_templates
                    SET execution_mode = 'parallel'
                    WHERE phase_name IN ('Request for Information', 'Test Execution', 'Observation Management')
                    AND activity_type = 'TASK'
                    AND execution_mode IS NULL
                """))
                logger.info("  ✓ Set execution modes for parallel phases")
                success_count += 1
            except Exception as e:
                logger.error(f"  ✗ Error setting execution modes: {e}")
            
            # 7. Set retry policies
            logger.info("\nSetting retry policies...")
            total_operations += 1
            try:
                await conn.execute(text("""
                    UPDATE workflow_activity_templates
                    SET retry_policy = '{"max_attempts": 3, "initial_interval": 2, "max_interval": 60, "backoff": 2}'::json
                    WHERE activity_type IN ('TASK', 'START', 'COMPLETE')
                    AND is_manual = false
                    AND retry_policy IS NULL
                """))
                logger.info("  ✓ Set retry policies for automated activities")
                success_count += 1
            except Exception as e:
                logger.error(f"  ✗ Error setting retry policies: {e}")
            
            # 8. Set timeout values
            logger.info("\nSetting timeout values...")
            total_operations += 1
            try:
                await conn.execute(text("""
                    UPDATE workflow_activity_templates
                    SET timeout_seconds = CASE
                        WHEN is_manual = true AND activity_type = 'APPROVAL' THEN 172800  -- 48 hours
                        WHEN is_manual = true AND activity_type = 'REVIEW' THEN 86400    -- 24 hours
                        WHEN is_manual = true AND activity_type = 'TASK' THEN 86400      -- 24 hours
                        WHEN activity_name LIKE '%Generate%' THEN 900                     -- 15 minutes
                        WHEN activity_name LIKE '%Execute%' THEN 1800                     -- 30 minutes
                        WHEN activity_type IN ('START', 'COMPLETE') THEN 60              -- 1 minute
                        ELSE 300                                                          -- 5 minutes default
                    END
                    WHERE timeout_seconds IS NULL OR timeout_seconds = 300
                """))
                logger.info("  ✓ Set appropriate timeout values")
                success_count += 1
            except Exception as e:
                logger.error(f"  ✗ Error setting timeout values: {e}")
            
            # 9. Add conditional expressions for specific activities
            logger.info("\nSetting conditional expressions...")
            total_operations += 1
            try:
                await conn.execute(text("""
                    UPDATE workflow_activity_templates
                    SET conditional_expression = '{"all_observations_complete": true}'
                    WHERE phase_name = 'Finalize Test Report'
                    AND activity_name = 'Start Report Finalization'
                """))
                logger.info("  ✓ Set conditional expression for report finalization")
                success_count += 1
            except Exception as e:
                logger.error(f"  ✗ Error setting conditional expressions: {e}")
            
            # 10. Create activity dependency table if not exists
            logger.info("\nCreating activity dependency table...")
            total_operations += 1
            try:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS workflow_activity_dependencies (
                        dependency_id SERIAL PRIMARY KEY,
                        phase_name VARCHAR(100) NOT NULL,
                        activity_name VARCHAR(255) NOT NULL,
                        depends_on_activity VARCHAR(255) NOT NULL,
                        dependency_type VARCHAR(50) NOT NULL DEFAULT 'completion',
                        is_active BOOLEAN NOT NULL DEFAULT true,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(phase_name, activity_name, depends_on_activity)
                    )
                """))
                logger.info("  ✓ Created activity dependency table")
                success_count += 1
            except Exception as e:
                logger.error(f"  ✗ Error creating dependency table: {e}")
            
            # 11. Insert some basic dependencies
            logger.info("\nInserting activity dependencies...")
            total_operations += 1
            try:
                # Clear existing dependencies
                await conn.execute(text("DELETE FROM workflow_activity_dependencies"))
                
                # Insert dependencies
                dependencies = [
                    # Planning phase dependencies
                    ('Planning', 'Review Generated Attributes', 'Generate Attributes', 'completion'),
                    ('Planning', 'Submit for Approval', 'Review Generated Attributes', 'completion'),
                    ('Planning', 'Report Owner Approval', 'Submit for Approval', 'completion'),
                    ('Planning', 'Complete Planning Phase', 'Report Owner Approval', 'approval'),
                    
                    # Scoping phase dependencies
                    ('Scoping', 'Review Scoping Results', 'Execute Scoping', 'completion'),
                    ('Scoping', 'Scoping Approval', 'Review Scoping Results', 'completion'),
                    ('Scoping', 'Complete Scoping Phase', 'Scoping Approval', 'approval'),
                    
                    # Sample Selection dependencies
                    ('Sample Selection', 'Review and Tag Samples', 'Generate Samples', 'completion'),
                    ('Sample Selection', 'Complete Sample Selection', 'Review and Tag Samples', 'completion'),
                    
                    # Request for Information dependencies
                    ('Request for Information', 'Upload Data', 'Send Data Request', 'completion'),
                    ('Request for Information', 'Validate Data Upload', 'Upload Data', 'completion'),
                    ('Request for Information', 'Generate Test Cases', 'Validate Data Upload', 'completion'),
                    
                    # Test Execution dependencies
                    ('Test Execution', 'Review Test Results', 'Execute Tests', 'completion'),
                    ('Test Execution', 'Document Test Evidence', 'Execute Tests', 'completion'),
                    
                    # Observation Management dependencies
                    ('Observation Management', 'Review Observations', 'Create Observations', 'completion'),
                    ('Observation Management', 'Data Owner Response', 'Review Observations', 'completion'),
                    ('Observation Management', 'Finalize Observations', 'Data Owner Response', 'completion'),
                ]
                
                for dep in dependencies:
                    await conn.execute(text("""
                        INSERT INTO workflow_activity_dependencies 
                        (phase_name, activity_name, depends_on_activity, dependency_type)
                        VALUES (:p1, :p2, :p3, :p4)
                        ON CONFLICT (phase_name, activity_name, depends_on_activity) DO NOTHING
                    """), {"p1": dep[0], "p2": dep[1], "p3": dep[2], "p4": dep[3]})
                
                logger.info(f"  ✓ Inserted {len(dependencies)} activity dependencies")
                success_count += 1
            except Exception as e:
                logger.error(f"  ✗ Error inserting dependencies: {e}")
            
            # Commit transaction
            await trans.commit()
            logger.info(f"\n✅ Transaction committed successfully!")
            
        except Exception as e:
            await trans.rollback()
            logger.error(f"\n❌ Transaction rolled back due to error: {e}")
            raise
    
    await engine.dispose()
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"Update Summary:")
    logger.info(f"  Total operations: {total_operations}")
    logger.info(f"  Successful: {success_count}")
    logger.info(f"  Failed: {total_operations - success_count}")
    logger.info(f"{'='*50}")
    
    # Verify final state
    await verify_schema()


async def verify_schema():
    """Verify the final schema state"""
    database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(database_url)
    
    logger.info("\nVerifying final schema...")
    
    async with engine.connect() as conn:
        # Check workflow_activity_templates columns
        result = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'workflow_activity_templates'
            AND column_name IN ('handler_name', 'timeout_seconds', 'retry_policy', 'execution_mode')
            ORDER BY column_name
        """))
        columns = result.fetchall()
        logger.info(f"\nworkflow_activity_templates new columns: {len(columns)}")
        for col in columns:
            logger.info(f"  ✓ {col[0]}: {col[1]}")
        
        # Check workflow_activities columns
        result = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'workflow_activities'
            AND column_name IN ('instance_id', 'parent_activity_id', 'retry_count')
            ORDER BY column_name
        """))
        columns = result.fetchall()
        logger.info(f"\nworkflow_activities new columns: {len(columns)}")
        for col in columns:
            logger.info(f"  ✓ {col[0]}: {col[1]}")
        
        # Check templates with handlers
        result = await conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(handler_name) as with_handler,
                   COUNT(retry_policy) as with_retry,
                   COUNT(CASE WHEN execution_mode = 'parallel' THEN 1 END) as parallel
            FROM workflow_activity_templates
        """))
        stats = result.fetchone()
        logger.info(f"\nTemplate statistics:")
        logger.info(f"  Total templates: {stats[0]}")
        logger.info(f"  With handler: {stats[1]}")
        logger.info(f"  With retry policy: {stats[2]}")
        logger.info(f"  Parallel activities: {stats[3]}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(apply_full_updates())