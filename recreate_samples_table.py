#!/usr/bin/env python3
"""Recreate samples table with correct structure"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def recreate_table():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=True
    )
    
    async with AsyncSession(engine) as db:
        print("=== Recreating cycle_report_sample_selection_samples table ===")
        
        # Drop the old table
        await db.execute(text("""
            DROP TABLE IF EXISTS cycle_report_sample_selection_samples CASCADE
        """))
        
        # Create enum types if they don't exist
        await db.execute(text("""
            DO $$ BEGIN
                CREATE TYPE sample_category_enum AS ENUM (
                    'clean', 'anomaly', 'boundary'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        await db.execute(text("""
            DO $$ BEGIN
                CREATE TYPE sample_source_enum AS ENUM (
                    'tester', 'llm', 'manual', 'carried_forward'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        await db.execute(text("""
            DO $$ BEGIN
                CREATE TYPE sample_decision_enum AS ENUM (
                    'approved', 'rejected', 'pending'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        # Create the table with correct structure matching the model
        await db.execute(text("""
            CREATE TABLE cycle_report_sample_selection_samples (
                sample_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                version_id UUID NOT NULL REFERENCES cycle_report_sample_selection_versions(version_id) ON DELETE CASCADE,
                phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
                lob_id INTEGER NOT NULL REFERENCES lobs(lob_id),
                sample_identifier VARCHAR(255) NOT NULL,
                sample_data JSONB NOT NULL,
                sample_category sample_category_enum NOT NULL,
                sample_source sample_source_enum NOT NULL,
                tester_decision sample_decision_enum NOT NULL DEFAULT 'pending',
                tester_decision_notes TEXT,
                tester_decision_at TIMESTAMP WITH TIME ZONE,
                tester_decision_by_id INTEGER REFERENCES users(user_id),
                report_owner_decision sample_decision_enum NOT NULL DEFAULT 'pending',
                report_owner_decision_notes TEXT,
                report_owner_decision_at TIMESTAMP WITH TIME ZONE,
                report_owner_decision_by_id INTEGER REFERENCES users(user_id),
                risk_score FLOAT,
                confidence_score FLOAT,
                generation_metadata JSONB,
                validation_results JSONB,
                carried_from_version_id UUID REFERENCES cycle_report_sample_selection_versions(version_id),
                carried_from_sample_id UUID REFERENCES cycle_report_sample_selection_samples(sample_id),
                carry_forward_reason TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                created_by_id INTEGER REFERENCES users(user_id),
                updated_by_id INTEGER REFERENCES users(user_id)
            )
        """))
        
        # Create indexes
        await db.execute(text("""
            CREATE INDEX idx_sample_selection_samples_version_id 
            ON cycle_report_sample_selection_samples(version_id)
        """))
        
        await db.execute(text("""
            CREATE INDEX idx_sample_selection_samples_phase_id 
            ON cycle_report_sample_selection_samples(phase_id)
        """))
        
        await db.execute(text("""
            CREATE INDEX idx_sample_selection_samples_lob_id 
            ON cycle_report_sample_selection_samples(lob_id)
        """))
        
        await db.execute(text("""
            CREATE INDEX idx_sample_selection_samples_identifier 
            ON cycle_report_sample_selection_samples(sample_identifier)
        """))
        
        await db.execute(text("""
            CREATE INDEX idx_sample_selection_samples_category 
            ON cycle_report_sample_selection_samples(sample_category)
        """))
        
        await db.execute(text("""
            CREATE INDEX idx_sample_selection_samples_tester_decision 
            ON cycle_report_sample_selection_samples(tester_decision)
        """))
        
        await db.execute(text("""
            CREATE INDEX idx_sample_selection_samples_report_owner_decision 
            ON cycle_report_sample_selection_samples(report_owner_decision)
        """))
        
        # Create trigger
        await db.execute(text("""
            CREATE TRIGGER update_cycle_report_sample_selection_samples_updated_at 
            BEFORE UPDATE ON cycle_report_sample_selection_samples 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """))
        
        await db.commit()
        print("\n✅ Table recreated successfully!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(recreate_table())