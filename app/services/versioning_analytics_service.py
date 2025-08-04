"""
Versioning Analytics and Monitoring Service
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.versioning_complete import (
    PlanningPhaseVersion, DataProfilingVersion, ScopingVersion,
    SampleSelectionVersion, ObservationVersion, TestReportVersion,
    DataOwnerAssignment, DocumentSubmission, TestExecutionAudit,
    WorkflowVersionOperation, SampleDecision, ApprovalStatus, VersionStatus
)
from app.models.workflow_tracking import WorkflowExecution, WorkflowStep


class VersioningAnalyticsService:
    """Service for versioning analytics and monitoring"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_phase_metrics(
        self,
        cycle_id: int,
        report_id: int,
        phase_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive metrics for phases"""
        metrics = {}
        
        if phase_name:
            metrics[phase_name] = await self._get_single_phase_metrics(
                cycle_id, report_id, phase_name
            )
        else:
            # Get metrics for all phases
            phases = [
                "Planning", "Data Profiling", "Scoping", "CycleReportSampleSelectionSamples Selection",
                "Data Owner ID", "Request Info", "Test Execution",
                "Observation Management", "Finalize Test Report"
            ]
            
            for phase in phases:
                metrics[phase] = await self._get_single_phase_metrics(
                    cycle_id, report_id, phase
                )
        
        return metrics
    
    async def _get_single_phase_metrics(
        self,
        cycle_id: int,
        report_id: int,
        phase_name: str
    ) -> Dict[str, Any]:
        """Get metrics for a single phase"""
        metrics = {
            "phase_name": phase_name,
            "version_count": 0,
            "average_approval_time_hours": 0,
            "rejection_rate": 0,
            "revision_count": 0,
            "current_version": None,
            "status": "not_started"
        }
        
        # Map phase to appropriate table
        if phase_name == "Planning":
            metrics.update(await self._get_planning_metrics(cycle_id, report_id))
        elif phase_name == "Data Profiling":
            metrics.update(await self._get_profiling_metrics(cycle_id, report_id))
        elif phase_name == "Scoping":
            metrics.update(await self._get_scoping_metrics(cycle_id, report_id))
        elif phase_name == "CycleReportSampleSelectionSamples Selection":
            metrics.update(await self._get_sample_selection_metrics(cycle_id, report_id))
        elif phase_name == "Data Owner ID":
            metrics.update(await self._get_data_owner_metrics(cycle_id, report_id))
        elif phase_name == "Request Info":
            metrics.update(await self._get_request_info_metrics(cycle_id, report_id))
        elif phase_name == "Test Execution":
            metrics.update(await self._get_test_execution_metrics(cycle_id, report_id))
        elif phase_name == "Observation Management":
            metrics.update(await self._get_observation_metrics(cycle_id, report_id))
        elif phase_name == "Finalize Test Report":
            metrics.update(await self._get_test_report_metrics(cycle_id, report_id))
        
        return metrics
    
    async def _get_planning_metrics(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Get planning phase metrics"""
        result = await self.db.execute(
            select(
                func.count(PlanningPhaseVersion.version_id).label("version_count"),
                func.max(PlanningPhaseVersion.version_number).label("latest_version"),
                func.avg(
                    func.extract(
                        'epoch',
                        PlanningPhaseVersion.version_reviewed_at - 
                        PlanningPhaseVersion.version_created_at
                    ) / 3600
                ).label("avg_approval_hours")
            ).where(
                and_(
                    PlanningPhaseVersion.cycle_id == cycle_id,
                    PlanningPhaseVersion.report_id == report_id
                )
            )
        )
        
        row = result.one()
        
        # Get current version
        current_result = await self.db.execute(
            select(PlanningPhaseVersion).where(
                and_(
                    PlanningPhaseVersion.cycle_id == cycle_id,
                    PlanningPhaseVersion.report_id == report_id,
                    PlanningPhaseVersion.version_status == VersionStatus.APPROVED
                )
            ).order_by(PlanningPhaseVersion.version_number.desc())
        )
        current = current_result.scalar_one_or_none()
        
        return {
            "version_count": row.version_count or 0,
            "average_approval_time_hours": float(row.avg_approval_hours or 0),
            "current_version": str(current.version_id) if current else None,
            "status": "complete" if current else "in_progress"
        }
    
    async def _get_sample_selection_metrics(
        self, 
        cycle_id: int, 
        report_id: int
    ) -> Dict[str, Any]:
        """Get sample selection metrics with detailed statistics"""
        # Get all versions
        versions_result = await self.db.execute(
            select(SampleSelectionVersion).where(
                and_(
                    SampleSelectionVersion.cycle_id == cycle_id,
                    SampleSelectionVersion.report_id == report_id
                )
            ).order_by(SampleSelectionVersion.version_number)
        )
        versions = versions_result.scalars().all()
        
        if not versions:
            return {
                "version_count": 0,
                "status": "not_started"
            }
        
        # Calculate revision count (versions with parent)
        revision_count = sum(1 for v in versions if v.parent_version_id)
        
        # Get sample statistics for current version
        current_version = max(versions, key=lambda v: v.version_number)
        
        sample_stats_result = await self.db.execute(
            select(
                func.count(SampleDecision.decision_id).label("total_samples"),
                func.sum(
                    case(
                        (SampleDecision.decision_status == ApprovalStatus.APPROVED, 1),
                        else_=0
                    )
                ).label("approved_samples"),
                func.sum(
                    case(
                        (SampleDecision.decision_status == ApprovalStatus.REJECTED, 1),
                        else_=0
                    )
                ).label("rejected_samples"),
                func.sum(
                    case(
                        (SampleDecision.recommendation_source == 'carried_forward', 1),
                        else_=0
                    )
                ).label("carried_forward_samples")
            ).where(
                SampleDecision.selection_version_id == current_version.version_id
            )
        )
        
        sample_stats = sample_stats_result.one()
        
        # Calculate approval time
        approval_times = []
        for v in versions:
            if v.version_reviewed_at and v.version_created_at:
                delta = v.version_reviewed_at - v.version_created_at
                approval_times.append(delta.total_seconds() / 3600)
        
        avg_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0
        
        return {
            "version_count": len(versions),
            "revision_count": revision_count,
            "average_approval_time_hours": avg_approval_time,
            "current_version": str(current_version.version_id),
            "status": "complete" if current_version.version_status == VersionStatus.APPROVED else "in_progress",
            "sample_statistics": {
                "total": sample_stats.total_samples or 0,
                "approved": sample_stats.approved_samples or 0,
                "rejected": sample_stats.rejected_samples or 0,
                "carried_forward": sample_stats.carried_forward_samples or 0,
                "approval_rate": (
                    (sample_stats.approved_samples or 0) / sample_stats.total_samples * 100
                ) if sample_stats.total_samples else 0
            }
        }
    
    async def _get_data_owner_metrics(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Get data owner assignment metrics"""
        result = await self.db.execute(
            select(
                func.count(DataOwnerAssignment.assignment_id).label("total_assignments"),
                func.count(
                    func.distinct(DataOwnerAssignment.lob_id)
                ).label("unique_lobs"),
                func.sum(
                    case(
                        (DataOwnerAssignment.previous_assignment_id.isnot(None), 1),
                        else_=0
                    )
                ).label("reassignment_count")
            ).where(
                and_(
                    DataOwnerAssignment.cycle_id == cycle_id,
                    DataOwnerAssignment.report_id == report_id,
                    DataOwnerAssignment.status == "active"
                )
            )
        )
        
        row = result.one()
        
        return {
            "total_assignments": row.total_assignments or 0,
            "unique_lobs": row.unique_lobs or 0,
            "reassignment_count": row.reassignment_count or 0,
            "status": "complete" if row.total_assignments > 0 else "not_started"
        }
    
    async def get_workflow_version_metrics(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """Get metrics for all versions in a workflow"""
        # Get all version operations for this workflow
        operations_result = await self.db.execute(
            select(WorkflowVersionOperation).where(
                WorkflowVersionOperation.workflow_execution_id == workflow_id
            ).order_by(WorkflowVersionOperation.initiated_at)
        )
        operations = operations_result.scalars().all()
        
        if not operations:
            return {
                "workflow_id": workflow_id,
                "total_operations": 0,
                "phases_with_versions": []
            }
        
        # Group by phase
        phase_operations = {}
        for op in operations:
            if op.phase_name not in phase_operations:
                phase_operations[op.phase_name] = []
            phase_operations[op.phase_name].append(op)
        
        # Calculate metrics per phase
        phase_metrics = []
        for phase, ops in phase_operations.items():
            create_ops = [op for op in ops if op.operation_type == "create"]
            approve_ops = [op for op in ops if op.operation_type == "approve"]
            
            # Calculate average time to approval
            approval_times = []
            for approve_op in approve_ops:
                # Find corresponding create operation
                create_op = next(
                    (op for op in create_ops if op.version_id == approve_op.version_id),
                    None
                )
                if create_op and approve_op.completed_at and create_op.completed_at:
                    delta = approve_op.completed_at - create_op.completed_at
                    approval_times.append(delta.total_seconds() / 3600)
            
            phase_metrics.append({
                "phase": phase,
                "total_operations": len(ops),
                "versions_created": len(create_ops),
                "versions_approved": len(approve_ops),
                "average_approval_time_hours": (
                    sum(approval_times) / len(approval_times) if approval_times else 0
                ),
                "success_rate": (
                    sum(1 for op in ops if op.success) / len(ops) * 100
                ) if ops else 0
            })
        
        return {
            "workflow_id": workflow_id,
            "total_operations": len(operations),
            "phases_with_versions": phase_metrics,
            "overall_success_rate": (
                sum(1 for op in operations if op.success) / len(operations) * 100
            ) if operations else 0
        }
    
    async def get_version_trend_analysis(
        self,
        phase_name: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get version creation trends over time"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Map phase to table
        table_map = {
            "Planning": PlanningPhaseVersion,
            "Data Profiling": DataProfilingVersion,
            "Scoping": ScopingVersion,
            "CycleReportSampleSelectionSamples Selection": SampleSelectionVersion,
            "Observation Management": ObservationVersion,
            "Finalize Test Report": TestReportVersion
        }
        
        if phase_name not in table_map:
            return []
        
        model = table_map[phase_name]
        
        # Get daily version counts
        result = await self.db.execute(
            select(
                func.date(model.version_created_at).label("date"),
                func.count(model.version_id).label("version_count"),
                func.avg(
                    case(
                        (model.version_status == VersionStatus.APPROVED, 1),
                        (model.version_status == VersionStatus.REJECTED, 0),
                        else_=None
                    )
                ).label("approval_rate")
            ).where(
                model.version_created_at >= since_date
            ).group_by(
                func.date(model.version_created_at)
            ).order_by(
                func.date(model.version_created_at)
            )
        )
        
        return [
            {
                "date": row.date.isoformat(),
                "version_count": row.version_count,
                "approval_rate": float(row.approval_rate * 100) if row.approval_rate else 0
            }
            for row in result
        ]
    
    async def get_bottleneck_analysis(
        self,
        cycle_id: int,
        report_id: int
    ) -> List[Dict[str, Any]]:
        """Identify bottlenecks in the versioning process"""
        bottlenecks = []
        
        # Check each phase for potential bottlenecks
        phases = [
            ("Planning", PlanningPhaseVersion),
            ("Data Profiling", DataProfilingVersion),
            ("Scoping", ScopingVersion),
            ("CycleReportSampleSelectionSamples Selection", SampleSelectionVersion),
            ("Observation Management", ObservationVersion),
            ("Finalize Test Report", TestReportVersion)
        ]
        
        for phase_name, model in phases:
            # Get versions with long approval times
            result = await self.db.execute(
                select(
                    model.version_id,
                    model.version_number,
                    (model.version_reviewed_at - model.version_created_at).label("approval_time")
                ).where(
                    and_(
                        model.cycle_id == cycle_id,
                        model.report_id == report_id,
                        model.version_reviewed_at.isnot(None)
                    )
                )
            )
            
            versions = result.all()
            
            if versions:
                approval_times = [
                    v.approval_time.total_seconds() / 3600 
                    for v in versions if v.approval_time
                ]
                
                if approval_times:
                    avg_time = sum(approval_times) / len(approval_times)
                    max_time = max(approval_times)
                    
                    # Flag as bottleneck if average > 24 hours or max > 48 hours
                    if avg_time > 24 or max_time > 48:
                        bottlenecks.append({
                            "phase": phase_name,
                            "issue": "Long approval times",
                            "average_hours": avg_time,
                            "max_hours": max_time,
                            "severity": "high" if avg_time > 48 else "medium"
                        })
            
            # Check for high rejection rates
            if phase_name == "CycleReportSampleSelectionSamples Selection":
                rejection_result = await self.db.execute(
                    select(
                        func.count(model.version_id).label("total"),
                        func.sum(
                            case(
                                (model.parent_version_id.isnot(None), 1),
                                else_=0
                            )
                        ).label("revisions")
                    ).where(
                        and_(
                            model.cycle_id == cycle_id,
                            model.report_id == report_id
                        )
                    )
                )
                
                rejection_data = rejection_result.one()
                if rejection_data.total > 0:
                    revision_rate = (rejection_data.revisions or 0) / rejection_data.total * 100
                    if revision_rate > 50:
                        bottlenecks.append({
                            "phase": phase_name,
                            "issue": "High revision rate",
                            "revision_rate": revision_rate,
                            "severity": "high" if revision_rate > 75 else "medium"
                        })
        
        return bottlenecks
    
    async def get_user_activity_metrics(
        self,
        user_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user activity metrics for versioning"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get version creation activity
        creation_query = select(
            WorkflowVersionOperation.phase_name,
            func.count(WorkflowVersionOperation.operation_id).label("operation_count")
        ).where(
            and_(
                WorkflowVersionOperation.operation_type == "create",
                WorkflowVersionOperation.initiated_at >= since_date
            )
        ).group_by(WorkflowVersionOperation.phase_name)
        
        if user_id:
            # Need to join with version tables to get user info
            # This is simplified - actual implementation would join appropriately
            pass
        
        creation_result = await self.db.execute(creation_query)
        
        return {
            "period_days": days,
            "version_creation_by_phase": [
                {"phase": row.phase_name, "count": row.operation_count}
                for row in creation_result
            ]
        }


# Analytics API endpoints
from fastapi import APIRouter, Depends, Query
from app.core.database import get_db
from typing import Optional

analytics_router = APIRouter()

@analytics_router.get("/phases/{phase_name}/metrics")
async def get_phase_metrics(
    phase_name: str,
    cycle_id: int = Query(...),
    report_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get metrics for a specific phase"""
    service = VersioningAnalyticsService(db)
    return await service.get_phase_metrics(cycle_id, report_id, phase_name)

@analytics_router.get("/workflows/{workflow_id}/metrics")
async def get_workflow_metrics(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get version metrics for entire workflow"""
    service = VersioningAnalyticsService(db)
    return await service.get_workflow_version_metrics(workflow_id)

@analytics_router.get("/trends/{phase_name}")
async def get_version_trends(
    phase_name: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get version creation trends"""
    service = VersioningAnalyticsService(db)
    return await service.get_version_trend_analysis(phase_name, days)

@analytics_router.get("/bottlenecks")
async def get_bottlenecks(
    cycle_id: int = Query(...),
    report_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Identify process bottlenecks"""
    service = VersioningAnalyticsService(db)
    return await service.get_bottleneck_analysis(cycle_id, report_id)