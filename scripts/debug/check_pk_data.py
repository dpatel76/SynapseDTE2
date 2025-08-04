import sys
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from app.models.request_info import TestCase
from app.models.testing import Sample
from app.models.sample_selection import SampleRecord
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import asyncio
import json

async def check_pk_data():
    async with AsyncSessionLocal() as db:
        # Get a test case with sample data
        query = select(TestCase).options(
            selectinload(TestCase.cycle),
            selectinload(TestCase.report)
        ).where(TestCase.data_owner_id == 6).limit(1)
        
        result = await db.execute(query)
        test_cases = result.scalars().all()
        
        if test_cases:
            tc = test_cases[0]
            print(f"Test Case ID: {tc.test_case_id}")
            print(f"Sample ID: {tc.sample_id}")
            print(f"Sample Identifier: {tc.sample_identifier}")
            print(f"Primary Key Attributes (from test case): {tc.primary_key_attributes}")
            
            # Check if we can get the actual sample data
            sample_query = select(Sample).where(Sample.sample_id == tc.sample_id)
            sample_result = await db.execute(sample_query)
            sample = sample_result.scalar_one_or_none()
            
            if sample:
                print(f"Sample found: {sample.sample_identifier}")
                print(f"Sample data: {sample.sample_data}")
            else:
                print("Sample not found in testing.Sample")
                
                # Try SampleRecord
                sample_record_query = select(SampleRecord).where(SampleRecord.sample_id == tc.sample_id)
                sample_record_result = await db.execute(sample_record_query)
                sample_record = sample_record_result.scalar_one_or_none()
                
                if sample_record:
                    print(f"SampleRecord found: {sample_record.sample_identifier}")
                    print(f"SampleRecord data: {sample_record.sample_data}")
                else:
                    print("Sample not found in SampleRecord either")
        else:
            print('No test cases found')

asyncio.run(check_pk_data()) 