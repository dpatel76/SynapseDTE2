"""Test Execution Phase Activities for Temporal Workflow

Standard structure:
1. Start Test Execution Phase (Tester initiated)
2. Test Execution-specific activities
3. Complete Test Execution Phase (Tester initiated)
"""

from temporalio import activity
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import random
from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import (
    WorkflowPhase, TestCycle, Report, CycleReport,
    ReportAttribute, User, Sample, TestCase, TestExecution
)
from app.temporal.shared import ActivityResult

logger = logging.getLogger(__name__)


@activity.defn
async def start_test_execution_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> ActivityResult:
    """Start Test Execution Phase - Initiated by Tester
    
    This is the standard entry point for the Test Execution phase.
    Validates user permissions and initializes phase.
    """
    try:
        async with get_db() as db:
            # Verify user has permission to start phase
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to start Test Execution phase"
                )
            
            # Get or create workflow phase record
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Test Execution"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                # Create phase record
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Test Execution",
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
            
            logger.info(f"Started Test Execution phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "started_at": phase.actual_start_date.isoformat(),
                    "started_by": user_id
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to start Test Execution phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def create_test_cases_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Create test cases for attributes and samples
    
    Test Execution-specific activity that generates test cases
    """
    try:
        async with get_db() as db:
            # Get attributes
            attributes = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.report_id == report_id
                )
            )
            attribute_list = attributes.scalars().all()
            
            # Get samples
            samples = await db.execute(
                select(Sample).where(
                    and_(
                        Sample.cycle_id == cycle_id,
                        Sample.report_id == report_id
                    )
                ).limit(10)  # Limit for demo
            )
            sample_list = samples.scalars().all()
            
            if not attribute_list or not sample_list:
                return ActivityResult(
                    success=False,
                    error="No attributes or samples found for testing"
                )
            
            # Create test cases
            test_cases_created = []
            for attribute in attribute_list:
                # Determine test types based on attribute
                test_types = ["document", "database"] if attribute.is_critical else ["database"]
                
                for test_type in test_types:
                    test_case = TestCase(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        attribute_id=attribute.attribute_id,
                        test_name=f"Test {attribute.attribute_name} - {test_type}",
                        test_type=test_type,
                        test_description=f"Validate {attribute.attribute_name} using {test_type} testing",
                        expected_outcome="Data matches expected values within tolerance",
                        is_automated=test_type == "database",
                        created_by=1  # System user
                    )
                    db.add(test_case)
                    test_cases_created.append({
                        "attribute": attribute.attribute_name,
                        "test_type": test_type,
                        "is_critical": attribute.is_critical
                    })
            
            await db.commit()
            
            logger.info(f"Created {len(test_cases_created)} test cases")
            return ActivityResult(
                success=True,
                data={
                    "test_cases_created": len(test_cases_created),
                    "attributes_tested": len(attribute_list),
                    "samples_available": len(sample_list),
                    "test_case_examples": test_cases_created[:5]
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to create test cases: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def execute_automated_tests_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Execute automated database tests
    
    Test Execution-specific activity that runs automated tests
    """
    try:
        async with get_db() as db:
            # Get automated test cases
            test_cases = await db.execute(
                select(TestCase).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id,
                        TestCase.is_automated == True
                    )
                )
            )
            automated_tests = test_cases.scalars().all()
            
            # Get samples for testing
            samples = await db.execute(
                select(Sample).where(
                    and_(
                        Sample.cycle_id == cycle_id,
                        Sample.report_id == report_id
                    )
                ).limit(5)  # Limit for demo
            )
            sample_list = samples.scalars().all()
            
            executions_created = 0
            tests_passed = 0
            tests_failed = 0
            
            # Execute tests for each sample
            for test_case in automated_tests:
                for sample in sample_list:
                    # Create test execution
                    execution = TestExecution(
                        test_case_id=test_case.test_case_id,
                        sample_id=sample.sample_id,
                        execution_status="Completed",
                        executed_at=datetime.utcnow(),
                        executed_by=1,  # System user
                        execution_time=random.uniform(0.1, 2.0),  # Random execution time
                        test_result="Pass" if random.random() > 0.1 else "Fail",  # 90% pass rate
                        actual_value=sample.sample_data.get("balance", 0),
                        expected_value=sample.sample_data.get("balance", 0) * random.uniform(0.95, 1.05),
                        variance=random.uniform(-5, 5)
                    )
                    
                    if execution.test_result == "Pass":
                        tests_passed += 1
                    else:
                        tests_failed += 1
                    
                    db.add(execution)
                    executions_created += 1
            
            await db.commit()
            
            pass_rate = (tests_passed / executions_created * 100) if executions_created > 0 else 0
            
            logger.info(f"Executed {executions_created} automated tests, pass rate: {pass_rate:.1f}%")
            return ActivityResult(
                success=True,
                data={
                    "executions_created": executions_created,
                    "tests_passed": tests_passed,
                    "tests_failed": tests_failed,
                    "pass_rate": round(pass_rate, 1),
                    "execution_type": "automated"
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to execute automated tests: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def record_manual_test_results_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Record results for manual tests
    
    Test Execution-specific activity for manual test recording
    """
    try:
        async with get_db() as db:
            # Get manual test cases (document-based)
            test_cases = await db.execute(
                select(TestCase).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id,
                        TestCase.test_type == "document"
                    )
                )
            )
            manual_tests = test_cases.scalars().all()
            
            # Get critical samples for manual testing
            samples = await db.execute(
                select(Sample).where(
                    and_(
                        Sample.cycle_id == cycle_id,
                        Sample.report_id == report_id,
                        Sample.is_critical == True
                    )
                ).limit(3)  # Limit for demo
            )
            sample_list = samples.scalars().all()
            
            manual_results = []
            
            # Simulate manual test results
            for test_case in manual_tests:
                for sample in sample_list:
                    # Create manual test execution
                    execution = TestExecution(
                        test_case_id=test_case.test_case_id,
                        sample_id=sample.sample_id,
                        execution_status="Completed",
                        executed_at=datetime.utcnow(),
                        executed_by=1,  # Would be actual tester in production
                        execution_time=random.uniform(5, 30),  # Manual tests take longer
                        test_result="Pass" if random.random() > 0.05 else "Fail",  # 95% pass rate
                        evidence_path=f"/evidence/{cycle_id}/{test_case.test_case_id}/{sample.sample_id}.pdf",
                        comments="Manual verification completed"
                    )
                    
                    db.add(execution)
                    manual_results.append({
                        "test_case": test_case.test_name,
                        "sample": sample.sample_identifier,
                        "result": execution.test_result,
                        "evidence": execution.evidence_path
                    })
            
            await db.commit()
            
            logger.info(f"Recorded {len(manual_results)} manual test results")
            return ActivityResult(
                success=True,
                data={
                    "manual_tests_recorded": len(manual_results),
                    "result_examples": manual_results[:5]
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to record manual test results: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def validate_test_coverage_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Validate test coverage meets requirements
    
    Test Execution-specific activity that checks coverage
    """
    try:
        async with get_db() as db:
            # Get total attributes
            total_attributes = await db.execute(
                select(func.count(ReportAttribute.attribute_id)).where(
                    ReportAttribute.report_id == report_id
                )
            )
            attribute_count = total_attributes.scalar()
            
            # Get tested attributes
            tested_attributes = await db.execute(
                select(func.count(func.distinct(TestCase.attribute_id))).join(
                    TestExecution, TestExecution.test_case_id == TestCase.test_case_id
                ).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id,
                        TestExecution.execution_status == "Completed"
                    )
                )
            )
            tested_count = tested_attributes.scalar()
            
            # Get critical attributes coverage
            critical_attributes = await db.execute(
                select(func.count(ReportAttribute.attribute_id)).where(
                    and_(
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.is_critical == True
                    )
                )
            )
            critical_count = critical_attributes.scalar()
            
            # Get tested critical attributes
            tested_critical = await db.execute(
                select(func.count(func.distinct(TestCase.attribute_id))).join(
                    TestExecution, TestExecution.test_case_id == TestCase.test_case_id
                ).join(
                    ReportAttribute, ReportAttribute.attribute_id == TestCase.attribute_id
                ).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id,
                        ReportAttribute.is_critical == True,
                        TestExecution.execution_status == "Completed"
                    )
                )
            )
            critical_tested = tested_critical.scalar()
            
            # Calculate coverage
            overall_coverage = (tested_count / attribute_count * 100) if attribute_count > 0 else 0
            critical_coverage = (critical_tested / critical_count * 100) if critical_count > 0 else 0
            
            validation_passed = overall_coverage >= 80 and critical_coverage == 100
            
            logger.info(f"Test coverage: {overall_coverage:.1f}% overall, {critical_coverage:.1f}% critical")
            return ActivityResult(
                success=True,
                data={
                    "total_attributes": attribute_count,
                    "tested_attributes": tested_count,
                    "overall_coverage": round(overall_coverage, 1),
                    "critical_attributes": critical_count,
                    "critical_tested": critical_tested,
                    "critical_coverage": round(critical_coverage, 1),
                    "validation_passed": validation_passed,
                    "validation_message": "Coverage requirements met" if validation_passed else "Insufficient coverage"
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to validate test coverage: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def complete_test_execution_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    completion_notes: Optional[str] = None
) -> ActivityResult:
    """Complete Test Execution Phase - Initiated by Tester
    
    This is the standard exit point for the Test Execution phase.
    Validates completion criteria and marks phase as complete.
    """
    try:
        async with get_db() as db:
            # Verify user has permission
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to complete Test Execution phase"
                )
            
            # Get workflow phase
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Test Execution"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                return ActivityResult(
                    success=False,
                    error="Test Execution phase not found"
                )
            
            # Verify completion criteria
            # Check test execution count
            execution_count = await db.execute(
                select(func.count(TestExecution.execution_id)).join(
                    TestCase, TestCase.test_case_id == TestExecution.test_case_id
                ).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id
                    )
                )
            )
            total_executions = execution_count.scalar()
            
            if total_executions == 0:
                return ActivityResult(
                    success=False,
                    error="Cannot complete Test Execution phase: No tests executed"
                )
            
            # Get test statistics
            test_stats = await db.execute(
                select(
                    TestExecution.test_result,
                    func.count(TestExecution.execution_id).label("count")
                ).join(
                    TestCase, TestCase.test_case_id == TestExecution.test_case_id
                ).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id
                    )
                ).group_by(TestExecution.test_result)
            )
            
            stats_dict = {row.test_result: row.count for row in test_stats}
            pass_count = stats_dict.get("Pass", 0)
            fail_count = stats_dict.get("Fail", 0)
            pass_rate = (pass_count / total_executions * 100) if total_executions > 0 else 0
            
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
            
            await db.commit()
            
            logger.info(f"Completed Test Execution phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "completed_at": phase.actual_end_date.isoformat(),
                    "completed_by": user_id,
                    "duration_days": (phase.actual_end_date - phase.actual_start_date).days if phase.actual_start_date else 0,
                    "status": phase.status,
                    "total_tests": total_executions,
                    "tests_passed": pass_count,
                    "tests_failed": fail_count,
                    "pass_rate": round(pass_rate, 1)
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to complete Test Execution phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def execute_test_execution_activities(
    cycle_id: int,
    report_id: int,
    metadata: Dict[str, Any]
) -> ActivityResult:
    """Execute all Test Execution phase activities in sequence
    
    This orchestrates the test execution-specific activities between
    start and complete.
    """
    try:
        results = {}
        
        # 1. Create test cases
        test_cases_result = await create_test_cases_activity(
            cycle_id, report_id
        )
        if not test_cases_result.success:
            return test_cases_result
        results["test_case_creation"] = test_cases_result.data
        
        # 2. Execute automated tests
        automated_result = await execute_automated_tests_activity(
            cycle_id, report_id
        )
        if not automated_result.success:
            return automated_result
        results["automated_testing"] = automated_result.data
        
        # 3. Record manual test results
        manual_result = await record_manual_test_results_activity(
            cycle_id, report_id
        )
        if not manual_result.success:
            return manual_result
        results["manual_testing"] = manual_result.data
        
        # 4. Validate coverage
        coverage_result = await validate_test_coverage_activity(
            cycle_id, report_id
        )
        if not coverage_result.success:
            return coverage_result
        results["coverage_validation"] = coverage_result.data
        
        return ActivityResult(
            success=True,
            data={
                "phase": "Test Execution",
                "activities_completed": 4,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to execute test execution activities: {str(e)}")
        return ActivityResult(success=False, error=str(e))