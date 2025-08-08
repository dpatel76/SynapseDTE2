#!/usr/bin/env python3
"""
Fixed migration script for notifications to universal assignments
Corrected to match actual database schemas
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
    
    # Count data owner notifications (both tables)
    result = await session.execute(
        text("SELECT COUNT(*) FROM data_owner_notifications")
    )
    data_owner_count = result.scalar()
    
    result = await session.execute(
        text("SELECT COUNT(*) FROM data_provider_notifications")
    )
    data_provider_count = result.scalar()
    
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
        "data_provider_notifications": data_provider_count,
        "universal_assignments": universal_count,
        "already_migrated": migrated_count
    }

async def migrate_cdo_notifications(session: AsyncSession, dry_run: bool = True) -> int:
    """Migrate CDO notifications to universal assignments"""
    
    # First check the actual schema
    result = await session.execute(
        text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cdo_notifications'
            ORDER BY ordinal_position
        """)
    )
    columns = [row[0] for row in result]
    print(f"CDO notifications columns: {columns}")
    
    if dry_run:
        # Count what would be migrated
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM cdo_notifications cn
                WHERE NOT EXISTS (
                    SELECT 1 FROM universal_assignments ua
                    WHERE ua.assignment_metadata->>'migrated_from' = 'cdo_notifications'
                    AND (ua.assignment_metadata->>'original_id')::text = cn.notification_id::text
                )
            """)
        )
        return result.scalar()
    
    # Perform actual migration
    # Map cdo_notifications fields to universal assignments
    result = await session.execute(
        text("""
            INSERT INTO universal_assignments (
                assignment_id,
                assignment_type, 
                cycle_id, 
                report_id,
                from_user_id, 
                to_user_id,
                from_role, 
                to_role,
                title, 
                description,
                priority, 
                status,
                context_type,
                context_data,
                created_at, 
                assignment_metadata
            )
            SELECT 
                gen_random_uuid()::text,
                'LOB Assignment', 
                cycle_id, 
                report_id,
                COALESCE(
                    (SELECT user_id FROM users WHERE role = 'Data Executive' LIMIT 1),
                    1
                ), -- from_user_id (default to system user)
                cdo_id, -- to_user_id (CDO)
                'Data Executive', 
                'Data Executive', -- Updated from CDO
                'LOB Assignment Review Required', 
                COALESCE(
                    notification_data->>'message',
                    'Review LOB assignment for report'
                ),
                'High', 
                CASE 
                    WHEN is_complete THEN 'Completed'
                    WHEN responded_at IS NOT NULL THEN 'In Progress'
                    ELSE 'Assigned'
                END,
                'Report',
                jsonb_build_object(
                    'lob_id', lob_id,
                    'sla_hours', sla_hours
                ),
                notification_sent_at,
                jsonb_build_object(
                    'lob_id', lob_id,
                    'migrated_from', 'cdo_notifications',
                    'original_id', notification_id,
                    'migration_date', now()::text,
                    'original_data', notification_data,
                    'assignment_deadline', assignment_deadline,
                    'responded_at', responded_at,
                    'is_complete', is_complete
                )
            FROM cdo_notifications cn
            WHERE NOT EXISTS (
                SELECT 1 FROM universal_assignments ua
                WHERE ua.assignment_metadata->>'migrated_from' = 'cdo_notifications'
                AND (ua.assignment_metadata->>'original_id')::text = cn.notification_id::text
            )
            RETURNING assignment_id
        """)
    )
    
    return len(result.all())

async def migrate_data_provider_notifications(session: AsyncSession, dry_run: bool = True) -> int:
    """Migrate data provider notifications to universal assignments"""
    
    # Check which table exists and has data
    result = await session.execute(
        text("SELECT COUNT(*) FROM data_provider_notifications")
    )
    provider_count = result.scalar()
    
    if provider_count == 0:
        print("No data in data_provider_notifications, skipping...")
        return 0
    
    # Check the actual schema
    result = await session.execute(
        text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'data_provider_notifications'
            ORDER BY ordinal_position
        """)
    )
    columns = [row[0] for row in result]
    print(f"Data provider notifications columns: {columns}")
    
    if dry_run:
        # Count what would be migrated
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM data_provider_notifications dpn
                WHERE NOT EXISTS (
                    SELECT 1 FROM universal_assignments ua
                    WHERE ua.assignment_metadata->>'migrated_from' = 'data_provider_notifications'
                    AND ua.assignment_metadata->>'original_id' = dpn.notification_id
                )
            """)
        )
        return result.scalar()
    
    # Perform actual migration
    result = await session.execute(
        text("""
            INSERT INTO universal_assignments (
                assignment_id,
                assignment_type, 
                cycle_id, 
                report_id,
                from_user_id, 
                to_user_id,
                from_role, 
                to_role,
                title, 
                description,
                priority, 
                status,
                context_type,
                context_data,
                due_date,
                created_at,
                assignment_metadata
            )
            SELECT 
                gen_random_uuid()::text,
                'Information Request', 
                cycle_id, 
                report_id,
                COALESCE(
                    (SELECT user_id FROM users WHERE role = 'Test Manager' LIMIT 1),
                    1
                ), -- from_user_id
                data_provider_id, -- to_user_id
                'Test Manager', 
                'Data Owner', -- Updated from Data Provider
                'Information Request - Data Submission Required',
                COALESCE(
                    custom_instructions,
                    'Please provide data for the assigned attributes'
                ),
                'Medium',
                CASE status
                    WHEN 'Pending' THEN 'Assigned'
                    WHEN 'In Progress' THEN 'In Progress'
                    WHEN 'Submitted' THEN 'Completed'
                    WHEN 'Validated' THEN 'Completed'
                    WHEN 'Requires Revision' THEN 'In Progress'
                    WHEN 'Overdue' THEN 'Overdue'
                    ELSE 'Assigned'
                END,
                'Phase',
                jsonb_build_object(
                    'phase_id', phase_id,
                    'assigned_attributes', assigned_attributes,
                    'sample_count', sample_count
                ),
                submission_deadline,
                created_at,
                jsonb_build_object(
                    'phase_id', phase_id,
                    'assigned_attributes', assigned_attributes,
                    'sample_count', sample_count,
                    'portal_access_url', portal_access_url,
                    'migrated_from', 'data_provider_notifications',
                    'original_id', notification_id,
                    'migration_date', now()::text,
                    'notification_sent_at', notification_sent_at,
                    'first_access_at', first_access_at,
                    'last_access_at', last_access_at,
                    'access_count', access_count,
                    'is_acknowledged', is_acknowledged,
                    'acknowledged_at', acknowledged_at,
                    'original_status', status
                )
            FROM data_provider_notifications dpn
            WHERE NOT EXISTS (
                SELECT 1 FROM universal_assignments ua
                WHERE ua.assignment_metadata->>'migrated_from' = 'data_provider_notifications'
                AND ua.assignment_metadata->>'original_id' = dpn.notification_id
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
            WHERE assignment_metadata->>'migrated_from' IN (
                'cdo_notifications', 
                'data_owner_notifications', 
                'data_provider_notifications'
            );
            
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
    print("NOTIFICATION TO UNIVERSAL ASSIGNMENT MIGRATION (FIXED)")
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
            provider_to_migrate = await migrate_data_provider_notifications(session, dry_run=True)
            
            print(f"\n📋 Migration Plan:")
            print(f"  CDO notifications to migrate: {cdo_to_migrate}")
            print(f"  Data provider notifications to migrate: {provider_to_migrate}")
            print(f"  Total: {cdo_to_migrate + provider_to_migrate}")
            
            if not dry_run and (cdo_to_migrate > 0 or provider_to_migrate > 0):
                print("\n🚀 Performing migration...")
                
                # Create rollback procedures first
                await create_rollback_procedures(session)
                
                # Migrate CDO notifications
                if cdo_to_migrate > 0:
                    migrated = await migrate_cdo_notifications(session, dry_run=False)
                    print(f"  ✓ Migrated {migrated} CDO notifications")
                
                # Migrate data provider notifications
                if provider_to_migrate > 0:
                    migrated = await migrate_data_provider_notifications(session, dry_run=False)
                    print(f"  ✓ Migrated {migrated} data provider notifications")
                
                await session.commit()
                
                # Count after
                print("\n📊 Final Status:")
                counts_after = await count_notifications(session)
                for key, value in counts_after.items():
                    print(f"  {key}: {value}")
                
                # Save migration log
                os.makedirs("backup_logs", exist_ok=True)
                migration_log = {
                    "timestamp": datetime.now().isoformat(),
                    "counts_before": counts_before,
                    "counts_after": counts_after,
                    "cdo_migrated": cdo_to_migrate,
                    "provider_migrated": provider_to_migrate
                }
                
                log_file = f"backup_logs/notification_migration_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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