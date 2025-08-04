#!/usr/bin/env python3
"""
Script to create comprehensive test data for all workflow phases
Creates specific test data expected by comprehensive_test.py
"""

import asyncio
import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.core.auth import get_password_hash
from app.models.lob import LOB
from app.models.user import User
from app.models.report import Report
from app.models.test_cycle import TestCycle
from app.models.cycle_report import CycleReport
from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.models.sample_selection import SampleSet, SampleRecord
from app.models.request_info import TestCase
from app.models.testing import DataProviderAssignment
from app.models.test_execution import TestingTestExecution as TestExecution
from app.models.observation_management import ObservationRecord as Observation
from app.models.sla import SLAConfiguration
from app.models.rbac import Permission, Role
from app.models.audit import AuditLog


async def clear_existing_data(db: AsyncSession):
    """Clear existing test data to ensure clean state"""
    print("Clearing existing test data...")
    
    # Clear in reverse dependency order
    tables_to_clear = [
        Observation,
        TestExecution,
        DataProviderAssignment,
        TestCase,
        SampleRecord,
        SampleSet,
        ReportAttribute,
        WorkflowPhase,
        CycleReport,
        TestCycle,
        Report,
        User,
        LOB,
        SLAConfiguration,
        AuditLog
    ]
    
    for table in tables_to_clear:
        await db.execute(delete(table))
    
    await db.commit()
    print("✅ Cleared existing test data")


async def create_comprehensive_test_data():
    """Create comprehensive test data for all workflow phases"""
    print("Creating comprehensive test data...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Clear existing data first
            await clear_existing_data(db)
            
            # Create LOBs
            lobs_data = [
                {"lob_id": 1, "lob_name": "Retail Banking"},
                {"lob_id": 2, "lob_name": "Commercial Banking"},
                {"lob_id": 3, "lob_name": "Investment Banking"},
                {"lob_id": 4, "lob_name": "Risk Management"},
                {"lob_id": 5, "lob_name": "Compliance"}
            ]
            
            lobs = []
            for lob_data in lobs_data:
                lob = LOB(**lob_data)
                db.add(lob)
                lobs.append(lob)
            
            await db.flush()
            print(f"✅ Created {len(lobs_data)} LOBs")
            
            # Create Users (matching test users from comprehensive_test.py)
            users_data = [
                {
                    "user_id": 1,
                    "first_name": "Admin",
                    "last_name": "User",
                    "email": "admin@synapsedt.com",
                    "phone": "+1-555-0001",
                    "role": "Admin",
                    "lob_id": None,
                    "is_active": True,
                    "hashed_password": get_password_hash("TestUser123!")
                },
                {
                    "user_id": 2,
                    "first_name": "Test",
                    "last_name": "Manager",
                    "email": "testmgr@synapse.com",
                    "phone": "+1-555-0002",
                    "role": "Test Executive",
                    "lob_id": None,
                    "is_active": True,
                    "hashed_password": get_password_hash("TestUser123!")
                },
                {
                    "user_id": 3,
                    "first_name": "Test",
                    "last_name": "User",
                    "email": "tester@synapse.com",
                    "phone": "+1-555-0003",
                    "role": "Tester",
                    "lob_id": 1,  # Retail Banking
                    "is_active": True,
                    "hashed_password": get_password_hash("TestUser123!")
                },
                {
                    "user_id": 4,
                    "first_name": "Report",
                    "last_name": "Owner",
                    "email": "owner@synapse.com",
                    "phone": "+1-555-0004",
                    "role": "Report Owner",
                    "lob_id": None,
                    "is_active": True,
                    "hashed_password": get_password_hash("TestUser123!")
                },
                {
                    "user_id": 5,
                    "first_name": "Report",
                    "last_name": "Executive",
                    "email": "exec@synapse.com",
                    "phone": "+1-555-0005",
                    "role": "Report Owner Executive",
                    "lob_id": None,
                    "is_active": True,
                    "hashed_password": get_password_hash("TestUser123!")
                },
                {
                    "user_id": 6,
                    "first_name": "Data",
                    "last_name": "Provider",
                    "email": "provider@synapse.com",
                    "phone": "+1-555-0006",
                    "role": "Data Owner",
                    "lob_id": 1,  # Retail Banking
                    "is_active": True,
                    "hashed_password": get_password_hash("TestUser123!")
                },
                {
                    "user_id": 7,
                    "first_name": "Chief Data",
                    "last_name": "Officer",
                    "email": "cdo@synapse.com",
                    "phone": "+1-555-0007",
                    "role": "Data Executive",
                    "lob_id": 1,  # Retail Banking
                    "is_active": True,
                    "hashed_password": get_password_hash("TestUser123!")
                }
            ]
            
            users = []
            for user_data in users_data:
                user = User(**user_data)
                db.add(user)
                users.append(user)
            
            await db.flush()
            print(f"✅ Created {len(users_data)} users")
            
            # Create Reports
            reports_data = [
                {
                    "report_id": 1,
                    "report_name": "CCAR Stress Testing Report",
                    "regulation": "Federal Reserve CCAR",
                    "report_owner_id": 4,  # Report Owner
                    "lob_id": 1  # Retail Banking
                },
                {
                    "report_id": 2,
                    "report_name": "Basel III Capital Adequacy Report",
                    "regulation": "Basel III",
                    "report_owner_id": 4,  # Report Owner
                    "lob_id": 2  # Commercial Banking
                },
                {
                    "report_id": 3,
                    "report_name": "Liquidity Coverage Ratio Report",
                    "regulation": "Basel III LCR",
                    "report_owner_id": 4,  # Report Owner
                    "lob_id": 3  # Investment Banking
                }
            ]
            
            reports = []
            for report_data in reports_data:
                report = Report(**report_data)
                db.add(report)
                reports.append(report)
            
            await db.flush()
            print(f"✅ Created {len(reports_data)} reports")
            
            # Create Test Cycles
            test_cycles_data = [
                {
                    "cycle_id": 1,
                    "cycle_name": "Q4 2024 Regulatory Testing Cycle",
                    "start_date": date(2024, 10, 1),
                    "end_date": date(2024, 12, 31),
                    "test_manager_id": 2,  # Test Manager
                    "status": "Active"
                },
                {
                    "cycle_id": 2,
                    "cycle_name": "Q1 2025 Regulatory Testing Cycle",
                    "start_date": date(2025, 1, 1),
                    "end_date": date(2025, 3, 31),
                    "test_manager_id": 2,  # Test Manager
                    "status": "Pending"
                }
            ]
            
            test_cycles = []
            for cycle_data in test_cycles_data:
                cycle = TestCycle(**cycle_data)
                db.add(cycle)
                test_cycles.append(cycle)
            
            await db.flush()
            print(f"✅ Created {len(test_cycles_data)} test cycles")
            
            # Create CycleReports (link cycles to reports)
            cycle_reports = []
            for cycle_id in [1, 2]:
                for report_id in [1, 2, 3]:
                    cycle_report = CycleReport(
                        cycle_id=cycle_id,
                        report_id=report_id
                    )
                    db.add(cycle_report)
                    cycle_reports.append(cycle_report)
            
            await db.flush()
            print(f"✅ Created {len(cycle_reports)} cycle-report associations")
            
            # Create Workflow Phases for cycle 1
            workflow_phases = []
            phases = [
                ("Planning", "COMPLETED", "Phase 1: Planning"),
                ("Scoping", "IN_PROGRESS", "Phase 2: Scoping"),
                ("Data Owner Identification", "NOT_STARTED", "Phase 3: Data Provider ID"),
                ("Sample Selection", "NOT_STARTED", "Phase 4: Sample Selection"),
                ("Request for Information", "NOT_STARTED", "Phase 5: Request Info"),
                ("Testing Execution", "NOT_STARTED", "Phase 6: Testing"),
                ("Observation Management", "NOT_STARTED", "Phase 7: Observations")
            ]
            
            for i, (phase_name, status, description) in enumerate(phases, 1):
                for report_id in [1, 2, 3]:
                    phase = WorkflowPhase(
                        cycle_id=1,
                        report_id=report_id,
                        phase_name=phase_name,
                        status=status,
                        state="active" if status == "IN_PROGRESS" else "complete" if status == "COMPLETED" else "pending",
                        description=description,
                        assigned_to_id=3 if phase_name in ["Planning", "Scoping"] else None,  # Assign to Tester
                        started_at=datetime.utcnow() if status in ["COMPLETED", "IN_PROGRESS"] else None,
                        completed_at=datetime.utcnow() if status == "COMPLETED" else None
                    )
                    db.add(phase)
                    workflow_phases.append(phase)
            
            await db.flush()
            print(f"✅ Created {len(workflow_phases)} workflow phases")
            
            # Create Report Attributes for report 1
            attributes_data = [
                {
                    "report_id": 1,
                    "attribute_name": "Total Assets",
                    "attribute_type": "Monetary",
                    "description": "Total assets of the institution",
                    "is_critical": True,
                    "expected_value": "1000000000.00",
                    "tolerance_percentage": Decimal("5.0")
                },
                {
                    "report_id": 1,
                    "attribute_name": "Risk-Weighted Assets",
                    "attribute_type": "Monetary",
                    "description": "Risk-weighted assets calculation",
                    "is_critical": True,
                    "expected_value": "750000000.00",
                    "tolerance_percentage": Decimal("3.0")
                },
                {
                    "report_id": 1,
                    "attribute_name": "Tier 1 Capital Ratio",
                    "attribute_type": "Percentage",
                    "description": "Tier 1 capital adequacy ratio",
                    "is_critical": True,
                    "expected_value": "12.5",
                    "tolerance_percentage": Decimal("1.0")
                }
            ]
            
            attributes = []
            for i, attr_data in enumerate(attributes_data, 1):
                attr = ReportAttribute(attribute_id=i, **attr_data)
                db.add(attr)
                attributes.append(attr)
            
            await db.flush()
            print(f"✅ Created {len(attributes_data)} report attributes")
            
            # Create Sample Selections
            sample_selections = []
            for i, attr in enumerate(attributes, 1):
                sample = SampleSelection(
                    attribute_id=attr.attribute_id,
                    sample_identifier=f"SAMPLE-{i:03d}",
                    sample_description=f"Sample for {attr.attribute_name}",
                    selected_by_id=3,  # Tester
                    selected_date=datetime.utcnow()
                )
                db.add(sample)
                sample_selections.append(sample)
            
            await db.flush()
            print(f"✅ Created {len(sample_selections)} sample selections")
            
            # Create Test Cases
            test_cases = []
            for i, sample in enumerate(sample_selections, 1):
                test_case = TestCase(
                    test_case_id=i,
                    sample_id=sample.sample_id,
                    test_name=f"Test Case {i}",
                    test_description=f"Test case for sample {sample.sample_identifier}",
                    test_type="Database",
                    query_string=f"SELECT value FROM financial_data WHERE id = '{sample.sample_identifier}'",
                    expected_result=attributes[i-1].expected_value,
                    created_by_id=3  # Tester
                )
                db.add(test_case)
                test_cases.append(test_case)
            
            await db.flush()
            print(f"✅ Created {len(test_cases)} test cases")
            
            # Create Data Owner Assignments
            assignments = []
            for test_case in test_cases:
                assignment = DataOwnerAssignment(
                    test_case_id=test_case.test_case_id,
                    assigned_by_id=7,  # CDO
                    assigned_to_id=6,  # Data Provider
                    assigned_date=datetime.utcnow(),
                    status="Pending"
                )
                db.add(assignment)
                assignments.append(assignment)
            
            await db.flush()
            print(f"✅ Created {len(assignments)} data owner assignments")
            
            # Create Test Executions (for first test case only)
            test_execution = TestExecution(
                test_case_id=1,
                run_number=1,
                executed_by_id=3,  # Tester
                execution_date=datetime.utcnow(),
                status="Passed",
                actual_result=attributes[0].expected_value,
                comments="Test executed successfully"
            )
            db.add(test_execution)
            
            await db.flush()
            print("✅ Created test execution")
            
            # Create Observations
            observation = Observation(
                cycle_id=1,
                report_id=1,
                issue_description="Minor discrepancy in risk calculation",
                severity="Low",
                reported_by_id=3,  # Tester
                reported_date=datetime.utcnow(),
                status="Open",
                assigned_to_id=4  # Report Owner
            )
            db.add(observation)
            
            await db.flush()
            print("✅ Created observation")
            
            # Create SLA Configurations
            sla_configs = [
                {
                    "phase_name": "Planning",
                    "role": "Tester",
                    "sla_hours": 48,
                    "warning_threshold_hours": 24,
                    "escalation_role": "Test Executive"
                },
                {
                    "phase_name": "Scoping",
                    "role": "Tester",
                    "sla_hours": 72,
                    "warning_threshold_hours": 48,
                    "escalation_role": "Test Executive"
                },
                {
                    "phase_name": "Data Owner Identification",
                    "role": "Data Executive",
                    "sla_hours": 24,
                    "warning_threshold_hours": 12,
                    "escalation_role": "Test Executive"
                },
                {
                    "phase_name": "Sample Selection",
                    "role": "Tester",
                    "sla_hours": 48,
                    "warning_threshold_hours": 24,
                    "escalation_role": "Test Executive"
                },
                {
                    "phase_name": "Request for Information",
                    "role": "Data Owner",
                    "sla_hours": 120,
                    "warning_threshold_hours": 96,
                    "escalation_role": "Data Executive"
                },
                {
                    "phase_name": "Testing Execution",
                    "role": "Tester",
                    "sla_hours": 168,
                    "warning_threshold_hours": 144,
                    "escalation_role": "Test Executive"
                },
                {
                    "phase_name": "Observation Management",
                    "role": "Report Owner",
                    "sla_hours": 72,
                    "warning_threshold_hours": 48,
                    "escalation_role": "Report Owner Executive"
                }
            ]
            
            for sla_data in sla_configs:
                sla = SLAConfiguration(**sla_data)
                db.add(sla)
            
            await db.flush()
            print(f"✅ Created {len(sla_configs)} SLA configurations")
            
            # Create sample notifications
            notifications_data = [
                {
                    "user_id": 3,  # Tester
                    "title": "New Scoping Task Assigned",
                    "message": "You have been assigned to scope the CCAR Stress Testing Report",
                    "type": "assignment",
                    "priority": "medium",
                    "created_at": datetime.utcnow() - timedelta(hours=2),
                    "is_read": True
                },
                {
                    "user_id": 3,  # Tester
                    "title": "Planning Phase Completed",
                    "message": "Planning phase for Basel III Capital Adequacy Report has been completed",
                    "type": "workflow",
                    "priority": "low",
                    "created_at": datetime.utcnow() - timedelta(hours=1),
                    "is_read": False
                },
                {
                    "user_id": 4,  # Report Owner
                    "title": "New Observation Reported",
                    "message": "A new observation has been reported for your review",
                    "type": "observation",
                    "priority": "high",
                    "created_at": datetime.utcnow() - timedelta(minutes=30),
                    "is_read": False
                }
            ]
            
            for notif_data in notifications_data:
                notification = Notification(**notif_data)
                db.add(notification)
            
            await db.flush()
            print(f"✅ Created {len(notifications_data)} notifications")
            
            # Commit all changes
            await db.commit()
            
            print("\n🎉 Comprehensive test data creation completed successfully!")
            print("\nTest Users Created:")
            print("- Admin: admin@synapsedt.com / TestUser123!")
            print("- Test Executive: testmgr@synapse.com / TestUser123!")
            print("- Tester: tester@synapse.com / TestUser123!")
            print("- Report Owner: owner@synapse.com / TestUser123!")
            print("- Report Owner Executive: exec@synapse.com / TestUser123!")
            print("- Data Owner: provider@synapse.com / TestUser123!")
            print("- Data Executive: cdo@synapse.com / TestUser123!")
            print("\nTest Data Created:")
            print(f"- Test Cycles: {len(test_cycles)}")
            print(f"- Reports: {len(reports)}")
            print(f"- Workflow Phases: {len(workflow_phases)}")
            print(f"- Report Attributes: {len(attributes)}")
            print(f"- Sample Selections: {len(sample_selections)}")
            print(f"- Test Cases: {len(test_cases)}")
            print(f"- Data Owner Assignments: {len(assignments)}")
            print("\nKey IDs for Testing:")
            print("- Cycle ID: 1 (Active)")
            print("- Report ID: 1 (CCAR Stress Testing Report)")
            print("- Sample IDs: 1, 2, 3")
            print("- Test Case IDs: 1, 2, 3")
            
        except Exception as e:
            print(f"❌ Error creating comprehensive test data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_comprehensive_test_data())