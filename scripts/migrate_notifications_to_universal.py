#!/usr/bin/env python3
"""
Migrate historical notifications to universal assignments
"""

import asyncio
import os
from datetime import datetime
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import json

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/synapse_dt")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async def count_notifications(session: AsyncSession) -> dict:
    """Count notifications in both systems"""
    
    # Count CDO notifications
    result = await session.execute(
        text("SELECT COUNT(*) FROM cdo_notifications")
    )
    cdo_count = result.scalar()
    
    # Count data owner notifications
    result = await session.execute(
        text("SELECT COUNT(*) FROM data_owner_notifications")
    )
    data_owner_count = result.scalar()
    
    # Count universal assignments
    result = await session.execute(
        text("""
            SELECT COUNT(*) FROM universal_assignments 
            WHERE assignment_type IN ('LOB Assignment', 'Information Request')
        """)
    )
    universal_count = result.scalar()
    
    # Count migrated records
    result = await session.execute(
        text("""
            SELECT COUNT(*) FROM universal_assignments 
            WHERE assignment_metadata->>'migrated_from' IS NOT NULL
        """)
    )
    migrated_count = result.scalar()
    
    return {
        "cdo_notifications": cdo_count,
        "data_owner_notifications": data_owner_count,
        "universal_assignments": universal_count,
        "already_migrated": migrated_count
    }

async def migrate_cdo_notifications(session: AsyncSession, dry_run: bool = True) -> int:
    """Migrate CDO notifications to universal assignments"""
    
    if dry_run:
        # Just count what would be migrated
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM cdo_notifications cn
                WHERE NOT EXISTS (
                    SELECT 1 FROM universal_assignments ua
                    WHERE ua.assignment_metadata->>'migrated_from' = 'cdo_notifications'
                    AND (ua.assignment_metadata->>'original_id')::int = cn.notification_id
                )
            """)
        )
        return result.scalar()
    
    # Perform actual migration
    result = await session.execute(
        text("""
            INSERT INTO universal_assignments (
                assignment_type, cycle_id, report_id,
                from_user_id, to_user_id,
                from_role, to_role,
                title, description,
                priority, status,
                created_at, created_by,
                acknowledged_at, completed_at,
                assignment_metadata
            )
            SELECT 
                'LOB Assignment', cycle_id, report_id,
                created_by, cdo_user_id,
                'Data Executive', 'CDO',
                'LOB Assignment Review Required', notification_text,
                'High', 
                CASE status 
                    WHEN 'sent' THEN 'Assigned'
                    WHEN 'acknowledged' THEN 'Acknowledged'
                    WHEN 'in_progress' THEN 'In Progress'
                    WHEN 'complete' THEN 'Completed'
                    WHEN 'completed' THEN 'Completed'
                    ELSE 'Assigned'
                END,
                created_at, created_by,
                acknowledged_at, completed_at,
                jsonb_build_object(
                    'lob_id', lob_id,
                    'migrated_from', 'cdo_notifications',
                    'original_id', notification_id,
                    'migration_date', now()::text,
                    'original_status', status
                )
            FROM cdo_notifications cn
            WHERE NOT EXISTS (
                SELECT 1 FROM universal_assignments ua
                WHERE ua.assignment_metadata->>'migrated_from' = 'cdo_notifications'
                AND (ua.assignment_metadata->>'original_id')::int = cn.notification_id
            )
            RETURNING assignment_id
        """)
    )
    
    return len(result.all())

async def migrate_data_owner_notifications(session: AsyncSession, dry_run: bool = True) -> int:
    """Migrate data owner notifications to universal assignments"""
    
    if dry_run:
        # Just count what would be migrated
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM data_owner_notifications don
                WHERE NOT EXISTS (
                    SELECT 1 FROM universal_assignments ua
                    WHERE ua.assignment_metadata->>'migrated_from' = 'data_owner_notifications'
                    AND (ua.assignment_metadata->>'original_id')::int = don.notification_id
                )
            """)
        )
        return result.scalar()
    
    # Perform actual migration
    result = await session.execute(
        text("""
            INSERT INTO universal_assignments (
                assignment_type, cycle_id, report_id,
                from_user_id, to_user_id,
                from_role, to_role,
                title, description,
                priority, status,
                created_at, created_by,
                acknowledged_at, completed_at,
                assignment_metadata
            )
            SELECT 
                'Information Request', cycle_id, report_id,
                created_by, data_provider_id,
                'Test Manager', 'Data Provider',
                'Information Request', notification_text,
                'Medium',
                CASE status 
                    WHEN 'sent' THEN 'Assigned'
                    WHEN 'acknowledged' THEN 'Acknowledged'
                    WHEN 'in_progress' THEN 'In Progress'
                    WHEN 'complete' THEN 'Completed'
                    WHEN 'completed' THEN 'Completed'
                    ELSE 'Assigned'
                END,
                created_at, created_by,
                acknowledged_at, completed_at,
                jsonb_build_object(
                    'test_case_ids', test_case_ids,
                    'migrated_from', 'data_owner_notifications',
                    'original_id', notification_id,
                    'migration_date', now()::text,
                    'original_status', status
                )
            FROM data_owner_notifications don
            WHERE NOT EXISTS (
                SELECT 1 FROM universal_assignments ua
                WHERE ua.assignment_metadata->>'migrated_from' = 'data_owner_notifications'
                AND (ua.assignment_metadata->>'original_id')::int = don.notification_id
            )
            RETURNING assignment_id
        """)
    )
    
    return len(result.all())

async def create_rollback_procedures(session: AsyncSession):
    """Create stored procedures for rollback if needed"""
    
    await session.execute(text("""
        CREATE OR REPLACE FUNCTION rollback_notification_migration()
        RETURNS void AS $$
        BEGIN
            -- Delete migrated records
            DELETE FROM universal_assignments 
            WHERE assignment_metadata->>'migrated_from' IN ('cdo_notifications', 'data_owner_notifications');
            
            -- Log the rollback
            INSERT INTO audit_log (user_id, action, details, created_at)
            VALUES (0, 'NOTIFICATION_MIGRATION_ROLLBACK', 
                    jsonb_build_object('rolled_back_at', now()::text),
                    now());
        END;
        $$ LANGUAGE plpgsql;
    """))
    
    print("✓ Created rollback procedure")

async def main():
    """Main migration function"""
    print("=" * 60)
    print("NOTIFICATION TO UNIVERSAL ASSIGNMENT MIGRATION")
    print("=" * 60)
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
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Count before
            print("\n📊 Current Status:")
            counts_before = await count_notifications(session)
            for key, value in counts_before.items():
                print(f"  {key}: {value}")
            
            # Check what would be migrated
            cdo_to_migrate = await migrate_cdo_notifications(session, dry_run=True)
            data_owner_to_migrate = await migrate_data_owner_notifications(session, dry_run=True)
            
            print(f"\n📋 Migration Plan:")
            print(f"  CDO notifications to migrate: {cdo_to_migrate}")
            print(f"  Data owner notifications to migrate: {data_owner_to_migrate}")
            print(f"  Total: {cdo_to_migrate + data_owner_to_migrate}")
            
            if not dry_run and (cdo_to_migrate > 0 or data_owner_to_migrate > 0):
                print("\n🚀 Performing migration...")
                
                # Create rollback procedures first
                await create_rollback_procedures(session)
                
                # Migrate CDO notifications
                if cdo_to_migrate > 0:
                    migrated = await migrate_cdo_notifications(session, dry_run=False)
                    print(f"  ✓ Migrated {migrated} CDO notifications")
                
                # Migrate data owner notifications
                if data_owner_to_migrate > 0:
                    migrated = await migrate_data_owner_notifications(session, dry_run=False)
                    print(f"  ✓ Migrated {migrated} data owner notifications")
                
                await session.commit()
                
                # Count after
                print("\n📊 Final Status:")
                counts_after = await count_notifications(session)
                for key, value in counts_after.items():
                    print(f"  {key}: {value}")
                
                # Save migration log
                migration_log = {
                    "timestamp": datetime.now().isoformat(),
                    "counts_before": counts_before,
                    "counts_after": counts_after,
                    "cdo_migrated": cdo_to_migrate,
                    "data_owner_migrated": data_owner_to_migrate
                }
                
                log_file = f"backup_logs/notification_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(log_file, 'w') as f:
                    json.dump(migration_log, f, indent=2)
                
                print(f"\n📄 Migration log saved: {log_file}")
                print("\n✅ Migration completed successfully!")
                print("\nTo rollback: SELECT rollback_notification_migration();")
            
            elif not dry_run:
                print("\n✅ No records to migrate")
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())