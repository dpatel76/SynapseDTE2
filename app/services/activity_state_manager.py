"""
Activity State Manager Service
Manages activity transitions and state updates with event-driven automation
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.activity_states import (
    ActivityState, ActivityType, ActivityTransitionValidator,
    ActivityStateTracker, ACTIVITY_TRANSITIONS, PHASE_ACTIVITIES
)
from app.models.workflow_tracking import WorkflowStep
from app.models.workflow import WorkflowPhase
from app.models.metrics import ExecutionMetrics
from app.models.workflow_tracking import WorkflowExecutionStatus
from app.schemas.workflow_phase import WorkflowPhaseState

logger = logging.getLogger(__name__)


class ActivityStateManager:
    """Manages activity state transitions and workflow automation"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._event_handlers = {}
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register event handlers for automatic transitions"""
        self._event_handlers = {
            "submission": self._handle_submission_event,
            "approval_decision": self._handle_approval_event,
            "all_assignments_complete": self._handle_assignments_complete,
            "all_providers_assigned": self._handle_providers_assigned,
            "previous_complete": self._handle_previous_complete
        }
    
    async def transition_activity(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        activity_name: str,
        target_state: ActivityState,
        user_id: str,
        user_role: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transition an activity to a new state
        
        Returns:
            Dict with success status and any error messages
        """
        try:
            # Get current phase and activity state
            phase = await self._get_workflow_phase(cycle_id, report_id, phase_name)
            if not phase:
                return {"success": False, "error": "Phase not found"}
            
            # Initialize activity tracker from phase data
            tracker = self._load_activity_tracker(phase)
            current_activity = tracker.activities.get(activity_name)
            
            if not current_activity:
                return {"success": False, "error": f"Activity {activity_name} not found"}
            
            current_state = current_activity["state"]
            
            # Validate transition
            can_transition, error = ActivityTransitionValidator.can_transition(
                activity_name=activity_name,
                current_state=current_state,
                target_state=target_state,
                user_role=user_role,
                context=context
            )
            
            if not can_transition:
                return {"success": False, "error": error}
            
            # Perform transition
            if target_state == ActivityState.IN_PROGRESS:
                tracker.start_activity(activity_name, user_id)
            elif target_state == ActivityState.COMPLETED:
                tracker.complete_activity(activity_name, user_id)
            elif target_state == ActivityState.REVISION_REQUESTED:
                tracker.request_revision(activity_name)
            
            # Update phase data
            await self._save_activity_tracker(phase, tracker)
            
            # Record execution metrics
            await self._record_execution_metrics(
                cycle_id, report_id, phase_name, activity_name,
                current_state, target_state, user_id
            )
            
            # Check for automatic transitions
            await self._check_automatic_transitions(
                cycle_id, report_id, phase_name, activity_name, target_state, tracker
            )
            
            # Update phase state if needed
            await self._update_phase_state_if_needed(
                phase, activity_name, target_state, tracker
            )
            
            return {
                "success": True,
                "activity_state": target_state,
                "phase_progress": tracker.get_phase_progress()
            }
            
        except Exception as e:
            logger.error(f"Error transitioning activity: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def handle_event(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle workflow events that trigger automatic transitions
        
        Events include:
        - submission: Form submitted for review
        - approval_decision: Approval or rejection
        - assignments_complete: All assignments done
        - etc.
        """
        try:
            handler = self._event_handlers.get(event_type)
            if not handler:
                logger.warning(f"No handler for event type: {event_type}")
                return {"success": False, "error": f"Unknown event type: {event_type}"}
            
            return await handler(cycle_id, report_id, phase_name, event_data)
            
        except Exception as e:
            logger.error(f"Error handling event {event_type}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_phase_activities(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str
    ) -> Dict[str, Any]:
        """Get current state of all activities in a phase"""
        try:
            phase = await self._get_workflow_phase(cycle_id, report_id, phase_name)
            if not phase:
                return {"error": "Phase not found"}
            
            tracker = self._load_activity_tracker(phase)
            
            return {
                "phase_name": phase_name,
                "activities": tracker.activities,
                "progress": tracker.get_phase_progress(),
                "next_activity": tracker.get_next_activity()
            }
            
        except Exception as e:
            logger.error(f"Error getting phase activities: {str(e)}")
            return {"error": str(e)}
    
    # Event Handlers
    
    async def _handle_submission_event(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle submission event - auto-complete Tester Review"""
        user_id = event_data.get("user_id")
        submission_id = event_data.get("submission_id")
        
        # Find and complete the Tester Review activity
        phase = await self._get_workflow_phase(cycle_id, report_id, phase_name)
        tracker = self._load_activity_tracker(phase)
        
        tester_review = None
        for activity_name, activity in tracker.activities.items():
            if "Tester Review" in activity_name and activity["state"] == ActivityState.IN_PROGRESS:
                tester_review = activity_name
                break
        
        if tester_review:
            result = await self.transition_activity(
                cycle_id, report_id, phase_name, tester_review,
                ActivityState.COMPLETED, user_id, "Tester", event_data
            )
            
            # Auto-start Report Owner Approval if present
            if result["success"]:
                await self._auto_start_next_activity(
                    cycle_id, report_id, phase_name, tracker
                )
            
            return result
        
        return {"success": False, "error": "No active Tester Review found"}
    
    async def _handle_approval_event(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle approval decision event"""
        user_id = event_data.get("user_id")
        decision = event_data.get("decision")  # approved or rejected
        
        phase = await self._get_workflow_phase(cycle_id, report_id, phase_name)
        tracker = self._load_activity_tracker(phase)
        
        # Find Report Owner Approval activity
        approval_activity = None
        for activity_name, activity in tracker.activities.items():
            if "Report Owner Approval" in activity_name and activity["state"] == ActivityState.IN_PROGRESS:
                approval_activity = activity_name
                break
        
        if not approval_activity:
            return {"success": False, "error": "No active approval found"}
        
        if decision == "approved":
            # Complete the approval
            result = await self.transition_activity(
                cycle_id, report_id, phase_name, approval_activity,
                ActivityState.COMPLETED, user_id, "Report Owner", event_data
            )
            
            # Auto-start next activity
            if result["success"]:
                await self._auto_start_next_activity(
                    cycle_id, report_id, phase_name, tracker
                )
            
            return result
        
        elif decision == "rejected":
            # Mark for revision
            tracker.request_revision(approval_activity)
            
            # Find previous activity (Tester Review) and mark for revision
            for activity_name, activity in tracker.activities.items():
                if "Tester Review" in activity_name:
                    tracker.request_revision(activity_name)
                    break
            
            await self._save_activity_tracker(phase, tracker)
            
            # Update phase state
            phase.state = WorkflowPhaseState.IN_PROGRESS
            await self.db.commit()
            
            return {"success": True, "action": "revision_requested"}
        
        return {"success": False, "error": "Invalid decision"}
    
    async def _handle_assignments_complete(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle all LOB assignments complete"""
        user_id = event_data.get("user_id")
        
        # Validate all LOBs are assigned
        lobs = event_data.get("lobs", [])
        all_assigned = all(lob.get("executive_assigned") for lob in lobs)
        
        if not all_assigned:
            return {"success": False, "error": "Not all LOBs assigned"}
        
        # Complete the Data Executive Assignment activity
        return await self.transition_activity(
            cycle_id, report_id, phase_name,
            "Data Executive Assignment",
            ActivityState.COMPLETED,
            user_id, "CDO", event_data
        )
    
    async def _handle_providers_assigned(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle all providers assigned"""
        user_id = event_data.get("user_id")
        
        # Validate all providers are assigned
        assignments = event_data.get("provider_assignments", [])
        all_assigned = all(a.get("provider_assigned") for a in assignments)
        
        if not all_assigned:
            return {"success": False, "error": "Not all providers assigned"}
        
        # Complete the Data Owner Assignment activity
        return await self.transition_activity(
            cycle_id, report_id, phase_name,
            "Data Owner Assignment",
            ActivityState.COMPLETED,
            user_id, "Data Owner", event_data
        )
    
    async def _handle_previous_complete(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle previous activity completion - auto-start next"""
        phase = await self._get_workflow_phase(cycle_id, report_id, phase_name)
        tracker = self._load_activity_tracker(phase)
        
        return await self._auto_start_next_activity(
            cycle_id, report_id, phase_name, tracker
        )
    
    # Helper Methods
    
    async def _get_workflow_phase(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str
    ) -> Optional[WorkflowPhase]:
        """Get workflow phase from database"""
        query = select(WorkflowPhase).where(
            (WorkflowPhase.cycle_id == cycle_id) &
            (WorkflowPhase.report_id == report_id) &
            (WorkflowPhase.phase_name == phase_name)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    def _load_activity_tracker(self, phase: WorkflowPhase) -> ActivityStateTracker:
        """Load activity tracker from phase data"""
        tracker = ActivityStateTracker(phase.phase_name)
        
        # Load saved state if exists
        if phase.phase_data and "activities" in phase.phase_data:
            tracker.activities = phase.phase_data["activities"]
        
        return tracker
    
    async def _save_activity_tracker(
        self,
        phase: WorkflowPhase,
        tracker: ActivityStateTracker
    ):
        """Save activity tracker to phase data"""
        if not phase.phase_data:
            phase.phase_data = {}
        
        phase.phase_data.update(tracker.to_dict())
        await self.db.commit()
    
    async def _check_automatic_transitions(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        completed_activity: str,
        new_state: ActivityState,
        tracker: ActivityStateTracker
    ):
        """Check for automatic transitions after activity state change"""
        if new_state != ActivityState.COMPLETED:
            return
        
        # Check if we should auto-start the next activity
        next_activity = tracker.get_next_activity()
        if next_activity:
            # Check if it's an auto-start activity
            activity_type = ActivityTransitionValidator._get_activity_type(next_activity)
            rules = ACTIVITY_TRANSITIONS.get(activity_type, {})
            
            if not rules.get("manual", False):
                # Auto-start the activity
                tracker.start_activity(next_activity, "system")
                await self._save_activity_tracker(
                    await self._get_workflow_phase(cycle_id, report_id, phase_name),
                    tracker
                )
                
                # Emit event for further processing
                await self.handle_event(
                    cycle_id, report_id, phase_name,
                    "previous_complete",
                    {"previous_activity": completed_activity}
                )
    
    async def _update_phase_state_if_needed(
        self,
        phase: WorkflowPhase,
        activity_name: str,
        activity_state: ActivityState,
        tracker: ActivityStateTracker
    ):
        """Update phase state based on activity transitions"""
        activity_type = ActivityTransitionValidator._get_activity_type(activity_name)
        rules = ACTIVITY_TRANSITIONS.get(activity_type, {})
        
        # Check if this activity updates phase state
        if activity_state == ActivityState.IN_PROGRESS and rules.get("updates_phase_state") == "In Progress":
            if phase.state == WorkflowPhaseState.NOT_STARTED:
                phase.state = WorkflowPhaseState.IN_PROGRESS
                phase.actual_start_date = datetime.utcnow()
                await self.db.commit()
        
        elif activity_state == ActivityState.COMPLETED and rules.get("updates_phase_state") == "Completed":
            phase.state = WorkflowPhaseState.COMPLETE
            phase.actual_end_date = datetime.utcnow()
            await self.db.commit()
    
    async def _record_execution_metrics(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        activity_name: str,
        from_state: ActivityState,
        to_state: ActivityState,
        user_id: str
    ):
        """Record activity execution metrics"""
        # Check if we're starting an activity
        if from_state == ActivityState.NOT_STARTED and to_state == ActivityState.IN_PROGRESS:
            metric = ExecutionMetrics(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name=phase_name,
                activity_name=activity_name,
                user_id=user_id,
                start_time=datetime.utcnow(),
                status="started"
            )
            self.db.add(metric)
        
        # Check if we're completing an activity
        elif from_state == ActivityState.IN_PROGRESS and to_state == ActivityState.COMPLETED:
            # Find the start record
            query = select(ExecutionMetrics).where(
                (ExecutionMetrics.cycle_id == cycle_id) &
                (ExecutionMetrics.report_id == report_id) &
                (ExecutionMetrics.phase_name == phase_name) &
                (ExecutionMetrics.activity_name == activity_name) &
                (ExecutionMetrics.status == "started")
            ).order_by(ExecutionMetrics.start_time.desc())
            
            result = await self.db.execute(query)
            start_metric = result.scalar_one_or_none()
            
            if start_metric:
                start_metric.end_time = datetime.utcnow()
                start_metric.duration_minutes = (
                    (start_metric.end_time - start_metric.start_time).total_seconds() / 60
                )
                start_metric.status = "completed"
            else:
                # Create completion record if no start found
                metric = ExecutionMetrics(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name=phase_name,
                    activity_name=activity_name,
                    user_id=user_id,
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    duration_minutes=0,
                    status="completed"
                )
                self.db.add(metric)
        
        await self.db.commit()
    
    async def _auto_start_next_activity(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        tracker: ActivityStateTracker
    ) -> Dict[str, Any]:
        """Automatically start the next activity if eligible"""
        next_activity = tracker.get_next_activity()
        if not next_activity:
            return {"success": True, "message": "No next activity"}
        
        # Check if it's an auto-start activity
        activity_type = ActivityTransitionValidator._get_activity_type(next_activity)
        rules = ACTIVITY_TRANSITIONS.get(activity_type, {})
        
        if not rules.get("manual", False):
            tracker.start_activity(next_activity, "system")
            phase = await self._get_workflow_phase(cycle_id, report_id, phase_name)
            await self._save_activity_tracker(phase, tracker)
            
            await self._record_execution_metrics(
                cycle_id, report_id, phase_name, next_activity,
                ActivityState.NOT_STARTED, ActivityState.IN_PROGRESS, "system"
            )
            
            return {
                "success": True,
                "auto_started": next_activity
            }
        
        return {"success": True, "next_activity_manual": next_activity}
    
    async def reset_activity_cascade(
        self,
        cycle_id: str,
        report_id: str,
        phase_name: str,
        activity_name: str,
        user_id: str,
        user_role: str
    ) -> Dict[str, Any]:
        """Reset an activity and all dependent activities"""
        
        # Check permissions - only Tester and Test Manager can reset
        if user_role not in ["Tester", "Test Manager"]:
            return {
                "success": False,
                "error": "Only Tester or Test Manager can reset activities"
            }
        
        try:
            # Get phase and load tracker
            phase = await self._get_workflow_phase(cycle_id, report_id, phase_name)
            if not phase:
                return {"success": False, "error": "Phase not found"}
            
            tracker = self._load_activity_tracker(phase)
            
            # Perform cascade reset
            reset_activities = tracker.reset_activity_cascade(activity_name, user_id)
            
            if not reset_activities:
                return {
                    "success": False,
                    "error": "Activity cannot be reset or is not completed"
                }
            
            # Update phase state if needed
            if phase.state == 'Complete':
                phase.state = 'In Progress'
                phase.actual_end_date = None
                phase.completed_by = None
            
            # Save updated tracker
            await self._save_activity_tracker(phase, tracker)
            
            # Log the reset action
            logger.info(
                f"User {user_id} reset {len(reset_activities)} activities "
                f"in phase {phase_name} for cycle {cycle_id}, report {report_id}"
            )
            
            return {
                "success": True,
                "reset_activities": reset_activities,
                "message": f"Reset {len(reset_activities)} activities successfully"
            }
            
        except Exception as e:
            logger.error(f"Error resetting activities: {str(e)}")
            return {"success": False, "error": str(e)}


# Service singleton
_activity_state_manager = None


def get_activity_state_manager(db: AsyncSession) -> ActivityStateManager:
    """Get activity state manager instance"""
    global _activity_state_manager
    if _activity_state_manager is None or _activity_state_manager.db != db:
        _activity_state_manager = ActivityStateManager(db)
    return _activity_state_manager