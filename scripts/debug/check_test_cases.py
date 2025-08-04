#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('.')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.testing import DataProviderAssignment
from app.models.sample_selection import SampleRecord, SampleSet
from app.models.request_info import RequestInfoPhase, TestCase

async def debug_test_case_generation():
    """Debug test case generation requirements"""
    
    cycle_id = 9
    report_id = 156
    
    print(f"Debugging test case generation for cycle {cycle_id}, report {report_id}")
    
    async for db in get_db():
        try:
            # Check existing test cases first
            test_cases_result = await db.execute(
                select(TestCase).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id
                    )
                )
            )
            existing_test_cases = test_cases_result.scalars().all()
            print(f"Existing test cases: {len(existing_test_cases)}")
            
            # Check if phase exists
            phase_result = await db.execute(
                select(RequestInfoPhase).where(
                    and_(
                        RequestInfoPhase.cycle_id == cycle_id,
                        RequestInfoPhase.report_id == report_id
                    )
                )
            )
            phase = phase_result.scalar_one_or_none()
            print(f"Phase found: {phase is not None}")
            if phase:
                print(f"Phase ID: {phase.phase_id}, Status: {phase.phase_status}")
            
            # Check data provider assignments
            assignments_result = await db.execute(
                select(DataProviderAssignment)
                .options(selectinload(DataProviderAssignment.attribute))
                .where(
                    and_(
                        DataProviderAssignment.cycle_id == cycle_id,
                        DataProviderAssignment.report_id == report_id
                    )
                )
            )
            assignments = assignments_result.scalars().all()
            print(f"Total assignments found: {len(assignments)}")
            
            # Check PK vs non-PK assignments
            pk_assignments = [a for a in assignments if a.attribute and a.attribute.is_primary_key]
            non_pk_assignments = [a for a in assignments if a.attribute and not a.attribute.is_primary_key]
            
            print(f"PK assignments: {len(pk_assignments)}")
            print(f"Non-PK assignments: {len(non_pk_assignments)}")
            
            if non_pk_assignments:
                print("Non-PK attributes:")
                for a in non_pk_assignments:
                    print(f"  - {a.attribute.attribute_name} (ID: {a.attribute_id}, DP: {a.data_owner_id})")
            
            if pk_assignments:
                print("PK attributes:")
                for a in pk_assignments:
                    print(f"  - {a.attribute.attribute_name} (ID: {a.attribute_id})")
            
            # Check sample records
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
            print(f"Sample records found: {len(samples)}")
            
            if samples:
                print("Sample identifiers:")
                for sample in samples[:5]:  # Show first 5
                    print(f"  - {sample.sample_identifier} (ID: {sample.record_id})")
                if len(samples) > 5:
                    print(f"  ... and {len(samples) - 5} more")
            
            # Calculate expected test cases
            expected_test_cases = len(non_pk_assignments) * len(samples)
            print(f"Expected test cases: {expected_test_cases} ({len(non_pk_assignments)} attributes × {len(samples)} samples)")
            
            # Check raw counts with SQL
            print("\nRaw SQL counts:")
            result = await db.execute(text("SELECT COUNT(*) FROM data_owner_assignments WHERE cycle_id = :cycle_id AND report_id = :report_id"), {"cycle_id": cycle_id, "report_id": report_id})
            print(f"Total assignments (SQL): {result.scalar()}")
            
            result = await db.execute(text("SELECT COUNT(*) FROM sample_records sr JOIN sample_sets ss ON sr.sample_set_id = ss.sample_set_id WHERE ss.cycle_id = :cycle_id AND ss.report_id = :report_id"), {"cycle_id": cycle_id, "report_id": report_id})
            print(f"Sample records (SQL): {result.scalar()}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(debug_test_case_generation()) 