#!/usr/bin/env python3
"""
Migration script for observation_records to observations table
Includes both table rename and data migration
"""

import asyncio
import os
from datetime import datetime
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
import json

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/synapse_dt")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

def create_migration_log():
    """Create a log file for the migration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"backup_logs/observation_migration_{timestamp}.json"
    return log_file

async def check_tables_exist(engine):
    """Check if both tables exist"""
    async with engine.begin() as conn:
        # Check observation_records
        result = await conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'observation_records')")
        )
        obs_records_exists = result.scalar()
        
        # Check observations
        result = await conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'observations')")
        )
        obs_exists = result.scalar()
        
        # Check if backup already exists
        result = await conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'observation_records_backup')")
        )
        backup_exists = result.scalar()
        
        return obs_records_exists, obs_exists, backup_exists

async def count_records(engine, table_name):
    """Count records in a table"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    except Exception:
        return 0

async def migrate_data(engine, dry_run=True):
    """Migrate data FROM cycle_report_observation_mgmt_observation_records to observations"""
    migration_log = {
        "timestamp": datetime.now().isoformat(),
        "dry_run": dry_run,
        "steps": []
    }
    
    try:
        # Check tables
        obs_records_exists, obs_exists, backup_exists = await check_tables_exist(engine)
        
        migration_log["steps"].append({
            "step": "check_tables",
            "observation_records_exists": obs_records_exists,
            "observations_exists": obs_exists,
            "backup_exists": backup_exists
        })
        
        if not obs_records_exists:
            print("❌ observation_records table does not exist")
            migration_log["error"] = "observation_records table not found"
            return migration_log
            
        if backup_exists:
            print("⚠️  observation_records_backup already exists")
            migration_log["warning"] = "backup already exists"
        
        # Count records
        obs_records_count = await count_records(engine, "cycle_report_observation_mgmt_observation_records")
        obs_count = await count_records(engine, "observations")
        
        print(f"\n📊 Table Status:")
        print(f"  observation_records: {obs_records_count} records")
        print(f"  observations: {obs_count} records")
        
        migration_log["steps"].append({
            "step": "count_records",
            "observation_records_count": obs_records_count,
            "observations_count": obs_count
        })
        
        if obs_records_count == 0:
            print("  ℹ️  No data to migrate")
        
        if dry_run:
            print("\n🔍 DRY RUN - No changes will be made")
            print("\nPlanned actions:")
            if obs_records_count > 0 and obs_exists:
                print("  1. Migrate data FROM cycle_report_observation_mgmt_observation_records to observations")
            print("  2. Rename observation_records → observation_records_backup")
        else:
            # Perform actual migration
            async with engine.begin() as conn:
                # Step 1: Migrate data if needed
                if obs_records_count > 0 and obs_exists:
                    print("\n📤 Migrating data...")
                    # This is a simplified migration - adjust based on actual schema differences
                    migration_sql = """
                    INSERT INTO observations (
                        observation_id,
                        cycle_id,
                        report_id,
                        test_execution_id,
                        observation_text,
                        severity,
                        status,
                        created_at,
                        created_by,
                        updated_at,
                        updated_by
                    )
                    SELECT 
                        observation_id,
                        cycle_id,
                        report_id,
                        test_execution_id,
                        observation_text,
                        severity,
                        status,
                        created_at,
                        created_by,
                        updated_at,
                        updated_by
                    FROM cycle_report_observation_mgmt_observation_records
                    WHERE NOT EXISTS (
                        SELECT 1 FROM observations o 
                        WHERE o.observation_id = observation_records.observation_id
                    )
                    """
                    result = await conn.execute(text(migration_sql))
                    rows_migrated = result.rowcount
                    print(f"  ✓ Migrated {rows_migrated} records")
                    
                    migration_log["steps"].append({
                        "step": "migrate_data",
                        "rows_migrated": rows_migrated
                    })
                
                # Step 2: Rename table
                print("\n📝 Renaming table...")
                await conn.execute(text('ALTER TABLE cycle_report_observation_mgmt_observation_records RENAME TO observation_records_backup'))
                print("  ✓ Renamed observation_records → observation_records_backup")
                
                migration_log["steps"].append({
                    "step": "rename_table",
                    "status": "success"
                })
                
                # Verify final state
                final_obs_count = await count_records(engine, "observations")
                backup_count = await count_records(engine, "observation_records_backup")
                
                print(f"\n✅ Migration Complete:")
                print(f"  observations: {final_obs_count} records")
                print(f"  observation_records_backup: {backup_count} records")
                
                migration_log["steps"].append({
                    "step": "verify",
                    "final_observations_count": final_obs_count,
                    "backup_count": backup_count
                })
        
        return migration_log
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        migration_log["error"] = str(e)
        return migration_log

async def create_rollback_script(log_file):
    """Create a rollback script"""
    rollback_content = f'''#!/usr/bin/env python3
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
'''
    
    rollback_file = log_file.replace('.json', '_rollback.py')
    with open(rollback_file, 'w') as f:
        f.write(rollback_content)
    os.chmod(rollback_file, 0o755)
    print(f"\n🔄 Rollback script created: {rollback_file}")

async def main():
    print("=" * 60)
    print("OBSERVATION TABLE MIGRATION")
    print("=" * 60)
    print()
    print("This script will:")
    print("1. Migrate data FROM cycle_report_observation_mgmt_observation_records to observations")
    print("2. Rename observation_records to observation_records_backup")
    print()
    
    # Check for dry run
    import sys
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    if dry_run:
        print("🔍 Running in DRY RUN mode")
    else:
        print("⚠️  Running in LIVE mode")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return
    
    # Create engine
    engine = create_async_engine(ASYNC_DATABASE_URL)
    
    try:
        # Run migration
        log_file = create_migration_log()
        migration_log = await migrate_data(engine, dry_run)
        
        # Save log
        with open(log_file, 'w') as f:
            json.dump(migration_log, f, indent=2)
        print(f"\n📄 Log saved: {log_file}")
        
        # Create rollback script
        if not dry_run:
            await create_rollback_script(log_file)
            
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())