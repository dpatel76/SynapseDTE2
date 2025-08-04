#!/usr/bin/env python3

import sys
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from app.models.scoping import TesterScopingDecision
from app.models.sample_selection import SampleRecord, SampleSet
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_
import asyncio

async def test_pk_fix():
    async with AsyncSessionLocal() as db:
        # Test the same logic as the fixed code
        cycle_id = 9
        report_id = 156
        
        print(f"Testing primary key fix for cycle {cycle_id}, report {report_id}")
        
        # Get primary key attributes from scoping decisions (same as fixed code)
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
        print(f"Found {len(pk_attributes)} PK attributes from scoping:")
        for pk_attr in pk_attributes:
            print(f"  - {pk_attr.attribute_name} (ID: {pk_attr.attribute_id})")
        
        # Get sample records (same as fixed code)
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
        print(f"\nFound {len(samples)} sample records")
        
        if samples and pk_attributes:
            # Test building primary key context for first sample
            sample = samples[0]
            print(f"\nTesting with sample: {sample.sample_identifier}")
            print(f"Sample data keys: {list(sample.sample_data.keys()) if sample.sample_data else 'No sample_data'}")
            
            # Build primary key context (same as fixed code)
            pk_context = {}
            for pk_attr in pk_attributes:
                value = sample.sample_data.get(pk_attr.attribute_name, "N/A") if sample.sample_data else "N/A"
                pk_context[pk_attr.attribute_name] = value
                print(f"  {pk_attr.attribute_name}: {value}")
            
            print(f"\nPrimary key context: {pk_context}")
            
            if pk_context and any(v != "N/A" for v in pk_context.values()):
                print("✅ SUCCESS: Primary key context has actual values!")
            else:
                print("❌ ISSUE: Primary key context is empty or all N/A values")
        else:
            print("❌ No samples or primary key attributes found")

asyncio.run(test_pk_fix()) 