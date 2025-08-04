"""
Workflow Orchestration Service
Handles automatic phase transitions, initialization, and dependency management with enhanced state/status tracking
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, date
import logging

from app.models.workflow import WorkflowPhase
from app.models.cycle_report import CycleReport
from app.models.report_attribute import ReportAttribute
from app.core.database import get_db
from app.utils.phase_helpers import get_cycle_report_from_phase, get_phase_id
from app.schemas.workflow_phase import (
    WorkflowPhaseUpdate, 
    PhaseTransitionRequest, 
    WorkflowPhaseState, 
    WorkflowPhaseStatus,
    WorkflowPhaseOverride
)

logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    """
    Central workflow orchestration service with enhanced state/status tracking
    """
    
    # Define phase dependencies
    PHASE_DEPENDENCIES = {
        'Planning': [],
        'Data Profiling': ['Planning'],
        'Scoping': ['Data Profiling'],
        'Sample Selection': ['Scoping'],
        'Data Owner Identification': ['Sample Selection'],
        'Request for Information': ['Data Owner Identification'],
        'Test Execution': ['Request for Information'],
        'Observations': ['Test Execution'],
        'Finalize Test Report': ['Observations']
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_cycle_report_optimized(self, cycle_id: int, report_id: int) -> Optional[CycleReport]:
        """Get cycle report with optimized query using phase_id when possible"""
        try:
            # Try to get phase_id first for more efficient query
            phase_id = await get_phase_id(self.db, cycle_id, report_id, "Planning")  # Use Planning as default
            
            if phase_id:
                # ✅ OPTIMIZED: More efficient query through phase
                result = await self.db.execute(
                    select(CycleReport)
                    .join(WorkflowPhase, WorkflowPhase.cycle_id == CycleReport.cycle_id)
                    .options(selectinload(CycleReport.cycle), selectinload(CycleReport.report))
                    .where(WorkflowPhase.phase_id == phase_id)
                )
            else:
                # Fallback to original query
                result = await self.db.execute(
                    select(CycleReport)
                    .options(selectinload(CycleReport.cycle), selectinload(CycleReport.report))
                    .where(and_(CycleReport.cycle_id == cycle_id, CycleReport.report_id == report_id))
                )
            
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting cycle report: {str(e)}")
            return None
    
    async def initialize_workflow_phases(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """
        Initialize all workflow phases for a report with enhanced state/status tracking
        Creates both generic WorkflowPhase records and specific phase records for complex phases
        """
        try:
            # Check if phases already exist
            existing_phases = await self.db.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id
                    )
                )
            )
            
            if existing_phases.scalars().first():
                raise ValueError("Workflow phases already initialized for this report")
            
            # Get cycle information for baseline date
            from app.models.test_cycle import TestCycle
            cycle_result = await self.db.execute(
                select(TestCycle).where(TestCycle.cycle_id == cycle_id)
            )
            cycle = cycle_result.scalar_one_or_none()
            baseline_date = cycle.start_date if cycle and cycle.start_date else datetime.now().date()
            
            # Define phase durations in days
            phase_durations = {
                'Planning': 7,
                'Data Profiling': 5,
                'Scoping': 7,
                'Sample Selection': 5,
                'Data Provider ID': 3,
                'Request Info': 7,
                'Test Execution': 14,
                'Testing': 14,  # Handle both variants
                'Observations': 7,
                'Finalize Test Report': 5
            }
            
            # Create all generic workflow phases
            created_phases = []
            current_start_date = baseline_date
            
            for phase_name in self.PHASE_DEPENDENCIES.keys():
                # Get phase duration
                duration = phase_durations.get(phase_name, 7)  # Default 7 days
                
                workflow_phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name=phase_name,
                    status='Not Started',  # Legacy field
                    state='Not Started',   # New state field
                    schedule_status='On Track',  # New status field
                    planned_start_date=current_start_date,
                    planned_end_date=current_start_date + timedelta(days=duration - 1)
                )
                
                self.db.add(workflow_phase)
                created_phases.append(phase_name)
                
                # Next phase starts after this one ends
                current_start_date = workflow_phase.planned_end_date + timedelta(days=1)
            
            # Skip creating specific phase records (models don't exist)
            # specific_phases_created = await self._create_specific_phase_records(cycle_id, report_id)
            specific_phases_created = []
            
            await self.db.commit()
            
            logger.info(f"Initialized {len(created_phases)} workflow phases for cycle {cycle_id}, report {report_id}")
            
            return {
                "message": "Workflow phases initialized successfully",
                "cycle_id": cycle_id,
                "report_id": report_id,
                "phases_created": len(created_phases),
                "phase_names": created_phases,
                "specific_phases_created": 0,
                "specific_phase_names": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to initialize workflow phases: {str(e)}")
            raise
    
    async def _create_specific_phase_records(self, cycle_id: int, report_id: int) -> List[str]:
        """
        Create specific phase records for all phases that need more than just WorkflowPhase
        """
        specific_phases_created = []
        
        # DEPRECATED: Now using unified WorkflowPhase for all phases
        # The phase-specific functionality is handled via phase_metadata in WorkflowPhase
        return specific_phases_created
        
        # OLD CODE BELOW - KEPT FOR REFERENCE
        """
        try:
            # Import specific phase models - DEPRECATED: Using unified WorkflowPhase
            # from app.models.planning_phase import PlanningPhase
            from app.models.data_profiling import DataProfilingFile
            # from app.models.scoping_phase import ScopingPhase
            # from app.models.data_owner_phase import DataProviderPhase
            # from app.models.sample_selection_phase import SampleSelectionPhase
            # from app.models.request_info import RequestInfoPhase
            # from app.models.test_execution import TestExecutionPhase
            # from app.models.observation_management import ObservationManagementPhase
            from datetime import datetime, timedelta
            
            # Create Planning Phase
            planning_phase = PlanningPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='Not Started',
                planned_start_date=datetime.utcnow(),
                planned_end_date=datetime.utcnow() + timedelta(days=7),
                document_requirements=['Report Template', 'Data Dictionary'],
                attribute_generation_strategy='hybrid'
            )
            self.db.add(planning_phase)
            specific_phases_created.append('PlanningPhase')
            
            # Create Data Profiling Phase
            data_profiling_phase =(
                cycle_id=cycle_id,
                report_id=report_id,
                status='Not Started',  # Using 'status' instead of 'phase_status'
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(data_profiling_phase)
            specific_phases_created.append('')
            
            # Create Scoping Phase
            scoping_phase = ScopingPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='Not Started',
                planned_start_date=datetime.utcnow() + timedelta(days=14),  # After Data Profiling
                planned_end_date=datetime.utcnow() + timedelta(days=21),
                llm_model_strategy='hybrid',
                confidence_threshold=7.0,
                use_regulatory_context=True
            )
            self.db.add(scoping_phase)
            specific_phases_created.append('ScopingPhase')
            
            # Create Data Provider Phase
            data_owner_phase = DataProviderPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='Not Started',
                planned_start_date=datetime.utcnow() + timedelta(days=21),  # After Scoping
                planned_end_date=datetime.utcnow() + timedelta(days=28),
                assignment_sla_hours=24,
                auto_escalation_enabled=True,
                use_historical_assignments=True
            )
            self.db.add(data_owner_phase)
            specific_phases_created.append('DataProviderPhase')
            
            # Create CycleReportSampleSelectionSamples Selection Phase
            sample_selection_phase = SampleSelectionPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='Not Started',
                planned_start_date=datetime.utcnow() + timedelta(days=21),  # Parallel with Data Provider
                planned_end_date=datetime.utcnow() + timedelta(days=35),
                target_sample_size=25,
                sampling_methodology='Risk-based sampling',
                llm_generation_enabled=True,
                manual_upload_enabled=True
            )
            self.db.add(sample_selection_phase)
            specific_phases_created.append('SampleSelectionPhase')
            
            # Create Request Info Phase
            request_info_phase = RequestInfoPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='Not Started',
                planned_start_date=datetime.utcnow() + timedelta(days=35),
                planned_end_date=datetime.utcnow() + timedelta(days=42),
                submission_deadline=datetime.utcnow() + timedelta(days=42),  # Required by database
                instructions='Please provide requested data and documentation',
                auto_generate_test_cases=True,
                notification_frequency_days=3
            )
            self.db.add(request_info_phase)
            specific_phases_created.append('RequestInfoPhase')
            
            # Create Test Execution Phase
            test_execution_phase = TestExecutionPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='Not Started',
                planned_start_date=datetime.utcnow() + timedelta(days=42),
                planned_end_date=datetime.utcnow() + timedelta(days=56),
                testing_methodology='Comprehensive validation',
                parallel_execution_enabled=True,
                auto_comparison_enabled=True
            )
            self.db.add(test_execution_phase)
            specific_phases_created.append('TestExecutionPhase')
            
            # Create Observation Management Phase
            observation_management_phase = ObservationManagementPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status='Not Started',
                planned_start_date=datetime.utcnow() + timedelta(days=56),
                planned_end_date=datetime.utcnow() + timedelta(days=63),
                auto_categorization_enabled=True,
                impact_assessment_required=True,
                approval_workflow_enabled=True
            )
            self.db.add(observation_management_phase)
            specific_phases_created.append('ObservationManagementPhase')
            
            # Commit all specific phase records
            await self.db.commit()
            
            logger.info(f"Created specific phase records for cycle {cycle_id}, report {report_id}: {specific_phases_created}")
            
        except Exception as e:
            logger.error(f"Error creating specific phase records: {str(e)}")
            await self.db.rollback()
            raise
            
        return specific_phases_created
        """
    
    async def update_phase_state(
        self, 
        cycle_id: int, 
        report_id: int, 
        phase_name: str,
        new_state: str,
        notes: Optional[str] = None,
        user_id: int = None
    ) -> WorkflowPhase:
        """Update phase state with automatic status calculation"""
        result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            raise ValueError(f"Phase {phase_name} not found")
        
        # Update state and related fields
        old_state = phase.state
        phase.state = new_state
        
        if notes:
            phase.notes = notes
        
        # Update actual dates based on state transitions
        if old_state != new_state:
            if new_state == 'In Progress' and not phase.actual_start_date:
                phase.actual_start_date = datetime.utcnow()
                phase.started_by = user_id
            elif new_state == 'Complete' and not phase.actual_end_date:
                phase.actual_end_date = datetime.utcnow()
                phase.completed_by = user_id
        
        # Recalculate schedule status
        phase.schedule_status = self._calculate_schedule_status(phase)
        
        # Handle workflow triggers on state changes
        if old_state != new_state:
            await self._handle_phase_state_transition(cycle_id, report_id, phase_name, old_state, new_state, user_id)
        
        await self.db.commit()
        await self.db.refresh(phase)
        
        logger.info(f"Phase {phase_name} state updated from {old_state} to {new_state} by user {user_id}")
        
        return phase
    
    async def override_phase_status(
        self, 
        cycle_id: int, 
        report_id: int, 
        phase_name: str,
        state_override: Optional[str] = None,
        status_override: Optional[str] = None,
        override_reason: str = "",
        user_id: int = None
    ) -> WorkflowPhase:
        """Override phase state or status"""
        result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            raise ValueError(f"Phase {phase_name} not found")
        
        # Update override fields
        phase.state_override = state_override
        phase.status_override = status_override
        phase.override_reason = override_reason
        phase.override_by = user_id
        phase.override_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(phase)
        
        logger.info(f"Phase {phase_name} overridden by user {user_id}: state={state_override}, status={status_override}")
        
        return phase
    
    async def clear_phase_overrides(
        self, 
        cycle_id: int, 
        report_id: int, 
        phase_name: str,
        user_id: int = None
    ) -> WorkflowPhase:
        """Clear phase overrides"""
        result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            raise ValueError(f"Phase {phase_name} not found")
        
        # Clear override fields
        phase.state_override = None
        phase.status_override = None
        phase.override_reason = None
        phase.override_by = None
        phase.override_at = None
        
        await self.db.commit()
        await self.db.refresh(phase)
        
        logger.info(f"Phase {phase_name} overrides cleared by user {user_id}")
        
        return phase
    
    async def update_phase_dates(
        self,
        cycle_id: int,
        report_id: int,
        phase_name: str,
        update_data: WorkflowPhaseUpdate
    ) -> WorkflowPhase:
        """Update phase dates and recalculate status"""
        
        phase = await self._get_phase(cycle_id, report_id, phase_name)
        if not phase:
            raise ValueError(f"Phase {phase_name} not found")
        
        # Update dates
        if update_data.planned_start_date is not None:
            phase.planned_start_date = update_data.planned_start_date
        
        if update_data.planned_end_date is not None:
            phase.planned_end_date = update_data.planned_end_date
        
        if update_data.actual_start_date is not None:
            phase.actual_start_date = update_data.actual_start_date
        
        if update_data.actual_end_date is not None:
            phase.actual_end_date = update_data.actual_end_date
        
        if update_data.notes is not None:
            phase.notes = update_data.notes
        
        # Recalculate schedule status (unless overridden)
        if not phase.status_override:
            phase.schedule_status = self._calculate_schedule_status(phase)
        
        await self.db.commit()
        
        logger.info(f"Updated dates for phase {phase_name}")
        
        return phase
    
    def _calculate_schedule_status(self, phase: WorkflowPhase) -> WorkflowPhaseStatus:
        """Calculate schedule status based on dates and current state"""
        
        # If no planned end date, default to on track
        if not phase.planned_end_date:
            return WorkflowPhaseStatus.ON_TRACK
        
        # If phase is complete, it's on track regardless of dates
        if phase.state == WorkflowPhaseState.COMPLETE:
            return WorkflowPhaseStatus.ON_TRACK
        
        today = date.today()
        
        # If past due date and not complete
        if today > phase.planned_end_date:
            return WorkflowPhaseStatus.PAST_DUE
        
        # If within 7 days of due date
        days_until_due = (phase.planned_end_date - today).days
        if 0 <= days_until_due <= 7:
            return WorkflowPhaseStatus.AT_RISK
        
        return WorkflowPhaseStatus.ON_TRACK
    
    async def _get_phase(self, cycle_id: int, report_id: int, phase_name: str) -> Optional[WorkflowPhase]:
        """Get a specific workflow phase"""
        result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_workflow_status(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Get comprehensive workflow status with enhanced state/status tracking"""
        
        # Get all phases
        result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id
                )
            ).order_by(WorkflowPhase.phase_id)
        )
        phases = result.scalars().all()
        
        if not phases:
            raise ValueError("No workflow phases found")
        
        # Calculate overall metrics
        total_phases = len(phases)
        completed_phases = sum(1 for p in phases if (p.state_override or p.state) == WorkflowPhaseState.COMPLETE)
        overall_progress = (completed_phases / total_phases) * 100 if total_phases > 0 else 0
        
        # Determine overall state and status
        if completed_phases == total_phases:
            overall_state = WorkflowPhaseState.COMPLETE
        elif any((p.state_override or p.state) == WorkflowPhaseState.IN_PROGRESS for p in phases):
            overall_state = WorkflowPhaseState.IN_PROGRESS
        else:
            overall_state = WorkflowPhaseState.NOT_STARTED
        
        # Overall status is worst case
        status_priority = {
            WorkflowPhaseStatus.PAST_DUE: 3,
            WorkflowPhaseStatus.AT_RISK: 2,
            WorkflowPhaseStatus.ON_TRACK: 1
        }
        
        overall_status = WorkflowPhaseStatus.ON_TRACK
        for phase in phases:
            effective_status = phase.status_override or phase.schedule_status
            if status_priority[effective_status] > status_priority[overall_status]:
                overall_status = effective_status
        
        # Find current phase
        current_phase = None
        for phase in phases:
            effective_state = phase.state_override or phase.state
            if effective_state == WorkflowPhaseState.IN_PROGRESS:
                current_phase = phase.phase_name
                break
        
        # Calculate progress for each phase
        phase_data = []
        for p in phases:
            progress = await self._calculate_phase_progress(cycle_id, report_id, p.phase_name)
            phase_info = {
                "phase_id": p.phase_id,
                "phase_name": p.phase_name,
                "state": p.state,
                "status": p.status,
                "schedule_status": p.schedule_status,
                "state_override": p.state_override,
                "status_override": p.status_override,
                "planned_start_date": p.planned_start_date.isoformat() if p.planned_start_date else None,
                "planned_end_date": p.planned_end_date.isoformat() if p.planned_end_date else None,
                "actual_start_date": p.actual_start_date.isoformat() if p.actual_start_date else None,
                "actual_end_date": p.actual_end_date.isoformat() if p.actual_end_date else None,
                "notes": p.notes,
                # Calculate phase-specific progress
                "progress_percentage": progress,
                # Include effective state and status
                "effective_state": p.state_override or p.state,
                "effective_status": p.status_override or p.schedule_status,
                # Include computed fields
                "has_overrides": p.state_override is not None or p.status_override is not None,
                "is_overdue": self._is_phase_overdue(p),
                "is_at_risk": self._is_phase_at_risk(p),
                "days_until_due": self._days_until_due(p),
                # Include legacy status for compatibility
                "started_at": p.actual_start_date.isoformat() if p.actual_start_date else None,
                "completed_at": p.actual_end_date.isoformat() if p.actual_end_date else None
            }
            phase_data.append(phase_info)
        
        return {
            "cycle_id": cycle_id,
            "report_id": report_id,
            "overall_state": overall_state,
            "overall_status": overall_status,
            "overall_progress": overall_progress,
            "current_phase": current_phase,
            "completed_phases": completed_phases,
            "total_phases": total_phases,
            "phases": phase_data
        }

    async def get_phase_date_status(self, cycle_id: int, report_id: int, phase_name: str) -> Dict[str, Any]:
        """Get date-based status for a specific phase"""
        result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            raise ValueError(f"Phase {phase_name} not found")
        
        return {
            "phase_name": phase.phase_name,
            "effective_status": self._calculate_schedule_status(phase),
            "is_overdue": self._is_phase_overdue(phase),
            "is_at_risk": self._is_phase_at_risk(phase),
            "days_until_due": self._days_until_due(phase)
        }
    
    async def _calculate_phase_progress(self, cycle_id: int, report_id: int, phase_name: str) -> float:
        """Calculate progress percentage for a specific phase"""
        from sqlalchemy import func, distinct
        
        # For phases that are complete, return 100%
        result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            return 0.0
        
        effective_state = phase.state_override or phase.state
        
        # If phase is complete, it's 100%
        if effective_state == 'Complete' or effective_state == WorkflowPhaseState.COMPLETE:
            return 100.0
        elif effective_state == 'In Progress' or effective_state == WorkflowPhaseState.IN_PROGRESS:
            # Phase-specific progress calculations
            try:
                if phase_name == 'Planning':
                    # Planning is 100% if attributes exist
                    result = await self.db.execute(
                        select(func.count(ReportAttribute.attribute_id))
                        .where(ReportAttribute.report_id == report_id)
                    )
                    count = result.scalar()
                    return 100.0 if count > 0 else 50.0
                    
                elif phase_name == 'Data Profiling':
                    # Progress based on profiling completion
                    from app.models.data_profiling import DataProfilingFile, ProfilingRule
                    
                    # Check if phase record exists via WorkflowPhase
                    dp_result = await self.db.execute(
                        select(WorkflowPhase).where(
                            and_(
                                WorkflowPhase.cycle_id == cycle_id,
                                WorkflowPhase.report_id == report_id,
                                WorkflowPhase.phase_name == "Data Profiling"
                            )
                        )
                    )
                    dp_phase = dp_result.scalar_one_or_none()
                    
                    if not dp_phase:
                        return 25.0
                    
                    # Progress milestones:
                    # - Data files uploaded: 25%
                    # - Rules generated: 50%
                    # - Profiling executed: 75%
                    # - Phase completed: 100%
                    
                    if dp_phase.phase_completed_at:
                        return 100.0
                    elif dp_phase.profiling_executed_at:
                        return 75.0
                    elif dp_phase.rules_generated_at:
                        return 50.0
                    elif dp_phase.data_received_at:
                        return 25.0
                    else:
                        return 10.0
                    
                elif phase_name == 'Scoping':
                    # Scoping progress based on scoped attributes
                    result = await self.db.execute(
                        select(
                            func.count(ReportAttribute.attribute_id).filter(ReportAttribute.is_scoped == True),
                            func.count(ReportAttribute.attribute_id)
                        ).where(ReportAttribute.report_id == report_id)
                    )
                    scoped, total = result.first()
                    if total > 0:
                        return (scoped / total) * 100
                    return 50.0
                    
                elif phase_name == 'Data Provider ID':
                    # Progress based on data owner assignments
                    from app.models.testing import DataProviderAssignment
                    result = await self.db.execute(
                        select(
                            func.count(distinct(DataProviderAssignment.attribute_id)).label('assigned'),
                            func.count(distinct(ReportAttribute.attribute_id)).label('total')
                        ).select_from(ReportAttribute)
                        .outerjoin(
                            DataProviderAssignment,
                            and_(
                                DataProviderAssignment.cycle_id == cycle_id,
                                DataProviderAssignment.report_id == report_id,
                                DataProviderAssignment.attribute_id == ReportAttribute.attribute_id
                            )
                        ).where(
                            and_(
                                ReportAttribute.report_id == report_id,
                                ReportAttribute.is_scoped == True
                            )
                        )
                    )
                    counts = result.first()
                    if counts and counts.total > 0:
                        return (counts.assigned / counts.total) * 100
                    return 50.0
                    
                elif phase_name == 'CycleReportSampleSelectionSamples Selection':
                    # Progress based on sample selection
                    from app.models.sample_selection import SampleSelection
                    result = await self.db.execute(
                        select(func.count(SampleSelection.sample_id))
                        .where(
                            and_(
                                SampleSelection.cycle_id == cycle_id,
                                SampleSelection.report_id == report_id
                            )
                        )
                    )
                    count = result.scalar()
                    # If we have samples, consider it complete (100%), otherwise 50%
                    return 100.0 if count > 0 else 50.0
                    
                elif phase_name == 'Request Info':
                    # Progress based on test cases generated
                    from app.models.request_info import CycleReportCycleReportTestCase
                    result = await self.db.execute(
                        select(func.count(CycleReportTestCase.test_case_id))
                        .where(
                            and_(
                                CycleReportTestCase.cycle_id == cycle_id,
                                CycleReportTestCase.report_id == report_id
                            )
                        )
                    )
                    count = result.scalar()
                    # If we have test cases, show 75% progress
                    return 75.0 if count > 0 else 25.0
                    
                elif phase_name == 'Testing':
                    # Progress based on test executions
                    from app.models.test_execution import TestExecution
                    result = await self.db.execute(
                        select(
                            func.count(TestExecution.execution_id).filter(TestExecution.status == 'Completed').label('completed'),
                            func.count(TestExecution.execution_id).label('total')
                        ).where(
                            and_(
                                TestExecution.cycle_id == cycle_id,
                                TestExecution.report_id == report_id
                            )
                        )
                    )
                    counts = result.first()
                    if counts and counts.total > 0:
                        return (counts.completed / counts.total) * 100
                    return 25.0
                    
                elif phase_name == 'Observations':
                    # Progress based on observations reviewed
                    from app.models.observation_management import Observation
                    result = await self.db.execute(
                        select(func.count(Observation.observation_id))
                        .where(
                            and_(
                                Observation.cycle_id == cycle_id,
                                Observation.report_id == report_id
                            )
                        )
                    )
                    count = result.scalar()
                    # If observations exist, show 50% progress
                    return 50.0 if count > 0 else 25.0
                    
                elif phase_name == 'Preparing Test Report':
                    # Progress based on report sections generated
                    from app.models.test_report import TestReportSection
                    result = await self.db.execute(
                        select(TestReportSection)
                        .where(
                            and_(
                                TestReportSection.phase_id == phase.phase_id
                            )
                        )
                    )
                    report_phase = result.scalar_one_or_none()
                    if report_phase:
                        # Count sections
                        result = await self.db.execute(
                            select(func.count(TestReportSection.section_id))
                            .where(TestReportSection.phase_id == report_phase.phase_id)
                        )
                        section_count = result.scalar()
                        # If we have sections, show 75% progress, if report is generated 100%
                        if report_phase.final_report_document_id:
                            return 100.0
                        elif section_count > 0:
                            return 75.0
                        else:
                            return 25.0
                    return 25.0
                    
                else:
                    # Default for other in-progress phases
                    return 50.0
                    
            except Exception as e:
                # If there's an error in calculation, return default
                logger.warning(f"Error calculating progress for {phase_name}: {str(e)}")
                return 50.0
        else:
            return 0.0
    
    def _is_phase_overdue(self, phase: WorkflowPhase) -> bool:
        """Check if a phase is overdue"""
        if not phase.planned_end_date:
            return False
        
        effective_state = phase.state_override or phase.state
        if effective_state == 'Complete' or effective_state == WorkflowPhaseState.COMPLETE:
            return False
        
        # Convert date to datetime for comparison
        if isinstance(phase.planned_end_date, date) and not isinstance(phase.planned_end_date, datetime):
            planned_end_datetime = datetime.combine(phase.planned_end_date, datetime.min.time())
        else:
            planned_end_datetime = phase.planned_end_date
            
        return datetime.utcnow() > planned_end_datetime
    
    def _is_phase_at_risk(self, phase: WorkflowPhase) -> bool:
        """Check if a phase is at risk (within 7 days of due date)"""
        if not phase.planned_end_date:
            return False
        
        effective_state = phase.state_override or phase.state
        if effective_state == 'Complete' or effective_state == WorkflowPhaseState.COMPLETE:
            return False
        
        # Convert date to datetime for comparison
        if isinstance(phase.planned_end_date, date) and not isinstance(phase.planned_end_date, datetime):
            planned_end_datetime = datetime.combine(phase.planned_end_date, datetime.min.time())
        else:
            planned_end_datetime = phase.planned_end_date
            
        days_until_due = (planned_end_datetime - datetime.utcnow()).days
        return 0 < days_until_due <= 7
    
    def _days_until_due(self, phase: WorkflowPhase) -> Optional[int]:
        """Calculate days until phase is due"""
        if not phase.planned_end_date:
            return None
        
        effective_state = phase.state_override or phase.state
        if effective_state == 'Complete' or effective_state == WorkflowPhaseState.COMPLETE:
            return None
        
        # Convert date to datetime for comparison
        if isinstance(phase.planned_end_date, date) and not isinstance(phase.planned_end_date, datetime):
            planned_end_datetime = datetime.combine(phase.planned_end_date, datetime.min.time())
        else:
            planned_end_datetime = phase.planned_end_date
            
        return (planned_end_datetime - datetime.utcnow()).days
    
    async def _handle_phase_state_transition(
        self, 
        cycle_id: int, 
        report_id: int, 
        phase_name: str, 
        old_state: str, 
        new_state: str, 
        user_id: int
    ):
        """Handle automated triggers when phases change state"""
        
        # When Data Provider ID starts, we only create the attribute/LOB mappings
        # Universal assignments are created later when tester clicks "Send to Data Executive"
        if phase_name == "Data Provider ID" and new_state == "In Progress":
            logger.info(f"Data Provider ID phase started - attribute/LOB mappings should already be created")
        
        # When Data Provider ID completes, create Data Upload assignments for Request Info
        elif phase_name == "Data Provider ID" and new_state == "Complete":
            await self._create_data_upload_assignments(cycle_id, report_id, user_id)
            
        # Additional workflow triggers can be added here
        logger.info(f"Handled phase transition: {phase_name} {old_state} -> {new_state}")
    
    async def _create_data_executive_assignment(self, cycle_id: int, report_id: int, tester_user_id: int):
        """Create LOB Assignment for Data Executive when CycleReportSampleSelectionSamples Selection completes"""
        try:
            # Check if data owner LOB mappings already exist
            from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping
            existing_check = await self.db.execute(
                select(func.count(DataOwnerLOBAttributeMapping.mapping_id))
                .join(WorkflowPhase, DataOwnerLOBAttributeMapping.phase_id == WorkflowPhase.phase_id)
                .where(and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Data Provider ID'
                ))
            )
            existing_count = existing_check.scalar()
            if existing_count > 0:
                logger.info(f"Data owner LOB assignments already exist ({existing_count} assignments) - skipping Data Executive assignment creation")
                return
            from app.services.universal_assignment_service import UniversalAssignmentService
            from app.services.email_service import EmailService
            from app.models.user import User
            from app.models.report import Report
            from app.models.cycle_report import CycleReport
            
            # ✅ OPTIMIZED: Get cycle and report info using optimized method
            cycle_report = await self.get_cycle_report_optimized(cycle_id, report_id)
            
            if not cycle_report:
                logger.error(f"Cycle report not found for cycle {cycle_id}, report {report_id}")
                return
            
            # Find Data Executive user
            result = await self.db.execute(
                select(User).where(User.role == "Data Executive").limit(1)
            )
            data_executive = result.scalar_one_or_none()
            
            if not data_executive:
                logger.warning("No Data Executive user found for assignment")
                return
            
            # Create universal assignment
            assignment_service = UniversalAssignmentService(self.db, EmailService())
            
            assignment = await assignment_service.create_assignment(
                assignment_type="LOB Assignment",
                from_role="Tester",
                to_role="Data Executive",
                from_user_id=tester_user_id,
                to_user_id=data_executive.user_id,
                title=f"Assign Data Owners for {cycle_report.report.report_name}",
                description=f"Please assign appropriate data owners for each attribute in {cycle_report.report.report_name} (Cycle {cycle_report.cycle.cycle_name}).",
                context_type="Report",
                context_data={
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "report_name": cycle_report.report.report_name,
                    "cycle_name": cycle_report.cycle.cycle_name,
                    "phase_name": "Data Provider ID"
                },
                task_instructions="Review each scoped attribute and assign the appropriate data owner (LOB) responsible for providing the necessary data and documentation.",
                priority="High",
                requires_approval=False
            )
            
            logger.info(f"Created Data Executive assignment {assignment.assignment_id} for cycle {cycle_id}, report {report_id}")
            
        except Exception as e:
            logger.error(f"Failed to create Data Executive assignment: {str(e)}")
    
    async def _create_data_upload_assignments(self, cycle_id: int, report_id: int, tester_user_id: int):
        """Create Data Upload Request assignments when Data Provider ID completes"""
        try:
            from app.services.universal_assignment_service import UniversalAssignmentService
            from app.services.email_service import EmailService
            from app.models.testing import DataProviderAssignment
            from app.models.user import User
            from app.models.cycle_report import CycleReport
            
            # Get assigned data providers
            result = await self.db.execute(
                select(DataProviderAssignment)
                .options(selectinload(DataProviderAssignment.data_provider))
                .where(and_(
                    DataProviderAssignment.cycle_id == cycle_id,
                    DataProviderAssignment.report_id == report_id
                ))
                .distinct(DataProviderAssignment.data_provider_id)
            )
            assignments = result.scalars().all()
            
            if not assignments:
                logger.warning(f"No data provider assignments found for cycle {cycle_id}, report {report_id}")
                return
            
            # ✅ OPTIMIZED: Get cycle and report info using optimized method
            cycle_report = await self.get_cycle_report_optimized(cycle_id, report_id)
            
            assignment_service = UniversalAssignmentService(self.db, EmailService())
            
            # Create assignment for each unique data provider
            unique_providers = {}
            for assignment in assignments:
                if assignment.data_provider_id not in unique_providers:
                    unique_providers[assignment.data_provider_id] = assignment.data_provider
            
            for provider_id, provider in unique_providers.items():
                assignment = await assignment_service.create_assignment(
                    assignment_type="Data Upload Request",
                    from_role="Tester",
                    to_role="Data Owner",
                    from_user_id=tester_user_id,
                    to_user_id=provider.user_id,
                    title=f"Upload Data for {cycle_report.report.report_name}",
                    description=f"Please upload the required data files for {cycle_report.report.report_name} (Cycle {cycle_report.cycle.cycle_name}).",
                    context_type="Report",
                    context_data={
                        "cycle_id": cycle_id,
                        "report_id": report_id,
                        "report_name": cycle_report.report.report_name,
                        "cycle_name": cycle_report.cycle.cycle_name,
                        "phase_name": "Request Info",
                        "data_provider_id": provider_id
                    },
                    task_instructions="Upload all necessary data files and documentation as specified in the testing requirements. Ensure files are in the correct format and contain all required attributes.",
                    priority="High",
                    requires_approval=False
                )
                
                logger.info(f"Created Data Upload assignment {assignment.assignment_id} for provider {provider.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to create Data Upload assignments: {str(e)}")
    
    def _calculate_schedule_status(self, phase: WorkflowPhase) -> str:
        """Calculate schedule status based on dates"""
        if self._is_phase_overdue(phase):
            return WorkflowPhaseStatus.PAST_DUE
        elif self._is_phase_at_risk(phase):
            return WorkflowPhaseStatus.AT_RISK
        else:
            return WorkflowPhaseStatus.ON_TRACK

# Utility functions for use in endpoints
async def get_workflow_orchestrator(db: AsyncSession = None) -> WorkflowOrchestrator:
    """Get workflow orchestrator instance"""
    if not db:
        # This would be used in endpoints where db is injected
        async for session in get_db():
            return WorkflowOrchestrator(session)
    return WorkflowOrchestrator(db) 