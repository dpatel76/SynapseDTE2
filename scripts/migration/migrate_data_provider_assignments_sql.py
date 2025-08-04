#!/usr/bin/env python3
"""
Migrate data from legacy data_provider_assignments table to new data_owner_assignments table
Using raw SQL since the old model may have been removed
"""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Convert sync URL to async URL
sync_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/synapse_dt')
DATABASE_URL = sync_url.replace('postgresql://', 'postgresql+asyncpg://')

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def migrate_assignments():
    """Migrate data provider assignments to data owner assignments"""
    print("Migrating Data Provider Assignments to Data Owner Assignments")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # First, check what's in the old table
        result = await session.execute(
            text("SELECT COUNT(*) FROM data_provider_assignments")
        )
        total_count = result.scalar()
        print(f"Found {total_count} assignments in legacy data_provider_assignments table")
        
        # Get all assignments from old table
        result = await session.execute(
            text("""
                SELECT dpa.*, ra.attribute_name, u.email as data_owner_email
                FROM data_provider_assignments dpa
                LEFT JOIN report_attributes ra ON dpa.attribute_id = ra.attribute_id
                LEFT JOIN users u ON dpa.data_provider_id = u.user_id
                ORDER BY dpa.created_at
            """)
        )
        old_assignments = result.fetchall()
        
        migrated_count = 0
        skipped_count = 0
        
        for row in old_assignments:
            # Check if assignment already exists in new table
            check_result = await session.execute(
                text("""
                    SELECT COUNT(*) FROM data_owner_assignments
                    WHERE cycle_id = :cycle_id
                    AND report_id = :report_id
                    AND attribute_id = :attribute_id
                    AND lob_id = :lob_id
                    AND data_owner_id = :data_owner_id
                """),
                {
                    "cycle_id": row.cycle_id,
                    "report_id": row.report_id,
                    "attribute_id": row.attribute_id,
                    "lob_id": row.lob_id,
                    "data_owner_id": row.data_provider_id
                }
            )
            
            if check_result.scalar() > 0:
                skipped_count += 1
                print(f"  ⏭️  Skipping duplicate - {row.attribute_name} for {row.data_owner_email}")
                continue
            
            # Insert into new table
            await session.execute(
                text("""
                    INSERT INTO data_owner_assignments 
                    (cycle_id, report_id, attribute_id, lob_id, cdo_id, data_owner_id, 
                     assigned_by, assigned_at, status, created_at, updated_at)
                    VALUES 
                    (:cycle_id, :report_id, :attribute_id, :lob_id, :cdo_id, :data_owner_id,
                     :assigned_by, :assigned_at, :status, :created_at, :updated_at)
                """),
                {
                    "cycle_id": row.cycle_id,
                    "report_id": row.report_id,
                    "attribute_id": row.attribute_id,
                    "lob_id": row.lob_id,
                    "cdo_id": row.cdo_id,
                    "data_owner_id": row.data_provider_id,
                    "assigned_by": row.assigned_by,
                    "assigned_at": row.assigned_at,
                    "status": row.status,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at
                }
            )
            
            migrated_count += 1
            print(f"  ✅ Migrated - {row.attribute_name} to {row.data_owner_email} (Status: {row.status})")
        
        # Commit all migrations
        await session.commit()
        
        print(f"\n📊 Migration Summary:")
        print(f"  - Total assignments found: {total_count}")
        print(f"  - Successfully migrated: {migrated_count}")
        print(f"  - Skipped (duplicates): {skipped_count}")
        
        # Verify migration for CDO user 5
        result = await session.execute(
            text("""
                SELECT da.*, ra.attribute_name 
                FROM data_owner_assignments da
                JOIN report_attributes ra ON da.attribute_id = ra.attribute_id
                WHERE da.cdo_id = 5
            """)
        )
        cdo_assignments = result.fetchall()
        
        print(f"\n🔍 Verification for CDO (user_id=5):")
        print(f"  - Total assignments in new table: {len(cdo_assignments)}")
        for assignment in cdo_assignments:
            print(f"    • Assignment {assignment.assignment_id}: "
                  f"{assignment.attribute_name}, Status: {assignment.status}")
        
        print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_assignments())