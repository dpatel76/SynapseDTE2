#!/usr/bin/env python3
"""
Create data owner assignments for CDO
This simulates the CDO assigning data owners to attributes in their LOB
"""

import asyncio
import os
from datetime import datetime, timedelta
import random
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import models
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# AttributeLOBAssignment removed - table doesn't exist
from app.models.testing import DataOwnerAssignment
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report

load_dotenv()

# Convert sync URL to async URL
sync_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/synapse_dt')
DATABASE_URL = sync_url.replace('postgresql://', 'postgresql+asyncpg://')

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_cdo_assignments():
    """Create data owner assignments for CDO"""
    print("Creating CDO Data Owner Assignments")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        # Get the CDO user
        result = await session.execute(
            select(User).where(User.email == "cdo@example.com")
        )
        cdo_user = result.scalar_one_or_none()
        
        if not cdo_user:
            print("❌ CDO user (cdo@example.com) not found!")
            return
            
        print(f"✅ Found CDO: {cdo_user.first_name} {cdo_user.last_name} (ID: {cdo_user.user_id})")
        print(f"   LOB: {cdo_user.lob_id}")
        
        # Get data owners in the same LOB
        result = await session.execute(
            select(User).where(
                User.lob_id == cdo_user.lob_id,
                User.role == "Data Owner",
                User.is_active == True
            )
        )
        data_owners = result.scalars().all()
        
        if not data_owners:
            print("❌ No Data Owners found in CDO's LOB!")
            return
            
        print(f"✅ Found {len(data_owners)} Data Owners in LOB {cdo_user.lob_id}")
        
        # Get attribute-LOB assignments for the CDO's LOB
        result = await session.execute(
            select(AttributeLOBAssignment)
            .where(AttributeLOBAssignment.lob_id == cdo_user.lob_id)
            .limit(10)  # Take first 10 for testing
        )
        attribute_assignments = result.scalars().all()
        
        if not attribute_assignments:
            print("❌ No attribute-LOB assignments found for CDO's LOB!")
            return
            
        print(f"✅ Found {len(attribute_assignments)} attribute-LOB assignments")
        
        # Create data owner assignments
        assignments_created = 0
        
        for i, attr_assignment in enumerate(attribute_assignments):
            # Randomly assign to a data owner
            data_owner = random.choice(data_owners)
            
            # Check if assignment already exists
            existing = await session.execute(
                select(DataOwnerAssignment).where(
                    and_(
                        DataOwnerAssignment.cycle_id == attr_assignment.cycle_id,
                        DataOwnerAssignment.report_id == attr_assignment.report_id,
                        DataOwnerAssignment.attribute_id == attr_assignment.attribute_id,
                        DataOwnerAssignment.lob_id == attr_assignment.lob_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            # Create the assignment
            assignment = DataOwnerAssignment(
                cycle_id=attr_assignment.cycle_id,
                report_id=attr_assignment.report_id,
                attribute_id=attr_assignment.attribute_id,
                lob_id=attr_assignment.lob_id,
                cdo_id=cdo_user.user_id,
                data_owner_id=data_owner.user_id,
                assigned_by=cdo_user.user_id,
                assigned_at=datetime.utcnow() - timedelta(days=random.randint(1, 7)),
                status='Pending' if i % 3 != 0 else 'Completed'  # 2/3 pending, 1/3 completed
            )
            
            session.add(assignment)
            assignments_created += 1
            print(f"  - Created assignment for attribute {attr_assignment.attribute_id} to {data_owner.email} - Status: {assignment.status}")
        
        await session.commit()
        
        print(f"\n✅ Created {assignments_created} data owner assignments")
        
        # Summary
        result = await session.execute(
            select(DataOwnerAssignment).where(DataOwnerAssignment.cdo_id == cdo_user.user_id)
        )
        total_assignments = len(result.scalars().all())
        
        print(f"\n📊 Summary:")
        print(f"  - Total assignments by CDO: {total_assignments}")
        print(f"  - CDO can now see meaningful data in their dashboard!")

if __name__ == "__main__":
    asyncio.run(create_cdo_assignments())