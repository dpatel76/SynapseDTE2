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
                
                # Special case for LLM generation activities - they can be completed manually
                if activity.status == ActivityStatus.IN_PROGRESS and (
                    "Generate LLM" in activity.activity_name or
                    "LLM" in activity.activity_name and "Generate" in activity.activity_name
                ):
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
        
        # Handle special activity types BEFORE any commit
        result = {
            'success': True,
            'activity_code': activity_code,
            'new_status': target_status,
            'message': f"{activity.activity_name} {target_status}"
        }
        
        # Auto-complete START activities when they are started - BEFORE commit
        if activity.activity_type == ActivityType.START and new_status == ActivityStatus.IN_PROGRESS:
            logger.info(f"Auto-completing START activity: {activity.activity_name}")
            # Immediately transition to completed
            activity.status = ActivityStatus.COMPLETED
            activity.completed_at = datetime.utcnow()
            activity.completed_by = user_id
            activity.can_complete = False
            # Update new_status so phase update logic works
            new_status = ActivityStatus.COMPLETED
            
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
            
            # Handle Data Provider ID phase initialization BEFORE commit
            if phase_name == "Data Provider ID":
                logger.info(f"Initializing Data Provider ID phase - creating LOB attribute mappings")
                try:
                    await self._initialize_data_provider_phase(cycle_id, report_id, user_id)
                    result['data_provider_initialized'] = True
                except Exception as e:
                    logger.error(f"Failed to initialize Data Provider ID phase: {str(e)}")
                    # Continue anyway - don't fail the whole START activity
            
            # Handle Request Info phase initialization BEFORE commit
            elif phase_name == "Request Info":
                logger.info(f"Initializing Request Info phase - generating test cases")
                try:
                    await self._initialize_request_info_phase(cycle_id, report_id, user_id)
                    result['request_info_initialized'] = True
                except Exception as e:
                    logger.error(f"Failed to initialize Request Info phase: {str(e)}")
                    # Continue anyway - don't fail the whole START activity
            
            # Handle Scoping phase initialization BEFORE commit
            elif phase_name == "Scoping":
                logger.info(f"Initializing Scoping phase - importing approved planning attributes")
                
                try:
                    # Import scoping service
                    from app.services.scoping_service import ScopingService
                    from app.models.report_attribute import ReportAttribute
                    
                    # Get planning phase
                    planning_phase_query = select(WorkflowPhase).where(
                        and_(
                            WorkflowPhase.cycle_id == cycle_id,
                            WorkflowPhase.report_id == report_id,
                            WorkflowPhase.phase_name == "Planning"
                        )
                    )
                    planning_phase_result = await self.db.execute(planning_phase_query)
                    planning_phase = planning_phase_result.scalar_one_or_none()
                    
                    if planning_phase:
                        # Get approved planning attributes (no approval_status column, just use is_active)
                        attrs_query = select(ReportAttribute).where(
                            and_(
                                ReportAttribute.phase_id == planning_phase.phase_id,
                                ReportAttribute.is_active == True
                            )
                        ).order_by(ReportAttribute.line_item_number)
                        
                        attrs_result = await self.db.execute(attrs_query)
                        attributes = attrs_result.scalars().all()
                        
                        if attributes:
                            # Get scoping phase
                            scoping_phase_query = select(WorkflowPhase).where(
                                and_(
                                    WorkflowPhase.cycle_id == cycle_id,
                                    WorkflowPhase.report_id == report_id,
                                    WorkflowPhase.phase_name == "Scoping"
                                )
                            )
                            scoping_phase_result = await self.db.execute(scoping_phase_query)
                            scoping_phase = scoping_phase_result.scalar_one_or_none()
                            
                            if scoping_phase:
                                # Create scoping service and initial version
                                scoping_service = ScopingService(self.db)
                                
                                # Create initial version
                                new_version = await scoping_service.create_version(
                                    phase_id=scoping_phase.phase_id,
                                    user_id=user_id,
                                    notes="Initial version created when starting Scoping phase"
                                )
                                
                                # Import attributes (without LLM recommendations yet)
                                attribute_ids = [attr.id for attr in attributes]
                                await scoping_service.add_attributes_to_version(
                                    version_id=new_version.version_id,
                                    attribute_ids=attribute_ids,
                                    llm_recommendations=[{
                                        "provider": None,
                                        "recommendation": None,
                                        "confidence_score": None,
                                        "rationale": None,
                                        "processing_time_ms": 0,
                                        "response_payload": {}
                                    }] * len(attribute_ids),
                                    user_id=user_id
                                )
                                
                                logger.info(f"Imported {len(attributes)} approved planning attributes to scoping version {new_version.version_id}")
                                result['scoping_initialized'] = True
                                result['attributes_imported'] = len(attributes)
                                result['version_id'] = str(new_version.version_id)
                except Exception as e:
                    logger.error(f"Failed to initialize Scoping phase: {str(e)}")
                    # Continue anyway - don't fail the whole START activity
            
            # Don't commit yet - wait until the end
            result['auto_completed'] = True
            result['new_status'] = 'completed'
            result['message'] = f"{activity.activity_name} started and completed"
        
        # Auto-complete COMPLETE activities when they are started (if not manual)
        elif activity.activity_type == ActivityType.COMPLETE and new_status == ActivityStatus.IN_PROGRESS and not activity.is_manual:
            logger.info(f"Auto-completing COMPLETE activity: {activity.activity_name}")
            # Immediately transition to completed
            activity.status = ActivityStatus.COMPLETED
            activity.completed_at = datetime.utcnow()
            activity.completed_by = user_id
            activity.can_complete = False
            # Update new_status so phase update logic works
            new_status = ActivityStatus.COMPLETED
            
            # No next activity for COMPLETE activities (they're the last in the phase)
            # Don't commit yet - wait until the end
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
                phase.actual_start_date = datetime.utcnow()
                phase.started_by = user_id
                # Don't commit yet - wait until the end
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
                phase.actual_end_date = datetime.utcnow()
                phase.progress_percentage = 100
                phase.completed_by = user_id
                # Don't commit yet - wait until the end
                result['phase_updated'] = True
        
        # Single commit at the end - all or nothing
        await self.db.commit()
        
        return result
    
    async def _initialize_data_provider_phase(self, cycle_id: int, report_id: int, user_id: int):
        """Initialize data provider phase by creating LOB attribute mappings"""
        logger.info(f"Initializing data provider phase for cycle {cycle_id}, report {report_id}")
        
        try:
            # Get scoped attributes that are approved and non-PK
            from app.models.scoping import ScopingAttribute, ScopingVersion
            from app.models.sample_selection import SampleSelectionSample, SampleSelectionVersion
            from app.models.report_attribute import ReportAttribute as PlanningAttribute
            
            # Get scoping phase
            scoping_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Scoping"
                )
            )
            scoping_phase_result = await self.db.execute(scoping_phase_query)
            scoping_phase = scoping_phase_result.scalar_one_or_none()
            
            if not scoping_phase:
                logger.warning(f"No scoping phase found for cycle {cycle_id}, report {report_id}")
                return
            
            # Get the approved scoping version - check for version_status only
            scoping_version_query = select(ScopingVersion).where(
                and_(
                    ScopingVersion.phase_id == scoping_phase.phase_id,
                    ScopingVersion.version_status == "approved"
                )
            ).order_by(ScopingVersion.version_number.desc())
            scoping_version_result = await self.db.execute(scoping_version_query)
            approved_scoping_version = scoping_version_result.scalar_one_or_none()
            
            if not approved_scoping_version:
                logger.warning(f"No approved scoping version found for phase {scoping_phase.phase_id}")
                return
            
            # Get all scoped-in non-PK attributes
            # Note: attribute_id in ScopingAttribute IS the planning attribute id
            # Select only specific columns to avoid querying non-existent columns
            scoped_attrs_query = select(
                ScopingAttribute.attribute_id,
                PlanningAttribute.id,
                PlanningAttribute.attribute_name
            ).select_from(ScopingAttribute).join(
                PlanningAttribute, ScopingAttribute.attribute_id == PlanningAttribute.id
            ).where(
                and_(
                    ScopingAttribute.version_id == approved_scoping_version.version_id,
                    ScopingAttribute.tester_decision == "accept",
                    ScopingAttribute.report_owner_decision == "approved",  # Use "approved" not "accept" for report owner
                    PlanningAttribute.is_primary_key == False
                )
            )
            scoped_attrs_result = await self.db.execute(scoped_attrs_query)
            scoped_attributes = scoped_attrs_result.all()
            
            logger.info(f"Found {len(scoped_attributes)} approved non-PK attributes")
            
            # Get sample selection phase
            sample_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
            sample_phase_result = await self.db.execute(sample_phase_query)
            sample_phase = sample_phase_result.scalar_one_or_none()
            
            if not sample_phase:
                logger.warning(f"No sample selection phase found for cycle {cycle_id}, report {report_id}")
                return
            
            # Get approved sample selection version - check version_status only
            sample_version_query = select(SampleSelectionVersion).where(
                and_(
                    SampleSelectionVersion.phase_id == sample_phase.phase_id,
                    SampleSelectionVersion.version_status == "approved"
                )
            ).order_by(SampleSelectionVersion.version_number.desc())
            sample_version_result = await self.db.execute(sample_version_query)
            approved_sample_version = sample_version_result.scalar_one_or_none()
            
            if not approved_sample_version:
                logger.warning(f"No approved sample selection version found for phase {sample_phase.phase_id}")
                return
            
            # Get unique LOBs from approved samples
            lob_query = select(SampleSelectionSample.lob_id).distinct().where(
                and_(
                    SampleSelectionSample.version_id == approved_sample_version.version_id,
                    SampleSelectionSample.report_owner_decision == "approved"
                )
            )
            lob_result = await self.db.execute(lob_query)
            unique_lob_ids = [row[0] for row in lob_result.all()]
            
            logger.info(f"Found {len(unique_lob_ids)} unique LOBs from approved samples")
            
            if not unique_lob_ids or not scoped_attributes:
                logger.warning("No LOBs or scoped attributes found to create mappings")
                return
            
            # Get Data Provider ID phase
            data_provider_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Provider ID"
                )
            )
            data_provider_phase_result = await self.db.execute(data_provider_phase_query)
            data_provider_phase = data_provider_phase_result.scalar_one_or_none()
            
            if not data_provider_phase:
                logger.error(f"Data Provider ID phase not found for cycle {cycle_id}, report {report_id}")
                return
            
            # Create LOB attribute mappings
            from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping, DataOwnerLOBAttributeVersion
            
            # Create a new version for the assignments
            version = DataOwnerLOBAttributeVersion(
                phase_id=data_provider_phase.phase_id,
                version_number=1,
                version_status='active',  # Use string value instead of enum
                data_executive_id=user_id,
                assignment_notes="Initial version created when starting Data Provider ID phase",
                created_by_id=user_id,
                updated_by_id=user_id
            )
            self.db.add(version)
            await self.db.flush()  # Get the version_id
            
            # Create mapping records for each attribute/LOB combination
            mappings_created = 0
            for row in scoped_attributes:
                attribute_id = row[0]  # From ScopingAttribute.attribute_id
                planning_id = row[1]   # From PlanningAttribute.id (should be same as attribute_id)
                attribute_name = row[2] # From PlanningAttribute.attribute_name
                
                for lob_id in unique_lob_ids:
                    # Check if mapping already exists
                    existing_query = select(DataOwnerLOBAttributeMapping).where(
                        and_(
                            DataOwnerLOBAttributeMapping.phase_id == data_provider_phase.phase_id,
                            DataOwnerLOBAttributeMapping.attribute_id == attribute_id,
                            DataOwnerLOBAttributeMapping.lob_id == lob_id
                        )
                    )
                    existing_result = await self.db.execute(existing_query)
                    existing = existing_result.scalar_one_or_none()
                    
                    if not existing:
                        # Get first approved sample for this LOB to use as reference
                        sample_query = select(SampleSelectionSample.sample_id).where(
                            and_(
                                SampleSelectionSample.version_id == approved_sample_version.version_id,
                                SampleSelectionSample.lob_id == lob_id,
                                SampleSelectionSample.report_owner_decision == "approved"
                            )
                        ).limit(1)
                        sample_result = await self.db.execute(sample_query)
                        sample_id = sample_result.scalar()
                        
                        if sample_id:
                            mapping = DataOwnerLOBAttributeMapping(
                                version_id=version.version_id,
                                phase_id=data_provider_phase.phase_id,
                                sample_id=sample_id,
                                attribute_id=attribute_id,
                                lob_id=lob_id,
                                assignment_status="unassigned",  # Use lowercase
                                created_by_id=user_id,
                                updated_by_id=user_id
                            )
                            self.db.add(mapping)
                            mappings_created += 1
            
            # Update version summary
            version.total_lob_attributes = mappings_created
            version.assigned_lob_attributes = 0
            version.unassigned_lob_attributes = mappings_created
            
            # Note: Don't commit here - let the main transaction handle it
            # The commit will happen in transition_activity after all work is done
            logger.info(f"Successfully created {mappings_created} LOB attribute mappings")
            
        except Exception as e:
            logger.error(f"Error initializing data provider phase: {str(e)}")
            # Don't rollback here either - let the main transaction handle it
            # Re-raise to let the caller know initialization failed
            raise
    
    async def _initialize_request_info_phase(self, cycle_id: int, report_id: int, user_id: int):
        """Initialize Request Info phase by generating test cases from Sample X non-PK Attribute matrix"""
        logger.info(f"Initializing Request Info phase for cycle {cycle_id}, report {report_id}")
        
        try:
            from app.models.scoping import ScopingAttribute, ScopingVersion
            from app.models.sample_selection import SampleSelectionSample, SampleSelectionVersion
            from app.models.report_attribute import ReportAttribute as PlanningAttribute
            from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping, DataOwnerLOBAttributeVersion
            from app.models.request_info import CycleReportTestCase
            import uuid
            
            # Get Request Info phase
            rfi_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request Info"
                )
            )
            rfi_phase_result = await self.db.execute(rfi_phase_query)
            rfi_phase = rfi_phase_result.scalar_one_or_none()
            
            if not rfi_phase:
                logger.error(f"Request Info phase not found for cycle {cycle_id}, report {report_id}")
                return
            
            # Get Sample Selection phase and approved samples
            sample_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
            sample_phase_result = await self.db.execute(sample_phase_query)
            sample_phase = sample_phase_result.scalar_one_or_none()
            
            if not sample_phase:
                logger.warning("No Sample Selection phase found - cannot generate test cases")
                return
            
            # Get approved sample selection version
            sample_version_query = select(SampleSelectionVersion).where(
                and_(
                    SampleSelectionVersion.phase_id == sample_phase.phase_id,
                    SampleSelectionVersion.version_status == "approved"
                )
            ).order_by(SampleSelectionVersion.version_number.desc())
            sample_version_result = await self.db.execute(sample_version_query)
            approved_sample_version = sample_version_result.scalar_one_or_none()
            
            if not approved_sample_version:
                logger.warning("No approved sample selection version found")
                return
            
            # Get approved samples using calculated_status (combines both tester and report owner decisions)
            samples_query = select(SampleSelectionSample).where(
                and_(
                    SampleSelectionSample.version_id == approved_sample_version.version_id,
                    SampleSelectionSample.calculated_status == "approved"
                )
            )
            samples_result = await self.db.execute(samples_query)
            approved_samples = samples_result.scalars().all()
            
            logger.info(f"Found {len(approved_samples)} approved samples")
            
            # Get Scoping phase and approved scoping version
            scoping_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Scoping"
                )
            )
            scoping_phase_result = await self.db.execute(scoping_phase_query)
            scoping_phase = scoping_phase_result.scalar_one_or_none()
            
            if not scoping_phase:
                logger.warning("No Scoping phase found - cannot get scoped attributes")
                return
            
            # Get approved scoping version
            scoping_version_query = select(ScopingVersion).where(
                and_(
                    ScopingVersion.phase_id == scoping_phase.phase_id,
                    ScopingVersion.version_status == "approved"
                )
            ).order_by(ScopingVersion.version_number.desc())
            scoping_version_result = await self.db.execute(scoping_version_query)
            approved_scoping_version = scoping_version_result.scalar_one_or_none()
            
            if not approved_scoping_version:
                logger.warning("No approved scoping version found")
                return
            
            # Get scoped-in non-PK attributes with final_scoping=true and calculated_status='approved'
            scoped_attrs_query = select(
                ScopingAttribute.attribute_id,
                PlanningAttribute.id,
                PlanningAttribute.attribute_name
            ).select_from(ScopingAttribute).join(
                PlanningAttribute, ScopingAttribute.attribute_id == PlanningAttribute.id
            ).where(
                and_(
                    ScopingAttribute.version_id == approved_scoping_version.version_id,
                    ScopingAttribute.calculated_status == "approved",
                    ScopingAttribute.final_scoping == True,
                    PlanningAttribute.is_primary_key == False
                )
            )
            scoped_attrs_result = await self.db.execute(scoped_attrs_query)
            scoped_non_pk_attrs = scoped_attrs_result.all()
            
            logger.info(f"Found {len(scoped_non_pk_attrs)} scoped non-PK attributes")
            
            if not approved_samples or not scoped_non_pk_attrs:
                logger.warning("No samples or attributes to create test cases from")
                return
            
            # Get Data Provider ID phase for data owner assignments
            data_provider_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Provider ID"
                )
            )
            data_provider_phase_result = await self.db.execute(data_provider_phase_query)
            data_provider_phase = data_provider_phase_result.scalar_one_or_none()
            
            # Get data owner assignments if available
            data_owner_map = {}
            if data_provider_phase:
                # Get the active version
                version_query = select(DataOwnerLOBAttributeVersion).where(
                    and_(
                        DataOwnerLOBAttributeVersion.phase_id == data_provider_phase.phase_id,
                        DataOwnerLOBAttributeVersion.version_status == "active"
                    )
                ).order_by(DataOwnerLOBAttributeVersion.version_number.desc())
                version_result = await self.db.execute(version_query)
                active_version = version_result.scalar_one_or_none()
                
                if active_version:
                    # Get all mappings for this version
                    mappings_query = select(DataOwnerLOBAttributeMapping).where(
                        DataOwnerLOBAttributeMapping.version_id == active_version.version_id
                    )
                    mappings_result = await self.db.execute(mappings_query)
                    mappings = mappings_result.scalars().all()
                    
                    # Build map: (attribute_id, lob_id) -> data_owner_id
                    for mapping in mappings:
                        if mapping.data_owner_id:
                            key = (mapping.attribute_id, mapping.lob_id)
                            data_owner_map[key] = mapping.data_owner_id
            
            # Create test cases: one for each sample X non-PK attribute combination
            test_cases_created = 0
            test_case_number = 1
            
            for sample in approved_samples:
                for row in scoped_non_pk_attrs:
                    # Extract values from row tuple
                    attribute_id = row[0]  # ScopingAttribute.attribute_id
                    planning_id = row[1]   # PlanningAttribute.id
                    attribute_name = row[2] # PlanningAttribute.attribute_name
                    
                    # Get reference number from sample data
                    ref_num = "Sample"
                    if sample.sample_data and isinstance(sample.sample_data, dict):
                        ref_num = sample.sample_data.get('reference_number', f'Sample-{sample.sample_id}')
                    
                    # Create test case with correct fields
                    test_case = CycleReportTestCase(
                        test_case_number=f"TC-{cycle_id}-{report_id}-{test_case_number:04d}",
                        test_case_name=f"{ref_num} - {attribute_name}",
                        description=f"Validate {attribute_name} for sample {sample.sample_id}",
                        phase_id=rfi_phase.phase_id,
                        sample_id=str(sample.sample_id),  # Convert to string as required
                        attribute_id=attribute_id,
                        attribute_name=attribute_name,
                        lob_id=sample.lob_id,
                        status="Not Started",
                        created_by=user_id,
                        updated_by=user_id
                    )
                    
                    # Set data owner if available
                    if sample.lob_id and data_owner_map:
                        key = (attribute_id, sample.lob_id)
                        if key in data_owner_map:
                            test_case.data_owner_id = data_owner_map[key]
                            test_case.assigned_by = user_id
                            test_case.assigned_at = datetime.utcnow()
                        else:
                            # No data owner assigned for this LOB-attribute combination
                            # Try to find data owner by LOB as fallback
                            from app.models.user import User
                            
                            if sample.lob_id:
                                # Find data owner for this LOB using the enum field
                                data_owner_query = select(User).where(
                                    and_(
                                        User.lob_id == sample.lob_id,
                                        User.role == "Data Owner",  # Using enum field, not role_id
                                        User.is_active == True
                                    )
                                ).order_by(User.created_at).limit(1)  # Get first/primary data owner for LOB
                                owner_result = await self.db.execute(data_owner_query)
                                lob_data_owner = owner_result.scalar_one_or_none()
                                
                                if lob_data_owner:
                                    test_case.data_owner_id = lob_data_owner.user_id
                                    test_case.assigned_by = user_id
                                    test_case.assigned_at = datetime.utcnow()
                                    logger.info(f"Auto-assigned test case to {lob_data_owner.first_name} {lob_data_owner.last_name} based on LOB {sample.lob_id}")
                                else:
                                    # No data owner found for LOB - leave unassigned
                                    logger.warning(f"No data owner found for LOB {sample.lob_id}, leaving test case unassigned")
                                    test_case.data_owner_id = None
                            else:
                                # Can't determine LOB or role - leave unassigned
                                logger.warning(f"Cannot auto-assign data owner for sample {sample.sample_id}")
                                test_case.data_owner_id = None
                    else:
                        # No data owner mapping available - try to find data owner by LOB
                        # This is a fallback when Data Provider ID phase assignments weren't completed
                        if sample.lob_id:
                            # Find a data owner with matching LOB
                            from app.models.user import User
                            
                            # Find data owner for this LOB using the enum field
                            data_owner_query = select(User).where(
                                and_(
                                    User.lob_id == sample.lob_id,
                                    User.role == "Data Owner",  # Using enum field, not role_id
                                    User.is_active == True
                                )
                            ).order_by(User.created_at).limit(1)  # Get first/primary data owner for LOB
                            owner_result = await self.db.execute(data_owner_query)
                            lob_data_owner = owner_result.scalar_one_or_none()
                            
                            if lob_data_owner:
                                test_case.data_owner_id = lob_data_owner.user_id
                                test_case.assigned_by = user_id
                                test_case.assigned_at = datetime.utcnow()
                                logger.info(f"Auto-assigned test case to {lob_data_owner.first_name} {lob_data_owner.last_name} based on LOB {sample.lob_id}")
                            else:
                                # No data owner found for LOB - leave unassigned
                                logger.warning(f"No data owner found for LOB {sample.lob_id}, leaving test case unassigned")
                                test_case.data_owner_id = None
                        else:
                            # No LOB ID on sample - can't auto-assign
                            logger.warning(f"Sample {sample.sample_id} has no LOB ID, cannot auto-assign data owner")
                            test_case.data_owner_id = None
                    
                    self.db.add(test_case)
                    test_cases_created += 1
                    test_case_number += 1
            
            logger.info(f"Successfully created {test_cases_created} test cases")
            
        except Exception as e:
            logger.error(f"Error initializing Request Info phase: {str(e)}")
            # Re-raise to let the caller know initialization failed
            raise
    
    async def _trigger_llm_recommendations(self, cycle_id: int, report_id: int, user_id: int):
        """Trigger LLM recommendation generation for Scoping phase"""
        logger.info(f"Triggering LLM recommendations for cycle {cycle_id}, report {report_id}")
        
        try:
            from app.services.scoping_service import ScopingService
            
            # Get scoping phase
            scoping_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Scoping"
                )
            )
            scoping_phase_result = await self.db.execute(scoping_phase_query)
            scoping_phase = scoping_phase_result.scalar_one_or_none()
            
            if not scoping_phase:
                logger.warning("No scoping phase found")
                return
            
            # Get active scoping version
            from app.models.scoping import ScopingVersion
            version_query = select(ScopingVersion).where(
                and_(
                    ScopingVersion.phase_id == scoping_phase.phase_id,
                    ScopingVersion.version_status == "active"
                )
            ).order_by(ScopingVersion.version_number.desc())
            version_result = await self.db.execute(version_query)
            active_version = version_result.scalar_one_or_none()
            
            if active_version:
                # Trigger LLM generation as background task
                scoping_service = ScopingService(self.db)
                # This would normally trigger a background job
                logger.info(f"LLM recommendations triggered for version {active_version.version_id}")
            
        except Exception as e:
            logger.error(f"Error triggering LLM recommendations: {str(e)}")
            raise
    
    async def _trigger_data_profiling_rules(self, cycle_id: int, report_id: int, user_id: int):
        """Trigger LLM data profiling rule generation"""
        logger.info(f"Triggering data profiling rules for cycle {cycle_id}, report {report_id}")
        
        try:
            from app.services.data_profiling_service import DataProfilingService
            
            # Get data profiling phase
            profiling_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Profiling"
                )
            )
            profiling_phase_result = await self.db.execute(profiling_phase_query)
            profiling_phase = profiling_phase_result.scalar_one_or_none()
            
            if profiling_phase:
                # Trigger rule generation as background task
                profiling_service = DataProfilingService(self.db)
                # This would normally trigger a background job
                logger.info(f"Data profiling rules triggered for phase {profiling_phase.phase_id}")
            
        except Exception as e:
            logger.error(f"Error triggering data profiling rules: {str(e)}")
            raise
    
    async def _trigger_sample_generation(self, cycle_id: int, report_id: int, user_id: int):
        """Trigger sample generation for Sample Selection phase"""
        logger.info(f"Triggering sample generation for cycle {cycle_id}, report {report_id}")
        
        try:
            from app.services.intelligent_data_sampling_service import IntelligentDataSamplingService
            
            # Get sample selection phase
            sample_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
            sample_phase_result = await self.db.execute(sample_phase_query)
            sample_phase = sample_phase_result.scalar_one_or_none()
            
            if sample_phase:
                # Trigger sample generation as background task
                sampling_service = IntelligentDataSamplingService(self.db)
                # This would normally trigger a background job
                logger.info(f"Sample generation triggered for phase {sample_phase.phase_id}")
            
        except Exception as e:
            logger.error(f"Error triggering sample generation: {str(e)}")
            raise
    
    async def _trigger_report_generation(self, cycle_id: int, report_id: int, user_id: int):
        """Trigger report generation for Finalize Test Report phase"""
        logger.info(f"Triggering report generation for cycle {cycle_id}, report {report_id}")
        
        try:
            # Get finalize phase
            finalize_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Finalize Test Report"
                )
            )
            finalize_phase_result = await self.db.execute(finalize_phase_query)
            finalize_phase = finalize_phase_result.scalar_one_or_none()
            
            if finalize_phase:
                # Report generation would be triggered here
                logger.info(f"Report generation triggered for phase {finalize_phase.phase_id}")
            
        except Exception as e:
            logger.error(f"Error triggering report generation: {str(e)}")
            raise
    
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