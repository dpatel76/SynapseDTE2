#!/usr/bin/env python3
"""
Migrate data from legacy data_provider_assignments table to new data_owner_assignments table
This ensures all historical CDO assignments are preserved in the new unified model
"""

import asyncio
import os
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import models
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.testing import DataOwnerAssignment, DataProviderAssignment

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
        # Get all data provider assignments
        result = await session.execute(
            select(DataProviderAssignment)
            .order_by(DataProviderAssignment.created_at)
        )
        old_assignments = result.scalars().all()
        
        print(f"Found {len(old_assignments)} assignments in legacy table")
        
        migrated_count = 0
        skipped_count = 0
        
        for old_assignment in old_assignments:
            # Check if assignment already exists in new table
            existing = await session.execute(
                select(DataOwnerAssignment).where(
                    and_(
                        DataOwnerAssignment.cycle_id == old_assignment.cycle_id,
                        DataOwnerAssignment.report_id == old_assignment.report_id,
                        DataOwnerAssignment.attribute_id == old_assignment.attribute_id,
                        DataOwnerAssignment.lob_id == old_assignment.lob_id,
                        DataOwnerAssignment.data_owner_id == old_assignment.data_provider_id
                    )
                )
            )
            
            if existing.scalar_one_or_none():
                skipped_count += 1
                print(f"  ⏭️  Skipping duplicate - Cycle: {old_assignment.cycle_id}, Report: {old_assignment.report_id}, Attribute: {old_assignment.attribute_id}")
                continue
            
            # Create new assignment
            new_assignment = DataOwnerAssignment(
                cycle_id=old_assignment.cycle_id,
                report_id=old_assignment.report_id,
                attribute_id=old_assignment.attribute_id,
                lob_id=old_assignment.lob_id,
                cdo_id=old_assignment.cdo_id,
                data_owner_id=old_assignment.data_provider_id,  # Map data_provider_id to data_owner_id
                assigned_by=old_assignment.assigned_by,
                assigned_at=old_assignment.assigned_at,
                status=old_assignment.status,
                created_at=old_assignment.created_at,
                updated_at=old_assignment.updated_at
            )
            
            session.add(new_assignment)
            migrated_count += 1
            
            print(f"  ✅ Migrated - Cycle: {old_assignment.cycle_id}, Report: {old_assignment.report_id}, "
                  f"Attribute: {old_assignment.attribute_id}, CDO: {old_assignment.cdo_id}, "
                  f"Data Owner: {old_assignment.data_provider_id}, Status: {old_assignment.status}")
        
        # Commit all migrations
        await session.commit()
        
        print(f"\n📊 Migration Summary:")
        print(f"  - Total assignments found: {len(old_assignments)}")
        print(f"  - Successfully migrated: {migrated_count}")
        print(f"  - Skipped (duplicates): {skipped_count}")
        
        # Verify migration for CDO user 5
        result = await session.execute(
            select(DataOwnerAssignment).where(DataOwnerAssignment.cdo_id == 5)
        )
        cdo_assignments = result.scalars().all()
        
        print(f"\n🔍 Verification for CDO (user_id=5):")
        print(f"  - Total assignments in new table: {len(cdo_assignments)}")
        for assignment in cdo_assignments:
            print(f"    • Assignment {assignment.assignment_id}: "
                  f"Attribute {assignment.attribute_id}, Status: {assignment.status}")
        
        print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_assignments())