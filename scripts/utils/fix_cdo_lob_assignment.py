#!/usr/bin/env python3
"""
Fix CDO LOB assignment
Assign an LOB to the CDO user so they can see dashboard data
"""

import asyncio
import os
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import models
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.user import User
from app.models.lob import LOB

load_dotenv()

# Convert sync URL to async URL
sync_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/synapse_dt')
DATABASE_URL = sync_url.replace('postgresql://', 'postgresql+asyncpg://')

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def fix_cdo_lob_assignment():
    """Assign LOB to CDO user"""
    print("Fixing CDO LOB Assignment")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        # Get the CDO user
        result = await session.execute(
            select(User).where(User.email == "cdo@synapse.com")
        )
        cdo_user = result.scalar_one_or_none()
        
        if not cdo_user:
            print("❌ CDO user not found!")
            return
            
        print(f"✅ Found CDO: {cdo_user.first_name} {cdo_user.last_name}")
        print(f"   Current LOB: {cdo_user.lob_id or 'None'}")
        
        # Find an LOB that has Data Owners
        result = await session.execute(
            select(User.lob_id, LOB.lob_name)
            .join(LOB, User.lob_id == LOB.lob_id)
            .where(User.role == "Data Owner", User.is_active == True, User.lob_id.isnot(None))
            .group_by(User.lob_id, LOB.lob_name)
        )
        lobs_with_data_owners = result.all()
        
        if lobs_with_data_owners:
            # Use the first LOB that has Data Owners
            lob_id, lob_name = lobs_with_data_owners[0]
            
            print(f"\n📍 Assigning CDO to LOB: {lob_name} (ID: {lob_id})")
            
            # Update CDO's LOB
            cdo_user.lob_id = lob_id
            await session.commit()
            
            print(f"✅ Successfully assigned CDO to LOB: {lob_name}")
            
            # Show Data Owners in this LOB
            result = await session.execute(
                select(User).where(
                    User.lob_id == lob_id,
                    User.role == "Data Owner",
                    User.is_active == True
                )
            )
            data_owners = result.scalars().all()
            
            print(f"\n👥 Data Owners in {lob_name}:")
            for do in data_owners:
                print(f"   - {do.first_name} {do.last_name} ({do.email})")
                
        else:
            print("❌ No LOBs with Data Owners found!")
            
            # Create a test LOB
            print("\nCreating a test LOB...")
            test_lob = LOB(
                lob_name="Corporate Finance",
                description="Corporate Finance Line of Business"
            )
            session.add(test_lob)
            await session.flush()
            
            # Assign CDO to this LOB
            cdo_user.lob_id = test_lob.lob_id
            await session.commit()
            
            print(f"✅ Created LOB 'Corporate Finance' and assigned CDO to it")

if __name__ == "__main__":
    asyncio.run(fix_cdo_lob_assignment())