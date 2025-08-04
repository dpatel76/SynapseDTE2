#!/usr/bin/env python3
"""Run the evidence table migration"""

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def run_migration():
    async with AsyncSessionLocal() as db:
        try:
            # Read and execute the SQL migration
            with open('scripts/database/rename_evidence_table.sql', 'r') as f:
                sql = f.read()
            
            # Execute the migration
            await db.execute(text(sql))
            await db.commit()
            
            print("✅ Migration completed successfully!")
            
            # Verify the new table exists
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'cycle_report_test_cases_evidence'
            """))
            if result.scalar():
                print("✅ Table 'cycle_report_test_cases_evidence' exists")
            else:
                print("❌ Table 'cycle_report_test_cases_evidence' not found")
                
            # Check if old table still exists
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'cycle_report_rfi_evidence'
            """))
            if result.scalar():
                print("❌ Old table 'cycle_report_rfi_evidence' still exists")
            else:
                print("✅ Old table 'cycle_report_rfi_evidence' has been renamed")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    print("Running evidence table migration...")
    asyncio.run(run_migration())