#!/usr/bin/env python3
"""Add document_type column to cycle_report_test_cases_document_submissions table"""

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def run_migration():
    async with AsyncSessionLocal() as db:
        try:
            # Check if enum type exists
            result = await db.execute(text(
                "SELECT 1 FROM pg_type WHERE typname = 'document_type_enum'"
            ))
            enum_exists = result.scalar() is not None
            
            if not enum_exists:
                print("Creating document_type_enum...")
                await db.execute(text("""
                    CREATE TYPE document_type_enum AS ENUM (
                        'Source Document',
                        'Supporting Evidence',
                        'Data Extract',
                        'Query Result',
                        'Other'
                    )
                """))
                await db.commit()
                print("✅ Created document_type_enum")
            else:
                print("✅ document_type_enum already exists")
            
            # Check if column exists
            result = await db.execute(text("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'cycle_report_test_cases_document_submissions' 
                AND column_name = 'document_type'
            """))
            column_exists = result.scalar() is not None
            
            if not column_exists:
                print("Adding document_type column...")
                # Add column with default value first
                await db.execute(text("""
                    ALTER TABLE cycle_report_test_cases_document_submissions 
                    ADD COLUMN document_type document_type_enum NOT NULL DEFAULT 'Source Document'
                """))
                await db.commit()
                
                # Remove the default
                await db.execute(text("""
                    ALTER TABLE cycle_report_test_cases_document_submissions 
                    ALTER COLUMN document_type DROP DEFAULT
                """))
                await db.commit()
                print("✅ Added document_type column")
            else:
                print("✅ document_type column already exists")
            
            # Verify the column was added
            result = await db.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'cycle_report_test_cases_document_submissions'
                AND column_name = 'document_type'
            """))
            column = result.fetchone()
            if column:
                print(f"✅ Verified: document_type column exists with type {column[1]}")
            else:
                print("❌ ERROR: document_type column not found after migration")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    print("Running migration to add document_type column...")
    asyncio.run(run_migration())
    print("Migration completed!")