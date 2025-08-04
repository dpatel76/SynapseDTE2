#!/usr/bin/env python3
"""Create sample selection versions table only"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def create_table():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=True
    )
    
    async with AsyncSession(engine) as db:
        print("=== Creating cycle_report_sample_selection_versions table ===")
        
        # Drop the table if it exists (to start fresh)
        await db.execute(text("""
            DROP TABLE IF EXISTS cycle_report_sample_selection_versions CASCADE
        """))
        
        # Create the enum type if it doesn't exist
        await db.execute(text("""
            DO $$ BEGIN
                CREATE TYPE sample_selection_version_status_enum AS ENUM (
                    'draft', 'pending_approval', 'approved', 'rejected', 'superseded'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        # Create the versions table
        await db.execute(text("""
            CREATE TABLE cycle_report_sample_selection_versions (
                version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
                workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id),
                version_number INTEGER NOT NULL,
                version_status sample_selection_version_status_enum NOT NULL,
                parent_version_id UUID REFERENCES cycle_report_sample_selection_versions(version_id),
                workflow_execution_id VARCHAR(255) NOT NULL,
                workflow_run_id VARCHAR(255) NOT NULL,
                activity_name VARCHAR(100) NOT NULL,
                selection_criteria JSONB NOT NULL,
                target_sample_size INTEGER NOT NULL,
                actual_sample_size INTEGER NOT NULL DEFAULT 0,
                intelligent_sampling_config JSONB,
                distribution_metrics JSONB,
                data_source_config JSONB,
                submission_notes TEXT,
                submitted_by_id INTEGER REFERENCES users(user_id),
                submitted_at TIMESTAMP WITH TIME ZONE,
                approval_notes TEXT,
                approved_by_id INTEGER REFERENCES users(user_id),
                approved_at TIMESTAMP WITH TIME ZONE,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                created_by_id INTEGER REFERENCES users(user_id),
                updated_by_id INTEGER REFERENCES users(user_id)
            )
        """))
        
        # Create indexes
        await db.execute(text("""
            CREATE INDEX idx_sample_selection_versions_phase_id 
            ON cycle_report_sample_selection_versions(phase_id)
        """))
        
        await db.execute(text("""
            CREATE UNIQUE INDEX idx_sample_selection_versions_phase_version 
            ON cycle_report_sample_selection_versions(phase_id, version_number)
        """))
        
        await db.execute(text("""
            CREATE INDEX idx_sample_selection_versions_status 
            ON cycle_report_sample_selection_versions(version_status)
        """))
        
        # Create trigger
        await db.execute(text("""
            CREATE TRIGGER update_cycle_report_sample_selection_versions_updated_at 
            BEFORE UPDATE ON cycle_report_sample_selection_versions 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """))
        
        await db.commit()
        print("\n✅ Table created successfully!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_table())