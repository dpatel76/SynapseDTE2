#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.testing import DataProviderAssignment
from app.models.sample_selection import SampleRecord, SampleSet
from app.models.request_info import RequestInfoPhase, TestCase
from datetime import datetime

async def debug_test_case_creation():
    """Debug the exact test case creation logic"""
    
    cycle_id = 9
    report_id = 156
    phase_id = "0980a908-336c-4d4e-9032-e30f0a335e84"
    user_id = 1  # Assuming user ID 1 exists
    submission_deadline = datetime(2024, 12, 31, 23, 59, 59)
    
    print(f"Debugging test case creation for phase {phase_id}")
    
    async for db in get_db():
        try:
            # Get the phase
            phase_result = await db.execute(
                select(RequestInfoPhase).where(RequestInfoPhase.phase_id == phase_id)
            )
            phase = phase_result.scalar_one_or_none()
            print(f"Phase found: {phase is not None}")
            
            if not phase:
                print("Phase not found, exiting")
                return
            
            # Get assignments with attributes
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
            print(f"Total assignments: {len(assignments)}")
            
            # Filter non-PK assignments
            non_pk_assignments = [a for a in assignments if a.attribute and not a.attribute.is_primary_key]
            pk_assignments = [a for a in assignments if a.attribute and a.attribute.is_primary_key]
            print(f"Non-PK assignments: {len(non_pk_assignments)}")
            print(f"PK assignments: {len(pk_assignments)}")
            
            # Get samples
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
            print(f"Samples found: {len(samples)}")
            
            if not non_pk_assignments:
                print("No non-PK assignments found")
                return
                
            if not samples:
                print("No samples found")
                return
            
            test_cases_created = 0
            
            # Simulate the exact creation logic
            for assignment in non_pk_assignments:
                print(f"\nProcessing assignment for attribute {assignment.attribute.attribute_name} (ID: {assignment.attribute_id})")
                for sample in samples:
                    print(f"  Creating test case for sample {sample.sample_identifier}")
                    
                    # Build primary key context
                    pk_context = {}
                    for pk_assignment in pk_assignments:
                        pk_context[pk_assignment.attribute.attribute_name] = sample.sample_data.get(
                            pk_assignment.attribute.attribute_name, "N/A"
                        )
                    
                    print(f"    PK context: {pk_context}")
                    
                    try:
                        test_case = TestCase(
                            phase_id=phase.phase_id,
                            cycle_id=phase.cycle_id,
                            report_id=phase.report_id,
                            attribute_id=assignment.attribute_id,
                            sample_id=sample.record_id,
                            sample_identifier=sample.sample_identifier,
                            data_owner_id=assignment.data_owner_id,
                            assigned_by=user_id,
                            attribute_name=assignment.attribute.attribute_name,
                            primary_key_attributes=pk_context,
                            submission_deadline=submission_deadline,
                            expected_evidence_type="Document",
                            special_instructions=f"Please provide evidence for {assignment.attribute.attribute_name} for the sample identified by: {', '.join([f'{k}: {v}' for k, v in pk_context.items()])}"
                        )
                        
                        print(f"    Created TestCase object: {test_case.test_case_id}")
                        db.add(test_case)
                        test_cases_created += 1
                        print(f"    Added to session, total created: {test_cases_created}")
                        
                    except Exception as e:
                        print(f"    ERROR creating test case: {e}")
                        import traceback
                        traceback.print_exc()
            
            print(f"\nTotal test cases to commit: {test_cases_created}")
            
            if test_cases_created > 0:
                try:
                    await db.commit()
                    print("Successfully committed test cases")
                    
                    # Verify they were created
                    verify_result = await db.execute(
                        select(TestCase).where(
                            and_(
                                TestCase.cycle_id == cycle_id,
                                TestCase.report_id == report_id
                            )
                        )
                    )
                    created_test_cases = verify_result.scalars().all()
                    print(f"Verification: {len(created_test_cases)} test cases found in database")
                    
                except Exception as e:
                    print(f"ERROR during commit: {e}")
                    import traceback
                    traceback.print_exc()
                    await db.rollback()
            else:
                print("No test cases to commit")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(debug_test_case_creation()) 