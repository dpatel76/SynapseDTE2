#!/usr/bin/env python3

import sys
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from app.models.testing import DataProviderAssignment
from app.models.sample_selection import SampleRecord
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import asyncio
import json

async def check_primary_keys():
    async with AsyncSessionLocal() as db:
        # Get assignments for cycle 9, report 156 (the test case we're looking at)
        cycle_id = 9
        report_id = 156
        
        print(f"Checking primary key attributes for cycle {cycle_id}, report {report_id}")
        
        # Get all assignments for this cycle/report
        query = select(DataProviderAssignment).options(
            selectinload(DataProviderAssignment.attribute)
        ).where(
            DataProviderAssignment.cycle_id == cycle_id,
            DataProviderAssignment.report_id == report_id
        )
        
        result = await db.execute(query)
        assignments = result.scalars().all()
        
        print(f"Found {len(assignments)} total assignments")
        
        # Check for primary key assignments
        pk_assignments = [a for a in assignments if a.attribute and a.attribute.is_primary_key]
        non_pk_assignments = [a for a in assignments if a.attribute and not a.attribute.is_primary_key]
        
        print(f"Primary key assignments: {len(pk_assignments)}")
        print(f"Non-primary key assignments: {len(non_pk_assignments)}")
        
        if pk_assignments:
            print("\nPrimary Key Attributes:")
            for pk_assignment in pk_assignments:
                print(f"  - {pk_assignment.attribute.attribute_name} (ID: {pk_assignment.attribute_id})")
        else:
            print("\nNo primary key attributes found!")
            
        print("\nAll Attributes:")
        for assignment in assignments:
            if assignment.attribute:
                print(f"  - {assignment.attribute.attribute_name} (ID: {assignment.attribute_id}, is_primary_key: {assignment.attribute.is_primary_key})")
        
        # Get sample data - fix the query
        sample_query = select(SampleRecord).where(
            SampleRecord.report_id == report_id
        ).limit(1)
        
        sample_result = await db.execute(sample_query)
        sample = sample_result.scalar_one_or_none()
        
        if sample:
            print(f"\nSample found: {sample.sample_identifier}")
            print(f"Sample data keys: {list(sample.sample_data.keys()) if sample.sample_data else 'No sample_data'}")
            
            if sample.sample_data:
                print("Sample data preview:")
                for key, value in list(sample.sample_data.items())[:10]:  # Show first 10 keys
                    print(f"  - {key}: {value}")
        else:
            print("\nNo sample records found!")

asyncio.run(check_primary_keys()) 