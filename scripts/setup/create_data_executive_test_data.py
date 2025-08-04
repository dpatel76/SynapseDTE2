#!/usr/bin/env python3
"""
Create test data for Data Executive dashboard
This simulates test case assignments made by a Data Executive
"""

import asyncio
import os
from datetime import datetime, timedelta
import random
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import models
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.request_info import TestCase
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report

load_dotenv()

# Convert sync URL to async URL
sync_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/synapse_dt')
DATABASE_URL = sync_url.replace('postgresql://', 'postgresql+asyncpg://')

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_data_executive_test_data():
    """Create test cases assigned by Data Executive"""
    print("Creating Data Executive Test Data")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        # Get the Data Executive user
        result = await session.execute(
            select(User).where(User.email == "cdo@example.com")
        )
        data_executive = result.scalar_one_or_none()
        
        if not data_executive:
            print("❌ Data Executive user (cdo@example.com) not found!")
            return
            
        print(f"✅ Found Data Executive: {data_executive.first_name} {data_executive.last_name} (ID: {data_executive.user_id})")
        
        # Get existing test cases to reassign some of them
        result = await session.execute(
            select(TestCase).limit(5)
        )
        test_cases = result.scalars().all()
        
        if test_cases:
            print(f"\nReassigning {len(test_cases)} test cases to Data Executive...")
            
            for tc in test_cases:
                # Update the test case to be assigned by the Data Executive
                tc.assigned_by = data_executive.user_id
                tc.assigned_at = datetime.utcnow() - timedelta(days=random.randint(1, 10))
                
                # Randomly set some as submitted
                if random.choice([True, False]):
                    tc.status = 'Submitted'
                    tc.submitted_at = tc.assigned_at + timedelta(hours=random.randint(4, 48))
                else:
                    tc.status = 'Pending'
                    tc.submitted_at = None
                
                print(f"  - Updated test case {tc.test_case_id} - Status: {tc.status}")
            
            await session.commit()
            print(f"\n✅ Successfully reassigned {len(test_cases)} test cases to Data Executive")
        
        # Also get some Data Owners in the same LOB to show in the dashboard
        if data_executive.lob_id:
            result = await session.execute(
                select(User).where(
                    User.lob_id == data_executive.lob_id,
                    User.role == "Data Owner",
                    User.is_active == True
                )
            )
            data_owners = result.scalars().all()
            
            if data_owners:
                print(f"\n✅ Found {len(data_owners)} Data Owners in the same LOB:")
                for do in data_owners:
                    print(f"  - {do.first_name} {do.last_name} ({do.email})")
            else:
                print(f"\n⚠️  No Data Owners found in LOB {data_executive.lob_id}")
                
                # Create a Data Owner in the same LOB for testing
                print("Creating a test Data Owner...")
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                test_data_owner = User(
                    email="test.dataowner@synapse.com",
                    first_name="Test",
                    last_name="DataOwner",
                    role="Data Owner",
                    lob_id=data_executive.lob_id,
                    hashed_password=pwd_context.hash("TestUser123!"),
                    is_active=True
                )
                session.add(test_data_owner)
                await session.commit()
                print("✅ Created test Data Owner: test.dataowner@synapse.com")
        
        # Create some new test cases if needed
        print("\nCreating additional test cases for better dashboard display...")
        
        # Get a test cycle and report
        result = await session.execute(
            select(TestCycle).where(TestCycle.status == "In Progress").limit(1)
        )
        cycle = result.scalar_one_or_none()
        
        if cycle:
            result = await session.execute(
                select(Report).where(Report.is_active == True).limit(1)
            )
            report = result.scalar_one_or_none()
            
            if report:
                # Create a few more test cases
                from app.models.report_attribute import ReportAttribute
                
                result = await session.execute(
                    select(ReportAttribute).where(
                        ReportAttribute.report_id == report.report_id
                    ).limit(3)
                )
                attributes = result.scalars().all()
                
                for i, attr in enumerate(attributes):
                    test_case = TestCase(
                        cycle_id=cycle.cycle_id,
                        report_id=report.report_id,
                        phase_id=f"phase_{cycle.cycle_id}_{report.report_id}",
                        attribute_id=attr.attribute_id,
                        attribute_name=attr.attribute_name,
                        sample_id=f"sample_{i+1}",
                        sample_identifier=f"SAMPLE-{i+1:03d}",
                        data_owner_id=data_executive.user_id,  # Assign to self for now
                        assigned_by=data_executive.user_id,
                        assigned_at=datetime.utcnow() - timedelta(days=random.randint(0, 5)),
                        primary_key_attributes={"id": f"ID-{i+1}", "name": f"Sample {i+1}"},
                        status='Pending' if i % 2 == 0 else 'Submitted',
                        submission_deadline=datetime.utcnow() + timedelta(days=7),
                        expected_evidence_type="Document",
                        special_instructions=f"Please provide evidence for {attr.attribute_name}"
                    )
                    
                    if test_case.status == 'Submitted':
                        test_case.submitted_at = test_case.assigned_at + timedelta(hours=random.randint(2, 24))
                    
                    session.add(test_case)
                    print(f"  - Created test case for {attr.attribute_name} - Status: {test_case.status}")
                
                await session.commit()
                print("\n✅ Created additional test cases")
            else:
                print("⚠️  No active reports found")
        else:
            print("⚠️  No in-progress test cycles found")
        
        # Summary
        result = await session.execute(
            select(TestCase).where(TestCase.assigned_by == data_executive.user_id)
        )
        total_assigned = len(result.scalars().all())
        
        print(f"\n📊 Summary:")
        print(f"  - Total test cases assigned by Data Executive: {total_assigned}")
        print(f"  - Data Executive can now see meaningful data in their dashboard!")

if __name__ == "__main__":
    asyncio.run(create_data_executive_test_data())