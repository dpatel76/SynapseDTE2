"""Observation Management Phase Activities for Temporal Workflow

Standard structure:
1. Start Observation Management Phase (Tester initiated)
2. Observation Management-specific activities
3. Complete Observation Management Phase (Tester initiated)
"""

from temporalio import activity
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import (
    WorkflowPhase, TestCycle, Report, CycleReport,
    ReportAttribute, User, TestExecution, TestCase,
    Observation, ObservationRecord
)
from app.temporal.shared import ActivityResult

logger = logging.getLogger(__name__)


@activity.defn
async def start_observation_management_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> ActivityResult:
    """Start Observation Management Phase - Initiated by Tester
    
    This is the standard entry point for the Observation Management phase.
    Validates user permissions and initializes phase.
    """
    try:
        async with get_db() as db:
            # Verify user has permission to start phase
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to start Observation Management phase"
                )
            
            # Get or create workflow phase record
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Observation Management"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                # Create phase record
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Observation Management",
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
                phase.updated_at = datetime.utcnow()
                phase.updated_by_id = user_id
            
            await db.commit()
            
            logger.info(f"Started Observation Management phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "started_at": phase.actual_start_date.isoformat(),
                    "started_by": user_id
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to start Observation Management phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def identify_failed_tests_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Identify failed tests that need observations
    
    Observation Management-specific activity that finds test failures
    """
    try:
        async with get_db() as db:
            # Get failed test executions
            failed_tests = await db.execute(
                select(
                    TestExecution.execution_id,
                    TestExecution.test_case_id,
                    TestExecution.sample_id,
                    TestExecution.test_result,
                    TestExecution.actual_value,
                    TestExecution.expected_value,
                    TestExecution.variance,
                    TestCase.test_name,
                    TestCase.attribute_id,
                    ReportAttribute.attribute_name,
                    ReportAttribute.is_critical
                ).join(
                    TestCase, TestCase.test_case_id == TestExecution.test_case_id
                ).join(
                    ReportAttribute, ReportAttribute.attribute_id == TestCase.attribute_id
                ).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id,
                        TestExecution.test_result == "Fail"
                    )
                )
            )
            
            failed_test_list = []
            critical_failures = 0
            
            for row in failed_tests:
                failed_test_list.append({
                    "execution_id": row.execution_id,
                    "test_name": row.test_name,
                    "attribute_name": row.attribute_name,
                    "is_critical": row.is_critical,
                    "variance": row.variance
                })
                if row.is_critical:
                    critical_failures += 1
            
            logger.info(f"Identified {len(failed_test_list)} failed tests, {critical_failures} critical")
            return ActivityResult(
                success=True,
                data={
                    "total_failures": len(failed_test_list),
                    "critical_failures": critical_failures,
                    "failed_tests": failed_test_list
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to identify failed tests: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def create_observations_activity(
    cycle_id: int,
    report_id: int,
    failed_tests_data: Dict[str, Any]
) -> ActivityResult:
    """Create observations for failed tests
    
    Observation Management-specific activity that creates observation records
    """
    try:
        async with get_db() as db:
            observations_created = []
            
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
            
            # Create observations for failed tests
            for failed_test in failed_tests_data.get("failed_tests", []):
                # Determine observation type and severity
                if failed_test["is_critical"]:
                    observation_type = "Critical Finding"
                    severity = "High"
                else:
                    observation_type = "Non-Critical Finding"
                    severity = "Medium" if abs(failed_test.get("variance", 0)) > 10 else "Low"
                
                observation = Observation(
                    cycle_report_id=cycle_report_obj.cycle_report_id,
                    observation_type=observation_type,
                    title=f"Test Failure: {failed_test['attribute_name']}",
                    description=f"Test '{failed_test['test_name']}' failed with variance of {failed_test.get('variance', 0):.2f}%",
                    severity=severity,
                    status="Open",
                    created_by=1,  # System user
                    test_execution_id=failed_test["execution_id"]
                )
                db.add(observation)
                
                observations_created.append({
                    "title": observation.title,
                    "type": observation.observation_type,
                    "severity": observation.severity
                })
            
            await db.commit()
            
            logger.info(f"Created {len(observations_created)} observations")
            return ActivityResult(
                success=True,
                data={
                    "observations_created": len(observations_created),
                    "observation_examples": observations_created[:10]
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to create observations: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def group_observations_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Group similar observations together
    
    Observation Management-specific activity that groups related observations
    """
    try:
        async with get_db() as db:
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
            
            # Get all observations
            observations = await db.execute(
                select(Observation).where(
                    Observation.cycle_report_id == cycle_report_obj.cycle_report_id
                )
            )
            observation_list = observations.scalars().all()
            
            # Group by observation type and severity
            groups_created = []
            grouped_by_type = {}
            
            for obs in observation_list:
                key = f"{obs.observation_type}_{obs.severity}"
                if key not in grouped_by_type:
                    grouped_by_type[key] = []
                grouped_by_type[key].append(obs)
            
            # Create observation groups
            for group_key, observations in grouped_by_type.items():
                if len(observations) > 1:  # Only group if multiple observations
                    obs_type, severity = group_key.split("_")
                    
                    group = ObservationRecord(
                        cycle_report_id=cycle_report_obj.cycle_report_id,
                        group_name=f"{obs_type} - {severity} Severity",
                        group_type=obs_type,
                        observation_count=len(observations),
                        created_by=1  # System user
                    )
                    db.add(group)
                    await db.flush()
                    
                    # Update observations with group ID
                    for obs in observations:
                        obs.observation_group_id = group.group_id
                    
                    groups_created.append({
                        "group_name": group.group_name,
                        "observation_count": group.observation_count
                    })
            
            await db.commit()
            
            logger.info(f"Created {len(groups_created)} observation groups")
            return ActivityResult(
                success=True,
                data={
                    "groups_created": len(groups_created),
                    "group_details": groups_created
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to group observations: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def generate_observation_summary_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Generate summary of all observations
    
    Observation Management-specific activity that creates summary statistics
    """
    try:
        async with get_db() as db:
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
            
            # Get observation statistics
            obs_stats = await db.execute(
                select(
                    Observation.observation_type,
                    Observation.severity,
                    func.count(Observation.observation_id).label("count")
                ).where(
                    Observation.cycle_report_id == cycle_report_obj.cycle_report_id
                ).group_by(
                    Observation.observation_type,
                    Observation.severity
                )
            )
            
            # Build summary
            summary = {
                "total_observations": 0,
                "by_type": {},
                "by_severity": {"High": 0, "Medium": 0, "Low": 0},
                "critical_findings": 0
            }
            
            for row in obs_stats:
                summary["total_observations"] += row.count
                
                if row.observation_type not in summary["by_type"]:
                    summary["by_type"][row.observation_type] = 0
                summary["by_type"][row.observation_type] += row.count
                
                summary["by_severity"][row.severity] += row.count
                
                if row.observation_type == "Critical Finding":
                    summary["critical_findings"] += row.count
            
            # Update cycle report with summary
            if not cycle_report_obj.metadata:
                cycle_report_obj.metadata = {}
            cycle_report_obj.metadata["observation_summary"] = summary
            
            await db.commit()
            
            logger.info(f"Generated observation summary: {summary['total_observations']} total observations")
            return ActivityResult(
                success=True,
                data=summary
            )
            
    except Exception as e:
        logger.error(f"Failed to generate observation summary: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def complete_observation_management_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    completion_notes: Optional[str] = None
) -> ActivityResult:
    """Complete Observation Management Phase - Initiated by Tester
    
    This is the standard exit point for the Observation Management phase.
    Validates completion criteria and marks phase as complete.
    """
    try:
        async with get_db() as db:
            # Verify user has permission
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to complete Observation Management phase"
                )
            
            # Get workflow phase
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Observation Management"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                return ActivityResult(
                    success=False,
                    error="Observation Management phase not found"
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
            
            # Verify observations exist for failed tests
            failed_test_count = await db.execute(
                select(func.count(TestExecution.execution_id)).join(
                    TestCase, TestCase.test_case_id == TestExecution.test_case_id
                ).where(
                    and_(
                        TestCase.cycle_id == cycle_id,
                        TestCase.report_id == report_id,
                        TestExecution.test_result == "Fail"
                    )
                )
            )
            failures = failed_test_count.scalar()
            
            observation_count = 0
            if cycle_report_obj:
                obs_count = await db.execute(
                    select(func.count(Observation.observation_id)).where(
                        Observation.cycle_report_id == cycle_report_obj.cycle_report_id
                    )
                )
                observation_count = obs_count.scalar()
            
            # Allow completion even if not all failures have observations (with warning)
            if failures > 0 and observation_count == 0:
                logger.warning(f"Completing phase with {failures} test failures but no observations")
            
            # Mark phase as complete
            phase.state = "Completed"
            phase.actual_end_date = datetime.utcnow()
            phase.completed_by = user_id
            phase.updated_at = datetime.utcnow()
            phase.updated_by_id = user_id
            if completion_notes:
                phase.notes = completion_notes
            
            # Calculate if on schedule
            if phase.planned_end_date and phase.actual_end_date > phase.planned_end_date:
                phase.status = "Behind Schedule"
            else:
                phase.status = "Complete"
            
            await db.commit()
            
            logger.info(f"Completed Observation Management phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "completed_at": phase.actual_end_date.isoformat(),
                    "completed_by": user_id,
                    "duration_days": (phase.actual_end_date - phase.actual_start_date).days if phase.actual_start_date else 0,
                    "status": phase.status,
                    "test_failures": failures,
                    "observations_created": observation_count
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to complete Observation Management phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def execute_observation_activities(
    cycle_id: int,
    report_id: int,
    metadata: Dict[str, Any]
) -> ActivityResult:
    """Execute all Observation Management phase activities in sequence
    
    This orchestrates the observation management-specific activities between
    start and complete.
    """
    try:
        results = {}
        
        # 1. Identify failed tests
        failed_tests_result = await identify_failed_tests_activity(
            cycle_id, report_id
        )
        if not failed_tests_result.success:
            return failed_tests_result
        results["failed_test_identification"] = failed_tests_result.data
        
        # 2. Create observations
        if failed_tests_result.data["total_failures"] > 0:
            observations_result = await create_observations_activity(
                cycle_id, report_id, failed_tests_result.data
            )
            if not observations_result.success:
                return observations_result
            results["observation_creation"] = observations_result.data
            
            # 3. Group observations
            grouping_result = await group_observations_activity(
                cycle_id, report_id
            )
            if not grouping_result.success:
                return grouping_result
            results["observation_grouping"] = grouping_result.data
        else:
            results["observation_creation"] = {"observations_created": 0}
            results["observation_grouping"] = {"groups_created": 0}
        
        # 4. Generate summary
        summary_result = await generate_observation_summary_activity(
            cycle_id, report_id
        )
        if not summary_result.success:
            return summary_result
        results["observation_summary"] = summary_result.data
        
        return ActivityResult(
            success=True,
            data={
                "phase": "Observation Management",
                "activities_completed": 4,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to execute observation management activities: {str(e)}")
        return ActivityResult(success=False, error=str(e))