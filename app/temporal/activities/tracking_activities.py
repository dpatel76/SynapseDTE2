"""Temporal activities for workflow tracking and metrics

Records workflow execution details, steps, transitions, and calculates metrics
"""

from temporalio import activity
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.workflow_tracking import (
    WorkflowExecution, WorkflowStep, WorkflowTransition,
    WorkflowMetrics, WorkflowAlert,
    WorkflowExecutionStatus, StepType
)

logger = logging.getLogger(__name__)


@activity.defn
async def record_workflow_start_activity(
    execution_id: str,
    workflow_id: str,
    workflow_run_id: str,
    workflow_type: str,
    cycle_id: int,
    report_id: Optional[int],
    initiated_by: int,
    input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Record the start of a workflow execution"""
    try:
        async with get_db() as db:
            workflow_execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                workflow_run_id=workflow_run_id,
                workflow_type=workflow_type,
                cycle_id=cycle_id,
                report_id=report_id,
                initiated_by=initiated_by,
                status=WorkflowExecutionStatus.RUNNING,
                started_at=datetime.utcnow(),
                input_data=input_data
            )
            
            db.add(workflow_execution)
            await db.commit()
            
            logger.info(f"Recorded workflow start: {execution_id}")
            return {"success": True, "execution_id": execution_id}
            
    except Exception as e:
        logger.error(f"Failed to record workflow start: {str(e)}")
        raise


@activity.defn
async def record_workflow_complete_activity(
    execution_id: str,
    status: str,
    output_data: Dict[str, Any],
    error_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Record workflow completion"""
    try:
        async with get_db() as db:
            # Update workflow execution
            result = await db.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.execution_id == execution_id
                )
            )
            workflow_execution = result.scalar_one()
            
            workflow_execution.status = WorkflowExecutionStatus(status)
            workflow_execution.completed_at = datetime.utcnow()
            workflow_execution.duration_seconds = (
                workflow_execution.completed_at - workflow_execution.started_at
            ).total_seconds()
            workflow_execution.output_data = output_data
            workflow_execution.error_details = error_details
            
            await db.commit()
            
            # Check for SLA violations or performance issues
            await _check_workflow_alerts(db, workflow_execution)
            
            logger.info(f"Recorded workflow completion: {execution_id} - {status}")
            return {"success": True}
            
    except Exception as e:
        logger.error(f"Failed to record workflow completion: {str(e)}")
        raise


@activity.defn
async def record_step_start_activity(
    execution_id: str,
    step_id: str,
    parent_step_id: Optional[str],
    step_name: str,
    step_type: str,
    phase_name: Optional[str],
    activity_name: Optional[str]
) -> Dict[str, Any]:
    """Record the start of a workflow step"""
    try:
        async with get_db() as db:
            workflow_step = WorkflowStep(
                step_id=step_id,
                execution_id=execution_id,
                parent_step_id=parent_step_id,
                step_name=step_name,
                step_type=StepType(step_type),
                phase_name=phase_name,
                activity_name=activity_name,
                status=WorkflowExecutionStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            
            db.add(workflow_step)
            await db.commit()
            
            logger.info(f"Recorded step start: {step_name} ({step_id})")
            return {"success": True, "step_id": step_id}
            
    except Exception as e:
        logger.error(f"Failed to record step start: {str(e)}")
        raise


@activity.defn
async def record_step_complete_activity(
    step_id: str,
    status: str,
    output_data: Optional[Dict[str, Any]] = None,
    error_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Record step completion"""
    try:
        async with get_db() as db:
            # Update step
            result = await db.execute(
                select(WorkflowStep).where(WorkflowStep.step_id == step_id)
            )
            step = result.scalar_one()
            
            step.status = WorkflowExecutionStatus(status)
            step.completed_at = datetime.utcnow()
            step.duration_seconds = (
                step.completed_at - step.started_at
            ).total_seconds()
            step.output_data = output_data
            step.error_details = error_details
            
            await db.commit()
            
            # Check for step-level alerts
            await _check_step_alerts(db, step)
            
            logger.info(f"Recorded step completion: {step.step_name} - {status}")
            return {"success": True, "duration": step.duration_seconds}
            
    except Exception as e:
        logger.error(f"Failed to record step completion: {str(e)}")
        raise


@activity.defn
async def record_transition_activity(
    execution_id: str,
    from_step_id: Optional[str],
    to_step_id: Optional[str],
    transition_type: str,
    condition_evaluated: Optional[str] = None
) -> Dict[str, Any]:
    """Record transition between workflow steps"""
    try:
        async with get_db() as db:
            import uuid
            
            transition = WorkflowTransition(
                transition_id=str(uuid.uuid4()),
                execution_id=execution_id,
                from_step_id=from_step_id,
                to_step_id=to_step_id,
                transition_type=transition_type,
                condition_evaluated=condition_evaluated,
                started_at=datetime.utcnow()
            )
            
            db.add(transition)
            await db.commit()
            
            logger.info(f"Recorded transition: {transition_type}")
            return {"success": True, "transition_id": transition.transition_id}
            
    except Exception as e:
        logger.error(f"Failed to record transition: {str(e)}")
        raise


@activity.defn
async def calculate_workflow_metrics_activity(
    execution_id: str
) -> Dict[str, Any]:
    """Calculate and store workflow metrics"""
    try:
        async with get_db() as db:
            # Get workflow execution
            result = await db.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.execution_id == execution_id
                )
            )
            execution = result.scalar_one()
            
            # Calculate metrics for each phase
            metrics_data = await _calculate_phase_metrics(db, execution)
            
            # Store aggregated metrics
            await _store_aggregated_metrics(db, execution, metrics_data)
            
            logger.info(f"Calculated metrics for workflow: {execution_id}")
            return {
                "success": True,
                "metrics": metrics_data
            }
            
    except Exception as e:
        logger.error(f"Failed to calculate workflow metrics: {str(e)}")
        raise


# Helper functions
async def _check_workflow_alerts(db: AsyncSession, execution: WorkflowExecution):
    """Check for workflow-level performance alerts"""
    # Check if workflow took too long
    expected_duration = 7 * 24 * 3600  # 7 days in seconds
    
    if execution.duration_seconds > expected_duration * 1.2:  # 20% over expected
        alert = WorkflowAlert(
            execution_id=execution.execution_id,
            workflow_type=execution.workflow_type,
            alert_type="slow_execution",
            severity="high" if execution.duration_seconds > expected_duration * 1.5 else "medium",
            threshold_value=expected_duration,
            actual_value=execution.duration_seconds,
            alert_message=f"Workflow execution took {execution.duration_seconds / 3600:.1f} hours, "
                         f"exceeding expected duration of {expected_duration / 3600:.1f} hours"
        )
        db.add(alert)
        await db.commit()


async def _check_step_alerts(db: AsyncSession, step: WorkflowStep):
    """Check for step-level performance alerts"""
    # Define expected durations for different step types (in seconds)
    expected_durations = {
        StepType.PHASE: {
            "Planning": 2 * 24 * 3600,  # 2 days
            "Scoping": 2 * 24 * 3600,
            "Sample Selection": 1 * 24 * 3600,
            "Data Owner Identification": 1 * 24 * 3600,
            "Request for Information": 3 * 24 * 3600,
            "Test Execution": 2 * 24 * 3600,
            "Observation Management": 1 * 24 * 3600,
            "Finalize Test Report": 1 * 24 * 3600
        },
        StepType.ACTIVITY: 3600,  # 1 hour for activities
        StepType.TRANSITION: 300   # 5 minutes for transitions
    }
    
    phase_durations = expected_durations.get(step.step_type, {})
    expected = phase_durations.get(step.phase_name, 3600) if isinstance(phase_durations, dict) else phase_durations
    
    if step.duration_seconds > expected * 1.5:  # 50% over expected
        # Get workflow execution for context
        result = await db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.execution_id == step.execution_id
            )
        )
        execution = result.scalar_one()
        
        alert = WorkflowAlert(
            execution_id=step.execution_id,
            workflow_type=execution.workflow_type,
            phase_name=step.phase_name,
            alert_type="slow_step",
            severity="high" if step.duration_seconds > expected * 2 else "medium",
            threshold_value=expected,
            actual_value=step.duration_seconds,
            alert_message=f"Step '{step.step_name}' took {step.duration_seconds / 3600:.1f} hours, "
                         f"exceeding expected duration of {expected / 3600:.1f} hours"
        )
        db.add(alert)
        await db.commit()


async def _calculate_phase_metrics(
    db: AsyncSession,
    execution: WorkflowExecution
) -> Dict[str, Any]:
    """Calculate metrics for each phase in the workflow"""
    # Get all steps for this execution
    result = await db.execute(
        select(WorkflowStep).where(
            and_(
                WorkflowStep.execution_id == execution.execution_id,
                WorkflowStep.step_type == StepType.PHASE
            )
        )
    )
    phase_steps = result.scalars().all()
    
    metrics = {}
    for step in phase_steps:
        if step.phase_name:
            metrics[step.phase_name] = {
                "duration": step.duration_seconds,
                "status": step.status,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                "substeps": await _get_substep_metrics(db, step.step_id)
            }
    
    return metrics


async def _get_substep_metrics(
    db: AsyncSession,
    parent_step_id: str
) -> List[Dict[str, Any]]:
    """Get metrics for substeps of a phase"""
    result = await db.execute(
        select(WorkflowStep).where(
            WorkflowStep.parent_step_id == parent_step_id
        )
    )
    substeps = result.scalars().all()
    
    return [
        {
            "name": step.step_name,
            "type": step.step_type,
            "duration": step.duration_seconds,
            "status": step.status
        }
        for step in substeps
    ]


async def _store_aggregated_metrics(
    db: AsyncSession,
    execution: WorkflowExecution,
    metrics_data: Dict[str, Any]
):
    """Store aggregated metrics for reporting"""
    # Define the current period (e.g., daily aggregation)
    period_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    period_end = period_start + timedelta(days=1)
    
    # Aggregate by workflow type
    workflow_metric = await _get_or_create_metric(
        db,
        workflow_type=execution.workflow_type,
        period_start=period_start,
        period_end=period_end
    )
    
    # Update workflow-level metrics
    workflow_metric.execution_count += 1
    if execution.status == WorkflowExecutionStatus.COMPLETED:
        workflow_metric.success_count += 1
    elif execution.status == WorkflowExecutionStatus.FAILED:
        workflow_metric.failure_count += 1
    
    # Update duration statistics (simplified - in production, use proper percentile calculation)
    if execution.duration_seconds:
        if not workflow_metric.avg_duration:
            workflow_metric.avg_duration = execution.duration_seconds
            workflow_metric.min_duration = execution.duration_seconds
            workflow_metric.max_duration = execution.duration_seconds
        else:
            # Update average (simplified)
            total_duration = workflow_metric.avg_duration * (workflow_metric.execution_count - 1)
            workflow_metric.avg_duration = (total_duration + execution.duration_seconds) / workflow_metric.execution_count
            
            # Update min/max
            workflow_metric.min_duration = min(workflow_metric.min_duration, execution.duration_seconds)
            workflow_metric.max_duration = max(workflow_metric.max_duration, execution.duration_seconds)
    
    # Aggregate by phase
    for phase_name, phase_data in metrics_data.items():
        phase_metric = await _get_or_create_metric(
            db,
            workflow_type=execution.workflow_type,
            phase_name=phase_name,
            period_start=period_start,
            period_end=period_end
        )
        
        phase_metric.execution_count += 1
        if phase_data["status"] == WorkflowExecutionStatus.COMPLETED:
            phase_metric.success_count += 1
        elif phase_data["status"] == WorkflowExecutionStatus.FAILED:
            phase_metric.failure_count += 1
        
        # Update phase duration statistics
        if phase_data["duration"]:
            if not phase_metric.avg_duration:
                phase_metric.avg_duration = phase_data["duration"]
                phase_metric.min_duration = phase_data["duration"]
                phase_metric.max_duration = phase_data["duration"]
            else:
                total_duration = phase_metric.avg_duration * (phase_metric.execution_count - 1)
                phase_metric.avg_duration = (total_duration + phase_data["duration"]) / phase_metric.execution_count
                phase_metric.min_duration = min(phase_metric.min_duration, phase_data["duration"])
                phase_metric.max_duration = max(phase_metric.max_duration, phase_data["duration"])
    
    await db.commit()


async def _get_or_create_metric(
    db: AsyncSession,
    workflow_type: str,
    period_start: datetime,
    period_end: datetime,
    phase_name: Optional[str] = None,
    activity_name: Optional[str] = None,
    step_type: Optional[StepType] = None
) -> WorkflowMetrics:
    """Get or create a workflow metric record"""
    result = await db.execute(
        select(WorkflowMetrics).where(
            and_(
                WorkflowMetrics.workflow_type == workflow_type,
                WorkflowMetrics.phase_name == phase_name,
                WorkflowMetrics.activity_name == activity_name,
                WorkflowMetrics.step_type == step_type,
                WorkflowMetrics.period_start == period_start,
                WorkflowMetrics.period_end == period_end
            )
        )
    )
    metric = result.scalar_one_or_none()
    
    if not metric:
        metric = WorkflowMetrics(
            workflow_type=workflow_type,
            phase_name=phase_name,
            activity_name=activity_name,
            step_type=step_type,
            period_start=period_start,
            period_end=period_end
        )
        db.add(metric)
    
    return metric