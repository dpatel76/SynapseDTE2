#!/usr/bin/env python3
"""
Test script to verify the Request Info phase flow
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.request_info import CycleReportTestCase
from app.models.workflow import WorkflowPhase
from sqlalchemy import select, func

# Database configuration
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/synapse_dt"

async def test_request_info():
    # Create database engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Check if there are any test cases with the new fields
        result = await session.execute(
            select(
                CycleReportTestCase.id,
                CycleReportTestCase.test_case_number,
                CycleReportTestCase.test_case_name,
                CycleReportTestCase.sample_id,
                CycleReportTestCase.attribute_id,
                CycleReportTestCase.attribute_name,
                CycleReportTestCase.lob_id,
                CycleReportTestCase.data_owner_id,
                CycleReportTestCase.status
            ).limit(5)
        )
        
        test_cases = result.all()
        
        print("\n=== Test Cases in Database ===")
        for tc in test_cases:
            print(f"\nTest Case ID: {tc.id}")
            print(f"  Number: {tc.test_case_number}")
            print(f"  Name: {tc.test_case_name}")
            print(f"  Sample ID: {tc.sample_id}")
            print(f"  Attribute ID: {tc.attribute_id}")
            print(f"  Attribute Name: {tc.attribute_name}")
            print(f"  LOB ID: {tc.lob_id}")
            print(f"  Data Owner ID: {tc.data_owner_id}")
            print(f"  Status: {tc.status}")
        
        # Count test cases by data owner
        count_result = await session.execute(
            select(
                CycleReportTestCase.data_owner_id,
                func.count(CycleReportTestCase.id).label('count')
            ).group_by(CycleReportTestCase.data_owner_id)
        )
        
        counts = count_result.all()
        
        print("\n=== Test Cases by Data Owner ===")
        for row in counts:
            print(f"Data Owner {row.data_owner_id}: {row.count} test cases")
        
        # Check workflow phases
        phase_result = await session.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.phase_name == "Request Info"
            ).limit(5)
        )
        
        phases = phase_result.scalars().all()
        
        print("\n=== Request Info Phases ===")
        for phase in phases:
            print(f"\nPhase ID: {phase.phase_id}")
            print(f"  Cycle ID: {phase.cycle_id}")
            print(f"  Report ID: {phase.report_id}")
            print(f"  Status: {phase.status}")
            print(f"  Started At: {phase.actual_start_date}")

if __name__ == "__main__":
    asyncio.run(test_request_info())