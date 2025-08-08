"""
Unified Status Service - Single source of truth for all phase and activity status
"""

from typing import Dict, List, Optional, Literal, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from dataclasses import dataclass

from app.models.workflow import WorkflowPhase
from app.models.scoping import ScopingSubmission, ReportOwnerScopingReview
from app.models.sample_selection import SampleSelectionVersion, SampleSelectionSample
from app.models.data_profiling import ProfilingResult, DataProfilingFile
from app.models.test_execution import TestExecution
from app.models.request_info import CycleReportTestCase
from app.models.observation_management import ObservationRecord
from app.models.report_attribute import ReportAttribute
from app.core.logging import get_logger
from app.core.activity_states import ActivityStateTracker, PHASE_ACTIVITIES, ActivityState
from app.services.activity_state_manager import ActivityStateManager
from app.services.activity_management_service import ActivityManagementService
from app.utils.phase_helpers import get_phase_id

logger = get_logger(__name__)

PhaseStatusType = Literal["not_started", "in_progress", "completed", "blocked"]
ActivityStatusType = Literal["pending", "active", "completed", "blocked", "skipped"]

@dataclass
class ActivityStatus:
    """Represents the status of an individual activity/step within a phase"""
    activity_id: str
    name: str
    description: str
    status: ActivityStatusType
    can_start: bool
    can_complete: bool
    can_reset: Optional[bool] = False
    completion_percentage: Optional[int] = None
    blocking_reason: Optional[str] = None
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = None

@dataclass
class PhaseStatus:
    """Unified status for a phase including all its activities"""
    phase_name: str
    cycle_id: int
    report_id: int
    phase_status: PhaseStatusType
    overall_completion_percentage: int
    activities: List[ActivityStatus]
    can_proceed_to_next: bool
    blocking_issues: List[str]
    last_updated: datetime
    metadata: Dict[str, Any] = None


class UnifiedStatusService:
    """Single service to handle all phase and activity status logic"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_phase_status(self, phase_name: str, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get unified status for any phase"""
        
        logger.info(f"Getting phase status for: {phase_name}, cycle: {cycle_id}, report: {report_id}")
        
        # Map database phase names to ActivityStateTracker names
        activity_tracker_mapping = {
            "Data Provider ID": "Data Provider Identification",
            "Request Info": "Request for Information",
            "Observations": "Observation Management",
            "Testing": "Test Execution"
        }
        
        # Get the ActivityStateTracker phase name
        tracker_phase_name = activity_tracker_mapping.get(phase_name, phase_name)
        
        # Use the activity management service for all phases
        # This ensures all phases use the database-driven activities
        try:
            return await self._get_phase_status_from_activity_management(phase_name, cycle_id, report_id)
        except Exception as e:
            logger.error(f"Error getting phase status from activity management: {e}")
            # Fallback to generic handler if activity management fails
            return await self._get_phase_status_generic(phase_name, cycle_id, report_id)
    
    async def _get_workflow_phase(self, phase_name: str, cycle_id: int, report_id: int) -> Optional[WorkflowPhase]:
        """Get the workflow phase record - OPTIMIZED with phase_id when available"""
        try:
            # ✅ OPTIMIZED: Try to get phase_id first for more efficient query
            phase_id = await get_phase_id(self.db, cycle_id, report_id, phase_name)
            
            if phase_id:
                # Direct phase_id lookup is much faster
                query = select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
            else:
                # Fallback to original composite key lookup
                query = select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == phase_name
                    )
                )
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting workflow phase: {str(e)}")
            # Fallback to original query
            query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
    
    async def _get_phase_status_from_activity_management(self, phase_name: str, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get phase status using the activity management service"""
        logger.info(f"Getting {phase_name} status from activity management for cycle {cycle_id}, report {report_id}")
        
        # Use the activity management service to get activities
        from app.services.activity_management_service import ActivityManagementService
        activity_service = ActivityManagementService(self.db)
        
        try:
            db_activities = await activity_service.get_phase_activities(
                phase_name=phase_name,
                cycle_id=cycle_id,
                report_id=report_id
            )
            logger.info(f"Got {len(db_activities)} activities from activity management service for {phase_name}")
        except Exception as e:
            logger.error(f"Failed to get activities from activity management service: {e}")
            raise
        
        # Convert to ActivityStatus objects
        activities = []
        for activity in db_activities:
            activities.append(ActivityStatus(
                activity_id=activity['activity_id'],
                name=activity['name'],
                description=activity['description'],
                status=activity['status'],
                can_start=activity['can_start'],
                can_complete=activity['can_complete'],
                can_reset=activity['can_reset'],
                completion_percentage=activity.get('completion_percentage', 0),
                blocking_reason=activity.get('blocking_reason'),
                last_updated=activity.get('last_updated'),
                metadata=activity.get('metadata', {})
            ))
        
        # Get workflow phase for overall status
        workflow_phase = await self._get_workflow_phase(phase_name, cycle_id, report_id)
        
        # Calculate overall phase status based on activities
        total = len(activities)
        completed = sum(1 for a in activities if a.status == 'completed')
        active = sum(1 for a in activities if a.status == 'active')
        
        if completed == total and total > 0:
            phase_status = "completed"
            # Don't update the database during a read operation
            # Phase state updates should be handled by activity transitions
        elif active > 0 or completed > 0:
            phase_status = "in_progress"
            # Don't update the database during a read operation
            # Phase state updates should be handled by activity transitions
        else:
            phase_status = "not_started"
        
        # Calculate overall completion
        if activities:
            total_completion = sum(a.completion_percentage or 0 for a in activities) / len(activities)
        else:
            total_completion = 0
        
        # Get phase-specific metadata for Data Provider ID
        metadata = {
            'started_at': workflow_phase.actual_start_date if workflow_phase else None,
            'completed_at': workflow_phase.actual_end_date if workflow_phase else None,
            'total_activities': total,
            'completed_activities': completed,
            'active_activities': active
        }
        
        # Use Universal Metrics Service for all phase-specific metrics
        try:
            from app.services.universal_metrics_service import (
                get_universal_metrics_service, MetricsContext
            )
            
            metrics_service = get_universal_metrics_service(self.db)
            metrics_context = MetricsContext(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name=phase_name
            )
            
            # Get phase-specific metrics
            phase_metrics = await metrics_service.get_phase_specific_metrics(metrics_context)
            
            # Add to metadata
            metadata.update(phase_metrics)
            
            logger.info(f"Added {phase_name} phase-specific metrics from Universal Metrics Service: {phase_metrics}")
        except Exception as e:
            logger.warning(f"Failed to get phase-specific metrics from Universal Metrics Service: {e}")
            # Continue without phase-specific metrics
        
        return PhaseStatus(
            phase_name=phase_name,
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase_status,
            overall_completion_percentage=int(total_completion),
            activities=activities,
            can_proceed_to_next=completed == total and total > 0,
            blocking_issues=[],
            last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow(),
            metadata=metadata
        )
    
    async def _get_phase_status_generic(self, phase_name: str, cycle_id: int, report_id: int) -> PhaseStatus:
        """Generic phase status using activity management service"""
        workflow_phase = await self._get_workflow_phase(phase_name, cycle_id, report_id)
        
        # Use ActivityManagementService for all phases
        activity_service = ActivityManagementService(self.db)
        try:
            db_activities = await activity_service.get_phase_activities(
                phase_name=phase_name,
                cycle_id=cycle_id,
                report_id=report_id
            )
            
            # Convert to ActivityStatus objects
            activities = []
            for activity in db_activities:
                activities.append(ActivityStatus(
                    activity_id=activity['activity_id'],
                    name=activity['name'],
                    description=activity['description'],
                    status=activity['status'],
                    can_start=activity['can_start'],
                    can_complete=activity['can_complete'],
                    can_reset=activity.get('can_reset', False),
                    completion_percentage=activity.get('completion_percentage', 0),
                    blocking_reason=activity.get('blocking_reason'),
                    last_updated=activity.get('last_updated'),
                    metadata=activity.get('metadata', {})
                ))
            
            # Calculate overall phase status
            total = len(activities)
            completed = sum(1 for a in activities if a.status == 'completed')
            in_progress = sum(1 for a in activities if a.status == 'active')
            
            if completed == total and total > 0:
                phase_status = "completed"
            elif in_progress > 0 or completed > 0:
                phase_status = "in_progress"
            else:
                phase_status = "not_started"
            
            completion_percentage = int((completed / total * 100) if total > 0 else 0)
            
            return PhaseStatus(
                phase_name=phase_name,
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status=phase_status,
                overall_completion_percentage=completion_percentage,
                activities=activities,
                can_proceed_to_next=bool(completed == total and total > 0),
                blocking_issues=[],
                last_updated=datetime.utcnow(),
                metadata={
                    'started_at': workflow_phase.actual_start_date if workflow_phase else None,
                    'completed_at': workflow_phase.actual_end_date if workflow_phase else None
                }
            )
        except Exception as e:
            logger.error(f"Error in _get_phase_status_generic: {e}")
            # Return empty phase status on error
            return PhaseStatus(
                phase_name=phase_name,
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status="not_started",
                overall_completion_percentage=0,
                activities=[],
                can_proceed_to_next=False,
                blocking_issues=[f"Error loading activities: {str(e)}"],
                last_updated=datetime.utcnow(),
                metadata={}
            )
    
    
    def _map_activity_state(self, state: str) -> ActivityStatusType:
        """Map ActivityState to ActivityStatusType"""
        mapping = {
            ActivityState.NOT_STARTED: "pending",
            ActivityState.IN_PROGRESS: "active",
            ActivityState.COMPLETED: "completed",
            ActivityState.REVISION_REQUESTED: "blocked"
        }
        return mapping.get(state, "pending")
    
    def _calculate_phase_status(self, tracker: ActivityStateTracker) -> PhaseStatusType:
        """Calculate overall phase status from activities"""
        progress = tracker.get_phase_progress()
        
        if progress['completed'] == progress['total_activities']:
            return "completed"
        elif progress['in_progress'] > 0 or progress['completed'] > 0:
            return "in_progress"
        else:
            return "not_started"
    
    def _get_blocking_issues(self, tracker: ActivityStateTracker) -> List[str]:
        """Get any blocking issues for the phase"""
        issues = []
        
        # Check for revision requested activities
        for activity_name, activity_data in tracker.activities.items():
            if activity_data['state'] == ActivityState.REVISION_REQUESTED:
                issues.append(f"{activity_name} requires revision")
        
        return issues
    
    async def _sync_phase_dates(self, workflow_phase: WorkflowPhase, tracker: ActivityStateTracker):
        """Automatically sync phase dates from activity tracker"""
        updates_needed = False
        
        # Find first started activity
        started_activities = [
            a for a in tracker.activities.values() 
            if a.get('started_at') is not None
        ]
        
        if started_activities:
            first_started = min(started_activities, key=lambda x: x['started_at'])
            if not workflow_phase.actual_start_date:
                workflow_phase.actual_start_date = first_started['started_at']
                workflow_phase.started_by = first_started.get('started_by')
                updates_needed = True
        
        # Check if all activities completed
        all_completed = all(
            a['state'] == ActivityState.COMPLETED 
            for a in tracker.activities.values()
        )
        
        if all_completed and not workflow_phase.actual_end_date:
            completed_activities = [
                a for a in tracker.activities.values() 
                if a.get('completed_at') is not None
            ]
            if completed_activities:
                last_completed = max(completed_activities, key=lambda x: x['completed_at'])
                workflow_phase.actual_end_date = last_completed['completed_at']
                workflow_phase.completed_by = last_completed.get('completed_by')
                workflow_phase.state = 'Complete'
                updates_needed = True
        
        if updates_needed:
            await self.db.commit()
    
    
    async def _get_planning_status(self, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get Planning phase status using activity management service"""
        workflow_phase = await self._get_workflow_phase("Planning", cycle_id, report_id)
        
        # Try to get activities from the activity management service first
        try:
            activity_service = ActivityManagementService(self.db)
            db_activities = await activity_service.get_phase_activities(
                phase_name="Planning",
                cycle_id=cycle_id,
                report_id=report_id
            )
            
            logger.info(f"Got {len(db_activities) if db_activities else 0} activities from activity management service for Planning phase")
            
            if db_activities:
                logger.info(f"Using database activities for Planning phase")
                # Convert database activities to ActivityStatus objects
                activities = []
                for db_activity in db_activities:
                    activities.append(ActivityStatus(
                        activity_id=db_activity['activity_id'],
                        name=db_activity['name'],
                        description=db_activity.get('description', ''),
                        status=db_activity['status'],
                        can_start=db_activity['can_start'],
                        can_complete=db_activity['can_complete'],
                        can_reset=db_activity.get('can_reset', False),
                        completion_percentage=100 if db_activity['status'] == "completed" else (50 if db_activity['status'] == "active" else 0),
                        blocking_reason=db_activity.get('blocking_reason'),
                        metadata=db_activity.get('metadata', {})
                    ))
                
                # Calculate overall phase status from activities
                completed_count = sum(1 for a in activities if a.status == "completed")
                active_count = sum(1 for a in activities if a.status == "active")
                total_count = len(activities)
                
                if completed_count == total_count and total_count > 0:
                    phase_status = "completed"
                elif active_count > 0 or completed_count > 0:
                    phase_status = "in_progress"
                else:
                    phase_status = "not_started"
                
                # Calculate overall completion
                total_completion = int((completed_count / total_count * 100)) if total_count > 0 else 0
                
                # Get additional metadata
                attr_query = select(func.count(ReportAttribute.id)).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.is_active == True
                    )
                )
                total_attrs = await self.db.scalar(attr_query) or 0
                
                approved_query = select(func.count(ReportAttribute.id)).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.is_active == True,
                        ReportAttribute.approval_status == 'approved'
                    )
                )
                approved_attrs = await self.db.scalar(approved_query) or 0
                
                return PhaseStatus(
                    phase_name="Planning",
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_status=phase_status,
                    overall_completion_percentage=total_completion,
                    activities=activities,
                    can_proceed_to_next=phase_status == "completed",
                    blocking_issues=[a.blocking_reason for a in activities if a.blocking_reason],
                    last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow(),
                    metadata={
                        "total_attributes": total_attrs,
                        "approved_attributes": approved_attrs,
                        "started_at": workflow_phase.actual_start_date if workflow_phase else None,
                        "completed_at": workflow_phase.actual_end_date if workflow_phase else None
                    }
                )
        except Exception as e:
            logger.error(f"Failed to get activities from activity management service: {e}", exc_info=True)
            # Fall back to legacy logic if activity management service fails
            pass
        
        # Legacy fallback logic (kept for backward compatibility)
        logger.warning("Using legacy fallback logic for Planning phase status")
        # Get attributes count
        attr_query = select(func.count(ReportAttribute.id)).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_active == True
            )
        )
        total_attrs = await self.db.scalar(attr_query)
        
        # Get approved attributes count
        approved_query = select(func.count(ReportAttribute.id)).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_active == True,
                ReportAttribute.approval_status == 'approved'
            )
        )
        approved_attrs = await self.db.scalar(approved_query)
        
        # Check if phase is started (first activity completed)
        phase_started = workflow_phase and workflow_phase.state in ["In Progress", "Complete"]
        
        # Define activities
        activities = [
            ActivityStatus(
                activity_id="start_planning",
                name="Start Planning Phase",
                description="Initialize planning phase and set timeline",
                status="completed" if phase_started else "pending",
                can_start=bool(not workflow_phase or workflow_phase.state == "Not Started"),
                can_complete=True,
                can_reset=bool(phase_started),
                completion_percentage=100 if phase_started else 0
            ),
            ActivityStatus(
                activity_id="load_attributes",
                name="Load Attributes",
                description="Load attributes from regulatory data dictionary",
                status="completed" if total_attrs > 0 else ("pending" if phase_started else "pending"),
                can_start=phase_started and total_attrs == 0,  # Can only start after phase is started
                can_complete=total_attrs > 0,
                can_reset=total_attrs > 0,
                completion_percentage=100 if total_attrs > 0 else 0
            ),
            ActivityStatus(
                activity_id="review_attributes",
                name="Review & Approve Attributes",
                description="Review and approve attributes for testing scope",
                status="completed" if approved_attrs == total_attrs and total_attrs > 0 else ("active" if total_attrs > 0 else "pending"),
                can_start=total_attrs > 0 and approved_attrs < total_attrs,  # Can only start after attributes are loaded
                can_complete=approved_attrs == total_attrs and total_attrs > 0,
                can_reset=bool(approved_attrs == total_attrs and total_attrs > 0),
                completion_percentage=int((approved_attrs / total_attrs * 100)) if total_attrs > 0 else 0
            ),
            ActivityStatus(
                activity_id="complete_planning",
                name="Complete Planning Phase",
                description="Finalize planning and proceed to scoping",
                status="completed" if workflow_phase and workflow_phase.state == "Complete" else ("active" if approved_attrs == total_attrs and total_attrs > 0 else "pending"),
                can_start=approved_attrs == total_attrs and total_attrs > 0,  # Can only start after all attributes approved
                can_complete=approved_attrs == total_attrs and total_attrs > 0,
                can_reset=bool(workflow_phase and workflow_phase.state == "Complete"),
                completion_percentage=100 if workflow_phase and workflow_phase.state == "Complete" else 0
            )
        ]
        
        # Determine overall phase status
        if not workflow_phase or workflow_phase.state == "Not Started":
            phase_status = "not_started"
        elif workflow_phase.state == "Complete":
            phase_status = "completed"
        else:
            phase_status = "in_progress"
        
        # Calculate overall completion
        total_completion = sum(a.completion_percentage or 0 for a in activities) / len(activities)
        
        return PhaseStatus(
            phase_name="Planning",
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase_status,
            overall_completion_percentage=int(total_completion),
            activities=activities,
            can_proceed_to_next=bool(workflow_phase and workflow_phase.state == "Complete"),
            blocking_issues=[],
            last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow(),
            metadata={
                "total_attributes": total_attrs or 0,
                "approved_attributes": approved_attrs or 0,
                "started_at": workflow_phase.actual_start_date if workflow_phase else None,
                "completed_at": workflow_phase.actual_end_date if workflow_phase else None
            }
        )
    
    async def _get_data_profiling_status(self, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get Data Profiling phase status"""
        logger.info(f"Getting Data Profiling status for cycle {cycle_id}, report {report_id}")
        
        # Use the activity management service to get activities
        activity_service = ActivityManagementService(self.db)
        try:
            db_activities = await activity_service.get_phase_activities(
                phase_name="Data Profiling",
                cycle_id=cycle_id,
                report_id=report_id
            )
            logger.info(f"Got {len(db_activities)} activities from activity management service")
        except Exception as e:
            logger.error(f"Failed to get activities from activity management service: {e}")
            logger.warning("Using legacy fallback logic for Data Profiling phase status")
            # Fallback to empty activities if service fails
            db_activities = []
        
        # Convert to ActivityStatus objects
        activities = []
        for activity in db_activities:
            activities.append(ActivityStatus(
                activity_id=activity['activity_id'],
                name=activity['name'],
                description=activity['description'],
                status=activity['status'],
                can_start=activity['can_start'],
                can_complete=activity['can_complete'],
                can_reset=activity['can_reset'],
                completion_percentage=activity.get('completion_percentage', 0),
                blocking_reason=activity.get('blocking_reason'),
                last_updated=activity.get('last_updated'),
                metadata=activity.get('metadata', {})
            ))
        
        # Get workflow phase for overall status
        workflow_phase = await self._get_workflow_phase("Data Profiling", cycle_id, report_id)
        
        # Determine overall phase status
        if not workflow_phase or workflow_phase.state == "Not Started":
            phase_status = "not_started"
        elif workflow_phase.state == "Complete":
            phase_status = "completed"
        else:
            phase_status = "in_progress"
        
        # Calculate overall completion
        if activities:
            total_completion = sum(a.completion_percentage or 0 for a in activities) / len(activities)
        else:
            total_completion = 0
        
        # Get profiling metrics from Planning phase
        from app.models.planning import PlanningAttribute
        
        # Get planning phase_id
        planning_phase_query = select(WorkflowPhase.phase_id).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        planning_phase_id = await self.db.scalar(planning_phase_query)
        
        # Count total attributes from planning phase
        total_attrs = 0
        if planning_phase_id:
            # Use the correct table name for planning attributes
            from app.models.planning import PlanningAttribute
            total_attrs_query = select(func.count(PlanningAttribute.attribute_id)).where(
                PlanningAttribute.phase_id == planning_phase_id
            )
            total_attrs = await self.db.scalar(total_attrs_query) or 0
        
        # Get data profiling phase_id
        data_profiling_phase_id = None
        if workflow_phase:
            data_profiling_phase_id = workflow_phase.phase_id
        
        # Count attributes with rules
        attributes_with_rules = 0
        total_profiling_rules = 0
        if data_profiling_phase_id:
            # Get latest version
            from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule
            latest_version_query = select(DataProfilingRuleVersion).where(
                DataProfilingRuleVersion.phase_id == data_profiling_phase_id
            ).order_by(DataProfilingRuleVersion.version_number.desc()).limit(1)
            latest_version_result = await self.db.execute(latest_version_query)
            latest_version = latest_version_result.scalar_one_or_none()
            
            if latest_version:
                # Count distinct attributes with rules (only approved by both tester and report owner)
                from app.models.data_profiling import Decision
                attrs_with_rules_query = select(func.count(func.distinct(ProfilingRule.attribute_id))).where(
                    and_(
                        ProfilingRule.version_id == latest_version.version_id,
                        ProfilingRule.tester_decision == Decision.APPROVED,
                        ProfilingRule.report_owner_decision == Decision.APPROVED
                    )
                )
                attributes_with_rules = await self.db.scalar(attrs_with_rules_query) or 0
                
                # Count total rules (only approved by both tester and report owner)
                total_rules_query = select(func.count(ProfilingRule.rule_id)).where(
                    and_(
                        ProfilingRule.version_id == latest_version.version_id,
                        ProfilingRule.tester_decision == Decision.APPROVED,
                        ProfilingRule.report_owner_decision == Decision.APPROVED
                    )
                )
                total_profiling_rules = await self.db.scalar(total_rules_query) or 0
        
        # Count profiled attributes (those with profiling results)
        profiled_attrs_query = select(func.count(func.distinct(ProfilingResult.attribute_id))).where(
            and_(
                ProfilingResult.phase_id == data_profiling_phase_id
            )
        )
        profiled_attrs = await self.db.scalar(profiled_attrs_query) or 0
        
        # Count attributes with anomalies (simplified - just count those with failed results)
        attributes_with_anomalies = 0
        cdes_with_anomalies = 0
        if data_profiling_phase_id:
            # Count attributes with any failed results
            anomaly_query = select(func.count(func.distinct(ProfilingResult.attribute_id))).where(
                and_(
                    ProfilingResult.phase_id == data_profiling_phase_id,
                    ProfilingResult.has_anomaly == True
                )
            )
            attributes_with_anomalies = await self.db.scalar(anomaly_query) or 0
            
            # For CDEs, we'd need to join with planning attributes to check is_cde flag
            # For now, just use 0
            cdes_with_anomalies = 0
        
        # Calculate completion percentage
        completion_percentage = 0
        if total_attrs > 0:
            completion_percentage = int((attributes_with_rules / total_attrs) * 100)
        
        return PhaseStatus(
            phase_name="Data Profiling",
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase_status,
            overall_completion_percentage=int(total_completion),
            activities=activities,
            can_proceed_to_next=bool(workflow_phase and workflow_phase.state == "Complete"),
            blocking_issues=[],
            last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow(),
            metadata={
                "total_attributes": total_attrs,
                "profiled_attributes": profiled_attrs,
                "attributes_with_rules": attributes_with_rules,
                "total_profiling_rules": total_profiling_rules,
                "rules_generated": total_profiling_rules,  # Same as total for now
                "attributes_with_anomalies": attributes_with_anomalies,
                "cdes_with_anomalies": cdes_with_anomalies,
                "days_elapsed": 1,  # TODO: Calculate from phase start date
                "completion_percentage": completion_percentage,
                "started_at": workflow_phase.actual_start_date if workflow_phase else None,
                "completed_at": workflow_phase.actual_end_date if workflow_phase else None
            }
        )
    
    async def _get_scoping_status(self, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get Scoping phase status"""
        workflow_phase = await self._get_workflow_phase("Scoping", cycle_id, report_id)
        
        # Get attributes data
        attr_query = select(ReportAttribute).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_active == True
            )
        )
        attributes = (await self.db.execute(attr_query)).scalars().all()
        
        total_attributes = len(attributes)
        approved_attributes = len([a for a in attributes if a.approval_status == 'approved'])
        attributes_with_recommendations = len([a for a in attributes if 
            a.llm_rationale or a.llm_risk_rationale or a.typical_source_documents])
        attributes_with_decisions = len([a for a in attributes if a.is_scoped is not None])
        scoped_attributes = len([a for a in attributes if a.is_scoped == True])
        
        # Get submission and review data
        submission_query = select(ScopingSubmission).where(
            and_(
                ScopingSubmission.cycle_id == cycle_id,
                ScopingSubmission.report_id == report_id
            )
        ).order_by(ScopingSubmission.version.desc())
        latest_submission = (await self.db.execute(submission_query)).scalars().first()
        
        review = None
        if latest_submission:
            review_query = select(ReportOwnerScopingReview).where(
                ReportOwnerScopingReview.submission_id == latest_submission.submission_id
            ).order_by(ReportOwnerScopingReview.created_at.desc())
            review = (await self.db.execute(review_query)).scalars().first()
        
        # Define activities
        activities = [
            ActivityStatus(
                activity_id="start_scoping",
                name="Start Scoping Phase",
                description="Initialize scoping phase and load attributes from planning",
                status="completed" if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else "pending",
                can_start=approved_attributes > 0,
                can_complete=approved_attributes > 0,
                can_reset=bool(workflow_phase and workflow_phase.state in ["In Progress", "Complete"]),
                completion_percentage=100 if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else 0
            ),
            ActivityStatus(
                activity_id="generate_recommendations",
                name="Generate LLM Recommendations",
                description="Generate AI-powered scoping recommendations for attributes",
                status="completed" if attributes_with_recommendations > 0 else ("active" if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else "pending"),
                can_start=workflow_phase and workflow_phase.state in ["In Progress", "Complete"],
                can_complete=attributes_with_recommendations > 0,
                can_reset=attributes_with_recommendations > 0,
                completion_percentage=int((attributes_with_recommendations / total_attributes * 100)) if total_attributes > 0 else 0
            ),
            ActivityStatus(
                activity_id="make_decisions",
                name="Make Scoping Decisions",
                description="Review recommendations and make final scoping decisions",
                status="completed" if attributes_with_decisions > 0 else ("active" if attributes_with_recommendations > 0 else "pending"),
                can_start=attributes_with_recommendations > 0,
                can_complete=attributes_with_decisions > 0,
                can_reset=attributes_with_decisions > 0,
                completion_percentage=int((attributes_with_decisions / total_attributes * 100)) if total_attributes > 0 else 0
            ),
            ActivityStatus(
                activity_id="submit_for_approval",
                name="Submit for Approval",
                description="Submit scoping decisions to Report Owner for review",
                status="completed" if latest_submission else ("active" if attributes_with_decisions > 0 else "pending"),
                can_start=attributes_with_decisions > 0,
                can_complete=attributes_with_decisions > 0,
                can_reset=latest_submission is not None,
                completion_percentage=100 if latest_submission else 0
            ),
            ActivityStatus(
                activity_id="report_owner_approval",
                name="Report Owner Approval",
                description="Report Owner reviews and approves scoping decisions",
                status="completed" if review and review.approval_status == "Approved" else ("active" if latest_submission else "pending"),
                can_start=latest_submission is not None,
                can_complete=False,  # Report Owner handles this
                can_reset=bool(review and review.approval_status == "Approved"),
                completion_percentage=100 if review and review.approval_status == "Approved" else 0
            ),
            ActivityStatus(
                activity_id="complete_scoping",
                name="Complete Scoping Phase",
                description="Finalize scoping and proceed to next phase",
                status="completed" if workflow_phase and workflow_phase.state == "Complete" else ("active" if review and review.approval_status == "Approved" else "pending"),
                can_start=review and review.approval_status == "Approved",
                can_complete=review and review.approval_status == "Approved",
                can_reset=bool(workflow_phase and workflow_phase.state == "Complete"),
                completion_percentage=100 if workflow_phase and workflow_phase.state == "Complete" else 0
            )
        ]
        
        # Determine overall phase status
        if not workflow_phase or workflow_phase.state == "Not Started":
            phase_status = "not_started"
        elif workflow_phase.state == "Complete":
            phase_status = "completed"
        else:
            phase_status = "in_progress"
        
        # Calculate overall completion
        total_completion = sum(a.completion_percentage or 0 for a in activities) / len(activities)
        
        blocking_issues = []
        if review and review.approval_status == "Needs Revision":
            blocking_issues.append("Report Owner requested revisions")
        
        return PhaseStatus(
            phase_name="Scoping",
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase_status,
            overall_completion_percentage=int(total_completion),
            activities=activities,
            can_proceed_to_next=bool(workflow_phase and workflow_phase.state == "Complete"),
            blocking_issues=blocking_issues,
            last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow(),
            metadata={
                "total_attributes": total_attributes,
                "attributes_with_decisions": attributes_with_decisions,
                "attributes_scoped_for_testing": scoped_attributes,
                "started_at": workflow_phase.actual_start_date if workflow_phase else None,
                "completed_at": workflow_phase.actual_end_date if workflow_phase else None
            }
        )
    
    async def _get_data_provider_id_status(self, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get Data Provider ID phase status"""
        workflow_phase = await self._get_workflow_phase("Data Provider ID", cycle_id, report_id)
        
        # Get metrics for Data Provider ID phase
        total_attributes_query = select(func.count(ReportAttribute.id)).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_latest_version == True
            )
        )
        total_attributes = await self.db.scalar(total_attributes_query) or 0
        
        scoped_attributes_query = select(func.count(ReportAttribute.id)).where(
            and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_scoped == True,
                ReportAttribute.is_latest_version == True
            )
        )
        scoped_attributes = await self.db.scalar(scoped_attributes_query) or 0
        
        # Get sample count (count unique samples used in test cases, same as Request Info phase)
        try:
            from app.models.request_info import CycleReportTestCase
            samples_query = select(func.count(func.distinct(CycleReportTestCase.sample_id))).where(
                and_(
                    CycleReportTestCase.cycle_id == cycle_id,
                    CycleReportTestCase.report_id == report_id
                )
            )
            total_samples = await self.db.scalar(samples_query) or 0
        except ImportError:
            total_samples = 0
        
        # Get LOB assignments and data providers
        try:
            # AttributeLOBAssignment removed - table doesn't exist
            from app.models.testing import DataOwnerAssignment
            from app.models.user import User
            from app.models.report import Report
            
            # Get the LOB for this specific report instead of LOB assignments
            report_lob_query = select(func.count(Report.lob_id)).where(
                Report.report_id == report_id
            )
            total_lobs = await self.db.scalar(report_lob_query) or 0
            
            # Get total data providers (users with Data Owner role)
            data_providers_query = select(func.count(User.user_id)).where(
                User.role == 'Data Owner'
            )
            total_data_providers = await self.db.scalar(data_providers_query) or 0
            
            # Get assigned data providers
            assigned_providers_query = select(func.count(func.distinct(DataOwnerAssignment.data_owner_id))).where(
                and_(
                    DataOwnerAssignment.cycle_id == cycle_id,
                    DataOwnerAssignment.report_id == report_id
                )
            )
            assigned_data_providers = await self.db.scalar(assigned_providers_query) or 0
            
            # Get data owner assignments count
            assignments_query = select(func.count(DataOwnerAssignment.assignment_id)).where(
                and_(
                    DataOwnerAssignment.cycle_id == cycle_id,
                    DataOwnerAssignment.report_id == report_id
                )
            )
            assignments_count = await self.db.scalar(assignments_query) or 0
            
            # Debug logging
            logger.info(f"Data Owner ID Status Debug - Cycle {cycle_id}, Report {report_id}")
            logger.info(f"Total attributes: {total_attributes}, Scoped attributes: {scoped_attributes}")
            logger.info(f"Total samples: {total_samples}")
            logger.info(f"Total LOBs: {total_lobs}, Total data providers: {total_data_providers}")
            logger.info(f"Assigned data providers: {assigned_data_providers}, Assignments count: {assignments_count}")
            
        except ImportError as e:
            logger.error(f"Import error in data provider status: {e}")
            # If models don't exist, use default values
            total_lobs = 0
            total_data_providers = 0
            assigned_data_providers = 0
            assignments_count = 0
        
        activities = [
            ActivityStatus(
                activity_id="start_data_provider_id",
                name="Start Data Owner ID Phase",
                description="Initialize data owner identification phase",
                status="completed" if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else "active",
                can_start=bool(not workflow_phase or workflow_phase.state == "Not Started"),
                can_complete=True,
                can_reset=bool(workflow_phase and workflow_phase.state in ["In Progress", "Complete"]),
                completion_percentage=100 if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else 0
            ),
            ActivityStatus(
                activity_id="identify_data_owners",
                name="Identify Data Owners",
                description="Identify and assign data owners for each attribute",
                status="completed" if assignments_count > 0 else "active",
                can_start=True,
                can_complete=assignments_count > 0,
                can_reset=assignments_count > 0,
                completion_percentage=100 if assignments_count > 0 else 0
            ),
            ActivityStatus(
                activity_id="complete_data_owner_assignments",
                name="Complete Data Owner Assignments",
                description="Finalize all data owner assignments",
                status="completed" if workflow_phase and workflow_phase.state == "Complete" else ("active" if assignments_count > 0 else "pending"),
                can_start=assignments_count > 0,
                can_complete=assignments_count > 0,
                can_reset=bool(workflow_phase and workflow_phase.state == "Complete"),
                completion_percentage=100 if workflow_phase and workflow_phase.state == "Complete" else 0
            )
        ]
        
        total_completion = sum(a.completion_percentage or 0 for a in activities) / len(activities)
        
        return PhaseStatus(
            phase_name="Data Provider ID",
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status="not_started" if not workflow_phase or workflow_phase.state == "Not Started" else "completed" if workflow_phase.state == "Complete" else "in_progress",
            overall_completion_percentage=int(total_completion),
            activities=activities,
            can_proceed_to_next=bool(workflow_phase and workflow_phase.state == "Complete"),
            blocking_issues=[],
            last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow(),
            metadata={
                "total_attributes": total_attributes,
                "scoped_attributes": scoped_attributes,
                "total_samples": total_samples,
                "total_lobs": total_lobs,
                "total_data_providers": total_data_providers,
                "assigned_data_providers": assigned_data_providers,
                "started_at": workflow_phase.actual_start_date if workflow_phase else None,
                "completed_at": workflow_phase.actual_end_date if workflow_phase else None
            }
        )
    
    async def _get_sample_selection_status(self, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get CycleReportSampleSelectionSamples Selection phase status"""
        workflow_phase = await self._get_workflow_phase("CycleReportSampleSelectionSamples Selection", cycle_id, report_id)
        
        # Get sample sets and reviews (using set_id as the primary key)
        sample_sets_query = select(SampleSet).where(
            and_(
                SampleSet.cycle_id == cycle_id,
                SampleSet.report_id == report_id
            )
        )
        sample_sets = (await self.db.execute(sample_sets_query)).scalars().all()
        
        total_sample_sets = len(sample_sets)
        
        # Get approval history
        # SampleApprovalHistory table removed - approval history now in SampleSelectionVersion.approval_notes
        # approval_history_query = select(SampleApprovalHistory).where(
        #     SampleApprovalHistory.set_id.in_([s.set_id for s in sample_sets])
        # ) if sample_sets else select(SampleApprovalHistory).where(False)
        approval_history = []  # SampleApprovalHistory table removed - data now in approval_notes
        
        # Get the latest approval status for each sample set
        # Updated to use status from SampleSelectionVersion instead of SampleApprovalHistory
        approved_sets = len([s for s in sample_sets if s.status == 'Approved'])
        reviewed_sets = len([s for s in sample_sets if s.status in ['Approved', 'Rejected', 'Revision Required']])
        
        # Count total samples and approved samples
        samples_count = sum(s.sample_count if hasattr(s, 'sample_count') else 0 for s in sample_sets)
        approved_samples = sum(s.sample_count if hasattr(s, 'sample_count') else 0 
                               for s in sample_sets if any(
                                   h.set_id == s.set_id and h.decision == 'Approved' 
                                   for h in approval_history
                               ))
        
        activities = [
            ActivityStatus(
                activity_id="generate_samples",
                name="Generate CycleReportSampleSelectionSamples Sets",
                description="Generate sample datasets for testing based on scoped attributes",
                status="completed" if total_sample_sets > 0 else "active",
                can_start=True,
                can_complete=total_sample_sets > 0,
                can_reset=total_sample_sets > 0,
                completion_percentage=100 if total_sample_sets > 0 else 0
            ),
            ActivityStatus(
                activity_id="review_samples",
                name="Review CycleReportSampleSelectionSamples Sets",
                description="Review and validate generated sample sets",
                status="completed" if reviewed_sets == total_sample_sets and total_sample_sets > 0 else ("active" if total_sample_sets > 0 else "pending"),
                can_start=total_sample_sets > 0,
                can_complete=total_sample_sets > 0,
                can_reset=bool(reviewed_sets == total_sample_sets and total_sample_sets > 0),
                completion_percentage=int((reviewed_sets / total_sample_sets * 100)) if total_sample_sets > 0 else 0
            ),
            ActivityStatus(
                activity_id="approve_samples",
                name="Approve CycleReportSampleSelectionSamples Sets",
                description="Final approval of sample sets for testing",
                status="completed" if approved_sets == total_sample_sets and total_sample_sets > 0 else ("active" if reviewed_sets > 0 else "pending"),
                can_start=reviewed_sets > 0,
                can_complete=approved_sets == total_sample_sets,
                can_reset=bool(approved_sets == total_sample_sets and total_sample_sets > 0),
                completion_percentage=int((approved_sets / total_sample_sets * 100)) if total_sample_sets > 0 else 0
            ),
            ActivityStatus(
                activity_id="complete_sample_selection",
                name="Complete CycleReportSampleSelectionSamples Selection",
                description="Finalize sample selection and proceed to next phase",
                status="completed" if workflow_phase and workflow_phase.state == "Complete" else ("active" if approved_sets == total_sample_sets and total_sample_sets > 0 else "pending"),
                can_start=approved_sets == total_sample_sets and total_sample_sets > 0,
                can_complete=approved_sets == total_sample_sets,
                can_reset=bool(workflow_phase and workflow_phase.state == "Complete"),
                completion_percentage=100 if workflow_phase and workflow_phase.state == "Complete" else 0
            )
        ]
        
        total_completion = sum(a.completion_percentage or 0 for a in activities) / len(activities)
        
        blocking_issues = []
        if total_sample_sets == 0:
            blocking_issues.append("No sample sets generated yet")
        
        return PhaseStatus(
            phase_name="CycleReportSampleSelectionSamples Selection",
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status="not_started" if not workflow_phase or workflow_phase.state == "Not Started" else "completed" if workflow_phase.state == "Complete" else "in_progress",
            overall_completion_percentage=int(total_completion),
            activities=activities,
            can_proceed_to_next=bool(workflow_phase and workflow_phase.state == "Complete"),
            blocking_issues=blocking_issues,
            last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow(),
            metadata={
                "total_attributes": await self.db.scalar(
                    select(func.count(ReportAttribute.id)).where(
                        and_(
                            ReportAttribute.cycle_id == cycle_id,
                            ReportAttribute.report_id == report_id,
                            ReportAttribute.is_scoped == True,
                            ReportAttribute.is_latest_version == True
                        )
                    )
                ) or 0,
                "total_samples": samples_count,
                "approved_samples": approved_samples,
                "started_at": workflow_phase.actual_start_date if workflow_phase else None,
                "completed_at": workflow_phase.actual_end_date if workflow_phase else None
            }
        )
    
    async def _get_request_info_status(self, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get Request Info phase status"""
        workflow_phase = await self._get_workflow_phase("Request Info", cycle_id, report_id)
        
        # Get request info phase and documents
        request_info_query = select(RequestInfoPhase).where(
            and_(
                RequestInfoPhase.cycle_id == cycle_id,
                RequestInfoPhase.report_id == report_id
            )
        )
        request_info_phase = (await self.db.execute(request_info_query)).scalars().first()
        
        # Get document submissions - check if DocumentSubmission model exists
        try:
            from app.models.document import DocumentSubmission
            documents_query = select(func.count(DocumentSubmission.submission_id)).where(
                and_(
                    DocumentSubmission.cycle_id == cycle_id,
                    DocumentSubmission.report_id == report_id
                )
            )
            documents_count = await self.db.scalar(documents_query) or 0
        except ImportError:
            # If DocumentSubmission model doesn't exist, assume no documents
            documents_count = 0
        
        # Check if phase has actually been started
        phase_started = workflow_phase and workflow_phase.state in ["In Progress", "Complete"]
        
        activities = [
            ActivityStatus(
                activity_id="start_phase",
                name="Start Request Info Phase",
                description="Begin the request for information phase",
                status="completed" if phase_started else "active",
                can_start=True,
                can_complete=True,
                can_reset=phase_started,
                completion_percentage=100 if phase_started else 0
            ),
            ActivityStatus(
                activity_id="initiate_requests",
                name="Initiate Information Requests",
                description="Send requests for additional information to data owners",
                status="completed" if request_info_phase else ("active" if phase_started else "pending"),
                can_start=phase_started,
                can_complete=phase_started,
                can_reset=request_info_phase is not None,
                completion_percentage=100 if request_info_phase else 0
            ),
            ActivityStatus(
                activity_id="collect_documents",
                name="Collect Documents",
                description="Collect and review submitted documents from data owners",
                status="completed" if documents_count > 0 else ("active" if request_info_phase else "pending"),
                can_start=request_info_phase is not None,
                can_complete=documents_count > 0,
                can_reset=documents_count > 0,
                completion_percentage=100 if documents_count > 0 else 0
            ),
            ActivityStatus(
                activity_id="complete_request_info",
                name="Complete Request Info Phase",
                description="Finalize information collection and proceed to testing",
                status="completed" if workflow_phase and workflow_phase.state == "Complete" else ("active" if documents_count > 0 else "pending"),
                can_start=documents_count > 0,
                can_complete=documents_count > 0,
                can_reset=bool(workflow_phase and workflow_phase.state == "Complete"),
                completion_percentage=100 if workflow_phase and workflow_phase.state == "Complete" else 0
            )
        ]
        
        total_completion = sum(a.completion_percentage or 0 for a in activities) / len(activities)
        
        # For Request Info phase, check the actual RequestInfoPhase status, not WorkflowPhase
        actual_phase_status = "not_started"
        if request_info_phase:
            if request_info_phase.phase_status == "In Progress":
                actual_phase_status = "in_progress"
            elif request_info_phase.phase_status == "Complete":
                actual_phase_status = "completed"
            else:
                actual_phase_status = "not_started"
        elif workflow_phase and workflow_phase.state in ["In Progress", "Complete"]:
            # Fallback to WorkflowPhase if RequestInfoPhase doesn't exist
            actual_phase_status = "completed" if workflow_phase.state == "Complete" else "in_progress"
        
        return PhaseStatus(
            phase_name="Request Info",
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=actual_phase_status,
            overall_completion_percentage=int(total_completion),
            activities=activities,
            can_proceed_to_next=bool(workflow_phase and workflow_phase.state == "Complete"),
            blocking_issues=[],
            last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow(),
            metadata={
                "total_attributes": await self.db.scalar(
                    select(func.count(ReportAttribute.id)).where(
                        and_(
                            ReportAttribute.cycle_id == cycle_id,
                            ReportAttribute.report_id == report_id,
                            ReportAttribute.is_scoped == True,
                            ReportAttribute.is_latest_version == True
                        )
                    )
                ) or 0,
                "scoped_attributes": await self.db.scalar(
                    select(func.count(ReportAttribute.id)).where(
                        and_(
                            ReportAttribute.cycle_id == cycle_id,
                            ReportAttribute.report_id == report_id,
                            ReportAttribute.is_scoped == True,
                            ReportAttribute.is_latest_version == True
                        )
                    )
                ) or 0,
                "test_cases": await self.db.scalar(
                    select(func.count(CycleReportTestCase.test_case_id)).where(
                        and_(
                            CycleReportTestCase.cycle_id == cycle_id,
                            CycleReportTestCase.report_id == report_id
                        )
                    )
                ) or 0,
                "documents_submitted": documents_count,
                "started_at": workflow_phase.actual_start_date if workflow_phase else None,
                "completed_at": workflow_phase.actual_end_date if workflow_phase else None
            }
        )
    
    async def _get_testing_status(self, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get Testing phase status"""
        # Try both "Testing" and "Test Execution" phase names
        workflow_phase = await self._get_workflow_phase("Test Execution", cycle_id, report_id)
        if not workflow_phase:
            workflow_phase = await self._get_workflow_phase("Testing", cycle_id, report_id)
        
        # Get test executions using ORM
        try:
            total_tests_query = select(func.count(TestExecution.id)).where(
                and_(
                    TestExecution.cycle_id == cycle_id,
                    TestExecution.report_id == report_id,
                    TestExecution.is_latest_execution == True
                )
            )
            total_tests = await self.db.scalar(total_tests_query) or 0
            
            completed_tests_query = select(func.count(TestExecution.id)).where(
                and_(
                    TestExecution.cycle_id == cycle_id,
                    TestExecution.report_id == report_id,
                    TestExecution.is_latest_execution == True,
                    TestExecution.test_result.isnot(None)
                )
            )
            completed_tests = await self.db.scalar(completed_tests_query) or 0
        except Exception as e:
            logger.error(f"Error querying test executions: {e}")
            total_tests = 0
            completed_tests = 0
        
        logger.info(f"Testing status check: total_tests={total_tests}, completed_tests={completed_tests}")
        
        # Get test results - check if TestResult model exists
        try:
            from app.models.testing import TestResult
            results_query = select(func.count(TestResult.test_result_id)).where(
                and_(
                    TestResult.cycle_id == cycle_id,
                    TestResult.report_id == report_id
                )
            )
            results_count = await self.db.scalar(results_query) or 0
        except ImportError:
            # If TestResult model doesn't exist, assume no results
            results_count = 0
        
        activities = [
            ActivityStatus(
                activity_id="start_phase",
                name="Start Test Execution Phase",
                description="Begin the test execution phase",
                status="completed" if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else "active",
                can_start=True,
                can_complete=True,
                can_reset=workflow_phase and workflow_phase.state in ["In Progress", "Complete"],
                completion_percentage=100 if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else 0
            ),
            ActivityStatus(
                activity_id="prepare_testing",
                name="Prepare Test Environment",
                description="Set up testing environment and validate sample data",
                status="completed" if total_tests > 0 else ("active" if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else "pending"),
                can_start=workflow_phase and workflow_phase.state in ["In Progress", "Complete"],
                can_complete=total_tests > 0,
                can_reset=total_tests > 0,
                completion_percentage=100 if total_tests > 0 else 0
            ),
            ActivityStatus(
                activity_id="execute_tests",
                name="Execute Tests",
                description="Execute testing procedures on sample data",
                status="completed" if completed_tests == total_tests and total_tests > 0 else ("active" if total_tests > 0 else "pending"),
                can_start=total_tests > 0,
                can_complete=completed_tests == total_tests,
                can_reset=completed_tests == total_tests and total_tests > 0,
                completion_percentage=int((completed_tests / total_tests * 100)) if total_tests > 0 else 0
            ),
            ActivityStatus(
                activity_id="document_results",
                name="Document Test Results",
                description="Document and validate test results",
                status="completed" if results_count > 0 else ("active" if completed_tests > 0 else "pending"),
                can_start=completed_tests > 0,
                can_complete=results_count > 0,
                can_reset=results_count > 0,
                completion_percentage=100 if results_count > 0 else 0
            ),
            ActivityStatus(
                activity_id="complete_testing",
                name="Complete Testing Phase",
                description="Finalize testing and proceed to observation management",
                status="completed" if workflow_phase and workflow_phase.state == "Complete" else ("active" if results_count > 0 else "pending"),
                can_start=results_count > 0,
                can_complete=results_count > 0,
                can_reset=bool(workflow_phase and workflow_phase.state == "Complete"),
                completion_percentage=100 if workflow_phase and workflow_phase.state == "Complete" else 0
            )
        ]
        
        total_completion = sum(a.completion_percentage or 0 for a in activities) / len(activities)
        
        blocking_issues = []
        if total_tests == 0:
            blocking_issues.append("No test executions found")
        
        can_proceed = completed_tests == total_tests and total_tests > 0
        logger.info(f"Testing can_proceed_to_next: {can_proceed} (completed_tests={completed_tests}, total_tests={total_tests})")
        
        # Determine phase status based on workflow state and activity completion
        if not workflow_phase or workflow_phase.state == "Not Started":
            phase_status = "not_started"
        elif workflow_phase.state == "Complete" or total_completion == 100:
            phase_status = "completed"
        else:
            phase_status = "in_progress"
        
        return PhaseStatus(
            phase_name="Test Execution",
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase_status,
            overall_completion_percentage=int(total_completion),
            activities=activities,
            can_proceed_to_next=can_proceed,
            blocking_issues=blocking_issues,
            last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow(),
            metadata={
                "total_attributes": await self.db.scalar(
                    select(func.count(ReportAttribute.id)).where(
                        and_(
                            ReportAttribute.cycle_id == cycle_id,
                            ReportAttribute.report_id == report_id,
                            ReportAttribute.is_latest_version == True
                        )
                    )
                ) or 0,
                "scoped_attributes": await self.db.scalar(
                    select(func.count(ReportAttribute.id)).where(
                        and_(
                            ReportAttribute.cycle_id == cycle_id,
                            ReportAttribute.report_id == report_id,
                            ReportAttribute.is_scoped == True,
                            ReportAttribute.is_latest_version == True
                        )
                    )
                ) or 0,
                "total_samples": await self.db.scalar(
                    select(func.count(func.distinct(CycleReportSampleSelectionSamples.id))).where(
                        and_(
                            CycleReportSampleSelectionSamples.cycle_id == cycle_id,
                            CycleReportSampleSelectionSamples.report_id == report_id,
                            CycleReportSampleSelectionSamples.approval_status == 'approved'
                        )
                    )
                ) or 0,
                "total_lobs": 1,  # Usually one LOB per report
                "total_data_providers": await self.db.scalar(
                    select(func.count(func.distinct(DataOwnerAssignment.data_owner_id))).where(
                        and_(
                            DataOwnerAssignment.cycle_id == cycle_id,
                            DataOwnerAssignment.report_id == report_id
                        )
                    )
                ) or 0,
                "started_at": workflow_phase.actual_start_date if workflow_phase else None,
                "completed_at": workflow_phase.actual_end_date if workflow_phase else None
            }
        )
    
    # Note: _get_test_execution_status removed as duplicate of _get_testing_status
    
    async def _get_observation_management_status(self, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get Observation Management phase status"""
        # Use "Observations" as the actual database enum value
        workflow_phase = await self._get_workflow_phase("Observations", cycle_id, report_id)
        
        # Get observation management phase and observations
        obs_mgmt_query = select(ObservationManagementPhase).where(
            and_(
                ObservationManagementPhase.cycle_id == cycle_id,
                ObservationManagementPhase.report_id == report_id
            )
        )
        obs_mgmt_phase = (await self.db.execute(obs_mgmt_query)).scalars().first()
        
        # Get observations - check if Observation model exists
        try:
            # Observation enhanced models removed - use observation_management models
            observations_query = select(func.count(Observation.observation_id)).where(
                and_(
                    Observation.cycle_id == cycle_id,
                    Observation.report_id == report_id
                )
            )
            observations_count = await self.db.scalar(observations_query) or 0
            
            # Get approved observation groups (approval status is on ObservationRecord, not Observation)
            # Observation enhanced models removed - use observation_management models
            approved_groups_query = select(func.count(ObservationRecord.group_id)).where(
                and_(
                    ObservationRecord.cycle_id == cycle_id,
                    ObservationRecord.report_id == report_id,
                    ObservationRecord.approval_status == ObservationApprovalStatusEnum.FULLY_APPROVED
                )
            )
            approved_observations = await self.db.scalar(approved_groups_query) or 0
        except ImportError:
            # If Observation model doesn't exist, assume no observations
            observations_count = 0
            approved_observations = 0
        
        activities = [
            ActivityStatus(
                activity_id="start_phase",
                name="Start Observation Management Phase",
                description="Begin the observation management phase",
                status="completed" if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else "active",
                can_start=True,
                can_complete=True,
                can_reset=workflow_phase and workflow_phase.state in ["In Progress", "Complete"],
                completion_percentage=100 if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else 0
            ),
            ActivityStatus(
                activity_id="identify_observations",
                name="Identify Observations",
                description="Identify and document testing observations and findings",
                status="completed" if observations_count > 0 else ("active" if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else "pending"),
                can_start=workflow_phase and workflow_phase.state in ["In Progress", "Complete"],
                can_complete=observations_count > 0,
                can_reset=observations_count > 0,
                completion_percentage=100 if observations_count > 0 else 0
            ),
            ActivityStatus(
                activity_id="review_observations",
                name="Review Observations",
                description="Review and validate identified observations",
                status="completed" if approved_observations == observations_count and observations_count > 0 else ("active" if observations_count > 0 else "pending"),
                can_start=observations_count > 0,
                can_complete=observations_count > 0,
                can_reset=approved_observations == observations_count and observations_count > 0,
                completion_percentage=int((approved_observations / observations_count * 100)) if observations_count > 0 else 0
            ),
            ActivityStatus(
                activity_id="complete_phase",
                name="Complete Observation Management Phase",
                description="Finalize all observations and complete the phase",
                status="completed" if workflow_phase and workflow_phase.state == "Complete" else ("active" if approved_observations == observations_count and observations_count > 0 else "pending"),
                can_start=approved_observations == observations_count and observations_count > 0,
                can_complete=approved_observations == observations_count and observations_count > 0,
                can_reset=bool(workflow_phase and workflow_phase.state == "Complete"),
                completion_percentage=100 if workflow_phase and workflow_phase.state == "Complete" else 0
            )
        ]
        
        total_completion = sum(a.completion_percentage or 0 for a in activities) / len(activities)
        
        blocking_issues = []
        if observations_count == 0:
            blocking_issues.append("No observations identified yet")
        
        return PhaseStatus(
            phase_name="Observations",  # Use the actual database enum value
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status="not_started" if not workflow_phase or workflow_phase.state == "Not Started" else "completed" if workflow_phase.state == "Complete" else "in_progress",
            overall_completion_percentage=int(total_completion),
            activities=activities,
            can_proceed_to_next=bool(workflow_phase and workflow_phase.state == "Complete"),
            blocking_issues=blocking_issues,
            last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow(),
            metadata={
                "total_attributes": await self.db.scalar(
                    select(func.count(ReportAttribute.id)).where(
                        and_(
                            ReportAttribute.cycle_id == cycle_id,
                            ReportAttribute.report_id == report_id,
                            ReportAttribute.is_latest_version == True
                        )
                    )
                ) or 0,
                "scoped_attributes": await self.db.scalar(
                    select(func.count(ReportAttribute.id)).where(
                        and_(
                            ReportAttribute.cycle_id == cycle_id,
                            ReportAttribute.report_id == report_id,
                            ReportAttribute.is_scoped == True,
                            ReportAttribute.is_latest_version == True
                        )
                    )
                ) or 0,
                "total_samples": await self.db.scalar(
                    select(func.count(func.distinct(CycleReportSampleSelectionSamples.id))).where(
                        and_(
                            CycleReportSampleSelectionSamples.cycle_id == cycle_id,
                            CycleReportSampleSelectionSamples.report_id == report_id,
                            CycleReportSampleSelectionSamples.approval_status == 'approved'
                        )
                    )
                ) or 0,
                "total_observations": observations_count,
                "approved_observations": approved_observations,
                "started_at": workflow_phase.actual_start_date if workflow_phase else None,
                "completed_at": workflow_phase.actual_end_date if workflow_phase else None
            }
        )
    
    async def _get_finalize_test_report_status(self, cycle_id: int, report_id: int) -> PhaseStatus:
        """Get Finalize Test Report phase status"""
        workflow_phase = await self._get_workflow_phase("Finalize Test Report", cycle_id, report_id)
        
        # Check if test report phase exists
        # TestReportPhase has been deprecated - using WorkflowPhase instead
        # # Observation enhanced models removed - use observation_management models
        from sqlalchemy import text
        
        # Get test report phase info
        result = await self.db.execute(
            text("SELECT status FROM test_report_phases WHERE cycle_id = :cycle_id AND report_id = :report_id"),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        report_status = result.scalar()
        
        # Check if report sections exist
        result = await self.db.execute(
            text("""
                SELECT COUNT(*) 
                FROM cycle_report_test_report_sections trs
                JOIN test_report_phases trp ON trs.phase_id = trp.phase_id
                WHERE trp.cycle_id = :cycle_id AND trp.report_id = :report_id
            """),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        sections_count = result.scalar() or 0
        
        activities = [
            ActivityStatus(
                activity_id="start_finalize_report",
                name="Start Finalize Report Phase",
                description="Initialize report finalization phase",
                status="completed" if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else "active",
                can_start=True,
                can_complete=True,
                can_reset=bool(workflow_phase and workflow_phase.state in ["In Progress", "Complete"]),
                completion_percentage=100 if workflow_phase and workflow_phase.state in ["In Progress", "Complete"] else 0
            ),
            ActivityStatus(
                activity_id="configure_report",
                name="Configure Report Settings",
                description="Configure report sections and options",
                status="completed" if report_status else "active",
                can_start=True,
                can_complete=True,
                can_reset=report_status is not None,
                completion_percentage=100 if report_status else 0
            ),
            ActivityStatus(
                activity_id="generate_report",
                name="Generate Test Report",
                description="Generate comprehensive test report with all findings",
                status="completed" if sections_count > 0 else ("active" if report_status else "pending"),
                can_start=report_status is not None,
                can_complete=report_status is not None,
                can_reset=sections_count > 0,
                completion_percentage=100 if sections_count > 0 else 0
            ),
            ActivityStatus(
                activity_id="review_report",
                name="Review & Finalize Report",
                description="Review and finalize the test report",
                status="completed" if report_status == "Report Generated" else ("active" if sections_count > 0 else "pending"),
                can_start=sections_count > 0,
                can_complete=sections_count > 0,
                can_reset=report_status == "Report Generated",
                completion_percentage=100 if report_status == "Report Generated" else 0
            ),
            ActivityStatus(
                activity_id="complete_phase",
                name="Complete Test Report Phase",
                description="Complete the test report phase and archive the cycle",
                status="completed" if workflow_phase and workflow_phase.state == "Complete" else ("active" if report_status == "Report Generated" else "pending"),
                can_start=report_status == "Report Generated",
                can_complete=report_status == "Report Generated",
                can_reset=bool(workflow_phase and workflow_phase.state == "Complete"),
                completion_percentage=100 if workflow_phase and workflow_phase.state == "Complete" else 0
            )
        ]
        
        total_completion = sum(a.completion_percentage or 0 for a in activities) / len(activities)
        
        blocking_issues = []
        if not report_status:
            blocking_issues.append("Report configuration not started")
        elif sections_count == 0:
            blocking_issues.append("Report not yet generated")
        
        return PhaseStatus(
            phase_name="Finalize Test Report",
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status="not_started" if not workflow_phase or workflow_phase.state == "Not Started" else "completed" if workflow_phase.state == "Complete" else "in_progress",
            overall_completion_percentage=int(total_completion),
            activities=activities,
            can_proceed_to_next=bool(workflow_phase and workflow_phase.state == "Complete"),
            blocking_issues=blocking_issues,
            last_updated=workflow_phase.updated_at if workflow_phase else datetime.utcnow()
        )

def get_unified_status_service(db: AsyncSession) -> UnifiedStatusService:
    """Dependency to get unified status service"""
    return UnifiedStatusService(db)