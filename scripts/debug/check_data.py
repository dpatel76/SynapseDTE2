#!/usr/bin/env python3
"""
Check what data exists for cycle 9, report 156
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.workflow import WorkflowPhase
from app.models.sample_selection import SampleSet
from app.models.request_info import RequestInfoPhase, TestCase
from app.models.test_execution import TestExecution
from sqlalchemy import select


async def check_data():
    """Check data for cycle 9, report 156"""
    async with AsyncSessionLocal() as db:
        try:
            cycle_id = 9
            report_id = 156
            
            print(f"Checking data for cycle_id={cycle_id}, report_id={report_id}\n")
            
            # Check workflow phases
            phases = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id
                ).order_by(WorkflowPhase.phase_name)
            )
            
            print("Workflow Phases:")
            for phase in phases.scalars():
                print(f"  - {phase.phase_name}: status={phase.status}, state={phase.state}")
            
            # Check sample sets
            sample_sets = await db.execute(
                select(SampleSet).where(
                    SampleSet.cycle_id == cycle_id,
                    SampleSet.report_id == report_id
                )
            )
            
            print(f"\nSample Sets: {len(list(sample_sets.scalars()))}")
            
            # Check request info phase
            req_phase = await db.execute(
                select(RequestInfoPhase).where(
                    RequestInfoPhase.cycle_id == cycle_id,
                    RequestInfoPhase.report_id == report_id
                )
            )
            req_phase = req_phase.scalar_one_or_none()
            
            if req_phase:
                print(f"\nRequest Info Phase found: phase_id={req_phase.phase_id}")
                
                # Check test cases
                test_cases = await db.execute(
                    select(TestCase).where(
                        TestCase.phase_id == req_phase.phase_id
                    )
                )
                test_case_list = list(test_cases.scalars())
                print(f"Test Cases: {len(test_case_list)}")
                for tc in test_case_list[:3]:  # Show first 3
                    print(f"  - {tc.test_case_id[:8]}... attribute={tc.attribute_name}")
            else:
                print("\nNo Request Info Phase found")
            
            # Check test executions
            test_execs = await db.execute(
                select(TestExecution).where(
                    TestExecution.cycle_id == cycle_id,
                    TestExecution.report_id == report_id
                )
            )
            
            print(f"\nTest Executions: {len(list(test_execs.scalars()))}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_data())