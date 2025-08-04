"""Finalize Test Report Phase Activities for Temporal Workflow

Standard structure:
1. Start Finalize Test Report Phase (Tester initiated)
2. Finalize Test Report-specific activities
3. Complete Finalize Test Report Phase (Tester initiated)
"""

from temporalio import activity
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import json
from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import (
    WorkflowPhase, TestCycle, Report, CycleReport,
    ReportAttribute, User, TestExecution
)
from app.models.request_info import CycleReportTestCase
# Observation enhanced models removed - use observation_management models
from app.temporal.shared import ActivityResult

logger = logging.getLogger(__name__)


@activity.defn
async def start_finalize_report_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> ActivityResult:
    """Start Finalize Test Report Phase - Initiated by Tester
    
    This is the standard entry point for the Finalize Test Report phase.
    Validates user permissions and initializes phase.
    """
    try:
        async with get_db() as db:
            # Verify user has permission to start phase
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to start Finalize Test Report phase"
                )
            
            # Get or create workflow phase record
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Finalize Test Report"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                # Create phase record
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Finalize Test Report",
                    state="In Progress",
                    status="On Schedule",
                    actual_start_date=datetime.utcnow(),
                    started_by=user_id
                )
                db.add(phase)
            else:
                # Update existing phase
                phase.state = "In Progress"
                phase.actual_start_date = datetime.utcnow()
                phase.started_by = user_id
            
            await db.commit()
            
            logger.info(f"Started Finalize Test Report phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "started_at": phase.actual_start_date.isoformat(),
                    "started_by": user_id
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to start Finalize Test Report phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def consolidate_test_results_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Consolidate all test results and metrics
    
    Finalize Test Report-specific activity that aggregates results
    """
    try:
        async with get_db() as db:
            # Get test execution statistics
            test_stats = await db.execute(
                select(
                    func.count(TestExecution.execution_id).label("total_tests"),
                    func.sum(func.cast(TestExecution.test_result == "Pass", int)).label("passed"),
                    func.sum(func.cast(TestExecution.test_result == "Fail", int)).label("failed"),
                    func.avg(TestExecution.execution_time).label("avg_execution_time")
                ).join(
                    TestCase, TestCase.test_case_id == TestExecution.test_case_id
                ).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id
                    )
                )
            )
            stats = test_stats.one()
            
            # Get attribute coverage
            total_attributes = await db.execute(
                select(func.count(ReportAttribute.attribute_id)).where(
                    ReportAttribute.report_id == report_id
                )
            )
            attribute_count = total_attributes.scalar()
            
            tested_attributes = await db.execute(
                select(func.count(func.distinct(TestCase.attribute_id))).join(
                    TestExecution, TestExecution.test_case_id == TestCase.test_case_id
                ).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id
                    )
                )
            )
            tested_count = tested_attributes.scalar()
            
            # Get cycle report
            cycle_report = await db.execute(
                select(CycleReport).where(
                    and_(
                        CycleReport.cycle_id == cycle_id,
                        CycleReport.report_id == report_id
                    )
                )
            )
            cycle_report_obj = cycle_report.scalar_one_or_none()
            
            # Get observation count
            observation_count = 0
            if cycle_report_obj:
                obs_count = await db.execute(
                    select(func.count(Observation.observation_id)).where(
                        Observation.cycle_report_id == cycle_report_obj.cycle_report_id
                    )
                )
                observation_count = obs_count.scalar()
            
            # Calculate metrics
            pass_rate = (stats.passed / stats.total_tests * 100) if stats.total_tests else 0
            coverage_rate = (tested_count / attribute_count * 100) if attribute_count else 0
            
            consolidated_results = {
                "test_execution": {
                    "total_tests": stats.total_tests or 0,
                    "tests_passed": stats.passed or 0,
                    "tests_failed": stats.failed or 0,
                    "pass_rate": round(pass_rate, 1),
                    "avg_execution_time": round(stats.avg_execution_time or 0, 2)
                },
                "coverage": {
                    "total_attributes": attribute_count,
                    "tested_attributes": tested_count,
                    "coverage_rate": round(coverage_rate, 1)
                },
                "observations": {
                    "total_observations": observation_count,
                    "require_remediation": stats.failed or 0
                }
            }
            
            logger.info(f"Consolidated test results: {stats.total_tests} tests, {pass_rate:.1f}% pass rate")
            return ActivityResult(
                success=True,
                data=consolidated_results
            )
            
    except Exception as e:
        logger.error(f"Failed to consolidate test results: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def generate_final_report_activity(
    cycle_id: int,
    report_id: int,
    consolidated_data: Dict[str, Any]
) -> ActivityResult:
    """Generate the final test report document
    
    Finalize Test Report-specific activity that creates report
    """
    try:
        async with get_db() as db:
            # Get report and cycle details
            report = await db.get(Report, report_id)
            cycle = await db.get(TestCycle, cycle_id)
            
            if not report or not cycle:
                return ActivityResult(
                    success=False,
                    error="Report or cycle not found"
                )
            
            # Get cycle report
            cycle_report = await db.execute(
                select(CycleReport).where(
                    and_(
                        CycleReport.cycle_id == cycle_id,
                        CycleReport.report_id == report_id
                    )
                )
            )
            cycle_report_obj = cycle_report.scalar_one_or_none()
            
            if not cycle_report_obj:
                return ActivityResult(
                    success=False,
                    error="Cycle report not found"
                )
            
            # Create test report
            test_report = TestReport(
                cycle_report_id=cycle_report_obj.cycle_report_id,
                report_name=f"{report.report_name} - {cycle.cycle_name} Test Report",
                report_type="final",
                status="Draft",
                executive_summary=f"Testing completed for {report.report_name} with "
                                f"{consolidated_data['test_execution']['pass_rate']}% pass rate. "
                                f"Total of {consolidated_data['test_execution']['total_tests']} tests executed "
                                f"covering {consolidated_data['coverage']['coverage_rate']}% of attributes.",
                test_summary=consolidated_data['test_execution'],
                coverage_summary=consolidated_data['coverage'],
                observation_summary=consolidated_data['observations'],
                recommendations=[
                    "Address all critical observations before production deployment",
                    "Retest failed test cases after remediation",
                    "Implement automated testing for recurring test scenarios"
                ],
                generated_at=datetime.utcnow(),
                generated_by=1  # System user
            )
            db.add(test_report)
            await db.commit()
            
            logger.info(f"Generated final test report: {test_report.report_name}")
            return ActivityResult(
                success=True,
                data={
                    "report_id": test_report.test_report_id,
                    "report_name": test_report.report_name,
                    "status": test_report.status,
                    "executive_summary": test_report.executive_summary
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to generate final report: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def request_executive_approval_activity(
    cycle_id: int,
    report_id: int,
    report_data: Dict[str, Any]
) -> ActivityResult:
    """Request executive approval for the report
    
    Finalize Test Report-specific activity that initiates approval workflow
    """
    try:
        async with get_db() as db:
            # Get report executives
            report_obj = await db.get(Report, report_id)
            if not report_obj:
                return ActivityResult(
                    success=False,
                    error="Report not found"
                )
            
            # Find Report Owner Executive users
            executives = await db.execute(
                select(User).where(
                    and_(
                        User.role == "Report Owner Executive",
                        User.is_active == True
                    )
                )
            )
            executive_list = executives.scalars().all()
            
            if not executive_list:
                return ActivityResult(
                    success=False,
                    error="No Report Owner Executives found for approval"
                )
            
            # Create approval requests
            approvals_created = []
            for executive in executive_list[:2]:  # Limit to 2 executives for demo
                approval = ReportApproval(
                    test_report_id=report_data["report_id"],
                    approver_id=executive.user_id,
                    approval_type="executive",
                    status="Pending",
                    requested_at=datetime.utcnow(),
                    due_date=datetime.utcnow() + timedelta(days=2)
                )
                db.add(approval)
                
                approvals_created.append({
                    "approver": executive.full_name,
                    "email": executive.email,
                    "due_date": approval.due_date.isoformat()
                })
            
            # Update test report status
            await db.execute(
                update(TestReport).where(
                    TestReport.test_report_id == report_data["report_id"]
                ).values(
                    status="Pending Approval"
                )
            )
            
            await db.commit()
            
            logger.info(f"Requested approval from {len(approvals_created)} executives")
            return ActivityResult(
                success=True,
                data={
                    "approvals_requested": len(approvals_created),
                    "approval_details": approvals_created
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to request executive approval: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def finalize_report_distribution_activity(
    cycle_id: int,
    report_id: int,
    report_data: Dict[str, Any]
) -> ActivityResult:
    """Finalize report and prepare for distribution
    
    Finalize Test Report-specific activity that completes report
    """
    try:
        async with get_db() as db:
            # Update test report as finalized
            await db.execute(
                update(TestReport).where(
                    TestReport.test_report_id == report_data["report_id"]
                ).values(
                    status="Finalized",
                    finalized_at=datetime.utcnow(),
                    distribution_list={
                        "report_owners": ["report-owner@company.com"],
                        "executives": ["executive@company.com"],
                        "testers": ["test-team@company.com"],
                        "stakeholders": ["stakeholder@company.com"]
                    }
                )
            )
            
            # Update cycle report completion
            cycle_report = await db.execute(
                select(CycleReport).where(
                    and_(
                        CycleReport.cycle_id == cycle_id,
                        CycleReport.report_id == report_id
                    )
                )
            )
            cycle_report_obj = cycle_report.scalar_one_or_none()
            
            if cycle_report_obj:
                cycle_report_obj.completion_status = "Completed"
                cycle_report_obj.completed_at = datetime.utcnow()
                cycle_report_obj.final_report_id = report_data["report_id"]
            
            await db.commit()
            
            logger.info(f"Finalized test report and prepared for distribution")
            return ActivityResult(
                success=True,
                data={
                    "report_status": "Finalized",
                    "finalized_at": datetime.utcnow().isoformat(),
                    "distribution_ready": True
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to finalize report distribution: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def complete_finalize_report_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    completion_notes: Optional[str] = None
) -> ActivityResult:
    """Complete Finalize Test Report Phase - Initiated by Tester
    
    This is the standard exit point for the Finalize Test Report phase.
    Validates completion criteria and marks phase as complete.
    """
    try:
        async with get_db() as db:
            # Verify user has permission
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to complete Finalize Test Report phase"
                )
            
            # Get workflow phase
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Finalize Test Report"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                return ActivityResult(
                    success=False,
                    error="Finalize Test Report phase not found"
                )
            
            # Verify test report exists
            cycle_report = await db.execute(
                select(CycleReport).where(
                    and_(
                        CycleReport.cycle_id == cycle_id,
                        CycleReport.report_id == report_id
                    )
                )
            )
            cycle_report_obj = cycle_report.scalar_one_or_none()
            
            test_report_exists = False
            if cycle_report_obj:
                test_report = await db.execute(
                    select(TestReport).where(
                        TestReport.cycle_report_id == cycle_report_obj.cycle_report_id
                    )
                )
                test_report_exists = test_report.scalar_one_or_none() is not None
            
            if not test_report_exists:
                return ActivityResult(
                    success=False,
                    error="Cannot complete phase: Test report not generated"
                )
            
            # Mark phase as complete
            phase.state = "Completed"
            phase.actual_end_date = datetime.utcnow()
            phase.completed_by = user_id
            if completion_notes:
                phase.notes = completion_notes
            
            # Calculate if on schedule
            if phase.planned_end_date and phase.actual_end_date > phase.planned_end_date:
                phase.status = "Behind Schedule"
            else:
                phase.status = "Complete"
            
            # Update test cycle as complete
            await db.execute(
                update(TestCycle).where(
                    TestCycle.cycle_id == cycle_id
                ).values(
                    status="Completed",
                    actual_end_date=datetime.utcnow()
                )
            )
            
            await db.commit()
            
            logger.info(f"Completed Finalize Test Report phase and test cycle for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "completed_at": phase.actual_end_date.isoformat(),
                    "completed_by": user_id,
                    "duration_days": (phase.actual_end_date - phase.actual_start_date).days if phase.actual_start_date else 0,
                    "status": phase.status,
                    "test_cycle_completed": True
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to complete Finalize Test Report phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def execute_finalize_report_activities(
    cycle_id: int,
    report_id: int,
    metadata: Dict[str, Any]
) -> ActivityResult:
    """Execute all Finalize Test Report phase activities in sequence
    
    This orchestrates the finalize report-specific activities between
    start and complete.
    """
    try:
        results = {}
        
        # 1. Consolidate test results
        consolidation_result = await consolidate_test_results_activity(
            cycle_id, report_id
        )
        if not consolidation_result.success:
            return consolidation_result
        results["result_consolidation"] = consolidation_result.data
        
        # 2. Generate final report
        report_result = await generate_final_report_activity(
            cycle_id, report_id, consolidation_result.data
        )
        if not report_result.success:
            return report_result
        results["report_generation"] = report_result.data
        
        # 3. Request executive approval
        approval_result = await request_executive_approval_activity(
            cycle_id, report_id, report_result.data
        )
        if not approval_result.success:
            return approval_result
        results["approval_request"] = approval_result.data
        
        # 4. Finalize for distribution
        distribution_result = await finalize_report_distribution_activity(
            cycle_id, report_id, report_result.data
        )
        if not distribution_result.success:
            return distribution_result
        results["distribution_preparation"] = distribution_result.data
        
        return ActivityResult(
            success=True,
            data={
                "phase": "Finalize Test Report",
                "activities_completed": 4,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to execute finalize report activities: {str(e)}")
        return ActivityResult(success=False, error=str(e))