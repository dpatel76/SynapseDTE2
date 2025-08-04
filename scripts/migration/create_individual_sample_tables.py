#!/usr/bin/env python3
"""
Create individual sample tables manually
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    """Create individual sample tables"""
    
    async with engine.begin() as conn:
        try:
            # Create enums first
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE testerdecision AS ENUM ('include', 'exclude', 'review_required');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE reportownerdecision AS ENUM ('approved', 'rejected', 'revision_required');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE submissionstatus AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'revision_required');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            logger.info("✅ Created enums")
            
            # Create sample_submissions table first
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sample_submissions (
                    id SERIAL PRIMARY KEY,
                    submission_id VARCHAR UNIQUE NOT NULL,
                    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
                    report_id INTEGER NOT NULL REFERENCES reports(report_id),
                    version_number INTEGER NOT NULL,
                    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    submitted_by_user_id INTEGER REFERENCES users(user_id),
                    submission_notes TEXT,
                    status submissionstatus DEFAULT 'pending_approval',
                    reviewed_at TIMESTAMP WITH TIME ZONE,
                    reviewed_by_user_id INTEGER REFERENCES users(user_id),
                    review_decision reportownerdecision,
                    review_feedback TEXT,
                    is_official_version BOOLEAN DEFAULT FALSE,
                    total_samples INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE
                );
            """))
            
            logger.info("✅ Created sample_submissions table")
            
            # Create individual_samples table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS individual_samples (
                    id SERIAL PRIMARY KEY,
                    sample_id VARCHAR UNIQUE NOT NULL,
                    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
                    report_id INTEGER NOT NULL REFERENCES reports(report_id),
                    primary_key_value VARCHAR NOT NULL,
                    sample_data JSONB NOT NULL,
                    generation_method VARCHAR NOT NULL,
                    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    generated_by_user_id INTEGER REFERENCES users(user_id),
                    tester_decision testerdecision,
                    tester_decision_date TIMESTAMP WITH TIME ZONE,
                    tester_decision_by_user_id INTEGER REFERENCES users(user_id),
                    tester_notes TEXT,
                    report_owner_decision reportownerdecision,
                    report_owner_feedback TEXT,
                    is_submitted BOOLEAN DEFAULT FALSE,
                    submission_id INTEGER REFERENCES sample_submissions(id),
                    version_number INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE
                );
            """))
            
            logger.info("✅ Created individual_samples table")
            
            # Create sample_submission_items table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sample_submission_items (
                    id SERIAL PRIMARY KEY,
                    submission_id INTEGER NOT NULL REFERENCES sample_submissions(id),
                    sample_id INTEGER NOT NULL REFERENCES individual_samples(id),
                    tester_decision testerdecision NOT NULL,
                    primary_key_value VARCHAR NOT NULL,
                    sample_data_snapshot JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            logger.info("✅ Created sample_submission_items table")
            
            # Create sample_feedback table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sample_feedback (
                    id SERIAL PRIMARY KEY,
                    sample_id INTEGER NOT NULL REFERENCES individual_samples(id),
                    submission_id INTEGER NOT NULL REFERENCES sample_submissions(id),
                    feedback_type VARCHAR NOT NULL,
                    feedback_text TEXT NOT NULL,
                    severity VARCHAR DEFAULT 'medium',
                    is_blocking BOOLEAN DEFAULT FALSE,
                    is_resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP WITH TIME ZONE,
                    resolved_by_user_id INTEGER REFERENCES users(user_id),
                    resolution_notes TEXT,
                    created_by_user_id INTEGER NOT NULL REFERENCES users(user_id),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE
                );
            """))
            
            logger.info("✅ Created sample_feedback table")
            
            # Create sample_audit_logs table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sample_audit_logs (
                    id SERIAL PRIMARY KEY,
                    sample_id INTEGER REFERENCES individual_samples(id),
                    submission_id INTEGER REFERENCES sample_submissions(id),
                    action VARCHAR NOT NULL,
                    action_details JSONB,
                    user_id INTEGER NOT NULL REFERENCES users(user_id),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            logger.info("✅ Created sample_audit_logs table")
            
            # Create indexes - execute one at a time
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_individual_samples_cycle_report 
                ON individual_samples(cycle_id, report_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_sample_submissions_cycle_report 
                ON sample_submissions(cycle_id, report_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_sample_feedback_sample_submission 
                ON sample_feedback(sample_id, submission_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_sample_audit_logs_sample 
                ON sample_audit_logs(sample_id)
            """))
            
            logger.info("✅ Created indexes")
            
            # Commit the transaction
            await conn.commit()
            
            logger.info("✅ All tables created successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise

if __name__ == "__main__":
    asyncio.run(create_tables())