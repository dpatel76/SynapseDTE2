#!/usr/bin/env python3
"""
Script to create test data specifically for comprehensive_test.py
Creates cycles, reports, and users with expected IDs
"""

import asyncio
import sys
import os
from datetime import date, datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.core.auth import get_password_hash
from app.models.lob import LOB
from app.models.user import User
from app.models.report import Report
from app.models.test_cycle import TestCycle
from app.models.cycle_report import CycleReport
from app.models.workflow import WorkflowPhase


async def ensure_test_users_exist(db: AsyncSession):
    """Ensure all test users exist"""
    print("Ensuring test users exist...")
    
    test_users = [
        ("admin@synapsedt.com", "Admin", "User", "Admin", None),
        ("testmgr@synapse.com", "Test", "Manager", "Test Executive", None),
        ("tester@synapse.com", "Test", "User", "Tester", 1),
        ("owner@synapse.com", "Report", "Owner", "Report Owner", None),
        ("exec@synapse.com", "Report", "Executive", "Report Owner Executive", None),
        ("provider@synapse.com", "Data", "Provider", "Data Owner", 1),
        ("cdo@synapse.com", "Chief Data", "Officer", "Data Executive", 1)
    ]
    
    for email, first_name, last_name, role, lob_id in test_users:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                lob_id=lob_id,
                phone=f"+1-555-{email[:4]}",
                is_active=True,
                hashed_password=get_password_hash("TestUser123!")
            )
            db.add(user)
            print(f"  Created user: {email}")
        else:
            print(f"  User exists: {email}")
    
    await db.commit()


async def ensure_lobs_exist(db: AsyncSession):
    """Ensure LOBs exist"""
    print("Ensuring LOBs exist...")
    
    lob_names = ["Retail Banking", "Commercial Banking", "Investment Banking", "Risk Management", "Compliance"]
    
    for lob_name in lob_names:
        result = await db.execute(select(LOB).where(LOB.lob_name == lob_name))
        lob = result.scalar_one_or_none()
        
        if not lob:
            lob = LOB(lob_name=lob_name)
            db.add(lob)
            print(f"  Created LOB: {lob_name}")
        else:
            print(f"  LOB exists: {lob_name}")
    
    await db.commit()


async def ensure_test_cycle_exists(db: AsyncSession):
    """Ensure test cycle with ID 1 exists"""
    print("Ensuring test cycle exists...")
    
    # Get test manager user
    result = await db.execute(select(User).where(User.email == "testmgr@synapse.com"))
    test_manager = result.scalar_one_or_none()
    
    if not test_manager:
        print("❌ Test manager user not found!")
        return None
    
    # Check if cycle exists
    result = await db.execute(select(TestCycle).where(TestCycle.cycle_id == 1))
    cycle = result.scalar_one_or_none()
    
    if not cycle:
        # Try to create with specific ID
        try:
            await db.execute(text("INSERT INTO test_cycles (cycle_id, cycle_name, start_date, end_date, test_manager_id, status) "
                                  "VALUES (1, :name, :start, :end, :manager_id, :status)"),
                             {"name": "Q4 2024 Regulatory Testing Cycle",
                              "start": date(2024, 10, 1),
                              "end": date(2024, 12, 31),
                              "manager_id": test_manager.user_id,
                              "status": "Active"})
            await db.commit()
            print(f"  Created test cycle with ID 1")
        except Exception as e:
            await db.rollback()
            # If specific ID fails, create normally
            cycle = TestCycle(
                cycle_name="Q4 2024 Regulatory Testing Cycle",
                start_date=date(2024, 10, 1),
                end_date=date(2024, 12, 31),
                test_manager_id=test_manager.user_id,
                status="Active"
            )
            db.add(cycle)
            await db.commit()
            print(f"  Created test cycle (ID will be auto-assigned)")
    else:
        print(f"  Test cycle exists with ID 1")
    
    return cycle


async def ensure_report_exists(db: AsyncSession):
    """Ensure report with ID 1 exists"""
    print("Ensuring report exists...")
    
    # Get report owner
    result = await db.execute(select(User).where(User.email == "owner@synapse.com"))
    report_owner = result.scalar_one_or_none()
    
    # Get Retail Banking LOB
    result = await db.execute(select(LOB).where(LOB.lob_name == "Retail Banking"))
    lob = result.scalar_one_or_none()
    
    if not report_owner or not lob:
        print("❌ Report owner or LOB not found!")
        return None
    
    # Check if report exists
    result = await db.execute(select(Report).where(Report.report_id == 1))
    report = result.scalar_one_or_none()
    
    if not report:
        # Try to create with specific ID
        try:
            await db.execute(text("INSERT INTO reports (report_id, report_name, regulation, report_owner_id, lob_id) "
                                  "VALUES (1, :name, :reg, :owner_id, :lob_id)"),
                             {"name": "CCAR Stress Testing Report",
                              "reg": "Federal Reserve CCAR",
                              "owner_id": report_owner.user_id,
                              "lob_id": lob.lob_id})
            await db.commit()
            print(f"  Created report with ID 1")
        except Exception as e:
            await db.rollback()
            # If specific ID fails, create normally
            report = Report(
                report_name="CCAR Stress Testing Report",
                regulation="Federal Reserve CCAR",
                report_owner_id=report_owner.user_id,
                lob_id=lob.lob_id
            )
            db.add(report)
            await db.commit()
            print(f"  Created report (ID will be auto-assigned)")
    else:
        print(f"  Report exists with ID 1")
    
    return report


async def ensure_cycle_report_exists(db: AsyncSession):
    """Ensure cycle-report association exists"""
    print("Ensuring cycle-report association exists...")
    
    # Check if both cycle 1 and report 1 exist
    cycle_result = await db.execute(select(TestCycle).where(TestCycle.cycle_id == 1))
    cycle = cycle_result.scalar_one_or_none()
    
    report_result = await db.execute(select(Report).where(Report.report_id == 1))
    report = report_result.scalar_one_or_none()
    
    if not cycle or not report:
        # Get any cycle and report
        cycle_result = await db.execute(select(TestCycle).limit(1))
        cycle = cycle_result.scalar_one_or_none()
        
        report_result = await db.execute(select(Report).limit(1))
        report = report_result.scalar_one_or_none()
        
        if not cycle or not report:
            print("❌ No cycles or reports found!")
            return
    
    # Check if association exists
    result = await db.execute(
        select(CycleReport).where(
            (CycleReport.cycle_id == cycle.cycle_id) & 
            (CycleReport.report_id == report.report_id)
        )
    )
    cycle_report = result.scalar_one_or_none()
    
    if not cycle_report:
        cycle_report = CycleReport(
            cycle_id=cycle.cycle_id,
            report_id=report.report_id
        )
        db.add(cycle_report)
        await db.commit()
        print(f"  Created cycle-report association: Cycle {cycle.cycle_id} - Report {report.report_id}")
    else:
        print(f"  Cycle-report association exists")


async def ensure_workflow_phases_exist(db: AsyncSession):
    """Ensure workflow phases exist for testing"""
    print("Ensuring workflow phases exist...")
    
    # Get first cycle and report
    cycle_result = await db.execute(select(TestCycle).limit(1))
    cycle = cycle_result.scalar_one_or_none()
    
    report_result = await db.execute(select(Report).limit(1))
    report = report_result.scalar_one_or_none()
    
    if not cycle or not report:
        print("❌ No cycles or reports found!")
        return
    
    # Get tester user
    tester_result = await db.execute(select(User).where(User.email == "tester@synapse.com"))
    tester = tester_result.scalar_one_or_none()
    
    # Define phases
    phases = [
        ("Planning", "Complete", "On Track"),
        ("Scoping", "In Progress", "On Track"),
        ("Data Provider ID", "Not Started", "On Track"),
        ("Sample Selection", "Not Started", "On Track"),
        ("Request Info", "Not Started", "On Track"),
        ("Testing", "Not Started", "On Track"),
        ("Observations", "Not Started", "On Track")
    ]
    
    for phase_name, state, schedule_status in phases:
        # Check if phase exists
        result = await db.execute(
            select(WorkflowPhase).where(
                (WorkflowPhase.cycle_id == cycle.cycle_id) & 
                (WorkflowPhase.report_id == report.report_id) & 
                (WorkflowPhase.phase_name == phase_name)
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            phase = WorkflowPhase(
                cycle_id=cycle.cycle_id,
                report_id=report.report_id,
                phase_name=phase_name,
                state=state,
                schedule_status=schedule_status,
                status="Complete" if state == "Complete" else "In Progress" if state == "In Progress" else "Not Started",
                started_by=tester.user_id if tester and state != "Not Started" else None,
                actual_start_date=datetime.utcnow() if state != "Not Started" else None,
                completed_by=tester.user_id if tester and state == "Complete" else None,
                actual_end_date=datetime.utcnow() if state == "Complete" else None
            )
            db.add(phase)
            print(f"  Created workflow phase: {phase_name}")
        else:
            print(f"  Workflow phase exists: {phase_name}")
    
    await db.commit()


async def create_test_data():
    """Create test data for comprehensive tests"""
    print("Creating test data for comprehensive tests...")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Create data in order
            await ensure_lobs_exist(db)
            await ensure_test_users_exist(db)
            await ensure_test_cycle_exists(db)
            await ensure_report_exists(db)
            await ensure_cycle_report_exists(db)
            await ensure_workflow_phases_exist(db)
            
            print("\n✅ Test data creation completed successfully!")
            print("\nTest Users:")
            print("- Admin: admin@synapsedt.com / TestUser123!")
            print("- Test Executive: testmgr@synapse.com / TestUser123!")
            print("- Tester: tester@synapse.com / TestUser123!")
            print("- Report Owner: owner@synapse.com / TestUser123!")
            print("- Report Owner Executive: exec@synapse.com / TestUser123!")
            print("- Data Owner: provider@synapse.com / TestUser123!")
            print("- Data Executive: cdo@synapse.com / TestUser123!")
            
        except Exception as e:
            print(f"❌ Error creating test data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_test_data())