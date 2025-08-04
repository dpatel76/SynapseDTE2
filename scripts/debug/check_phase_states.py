#!/usr/bin/env python3
"""Check actual phase states in the database"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.workflow import WorkflowPhase
import os
from dotenv import load_dotenv

load_dotenv()

async def check_phase_states():
    """Check phase states for cycle 9, report 156"""
    
    # Create async engine
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/synapse_dte")
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as db:
        # Get all workflow phases for cycle 9, report 156
        result = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == 9,
                WorkflowPhase.report_id == 156
            ).order_by(WorkflowPhase.phase_id)
        )
        phases = result.scalars().all()
        
        print("\n📊 Workflow Phases for Cycle 9, Report 156:")
        print("=" * 80)
        
        for phase in phases:
            print(f"\n{phase.phase_name}:")
            print(f"  - Phase ID: {phase.phase_id}")
            print(f"  - State: {phase.state}")
            print(f"  - Status: {phase.status}")
            print(f"  - Schedule Status: {phase.schedule_status}")
            print(f"  - State Override: {phase.state_override}")
            print(f"  - Status Override: {phase.status_override}")
            print(f"  - Actual Start Date: {phase.actual_start_date}")
            print(f"  - Actual End Date: {phase.actual_end_date}")
            print(f"  - Notes: {phase.notes}")
            
        # Check specific phase activities
        print("\n\n🔍 Checking Phase Activities:")
        print("=" * 80)
        
        # Check Request Info phase
        from app.models.request_info import RequestInfoSubmission, TestCase
        
        result = await db.execute(
            select(RequestInfoSubmission).where(
                RequestInfoSubmission.cycle_id == 9,
                RequestInfoSubmission.report_id == 156
            )
        )
        submissions = result.scalars().all()
        print(f"\nRequest Info Submissions: {len(submissions)}")
        
        result = await db.execute(
            select(TestCase).where(
                TestCase.cycle_id == 9,
                TestCase.report_id == 156
            )
        )
        test_cases = result.scalars().all()
        print(f"Test Cases Generated: {len(test_cases)}")
        
        # Check Testing phase
        from app.models.test_execution import TestExecution
        
        result = await db.execute(
            select(TestExecution).where(
                TestExecution.cycle_id == 9,
                TestExecution.report_id == 156
            )
        )
        test_executions = result.scalars().all()
        print(f"\nTest Executions: {len(test_executions)}")
        if test_executions:
            in_progress = sum(1 for t in test_executions if t.status == 'In Progress')
            completed = sum(1 for t in test_executions if t.status == 'Completed')
            print(f"  - In Progress: {in_progress}")
            print(f"  - Completed: {completed}")
        
        # Check Observations phase
        from app.models.observation_management import Observation
        
        result = await db.execute(
            select(Observation).where(
                Observation.cycle_id == 9,
                Observation.report_id == 156
            )
        )
        observations = result.scalars().all()
        print(f"\nObservations: {len(observations)}")
        if observations:
            draft = sum(1 for o in observations if o.status == 'Draft')
            pending = sum(1 for o in observations if o.status == 'Pending Approval')
            approved = sum(1 for o in observations if o.status == 'Approved')
            print(f"  - Draft: {draft}")
            print(f"  - Pending Approval: {pending}")
            print(f"  - Approved: {approved}")

if __name__ == "__main__":
    asyncio.run(check_phase_states())