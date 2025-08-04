#!/usr/bin/env python3
"""
Rollback script for observation table migration
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/synapse_dt")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async def rollback():
    engine = create_async_engine(ASYNC_DATABASE_URL)
    try:
        async with engine.begin() as conn:
            # Check if backup exists
            result = await conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'observation_records_backup')")
            )
            if result.scalar():
                # Rename back
                await conn.execute(text('ALTER TABLE cycle_report_observation_mgmt_observation_records_backup RENAME TO observation_records'))
                print("✓ Restored observation_records table")
                
                # Note: This doesn't remove migrated data from observations table
                # That would need to be done manually if required
            else:
                print("❌ No backup table found")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    response = input("Rollback observation table migration? (yes/no): ")
    if response.lower() == "yes":
        asyncio.run(rollback())
