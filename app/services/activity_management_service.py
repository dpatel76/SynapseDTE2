"""
Activity Management Service
Handles activity state transitions and dependency management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from app.models.workflow_activity import WorkflowActivity, ActivityStatus, ActivityType
from app.models.workflow import WorkflowPhase
from app.core.logging import get_logger
from app.core.exceptions import BusinessLogicException, ValidationException

logger = get_logger(__name__)


class ActivityManagementService:
    """Service for managing activity states and transitions"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_phase_activities(
        self, 
        phase_name: str, 
        cycle_id: int, 
        report_id: int
    ) -> List[Dict[str, Any]]:
        """Get all activities for a phase with their current states"""
        
        try:
            # Get workflow activities for the phase
            activities_query = select(WorkflowActivity).where(
                and_(
                    WorkflowActivity.cycle_id == cycle_id,
                    WorkflowActivity.report_id == report_id,
                    WorkflowActivity.phase_name == phase_name
                )
            ).order_by(WorkflowActivity.activity_order)
            
            result = await self.db.execute(activities_query)
            workflow_activities = result.scalars().all()
            
            # Build activity list
            activities = []
            
            for activity in workflow_activities:
                # Check if activity can be started based on previous activities
                can_start = activity.can_start
                can_complete = activity.can_complete
                blocking_reason = None
                
                if activity.activity_order > 1 and not can_start:
                    # Check if previous activity is completed
                    prev_activity_query = select(WorkflowActivity).where(
                        and_(
                            WorkflowActivity.cycle_id == cycle_id,
                            WorkflowActivity.report_id == report_id,
                            WorkflowActivity.phase_name == phase_name,
                            WorkflowActivity.activity_order == activity.activity_order - 1
                        )
                    )
                    prev_result = await self.db.execute(prev_activity_query)
                    prev_activity = prev_result.scalar_one_or_none()
                    
                    if prev_activity and prev_activity.status == ActivityStatus.COMPLETED:
                        can_start = True
                        # Update the activity
                        activity.can_start = True
                        await self.db.commit()
                    elif prev_activity:
                        blocking_reason = f"Previous activity '{prev_activity.activity_name}' must be completed first"
                
                # For manual activities that are in progress, they can be completed
                if activity.is_manual and activity.status == ActivityStatus.IN_PROGRESS:
                    can_complete = True
                
                activity_data = {
                    'activity_id': f"{activity.phase_name}_{activity.activity_order}",  # Create a unique ID
                    'name': activity.activity_name,
                    'description': f"{activity.activity_type.value} activity for {phase_name} phase",
                    'status': activity.status.value.lower(),  # Convert to lowercase for frontend
                    'can_start': can_start,
                    'can_complete': can_complete,
                    'can_reset': False,  # Not implemented yet
                    'completion_percentage': 100 if activity.status == ActivityStatus.COMPLETED else 0,
                    'blocking_reason': blocking_reason,
                    'last_updated': activity.updated_at or activity.created_at,
                    'metadata': {
                        'activity_type': activity.activity_type.value,
                        'button_text': self._get_button_text(activity, can_start, can_complete),
                        'success_message': f'{activity.activity_name} completed successfully',
                        'instructions': f'Complete the {activity.activity_name} activity',
                        'can_skip': activity.is_optional,
                        'started_by': activity.started_by,
                        'completed_by': activity.completed_by,
                        'definition_id': activity.activity_id,
                        'state_id': activity.activity_id,
                        'is_manual': activity.is_manual,
                        'activity_order': activity.activity_order
                    }
                }
                
                activities.append(activity_data)
            
            return activities
        
        except Exception as e:
            logger.error(f"Error in get_phase_activities: {str(e)}")
            raise
    
    def _get_button_text(self, activity: WorkflowActivity, can_start: bool, can_complete: bool) -> str:
        """Get appropriate button text based on activity type and state"""
        if activity.activity_type == ActivityType.START and can_start:
            return "Start Phase"
        elif activity.activity_type == ActivityType.COMPLETE and can_complete:
            return "Complete Phase"
        elif can_start:
            return "Start"
        elif can_complete:
            return "Complete"
        else:
            return "View"
    
    async def transition_activity(
        self,
        activity_code: str,
        target_status: str,
        cycle_id: int,
        report_id: int,
        phase_name: str,
        user_id: int,
        notes: Optional[str] = None,
        completion_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transition an activity to a new status"""
        
        # Parse activity_code which is in format "PhaseName_Order"
        parts = activity_code.split('_')
        if len(parts) < 2:
            raise ValidationException(f"Invalid activity code format: {activity_code}")
        
        activity_order = int(parts[-1])
        
        # Get the workflow activity
        activity_query = select(WorkflowActivity).where(
            and_(
                WorkflowActivity.cycle_id == cycle_id,
                WorkflowActivity.report_id == report_id,
                WorkflowActivity.phase_name == phase_name,
                WorkflowActivity.activity_order == activity_order
            )
        )
        result = await self.db.execute(activity_query)
        activity = result.scalar_one_or_none()
        
        if not activity:
            raise ValidationException(f"Activity '{activity_code}' not found")
        
        # Map frontend status to ActivityStatus enum
        status_map = {
            'active': ActivityStatus.IN_PROGRESS,
            'completed': ActivityStatus.COMPLETED,
            'pending': ActivityStatus.NOT_STARTED
        }
        
        new_status = status_map.get(target_status)
        if not new_status:
            raise ValidationException(f"Invalid target status: {target_status}")
        
        # Validate transition
        if new_status == ActivityStatus.IN_PROGRESS and activity.status != ActivityStatus.NOT_STARTED:
            raise BusinessLogicException(f"Cannot start activity in status '{activity.status.value}'")
        
        if new_status == ActivityStatus.COMPLETED and activity.status not in [ActivityStatus.IN_PROGRESS, ActivityStatus.NOT_STARTED]:
            # If already completed, return current state (idempotent behavior)
            if activity.status == ActivityStatus.COMPLETED:
                return {
                    "activity_code": activity_code,
                    "status": "completed",
                    "message": "Activity already completed",
                    "completed_at": activity.completed_at,
                    "completed_by": activity.completed_by
                }
            
            raise BusinessLogicException(f"Cannot complete activity in status '{activity.status.value}'")
        
        # Update activity
        activity.status = new_status
        
        if new_status == ActivityStatus.IN_PROGRESS:
            activity.started_at = datetime.utcnow()
            activity.started_by = user_id
        elif new_status == ActivityStatus.COMPLETED:
            if not activity.started_at:
                activity.started_at = datetime.utcnow()
                activity.started_by = user_id
            activity.completed_at = datetime.utcnow()
            activity.completed_by = user_id
            activity.can_complete = False
            
            # Enable next activity
            next_activity_query = select(WorkflowActivity).where(
                and_(
                    WorkflowActivity.cycle_id == cycle_id,
                    WorkflowActivity.report_id == report_id,
                    WorkflowActivity.phase_name == phase_name,
                    WorkflowActivity.activity_order == activity.activity_order + 1
                )
            )
            next_result = await self.db.execute(next_activity_query)
            next_activity = next_result.scalar_one_or_none()
            
            if next_activity:
                next_activity.can_start = True
        
        await self.db.commit()
        
        # Handle special activity types
        result = {
            'success': True,
            'activity_code': activity_code,
            'new_status': target_status,
            'message': f"{activity.activity_name} {target_status}"
        }
        
        # Auto-complete START activities when they are started
        if activity.activity_type == ActivityType.START and new_status == ActivityStatus.IN_PROGRESS:
            logger.info(f"Auto-completing START activity: {activity.activity_name}")
            # Immediately transition to completed
            activity.status = ActivityStatus.COMPLETED
            activity.completed_at = datetime.utcnow()
            activity.completed_by = user_id
            activity.can_complete = False
            
            # Enable next activity
            next_activity_query = select(WorkflowActivity).where(
                and_(
                    WorkflowActivity.cycle_id == cycle_id,
                    WorkflowActivity.report_id == report_id,
                    WorkflowActivity.phase_name == phase_name,
                    WorkflowActivity.activity_order == activity.activity_order + 1
                )
            )
            next_result = await self.db.execute(next_activity_query)
            next_activity = next_result.scalar_one_or_none()
            
            if next_activity:
                next_activity.can_start = True
                logger.info(f"Enabled next activity: {next_activity.activity_name}")
            
            await self.db.commit()
            result['auto_completed'] = True
            result['new_status'] = 'completed'
            result['message'] = f"{activity.activity_name} started and completed"
        
        # If this is a START activity being completed, update the workflow phase
        if activity.activity_type == ActivityType.START and new_status == ActivityStatus.COMPLETED:
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
            phase_result = await self.db.execute(phase_query)
            phase = phase_result.scalar_one_or_none()
            
            if phase:
                phase.status = "In Progress"
                phase.state = "In Progress"
                phase.started_at = datetime.utcnow()
                await self.db.commit()
                result['phase_updated'] = True
        
        # If this is a COMPLETE activity being completed, update the workflow phase
        elif activity.activity_type == ActivityType.COMPLETE and new_status == ActivityStatus.COMPLETED:
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
            phase_result = await self.db.execute(phase_query)
            phase = phase_result.scalar_one_or_none()
            
            if phase:
                phase.status = "Complete"
                phase.state = "Complete"
                phase.completed_at = datetime.utcnow()
                phase.progress_percentage = 100
                await self.db.commit()
                result['phase_updated'] = True
        
        return result
    
    async def reset_activity(
        self,
        activity_code: str,
        cycle_id: int,
        report_id: int,
        phase_name: str,
        user_id: int,
        cascade: bool = True
    ) -> Dict[str, Any]:
        """Reset an activity - not implemented for WorkflowActivity model"""
        raise NotImplementedError("Activity reset is not yet implemented for WorkflowActivity model")