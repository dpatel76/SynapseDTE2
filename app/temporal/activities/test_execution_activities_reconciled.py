"""Test Execution Phase Activities - Reconciled with all existing steps

These activities match the pre-Temporal workflow exactly:
1. Start Test Execution Phase
2. Create Test Execution Records
3. Execute Document Tests
4. Execute Database Tests
5. Record Test Results
6. Generate Test Summary
7. Complete Test Execution Phase
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
# Test execution service removed - will use direct logic
from app.models import TestCase, TestExecution, TestResultReview, ReportAttribute
from sqlalchemy import select, and_, update, func

logger = logging.getLogger(__name__)


@activity.defn
async def start_test_execution_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 1: Start test execution phase"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Start test execution phase
            phase = await orchestrator.update_phase_state(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Testing",
                new_state="In Progress",
                notes="Started via Temporal workflow",
                user_id=user_id
            )
            
            # Get test case statistics
            result = await db.execute(
                select(
                    func.count(TestCase.test_case_id).label('total'),
                    func.count(TestCase.test_case_id).filter(
                        TestCase.status == 'Submitted'
                    ).label('ready_for_testing')
                ).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id
                    )
                )
            )
            stats = result.first()
            
            logger.info(f"Started test execution phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "phase_id": phase.phase_id,
                "data": {
                    "phase_name": phase.phase_name,
                    "state": phase.state,
                    "status": phase.schedule_status,
                    "started_at": datetime.utcnow().isoformat(),
                    "total_test_cases": stats.total,
                    "ready_for_testing": stats.ready_for_testing
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to start test execution phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def create_test_execution_records_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 2: Create test execution records for all test cases"""
    try:
        async for db in get_db():
            # Get test cases ready for execution
            result = await db.execute(
                select(TestCase).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id,
                        TestCase.status.in_(['Submitted', 'Pending'])
                    )
                )
            )
            test_cases = result.scalars().all()
            
            if not test_cases:
                raise ValueError("No test cases found for execution")
            
            # Create execution records
            execution_records = []
            
            for test_case in test_cases:
                # Create test execution record
                execution = TestExecution(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    test_case_id=test_case.test_case_id,
                    sample_id=test_case.sample_id,
                    attribute_id=test_case.attribute_id,
                    execution_type='manual',  # Will be updated based on test type
                    status='pending',
                    assigned_to=user_id,
                    created_by=user_id
                )
                db.add(execution)
                execution_records.append(execution)
            
            await db.commit()
            
            logger.info(f"Created {len(execution_records)} test execution records for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "execution_records_created": len(execution_records),
                    "test_cases_count": len(test_cases),
                    "ready_for_execution": True
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to create test execution records: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def execute_document_tests_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    test_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 3: Execute document-based tests
    
    Human-in-the-loop activity for document testing.
    """
    try:
        async for db in get_db():
            if test_data and test_data.get('document_test_results'):
                # Process document test results
                results = test_data['document_test_results']
                passed_count = 0
                failed_count = 0
                
                for result in results:
                    execution_id = result['execution_id']
                    test_result = result['result']  # 'pass', 'fail', 'not_applicable'
                    
                    # Update test execution
                    execution = await db.get(TestExecution, execution_id)
                    if execution:
                        execution.execution_type = 'document'
                        execution.status = 'completed'
                        execution.test_result = test_result
                        execution.actual_result = result.get('actual_value', '')
                        execution.evidence_reference = result.get('document_reference', '')
                        execution.test_notes = result.get('notes', '')
                        execution.executed_by = user_id
                        execution.executed_at = datetime.utcnow()
                        
                        if test_result == 'pass':
                            passed_count += 1
                        elif test_result == 'fail':
                            failed_count += 1
                
                await db.commit()
                
                return {
                    "success": True,
                    "data": {
                        "document_tests_completed": len(results),
                        "passed": passed_count,
                        "failed": failed_count,
                        "completion_time": datetime.utcnow().isoformat()
                    }
                }
            else:
                # Get pending document tests
                result = await db.execute(
                    select(func.count(TestExecution.execution_id))
                    .join(TestCase)
                    .join(ReportAttribute)
                    .where(
                        and_(
                            TestExecution.cycle_id == cycle_id,
                            TestExecution.report_id == report_id,
                            TestExecution.status == 'pending',
                            ReportAttribute.typical_source_documents.isnot(None)
                        )
                    )
                )
                pending_count = result.scalar()
                
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_document_testing",
                        "message": "Waiting for document test execution",
                        "pending_document_tests": pending_count
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in document test execution: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def execute_database_tests_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    test_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 4: Execute database tests
    
    Human-in-the-loop activity for database testing.
    """
    try:
        async for db in get_db():
            if test_data and test_data.get('database_test_results'):
                # Process database test results
                results = test_data['database_test_results']
                passed_count = 0
                failed_count = 0
                
                for result in results:
                    execution_id = result['execution_id']
                    test_result = result['result']  # 'pass', 'fail', 'not_applicable'
                    
                    # Update test execution
                    execution = await db.get(TestExecution, execution_id)
                    if execution:
                        execution.execution_type = 'database'
                        execution.status = 'completed'
                        execution.test_result = test_result
                        execution.actual_result = result.get('actual_value', '')
                        execution.sql_query = result.get('sql_query', '')
                        execution.database_source = result.get('database_source', '')
                        execution.test_notes = result.get('notes', '')
                        execution.executed_by = user_id
                        execution.executed_at = datetime.utcnow()
                        
                        if test_result == 'pass':
                            passed_count += 1
                        elif test_result == 'fail':
                            failed_count += 1
                
                await db.commit()
                
                return {
                    "success": True,
                    "data": {
                        "database_tests_completed": len(results),
                        "passed": passed_count,
                        "failed": failed_count,
                        "completion_time": datetime.utcnow().isoformat()
                    }
                }
            else:
                # Get pending database tests
                result = await db.execute(
                    select(func.count(TestExecution.execution_id))
                    .where(
                        and_(
                            TestExecution.cycle_id == cycle_id,
                            TestExecution.report_id == report_id,
                            TestExecution.status == 'pending',
                            TestExecution.execution_type != 'document'
                        )
                    )
                )
                pending_count = result.scalar()
                
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_database_testing",
                        "message": "Waiting for database test execution",
                        "pending_database_tests": pending_count
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in database test execution: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def record_test_results_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 5: Record and consolidate all test results"""
    try:
        async for db in get_db():
            # Get all completed test executions
            result = await db.execute(
                select(TestExecution).where(
                    and_(
                        TestExecution.cycle_id == cycle_id,
                        TestExecution.report_id == report_id,
                        TestExecution.status == 'completed'
                    )
                )
            )
            executions = result.scalars().all()
            
            # Count test results
            results_created = len(executions)
            
            # Get summary statistics
            stats_result = await db.execute(
                select(
                    func.count(TestExecution.execution_id).label('total'),
                    func.count(TestExecution.execution_id).filter(
                        TestExecution.test_result == 'pass'
                    ).label('passed'),
                    func.count(TestExecution.execution_id).filter(
                        TestExecution.test_result == 'fail'
                    ).label('failed')
                ).where(
                    and_(
                        TestExecution.cycle_id == cycle_id,
                        TestExecution.report_id == report_id,
                        TestExecution.status == 'completed'
                    )
                )
            )
            stats = stats_result.first()
            
            logger.info(f"Recorded {results_created} test results for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "results_recorded": results_created,
                    "total_tests": stats.total,
                    "passed_tests": stats.passed,
                    "failed_tests": stats.failed,
                    "pass_rate": (stats.passed / stats.total * 100) if stats.total > 0 else 0
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to record test results: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def generate_test_summary_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 6: Generate test execution summary"""
    try:
        async for db in get_db():
            # Generate comprehensive test summary
            summary_result = await db.execute(
                select(
                    func.count(TestExecution.execution_id).label('total_tests'),
                    func.count(TestExecution.execution_id).filter(
                        TestExecution.test_result == 'pass'
                    ).label('passed_tests'),
                    func.count(TestExecution.execution_id).filter(
                        TestExecution.test_result == 'fail'
                    ).label('failed_tests')
                ).where(
                    and_(
                        TestExecution.cycle_id == cycle_id,
                        TestExecution.report_id == report_id,
                        TestExecution.status == 'completed'
                    )
                )
            )
            stats = summary_result.first()
            
            summary = {
                'total_tests': stats.total_tests,
                'passed_tests': stats.passed_tests,
                'failed_tests': stats.failed_tests,
                'pass_rate': (stats.passed_tests / stats.total_tests * 100) if stats.total_tests > 0 else 0
            }
            
            # Get detailed statistics by attribute
            attr_stats = await db.execute(
                select(
                    ReportAttribute.attribute_name,
                    func.count(TestExecution.execution_id).label('total'),
                    func.count(TestExecution.execution_id).filter(
                        TestExecution.test_result == 'pass'
                    ).label('passed'),
                    func.count(TestExecution.execution_id).filter(
                        TestExecution.test_result == 'fail'
                    ).label('failed')
                ).join(
                    TestExecution,
                    TestExecution.attribute_id == ReportAttribute.attribute_id
                ).where(
                    and_(
                        TestExecution.cycle_id == cycle_id,
                        TestExecution.report_id == report_id,
                        TestExecution.status == 'completed'
                    )
                ).group_by(ReportAttribute.attribute_name)
            )
            
            attribute_summary = []
            for row in attr_stats:
                attribute_summary.append({
                    'attribute_name': row.attribute_name,
                    'total_tests': row.total,
                    'passed': row.passed,
                    'failed': row.failed,
                    'pass_rate': (row.passed / row.total * 100) if row.total > 0 else 0
                })
            
            logger.info(f"Generated test summary for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "summary": summary,
                    "attribute_summary": attribute_summary,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to generate test summary: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def complete_test_execution_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    phase_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Step 7: Complete test execution phase"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Get final test statistics
            summary = phase_data.get('summary', {})
            
            # Complete test execution phase
            phase = await orchestrator.update_phase_state(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Testing",
                new_state="Complete",
                notes=f"Completed with {summary.get('pass_rate', 0):.1f}% pass rate",
                user_id=user_id
            )
            
            # Advance to Observations phase
            await orchestrator.advance_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                from_phase="Testing",
                to_phase="Observations",
                user_id=user_id
            )
            
            logger.info(f"Completed test execution phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_name": "Testing",
                    "total_tests": summary.get('total_tests', 0),
                    "pass_rate": summary.get('pass_rate', 0),
                    "completed_at": datetime.utcnow().isoformat(),
                    "next_phase": "Observations"
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to complete test execution phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }