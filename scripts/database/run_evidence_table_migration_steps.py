#!/usr/bin/env python3
"""Run the evidence table migration step by step"""

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def run_migration():
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Rename the table
            print("Step 1: Renaming table...")
            await db.execute(text(
                "ALTER TABLE cycle_report_rfi_evidence RENAME TO cycle_report_test_cases_evidence"
            ))
            await db.commit()
            print("✅ Table renamed")
            
            # Step 2: Add submission tracking fields
            print("\nStep 2: Adding submission tracking fields...")
            await db.execute(text("""
                ALTER TABLE cycle_report_test_cases_evidence 
                ADD COLUMN IF NOT EXISTS submission_number INTEGER DEFAULT 1,
                ADD COLUMN IF NOT EXISTS is_revision BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS revision_requested_by INTEGER REFERENCES users(user_id),
                ADD COLUMN IF NOT EXISTS revision_requested_at TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS revision_reason TEXT,
                ADD COLUMN IF NOT EXISTS revision_deadline TIMESTAMP WITH TIME ZONE
            """))
            await db.commit()
            print("✅ Submission tracking fields added")
            
            # Step 3: Add document type field
            print("\nStep 3: Adding document_type field...")
            # Check if column exists first
            result = await db.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'cycle_report_test_cases_evidence' 
                AND column_name = 'document_type'
            """))
            if not result.scalar():
                await db.execute(text(
                    "ALTER TABLE cycle_report_test_cases_evidence ADD COLUMN document_type document_type_enum"
                ))
                await db.commit()
                print("✅ document_type field added")
            else:
                print("✅ document_type field already exists")
            
            # Step 4: Rename submitted_by to data_owner_id
            print("\nStep 4: Renaming submitted_by to data_owner_id...")
            # Check if column exists
            result = await db.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'cycle_report_test_cases_evidence' 
                AND column_name = 'submitted_by'
            """))
            if result.scalar():
                await db.execute(text(
                    "ALTER TABLE cycle_report_test_cases_evidence RENAME COLUMN submitted_by TO data_owner_id"
                ))
                await db.commit()
                print("✅ Column renamed")
            else:
                print("✅ Column already renamed or doesn't exist")
            
            # Step 5: Add unique constraint
            print("\nStep 5: Adding unique constraint...")
            # Check if constraint exists
            result = await db.execute(text("""
                SELECT constraint_name FROM information_schema.table_constraints 
                WHERE table_name = 'cycle_report_test_cases_evidence' 
                AND constraint_name = 'uq_test_case_evidence_submission_number'
            """))
            if not result.scalar():
                await db.execute(text("""
                    ALTER TABLE cycle_report_test_cases_evidence
                    ADD CONSTRAINT uq_test_case_evidence_submission_number 
                    UNIQUE (test_case_id, submission_number)
                """))
                await db.commit()
                print("✅ Unique constraint added")
            else:
                print("✅ Unique constraint already exists")
            
            # Step 6: Add index
            print("\nStep 6: Adding index...")
            result = await db.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'cycle_report_test_cases_evidence' 
                AND indexname = 'idx_unique_current_evidence'
            """))
            if not result.scalar():
                await db.execute(text("""
                    CREATE UNIQUE INDEX idx_unique_current_evidence 
                    ON cycle_report_test_cases_evidence(test_case_id, is_current)
                    WHERE is_current = true
                """))
                await db.commit()
                print("✅ Index added")
            else:
                print("✅ Index already exists")
            
            # Step 7: Rename constraints
            print("\nStep 7: Renaming constraints...")
            # Check and rename primary key
            result = await db.execute(text("""
                SELECT constraint_name FROM information_schema.table_constraints 
                WHERE table_name = 'cycle_report_test_cases_evidence' 
                AND constraint_name = 'cycle_report_rfi_evidence_pkey'
            """))
            if result.scalar():
                await db.execute(text("""
                    ALTER TABLE cycle_report_test_cases_evidence 
                    RENAME CONSTRAINT cycle_report_rfi_evidence_pkey TO cycle_report_test_cases_evidence_pkey
                """))
                await db.commit()
                print("✅ Primary key constraint renamed")
            else:
                print("✅ Primary key constraint already renamed")
            
            # Check and rename foreign key
            result = await db.execute(text("""
                SELECT constraint_name FROM information_schema.table_constraints 
                WHERE table_name = 'cycle_report_test_cases_evidence' 
                AND constraint_name = 'cycle_report_rfi_evidence_parent_evidence_id_fkey'
            """))
            if result.scalar():
                await db.execute(text("""
                    ALTER TABLE cycle_report_test_cases_evidence
                    RENAME CONSTRAINT cycle_report_rfi_evidence_parent_evidence_id_fkey 
                    TO cycle_report_test_cases_evidence_parent_evidence_id_fkey
                """))
                await db.commit()
                print("✅ Foreign key constraint renamed")
            else:
                print("✅ Foreign key constraint already renamed")
            
            # Step 8: Rename sequence
            print("\nStep 8: Renaming sequence...")
            result = await db.execute(text("""
                SELECT sequence_name FROM information_schema.sequences 
                WHERE sequence_name = 'cycle_report_rfi_evidence_id_seq'
            """))
            if result.scalar():
                await db.execute(text("""
                    ALTER SEQUENCE cycle_report_rfi_evidence_id_seq 
                    RENAME TO cycle_report_test_cases_evidence_id_seq
                """))
                await db.commit()
                print("✅ Sequence renamed")
            else:
                print("✅ Sequence already renamed")
            
            # Step 9: Add table comment
            print("\nStep 9: Adding table comment...")
            await db.execute(text("""
                COMMENT ON TABLE cycle_report_test_cases_evidence IS 
                'Unified evidence table for test cases - stores both document and data source evidence'
            """))
            await db.commit()
            print("✅ Table comment added")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    print("Running evidence table migration step by step...")
    asyncio.run(run_migration())