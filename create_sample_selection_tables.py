#!/usr/bin/env python3
"""Create sample selection tables directly in database"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def create_tables():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=True
    )
    
    async with AsyncSession(engine) as db:
        print("=== Creating Sample Selection Tables ===")
        
        # Create enum types
        print("\n1. Creating enum types...")
        
        # Check if enum types exist first
        result = await db.execute(text("""
            SELECT typname FROM pg_type WHERE typname IN (
                'sample_selection_version_status_enum',
                'sample_category_enum',
                'sample_decision_enum',
                'sample_source_enum'
            )
        """))
        existing_types = {row.typname for row in result}
        
        if 'sample_selection_version_status_enum' not in existing_types:
            await db.execute(text("""
                CREATE TYPE sample_selection_version_status_enum AS ENUM (
                    'draft', 'pending_approval', 'approved', 'rejected', 'superseded'
                )
            """))
            print("   Created sample_selection_version_status_enum")
        else:
            print("   sample_selection_version_status_enum already exists")
            
        if 'sample_category_enum' not in existing_types:
            await db.execute(text("""
                CREATE TYPE sample_category_enum AS ENUM (
                    'clean', 'anomaly', 'boundary'
                )
            """))
            print("   Created sample_category_enum")
        else:
            print("   sample_category_enum already exists")
            
        if 'sample_decision_enum' not in existing_types:
            await db.execute(text("""
                CREATE TYPE sample_decision_enum AS ENUM (
                    'approved', 'rejected', 'pending'
                )
            """))
            print("   Created sample_decision_enum")
        else:
            print("   sample_decision_enum already exists")
            
        if 'sample_source_enum' not in existing_types:
            await db.execute(text("""
                CREATE TYPE sample_source_enum AS ENUM (
                    'tester', 'llm', 'manual', 'carried_forward'
                )
            """))
            print("   Created sample_source_enum")
        else:
            print("   sample_source_enum already exists")
        
        # Create versions table
        print("\n2. Creating cycle_report_sample_selection_versions table...")
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS cycle_report_sample_selection_versions (
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
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                created_by_id INTEGER REFERENCES users(user_id),
                updated_by_id INTEGER REFERENCES users(user_id)
            )
        """))
        
        # Create samples table
        print("\n3. Creating cycle_report_sample_selection_samples table...")
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS cycle_report_sample_selection_samples (
                sample_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                version_id UUID NOT NULL REFERENCES cycle_report_sample_selection_versions(version_id),
                phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
                workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id),
                line_of_business VARCHAR(100) NOT NULL,
                primary_attribute_value VARCHAR(255) NOT NULL,
                sample_category sample_category_enum NOT NULL,
                sample_source sample_source_enum NOT NULL,
                confidence_score FLOAT,
                included_in_version BOOLEAN NOT NULL DEFAULT true,
                exclusion_reason TEXT,
                data_row_snapshot JSONB NOT NULL,
                attribute_values JSONB NOT NULL,
                validation_rules JSONB,
                tester_decision sample_decision_enum,
                tester_decision_date TIMESTAMP WITH TIME ZONE,
                tester_decision_by_id INTEGER REFERENCES users(user_id),
                tester_notes TEXT,
                report_owner_decision sample_decision_enum,
                report_owner_decision_date TIMESTAMP WITH TIME ZONE,
                report_owner_decision_by_id INTEGER REFERENCES users(user_id),
                report_owner_notes TEXT,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                created_by_id INTEGER REFERENCES users(user_id),
                updated_by_id INTEGER REFERENCES users(user_id)
            )
        """))
        
        # Create indexes
        print("\n4. Creating indexes...")
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sample_selection_versions_phase_id 
            ON cycle_report_sample_selection_versions(phase_id)
        """))
        
        await db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_sample_selection_versions_phase_version 
            ON cycle_report_sample_selection_versions(phase_id, version_number)
        """))
        
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sample_selection_versions_status 
            ON cycle_report_sample_selection_versions(version_status)
        """))
        
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sample_selection_samples_version_id 
            ON cycle_report_sample_selection_samples(version_id)
        """))
        
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sample_selection_samples_phase_id 
            ON cycle_report_sample_selection_samples(phase_id)
        """))
        
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sample_selection_samples_lob 
            ON cycle_report_sample_selection_samples(line_of_business)
        """))
        
        # Create triggers
        print("\n5. Creating triggers...")
        await db.execute(text("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = now();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """))
        
        await db.execute(text("""
            DROP TRIGGER IF EXISTS update_cycle_report_sample_selection_versions_updated_at 
            ON cycle_report_sample_selection_versions
        """))
        
        await db.execute(text("""
            CREATE TRIGGER update_cycle_report_sample_selection_versions_updated_at 
            BEFORE UPDATE ON cycle_report_sample_selection_versions 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """))
        
        await db.execute(text("""
            DROP TRIGGER IF EXISTS update_cycle_report_sample_selection_samples_updated_at 
            ON cycle_report_sample_selection_samples
        """))
        
        await db.execute(text("""
            CREATE TRIGGER update_cycle_report_sample_selection_samples_updated_at 
            BEFORE UPDATE ON cycle_report_sample_selection_samples 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """))
        
        await db.commit()
        print("\n✅ Tables created successfully!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())