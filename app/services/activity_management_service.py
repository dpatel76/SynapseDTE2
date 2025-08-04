"""
Activity Management Service
Handles activity state transitions and dependency management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from app.models.activity_definition import ActivityDefinition, ActivityState
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
            # Get activity definitions for the phase (case-insensitive)
            definitions_query = select(ActivityDefinition).where(
                and_(
                    func.lower(ActivityDefinition.phase_name) == func.lower(phase_name),
                    ActivityDefinition.is_active == True
                )
            ).order_by(ActivityDefinition.sequence_order)
            
            definitions_result = await self.db.execute(definitions_query)
            definitions = definitions_result.scalars().all()
            
            # Get existing activity states (case-insensitive)
            states_query = select(ActivityState).where(
                and_(
                    ActivityState.cycle_id == cycle_id,
                    ActivityState.report_id == report_id,
                    func.lower(ActivityState.phase_name) == func.lower(phase_name)
                )
            )
            
            states_result = await self.db.execute(states_query)
            states = states_result.scalars().all()
            
            # Create a map of activity states by definition ID
            state_map = {state.activity_definition_id: state for state in states}
            
            # Build activity list with current states
            activities = []
            new_states = []  # Track new states to add later
        except Exception as e:
            logger.error(f"Error in get_phase_activities: {str(e)}")
            raise
        
        for definition in definitions:
            state = state_map.get(definition.id)
            
            # Create state if it doesn't exist
            if not state:
                state = ActivityState(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name=definition.phase_name,  # Use the actual phase name from definition
                    activity_definition_id=definition.id,
                    status='pending'
                )
                new_states.append(state)
                state_map[definition.id] = state
            
            # Check if this activity should be auto-skipped based on conditional rules
            if definition.conditional_skip_rules and state.status == 'pending':
                should_skip = await self._check_conditional_skip(
                    definition, cycle_id, report_id
                )
                if should_skip:
                    state.status = 'skipped'
                    state.completion_notes = 'Auto-skipped: Data source already configured'
            
            # Check dependencies
            try:
                is_blocked, blocking_reason = await self._check_dependencies(
                    definition, state_map, definitions
                )
            except Exception as e:
                logger.error(f"Error checking dependencies for {definition.activity_code}: {str(e)}")
                is_blocked = False
                blocking_reason = None
            
            # Special handling for phase_start and phase_complete activities
            if definition.activity_type == 'phase_start':
                can_start = state.status == 'pending' and not is_blocked
                can_complete = False  # Phase start activities complete automatically
            elif definition.activity_type == 'phase_complete':
                can_start = False  # Phase complete activities don't have a start action
                can_complete = state.status == 'pending' and not is_blocked  # Can complete when dependencies met
            else:
                can_start = state.status == 'pending' and not is_blocked
                can_complete = state.status == 'active'
                
                # Special handling for load_attributes - check if any attributes exist
                if definition.activity_code == 'load_attributes' and state.status == 'active':
                    from app.models.report_attribute import ReportAttribute
                    from app.models.workflow import WorkflowPhase
                    
                    # First get the phase_id for this cycle/report/phase
                    phase_query = select(WorkflowPhase.phase_id).where(
                        and_(
                            WorkflowPhase.cycle_id == cycle_id,
                            WorkflowPhase.report_id == report_id,
                            WorkflowPhase.phase_name == phase_name
                        )
                    )
                    phase_result = await self.db.execute(phase_query)
                    phase_id = phase_result.scalar()
                    
                    if phase_id:
                        # Check if any attributes exist for this phase
                        attr_count_query = select(func.count(ReportAttribute.id)).where(
                            ReportAttribute.phase_id == phase_id
                        )
                        attr_count_result = await self.db.execute(attr_count_query)
                        attr_count = attr_count_result.scalar() or 0
                        
                        # Can only complete if at least one attribute exists
                        can_complete = attr_count > 0
                        
                        
                        if not can_complete:
                            blocking_reason = "At least one attribute must be loaded before completing this activity"
                    else:
                        can_complete = False
                        blocking_reason = "Planning phase not found"
            
            activity_data = {
                'activity_id': definition.activity_code,
                'name': definition.activity_name,
                'description': definition.description,
                'status': state.status,
                'can_start': can_start,
                'can_complete': can_complete,
                'can_reset': definition.can_reset and state.status == 'completed',
                'completion_percentage': state.completion_percentage,
                'blocking_reason': blocking_reason if is_blocked else None,
                'last_updated': state.updated_at or state.created_at,
                'metadata': {
                    'activity_type': definition.activity_type,
                    'button_text': definition.button_text,
                    'success_message': definition.success_message,
                    'instructions': definition.instructions,
                    'can_skip': definition.can_skip,
                    'started_by': state.started_by,
                    'completed_by': state.completed_by,
                    'definition_id': definition.id,
                    'state_id': state.id if hasattr(state, 'id') and state.id else None
                }
            }
            
            # Debug logging
            if definition.activity_code == 'load_attributes':
                logger.info(f"Load Attributes activity: status={state.status}, can_start={activity_data['can_start']}, can_complete={activity_data['can_complete']}")
            
            activities.append(activity_data)
        
        # Add and commit any new states
        if new_states:
            for state in new_states:
                self.db.add(state)
            await self.db.commit()
        
        return activities
    
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
        logger.info(f"transition_activity called: activity_code={activity_code}, target_status={target_status}, cycle_id={cycle_id}, report_id={report_id}, phase_name={phase_name}")
        
        # Get activity definition
        definition_query = select(ActivityDefinition).where(
            ActivityDefinition.activity_code == activity_code
        )
        definition_result = await self.db.execute(definition_query)
        definition = definition_result.scalar_one_or_none()
        
        if not definition:
            raise ValidationException(f"Activity '{activity_code}' not found")
        
        logger.info(f"Activity {activity_code}: type={definition.activity_type}, target_status={target_status}")
        
        # Get or create activity state
        state_query = select(ActivityState).where(
            and_(
                ActivityState.cycle_id == cycle_id,
                ActivityState.report_id == report_id,
                ActivityState.activity_definition_id == definition.id
            )
        )
        state_result = await self.db.execute(state_query)
        state = state_result.scalar_one_or_none()
        
        if not state:
            state = ActivityState(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name=phase_name,
                activity_definition_id=definition.id,
                status='pending'
            )
            self.db.add(state)
        
        # Special handling for phase_start and phase_complete activities
        logger.info(f"Checking special handling: activity_type='{definition.activity_type}' (type: {type(definition.activity_type)}), target_status='{target_status}'")
        if definition.activity_type == 'phase_start' and target_status == 'active':
            # Phase start activities go directly to completed
            logger.info(f"Phase start activity {activity_code} - converting target_status from 'active' to 'completed'")
            target_status = 'completed'
        else:
            logger.info(f"No special handling applied for {activity_code}")
        
        # Validate transition
        if target_status == 'active' and state.status != 'pending':
            raise BusinessLogicException(f"Cannot start activity in status '{state.status}'")
        
        if target_status == 'completed' and state.status not in ['active', 'pending']:
            # If already completed, return current state (idempotent behavior)
            if state.status == 'completed':
                logger.info(f"Activity {activity_code} is already completed, returning current state")
                return {
                    "activity_code": activity_code,
                    "status": state.status,
                    "message": "Activity already completed",
                    "completed_at": state.completed_at,
                    "completed_by": state.completed_by
                }
            
            # Allow pending->completed for phase_start activities
            if not (definition.activity_type == 'phase_start' and state.status == 'pending'):
                raise BusinessLogicException(f"Cannot complete activity in status '{state.status}'")
        
        # Check dependencies for starting
        if target_status == 'active':
            all_states = await self._get_all_phase_states(cycle_id, report_id, phase_name)
            is_blocked, blocking_reason = await self._check_dependencies(
                definition, all_states, []
            )
            if is_blocked:
                raise BusinessLogicException(f"Cannot start activity: {blocking_reason}")
        
        # Update state
        state.status = target_status
        
        if target_status == 'active':
            state.started_at = datetime.utcnow()
            state.started_by = user_id
            state.is_blocked = False
            state.blocking_reason = None
        elif target_status == 'completed':
            # For phase_start activities that go directly to completed, set both timestamps
            if definition.activity_type == 'phase_start' and not state.started_at:
                state.started_at = datetime.utcnow()
                state.started_by = user_id
            state.completed_at = datetime.utcnow()
            state.completed_by = user_id
            state.completion_notes = notes
            state.completion_data = completion_data
        
        await self.db.commit()
        
        # Handle special activity types
        result = {
            'success': True,
            'activity_code': activity_code,
            'new_status': target_status,
            'message': definition.success_message or f"Activity {target_status}"
        }
        
        # If this is a phase start/complete activity, update the workflow phase
        if definition.activity_type == 'phase_start' and target_status == 'completed':
            await self._update_workflow_phase(cycle_id, report_id, phase_name, 'In Progress', user_id)
            result['phase_updated'] = True
            
            # Special handling for Scoping phase start - initialize scoping data
            if phase_name == 'Scoping':
                await self._initialize_scoping_phase(cycle_id, report_id, user_id)
                result['scoping_initialized'] = True
            
            # Special handling for Data Provider ID phase start - create LOB mappings
            elif phase_name == 'Data Provider ID':
                await self._initialize_data_provider_phase(cycle_id, report_id, user_id)
                result['data_provider_initialized'] = True
                
        elif definition.activity_type == 'phase_complete' and target_status == 'completed':
            await self._update_workflow_phase(cycle_id, report_id, phase_name, 'Complete', user_id)
            result['phase_updated'] = True
        
        # Special handling for Create Test Cases activity
        if activity_code == 'create_test_cases' and target_status == 'active':
            logger.info(f"Create Test Cases special handling triggered for cycle={cycle_id}, report={report_id}")
            from app.services.request_info_service import RequestInfoService
            request_info_service = RequestInfoService(self.db)
            test_cases_result = await request_info_service._create_test_cases_for_phase(cycle_id, report_id, user_id)
            logger.info(f"Test case creation result: {test_cases_result}")
            result['test_cases_created'] = test_cases_result
            
            # If test cases were created successfully, auto-complete the activity
            if test_cases_result.get('success', False):
                state.status = 'completed'
                state.completed_at = datetime.utcnow()
                state.completed_by = user_id
                result['new_status'] = 'completed'
                result['message'] = f"Created {test_cases_result.get('count', 0)} test cases successfully"
        
        # Check for auto-completion of dependent activities
        if target_status == 'completed':
            await self._check_auto_completions(cycle_id, report_id, phase_name, definition.activity_code)
        
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
        """Reset an activity and optionally cascade to dependent activities"""
        
        # Get activity definition
        definition_query = select(ActivityDefinition).where(
            ActivityDefinition.activity_code == activity_code
        )
        definition_result = await self.db.execute(definition_query)
        definition = definition_result.scalar_one_or_none()
        
        if not definition:
            raise ValidationException(f"Activity '{activity_code}' not found")
        
        if not definition.can_reset:
            raise BusinessLogicException(f"Activity '{activity_code}' cannot be reset")
        
        # Get activity state
        state_query = select(ActivityState).where(
            and_(
                ActivityState.cycle_id == cycle_id,
                ActivityState.report_id == report_id,
                ActivityState.activity_definition_id == definition.id
            )
        )
        state_result = await self.db.execute(state_query)
        state = state_result.scalar_one_or_none()
        
        if not state or state.status != 'completed':
            raise BusinessLogicException("Activity is not completed and cannot be reset")
        
        # Find dependent activities if cascading
        reset_activities = [state]
        if cascade:
            dependent_states = await self._find_dependent_activities(
                cycle_id, report_id, phase_name, activity_code
            )
            reset_activities.extend(dependent_states)
        
        # Reset all activities
        for activity_state in reset_activities:
            activity_state.status = 'pending'
            activity_state.started_at = None
            activity_state.started_by = None
            activity_state.completed_at = None
            activity_state.completed_by = None
            activity_state.completion_data = None
            activity_state.completion_notes = None
            activity_state.reset_count += 1
            activity_state.last_reset_at = datetime.utcnow()
            activity_state.last_reset_by = user_id
        
        await self.db.commit()
        
        return {
            'success': True,
            'reset_count': len(reset_activities),
            'message': f"Reset {len(reset_activities)} activities"
        }
    
    async def _check_dependencies(
        self,
        definition: ActivityDefinition,
        state_map: Dict[int, ActivityState],
        all_definitions: List[ActivityDefinition]
    ) -> tuple[bool, Optional[str]]:
        """Check if an activity's dependencies are met"""
        
        if not definition.depends_on_activity_codes:
            return False, None
        
        # Create a map of activity codes to definitions
        code_to_def = {d.activity_code: d for d in all_definitions}
        
        blocking_activities = []
        for dep_code in definition.depends_on_activity_codes:
            dep_definition = code_to_def.get(dep_code)
            if dep_definition:
                dep_state = state_map.get(dep_definition.id)
                if not dep_state or dep_state.status != 'completed':
                    blocking_activities.append(dep_definition.activity_name)
        
        if blocking_activities:
            reason = f"Waiting for: {', '.join(blocking_activities)}"
            return True, reason
        
        return False, None
    
    async def _update_workflow_phase(
        self,
        cycle_id: int,
        report_id: int,
        phase_name: str,
        new_status: str,
        user_id: int
    ):
        """Update the workflow phase status"""
        
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
            phase.status = new_status
            phase.state = new_status
            
            if new_status == 'In Progress':
                phase.actual_start_date = datetime.utcnow()
                phase.started_by = user_id
            elif new_status == 'Complete':
                phase.actual_end_date = datetime.utcnow()
                phase.completed_by = user_id
            
            await self.db.commit()
    
    async def _get_all_phase_states(
        self,
        cycle_id: int,
        report_id: int,
        phase_name: str
    ) -> Dict[int, ActivityState]:
        """Get all activity states for a phase"""
        
        states_query = select(ActivityState).where(
            and_(
                ActivityState.cycle_id == cycle_id,
                ActivityState.report_id == report_id,
                ActivityState.phase_name == phase_name
            )
        )
        states_result = await self.db.execute(states_query)
        states = states_result.scalars().all()
        
        return {state.activity_definition_id: state for state in states}
    
    async def _check_auto_completions(
        self,
        cycle_id: int,
        report_id: int,
        phase_name: str,
        completed_activity_code: str
    ):
        """Check if any activities should auto-complete based on conditions"""
        
        # Get all definitions with auto-complete conditions
        definitions_query = select(ActivityDefinition).where(
            and_(
                ActivityDefinition.phase_name == phase_name,
                ActivityDefinition.auto_complete_on_condition.isnot(None)
            )
        )
        definitions_result = await self.db.execute(definitions_query)
        definitions = definitions_result.scalars().all()
        
        # Check each definition's conditions
        for definition in definitions:
            conditions = definition.auto_complete_on_condition or {}
            if 'depends_on_completed' in conditions:
                if completed_activity_code in conditions['depends_on_completed']:
                    # Auto-complete this activity
                    state_query = select(ActivityState).where(
                        and_(
                            ActivityState.cycle_id == cycle_id,
                            ActivityState.report_id == report_id,
                            ActivityState.activity_definition_id == definition.id
                        )
                    )
                    state_result = await self.db.execute(state_query)
                    state = state_result.scalar_one_or_none()
                    
                    if state and state.status == 'active':
                        state.status = 'completed'
                        state.completed_at = datetime.utcnow()
                        state.completion_notes = 'Auto-completed'
                        await self.db.commit()
    
    async def _find_dependent_activities(
        self,
        cycle_id: int,
        report_id: int,
        phase_name: str,
        activity_code: str
    ) -> List[ActivityState]:
        """Find all activities that depend on the given activity"""
        
        # Get all definitions that depend on this activity
        # First get all definitions for this phase
        definitions_query = select(ActivityDefinition).where(
            ActivityDefinition.phase_name == phase_name
        )
        definitions_result = await self.db.execute(definitions_query)
        all_definitions = definitions_result.scalars().all()
        
        # Filter for definitions that depend on this activity
        dependent_definitions = []
        for definition in all_definitions:
            if definition.depends_on_activity_codes and activity_code in definition.depends_on_activity_codes:
                dependent_definitions.append(definition)
        
        # Get states for these definitions
        dependent_states = []
        for definition in dependent_definitions:
            state_query = select(ActivityState).where(
                and_(
                    ActivityState.cycle_id == cycle_id,
                    ActivityState.report_id == report_id,
                    ActivityState.activity_definition_id == definition.id
                )
            )
            state_result = await self.db.execute(state_query)
            state = state_result.scalar_one_or_none()
            
            if state and state.status == 'completed':
                dependent_states.append(state)
                
                # Recursively find activities that depend on this one
                recursive_deps = await self._find_dependent_activities(
                    cycle_id, report_id, phase_name, definition.activity_code
                )
                dependent_states.extend(recursive_deps)
        
        return dependent_states
    
    async def _check_conditional_skip(
        self,
        definition: ActivityDefinition,
        cycle_id: int,
        report_id: int
    ) -> bool:
        """Check if an activity should be skipped based on conditional rules"""
        
        if not definition.conditional_skip_rules:
            return False
        
        rules = definition.conditional_skip_rules
        
        # Check if we should skip based on data source configuration
        if rules.get('skip_if_data_source_configured') and rules.get('check_planning_attributes'):
            # Check if any planning attributes have data source configured via AttributeMapping
            from app.models.report_attribute import ReportAttribute
            from app.models.data_source import AttributeMapping
            from app.models.workflow import WorkflowPhase
            
            # First get the phase_id for this cycle/report/phase
            phase_query = select(WorkflowPhase.phase_id).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Planning'  # This is for conditional skip rules
                )
            )
            phase_result = await self.db.execute(phase_query)
            phase_id = phase_result.scalar()
            
            if not phase_id:
                return False  # Can't skip if we can't find the phase
            
            # Check if there are any attribute mappings for this phase
            query = select(AttributeMapping).join(
                ReportAttribute,
                AttributeMapping.attribute_id == ReportAttribute.id
            ).where(
                ReportAttribute.phase_id == phase_id
            )
            
            result = await self.db.execute(query)
            has_data_source = result.scalars().first() is not None
            
            if has_data_source:
                logger.info(f"Activity {definition.activity_code} will be auto-skipped - data source is configured via attribute mappings")
                return True
        
        return False
    
    async def _initialize_scoping_phase(self, cycle_id: int, report_id: int, user_id: int):
        """Initialize scoping phase by creating version and copying planning attributes"""
        logger.info(f"Initializing scoping phase for cycle {cycle_id}, report {report_id}")
        
        try:
            # Get the scoping phase
            from app.models.workflow import WorkflowPhase
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Scoping'
                )
            )
            phase_result = await self.db.execute(phase_query)
            scoping_phase = phase_result.scalar_one_or_none()
            
            if not scoping_phase:
                logger.error(f"Scoping phase not found for cycle {cycle_id}, report {report_id}")
                return
                
            scoping_phase_id = scoping_phase.phase_id
            
            # Get planning phase
            planning_phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Planning'
                )
            )
            planning_phase_result = await self.db.execute(planning_phase_query)
            planning_phase = planning_phase_result.scalar_one_or_none()
            
            if not planning_phase:
                logger.error(f"Planning phase not found for cycle {cycle_id}, report {report_id}")
                return
                
            planning_phase_id = planning_phase.phase_id
            
            # Check if scoping version already exists
            # Use raw SQL to avoid model import issues
            existing_version_query = text("""
                SELECT version_id, version_number 
                FROM cycle_report_scoping_versions 
                WHERE phase_id = :phase_id 
                ORDER BY version_number DESC 
                LIMIT 1
            """)
            existing_version_result = await self.db.execute(
                existing_version_query, 
                {"phase_id": scoping_phase_id}
            )
            existing_version = existing_version_result.first()
            
            if existing_version:
                logger.info(f"Scoping version already exists for phase {scoping_phase_id}")
                return
                
            # Create initial scoping version using raw SQL
            import uuid
            version_id = str(uuid.uuid4())
            create_version_query = text("""
                INSERT INTO cycle_report_scoping_versions (
                    version_id, phase_id, version_number, version_status,
                    total_attributes, scoped_attributes, 
                    created_by_id, updated_by_id, created_at, updated_at
                ) VALUES (
                    :version_id, :phase_id, 1, 'draft',
                    0, 0,
                    :user_id, :user_id, NOW(), NOW()
                )
            """)
            await self.db.execute(create_version_query, {
                "version_id": version_id,
                "phase_id": scoping_phase_id,
                "user_id": user_id
            })
            
            logger.info(f"Created scoping version {version_id}")
            
            # Get all active planning attributes
            planning_attrs_query = text("""
                SELECT id, attribute_name, data_type, is_primary_key, is_cde
                FROM cycle_report_planning_attributes
                WHERE phase_id = :phase_id 
                AND is_active = true
            """)
            planning_attrs_result = await self.db.execute(
                planning_attrs_query,
                {"phase_id": planning_phase_id}
            )
            planning_attrs = planning_attrs_result.fetchall()
            
            logger.info(f"Found {len(planning_attrs)} planning attributes to copy")
            
            # Create scoping attributes
            scoping_attrs_created = 0
            for planning_attr in planning_attrs:
                attr_id = str(uuid.uuid4())
                insert_query = text("""
                    INSERT INTO cycle_report_scoping_attributes (
                        attribute_id, version_id, phase_id, planning_attribute_id,
                        final_status, created_by_id, updated_by_id,
                        created_at, updated_at
                    ) VALUES (
                        :attr_id, :version_id, :phase_id, :planning_attr_id,
                        'pending', :user_id, :user_id,
                        NOW(), NOW()
                    )
                """)
                await self.db.execute(insert_query, {
                    "attr_id": attr_id,
                    "version_id": version_id,
                    "phase_id": scoping_phase_id,
                    "planning_attr_id": planning_attr.id,
                    "user_id": user_id
                })
                scoping_attrs_created += 1
                
            # Update version counts
            update_counts_query = text("""
                UPDATE cycle_report_scoping_versions 
                SET total_attributes = :total, scoped_attributes = 0
                WHERE version_id = :version_id
            """)
            await self.db.execute(update_counts_query, {
                "total": scoping_attrs_created,
                "version_id": version_id
            })
            
            await self.db.commit()
            logger.info(f"Successfully created {scoping_attrs_created} scoping attributes")
            
        except Exception as e:
            logger.error(f"Error initializing scoping phase: {str(e)}")
            await self.db.rollback()
            raise
    
    async def _initialize_data_provider_phase(self, cycle_id: int, report_id: int, user_id: int):
        """Initialize data provider phase by creating LOB attribute mappings"""
        logger.info(f"Initializing data provider phase for cycle {cycle_id}, report {report_id}")
        
        try:
            # Import required modules
            from app.application.use_cases.data_owner_universal import StartDataProviderPhaseUseCase
            from app.core.database import AsyncSessionLocal
            
            # Create a new session for this operation
            async with AsyncSessionLocal() as new_db:
                # Create an instance of the use case
                use_case = StartDataProviderPhaseUseCase()
                
                # Call the mapping creation method directly since the phase is already started
                logger.info("Calling _create_attribute_lob_mappings directly with new session")
                await use_case._create_attribute_lob_mappings(new_db, cycle_id, report_id, user_id)
                
                # Commit the mappings
                await new_db.commit()
                logger.info("Data provider phase initialized successfully - mappings created")
            
        except Exception as e:
            logger.error(f"Error initializing data provider phase: {str(e)}")
            # Don't re-raise - the phase is already started, just log the error