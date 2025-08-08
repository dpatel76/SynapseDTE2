#!/usr/bin/env python3

import sys
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from app.models.scoping import TesterScopingDecision
from app.models.sample_selection import SampleRecord, SampleSet
from app.models.request_info import TestCase
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, update
import asyncio

async def update_existing_test_cases():
    async with AsyncSessionLocal() as db:
        # Update test cases for cycle 9, report 156
        cycle_id = 9
        report_id = 156
        
        print(f"Updating existing test cases for cycle {cycle_id}, report {report_id}")
        
        # Get primary key attributes from scoping decisions
        pk_scoping_result = await db.execute(
            select(TesterScopingDecision)
            .options(selectinload(TesterScopingDecision.attribute))
            .where(
                and_(
                    TesterScopingDecision.cycle_id == cycle_id,
                    TesterScopingDecision.report_id == report_id,
                    TesterScopingDecision.final_scoping == True
                )
            )
        )
        pk_scoping_decisions = pk_scoping_result.scalars().all()
        pk_attributes = [s.attribute for s in pk_scoping_decisions if s.attribute and s.attribute.is_primary_key]
        print(f"Found {len(pk_attributes)} PK attributes from scoping")
        
        # Get all sample records
        samples_result = await db.execute(
            select(SampleRecord)
            .join(SampleSet)
            .where(
                and_(
                    SampleSet.cycle_id == cycle_id,
                    SampleSet.report_id == report_id
                )
            )
        )
        samples = samples_result.scalars().all()
        print(f"Found {len(samples)} sample records")
        
        # Create a mapping of sample_id to primary key context
        sample_pk_mapping = {}
        for sample in samples:
            pk_context = {}
            for pk_attr in pk_attributes:
                value = sample.sample_data.get(pk_attr.attribute_name, "N/A") if sample.sample_data else "N/A"
                pk_context[pk_attr.attribute_name] = value
            sample_pk_mapping[sample.record_id] = pk_context
        
        # Get existing test cases for this cycle/report
        test_cases_result = await db.execute(
            select(TestCase).where(
                and_(
                    TestCase.cycle_id == cycle_id,
                    TestCase.report_id == report_id
                )
            )
        )
        test_cases = test_cases_result.scalars().all()
        print(f"Found {len(test_cases)} existing test cases")
        
        # Update each test case with correct primary key attributes
        updated_count = 0
        for test_case in test_cases:
            if test_case.sample_id in sample_pk_mapping:
                new_pk_context = sample_pk_mapping[test_case.sample_id]
                
                # Only update if the primary key attributes are different
                if test_case.primary_key_attributes != new_pk_context:
                    print(f"Updating test case {test_case.test_case_id}")
                    print(f"  Old PK: {test_case.primary_key_attributes}")
                    print(f"  New PK: {new_pk_context}")
                    
                    # Update the test case
                    await db.execute(
                        update(TestCase)
                        .where(TestCase.test_case_id == test_case.test_case_id)
                        .values(
                            primary_key_attributes=new_pk_context,
                            special_instructions=f"Please provide evidence for {test_case.attribute_name} for the sample identified by: {', '.join([f'{k}: {v}' for k, v in new_pk_context.items()])}"
                        )
                    )
                    updated_count += 1
        
        await db.commit()
        print(f"\n✅ Updated {updated_count} test cases with correct primary key attributes")

asyncio.run(update_existing_test_cases()) 