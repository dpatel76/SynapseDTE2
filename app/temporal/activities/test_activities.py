"""Temporal activities for test execution"""

from temporalio import activity
from typing import Dict, Any, List
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.test_execution import TestExecution
from app.models.request_info import CycleReportTestCase
from app.models.report_attribute import ReportAttribute
from app.temporal.shared.types import ActivityResult, TestExecutionData

logger = logging.getLogger(__name__)


@activity.defn
async def create_test_cases_activity(
    cycle_report_id: int,
    attribute_ids: List[int],
    created_by: int
) -> ActivityResult:
    """Create test cases for attributes"""
    try:
        async with get_db() as db:
            from sqlalchemy import select
            
            created_cases = []
            
            for attr_id in attribute_ids:
                # Get attribute details
                stmt = select(ReportAttribute).where(ReportAttribute.attribute_id == attr_id)
                result = await db.execute(stmt)
                attribute = result.scalar_one_or_none()
                
                if attribute:
                    # Create test case
                    test_case = TestCase(
                        cycle_report_id=cycle_report_id,
                        attribute_id=attr_id,
                        test_name=f"Test for {attribute.attribute_name}",
                        test_description=f"Validate {attribute.attribute_name} attribute",
                        test_type="both",  # both document and database
                        created_by=created_by
                    )
                    db.add(test_case)
                    created_cases.append({
                        "attribute_id": attr_id,
                        "attribute_name": attribute.attribute_name
                    })
            
            await db.commit()
            
            return ActivityResult(
                success=True,
                data={
                    "created_count": len(created_cases),
                    "test_cases": created_cases
                }
            )
            
    except Exception as e:
        logger.error(f"Error creating test cases: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )


@activity.defn
async def execute_test_activity(test_data: TestExecutionData) -> ActivityResult:
    """Execute a single test"""
    try:
        async with get_db() as db:
            # Create test execution record
            execution = TestExecution(
                test_case_id=test_data.test_case_id,
                sample_id=test_data.sample_id,
                execution_status="In Progress",
                executed_at=datetime.utcnow()
            )
            db.add(execution)
            await db.flush()
            
            # Simulate test execution
            # In real implementation, this would connect to data sources
            test_passed = test_data.expected_value == test_data.actual_value
            
            # Create test result
            result = TestResult(
                test_execution_id=execution.test_execution_id,
                test_type=test_data.test_type,
                expected_value=str(test_data.expected_value),
                actual_value=str(test_data.actual_value),
                test_passed=test_passed,
                error_message=None if test_passed else "Values do not match"
            )
            db.add(result)
            
            # Update execution status
            execution.execution_status = "Complete"
            execution.completed_at = datetime.utcnow()
            
            await db.commit()
            
            return ActivityResult(
                success=True,
                data={
                    "execution_id": execution.test_execution_id,
                    "test_passed": test_passed,
                    "test_type": test_data.test_type
                }
            )
            
    except Exception as e:
        logger.error(f"Error executing test: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )


@activity.defn
async def batch_execute_tests_activity(
    cycle_report_id: int,
    test_case_ids: List[int],
    sample_ids: List[int]
) -> ActivityResult:
    """Execute multiple tests in batch"""
    try:
        results = []
        failed_count = 0
        passed_count = 0
        
        for test_case_id in test_case_ids:
            for sample_id in sample_ids:
                # Execute individual test
                test_data = TestExecutionData(
                    test_case_id=test_case_id,
                    sample_id=sample_id,
                    attribute_id=1,  # Would be fetched from test case
                    test_type="database",
                    expected_value="Expected",
                    actual_value="Expected"  # Simulated
                )
                
                result = await execute_test_activity(test_data)
                
                if result.success:
                    if result.data.get("test_passed"):
                        passed_count += 1
                    else:
                        failed_count += 1
                    results.append(result.data)
        
        return ActivityResult(
            success=True,
            data={
                "total_tests": len(results),
                "passed": passed_count,
                "failed": failed_count,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Error in batch test execution: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )


@activity.defn
async def validate_test_results_activity(
    cycle_report_id: int,
    threshold: float = 0.95
) -> ActivityResult:
    """Validate test results meet quality threshold"""
    try:
        async with get_db() as db:
            from sqlalchemy import select, func, and_
            
            # Get test statistics
            stmt = select(
                func.count(TestResult.test_result_id).label("total"),
                func.sum(func.cast(TestResult.test_passed, int)).label("passed")
            ).join(
                TestExecution
            ).join(
                TestCase
            ).where(
                TestCase.cycle_report_id == cycle_report_id
            )
            
            result = await db.execute(stmt)
            stats = result.first()
            
            if stats and stats.total > 0:
                pass_rate = stats.passed / stats.total
                meets_threshold = pass_rate >= threshold
                
                return ActivityResult(
                    success=True,
                    data={
                        "total_tests": stats.total,
                        "passed_tests": stats.passed,
                        "pass_rate": pass_rate,
                        "meets_threshold": meets_threshold,
                        "threshold": threshold
                    }
                )
            else:
                return ActivityResult(
                    success=True,
                    data={
                        "total_tests": 0,
                        "passed_tests": 0,
                        "pass_rate": 0,
                        "meets_threshold": False,
                        "threshold": threshold
                    }
                )
                
    except Exception as e:
        logger.error(f"Error validating test results: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )