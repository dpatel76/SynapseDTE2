#!/usr/bin/env python3
"""Setup test workflow data for comprehensive testing."""

import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
sys.path.append('.')

from app.models.workflow import WorkflowCycle, WorkflowReport, WorkflowPhase
from app.models.user import User

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

TEST_CYCLE_ID = "test_cycle_2025"
TEST_REPORT_ID = "test_report_001"


async def setup_test_workflow():
    """Setup test workflow data."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        try:
            # Get admin user
            admin_query = select(User).where(User.email == "admin@example.com")
            admin_result = await db.execute(admin_query)
            admin_user = admin_result.scalar_one_or_none()
            
            if not admin_user:
                print("Admin user not found! Please run setup_test_users.py first.")
                return
            
            # Check if cycle exists
            cycle_query = select(WorkflowCycle).where(WorkflowCycle.cycle_id == TEST_CYCLE_ID)
            cycle_result = await db.execute(cycle_query)
            cycle = cycle_result.scalar_one_or_none()
            
            if not cycle:
                # Create cycle
                cycle = WorkflowCycle(
                    cycle_id=TEST_CYCLE_ID,
                    cycle_name="Test Cycle 2025",
                    cycle_description="Test cycle for comprehensive testing",
                    start_date=datetime.utcnow(),
                    status="active",
                    created_by_id=admin_user.user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(cycle)
                print(f"Created cycle: {TEST_CYCLE_ID}")
            else:
                print(f"Cycle {TEST_CYCLE_ID} already exists")
            
            # Check if report exists
            report_query = select(WorkflowReport).where(
                (WorkflowReport.cycle_id == TEST_CYCLE_ID) &
                (WorkflowReport.report_id == TEST_REPORT_ID)
            )
            report_result = await db.execute(report_query)
            report = report_result.scalar_one_or_none()
            
            if not report:
                # Create report
                report = WorkflowReport(
                    report_id=TEST_REPORT_ID,
                    cycle_id=TEST_CYCLE_ID,
                    report_name="Test Report 001",
                    report_description="Test report for comprehensive testing",
                    status="active",
                    created_by_id=admin_user.user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(report)
                print(f"Created report: {TEST_REPORT_ID}")
            else:
                print(f"Report {TEST_REPORT_ID} already exists")
            
            # Create phases
            phases = [
                {
                    "phase_name": "Sample Selection",
                    "phase_description": "Sample selection phase for testing",
                    "sequence_order": 1
                },
                {
                    "phase_name": "Scoping", 
                    "phase_description": "Scoping phase for testing",
                    "sequence_order": 2
                },
                {
                    "phase_name": "Data Profiling",
                    "phase_description": "Data profiling phase for testing", 
                    "sequence_order": 3
                }
            ]
            
            for phase_data in phases:
                # Check if phase exists
                phase_query = select(WorkflowPhase).where(
                    (WorkflowPhase.cycle_id == TEST_CYCLE_ID) &
                    (WorkflowPhase.report_id == TEST_REPORT_ID) &
                    (WorkflowPhase.phase_name == phase_data["phase_name"])
                )
                phase_result = await db.execute(phase_query)
                phase = phase_result.scalar_one_or_none()
                
                if not phase:
                    # Create phase
                    phase_id = f"{TEST_CYCLE_ID}_{TEST_REPORT_ID}_{phase_data['phase_name'].lower().replace(' ', '_')}"
                    phase = WorkflowPhase(
                        phase_id=phase_id,
                        cycle_id=TEST_CYCLE_ID,
                        report_id=TEST_REPORT_ID,
                        phase_name=phase_data["phase_name"],
                        phase_description=phase_data["phase_description"],
                        sequence_order=phase_data["sequence_order"],
                        status="active",
                        created_by_id=admin_user.user_id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(phase)
                    print(f"Created phase: {phase_data['phase_name']}")
                else:
                    print(f"Phase {phase_data['phase_name']} already exists")
            
            await db.commit()
            print("\nTest workflow setup completed successfully!")
            
            # Verify setup
            print("\nVerifying workflow setup:")
            
            # Verify cycle
            cycle_query = select(WorkflowCycle).where(WorkflowCycle.cycle_id == TEST_CYCLE_ID)
            cycle_result = await db.execute(cycle_query)
            cycle = cycle_result.scalar_one_or_none()
            if cycle:
                print(f"✓ Cycle: {cycle.cycle_name}")
            
            # Verify report
            report_query = select(WorkflowReport).where(WorkflowReport.report_id == TEST_REPORT_ID)
            report_result = await db.execute(report_query)
            report = report_result.scalar_one_or_none()
            if report:
                print(f"✓ Report: {report.report_name}")
            
            # Verify phases
            phases_query = select(WorkflowPhase).where(
                (WorkflowPhase.cycle_id == TEST_CYCLE_ID) &
                (WorkflowPhase.report_id == TEST_REPORT_ID)
            ).order_by(WorkflowPhase.sequence_order)
            phases_result = await db.execute(phases_query)
            phases = phases_result.scalars().all()
            
            for phase in phases:
                print(f"✓ Phase: {phase.phase_name} (ID: {phase.phase_id})")
            
        except Exception as e:
            print(f"Error setting up workflow: {str(e)}")
            await db.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(setup_test_workflow())