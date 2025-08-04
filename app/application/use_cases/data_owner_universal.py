"""
Data Owner Identification use cases using universal assignments
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update, delete, text
from sqlalchemy.orm import selectinload
import uuid
import logging
import json

from app.application.use_cases.base import UseCase
from app.application.dtos.data_owner import (
    DataProviderPhaseStartDTO,
    DataProviderPhaseStatusDTO,
    LOBAssignmentSubmissionDTO,
    CDOAssignmentSubmissionDTO,
    HistoricalAssignmentResponseDTO,
    HistoricalAssignmentSuggestionDTO,
    AttributeAssignmentStatusDTO,
    AssignmentMatrixDTO,
    SLAViolationDTO,
    EscalationEmailRequestDTO,
    EscalationEmailResponseDTO,
    DataProviderPhaseCompleteDTO,
    DataOwnerAssignmentDTO,
    CDODashboardResponseDTO,
    CDODashboardMetricsDTO,
    CDOWorkflowStatusDTO,
    CDOAssignmentActivityDTO,
    DataOwnerAssignmentAuditLogDTO,
    AuditLogEntryDTO,
    AssignmentStatusEnum,
    EscalationLevelEnum
)
from app.models import (
    TestCycle,
    CycleReport,
    Report,
    WorkflowPhase,
    ReportAttribute,
    LOB,
    User,
    UniversalAssignment,
    # AttributeLOBAssignment removed - table doesn't exist
    # HistoricalDataOwnerAssignment removed - table doesn't exist
    DataOwnerSLAViolation,
    DataOwnerEscalationLog,
    DataOwnerPhaseAuditLog,
    # SampleSet,  # Temporarily disabled - model not found
    # SampleRecord,  # Temporarily disabled - model not found
    TesterScopingDecision
)
from app.services.workflow_orchestrator import get_workflow_orchestrator

logger = logging.getLogger(__name__)


class StartDataProviderPhaseUseCase(UseCase):
    """Start data owner identification phase using universal assignments"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        start_data: DataProviderPhaseStartDTO,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Start the phase"""
        
        # Verify cycle and report exist
        cycle_report = await db.execute(
            select(CycleReport)
            .options(selectinload(CycleReport.cycle), selectinload(CycleReport.report))
            .where(and_(CycleReport.cycle_id == cycle_id, CycleReport.report_id == report_id))
        )
        cycle_report = cycle_report.scalar_one_or_none()
        
        if not cycle_report:
            raise ValueError("Cycle report not found")
        
        # Verify tester assignment
        current_user = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        current_user = current_user.scalar_one()
        
        if cycle_report.tester_id != user_id:
            raise ValueError("Only assigned tester can start data owner phase")
        
        # Check if sampling phase is complete
        sampling_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Sample Selection'
            ))
        )
        sampling_phase = sampling_phase.scalar_one_or_none()
        
        if not sampling_phase or sampling_phase.status != 'Complete':
            raise ValueError("Sampling phase must be completed before starting data owner identification")
        
        # Check if data owner phase already exists
        data_owner_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Data Provider ID'
            ))
        )
        data_owner_phase = data_owner_phase.scalar_one_or_none()
        
        if data_owner_phase and data_owner_phase.actual_start_date:
            raise ValueError("Data owner identification phase already started")
        
        # Create phase if it doesn't exist, but don't start it yet
        if not data_owner_phase:
            data_owner_phase = WorkflowPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name='Data Provider ID',
                status='Not Started',
                state='Not Started',
                planned_start_date=start_data.planned_start_date,
                planned_end_date=start_data.planned_end_date
            )
            db.add(data_owner_phase)
            await db.commit()  # Commit so we have the phase_id
        
        # Create attribute LOB mappings for data owner identification
        logger.info(f"Calling _create_attribute_lob_mappings for cycle {cycle_id}, report {report_id}")
        await self._create_attribute_lob_mappings(db, cycle_id, report_id, user_id)
        
        try:
            await db.commit()
            logger.info("Successfully committed attribute LOB mappings")
        except Exception as e:
            logger.error(f"Failed to commit mappings: {str(e)}")
            await db.rollback()
            raise
        
        # Use workflow orchestrator to start the phase
        workflow_orchestrator = await get_workflow_orchestrator(db)
        try:
            await workflow_orchestrator.update_phase_state(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Data Provider ID",
                new_state="In Progress",
                notes=start_data.notes,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Workflow orchestrator update_phase_state failed: {str(e)}")
            raise ValueError(f"Failed to start Data Provider ID phase: {str(e)}")
        
        # Refresh the phase to get updated data from workflow orchestrator
        await db.refresh(data_owner_phase)
        
        # Create audit log - skipping for now as table doesn't exist
        # await self._create_audit_log(
        #     db, data_owner_phase.phase_id, "start_data_owner_phase", "WorkflowPhase",
        #     data_owner_phase.phase_id, user_id, notes=start_data.notes
        # )
        
        return {
            "success": True,
            "message": "Data owner identification phase started successfully",
            "phase_id": data_owner_phase.phase_id,
            "cycle_id": cycle_id,
            "report_id": report_id,
            "started_at": data_owner_phase.actual_start_date
        }
    
    async def _create_attribute_lob_mappings(
        self,
        db: AsyncSession,
        cycle_id: int,
        report_id: int,
        created_by: int
    ):
        """Create attribute LOB mappings for non-primary key scoped attributes"""
        logger.info(f"_create_attribute_lob_mappings started for cycle {cycle_id}, report {report_id}")
        
        # Get approved samples from Sample Selection phase
        sample_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Sample Selection',
                WorkflowPhase.status == 'Complete'
            ))
        )
        sample_phase = sample_phase.scalar_one_or_none()
        
        if not sample_phase:
            logger.warning(f"No completed sample selection phase found for cycle {cycle_id}, report {report_id}")
            return
        
        # Get approved sample selection version first
        from app.models.sample_selection import SampleSelectionSample, SampleSelectionVersion
        
        # Find the approved sample selection version using raw SQL
        approved_sample_version_result = await db.execute(
            text('''
                SELECT version_id, version_number 
                FROM cycle_report_sample_selection_versions 
                WHERE phase_id = :phase_id 
                AND version_status = 'approved'
                ORDER BY version_number DESC 
                LIMIT 1
            '''),
            {'phase_id': sample_phase.phase_id}
        )
        approved_sample_version_row = approved_sample_version_result.first()
        
        if not approved_sample_version_row:
            logger.warning(f"No approved sample selection version found for cycle {cycle_id}, report {report_id}")
            return
            
        approved_sample_version_id = approved_sample_version_row.version_id
        
        # Get unique LOBs from approved samples in the approved version
        lob_query = await db.execute(
            select(SampleSelectionSample.lob_id)
            .distinct()
            .where(and_(
                SampleSelectionSample.version_id == approved_sample_version_id,
                SampleSelectionSample.report_owner_decision == 'approved'
            ))
        )
        unique_lob_ids = [row[0] for row in lob_query.all()]
        
        logger.info(f"Found {len(unique_lob_ids)} unique LOB IDs: {unique_lob_ids}")
        
        if not unique_lob_ids:
            logger.warning(f"No LOBs found in approved samples for cycle {cycle_id}, report {report_id}")
            return
        
        # Get scoping phase to find approved non-PK attributes
        scoping_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Scoping',
                WorkflowPhase.status == 'Complete'
            ))
        )
        scoping_phase = scoping_phase.scalar_one_or_none()
        
        if not scoping_phase:
            logger.warning(f"No completed scoping phase found for cycle {cycle_id}, report {report_id}")
            return
            
        # Get approved version first
        from app.models.scoping import ScopingAttribute, ScopingVersion
        from app.models.report_attribute import ReportAttribute as PlanningAttribute
        
        # Find the approved scoping version using raw SQL to avoid enum issues
        # IMPORTANT: We need the LATEST approved version only
        approved_version_result = await db.execute(
            text('''
                SELECT version_id, version_number 
                FROM cycle_report_scoping_versions 
                WHERE phase_id = :phase_id 
                AND version_status = 'approved'
                ORDER BY version_number DESC 
                LIMIT 1
            '''),
            {'phase_id': scoping_phase.phase_id}
        )
        approved_version_row = approved_version_result.first()
        
        if not approved_version_row:
            logger.warning(f"No approved scoping version found for cycle {cycle_id}, report {report_id}")
            return
            
        approved_version_id = approved_version_row.version_id
        
        # Get approved non-PK attributes from the approved version
        scoped_attrs_query = await db.execute(
            select(ScopingAttribute, PlanningAttribute)
            .join(PlanningAttribute, ScopingAttribute.planning_attribute_id == PlanningAttribute.id)
            .where(and_(
                ScopingAttribute.version_id == approved_version_id,
                ScopingAttribute.is_primary_key == False,
                ScopingAttribute.tester_decision == 'accept'
            ))
        )
        scoped_attr_results = scoped_attrs_query.all()
        
        # Create a list of attribute objects with the name attached, filtering out PKs
        scoped_attributes = []
        for scoping_attr, planning_attr in scoped_attr_results:
            # Skip if this is actually a primary key in the planning attributes
            if planning_attr.is_primary_key:
                logger.info(f"Skipping primary key attribute: {planning_attr.attribute_name}")
                continue
            # Add attribute_name to the scoping attribute for easier access
            scoping_attr.attribute_name = planning_attr.attribute_name
            scoped_attributes.append(scoping_attr)
        
        logger.info(f"Found {len(scoped_attributes)} approved non-PK attributes in scoping version (after filtering PKs)")
        logger.info(f"Unique LOB IDs from samples: {unique_lob_ids}")
        
        # Get LOB and CDO information
        all_lobs = await db.execute(
            select(LOB).where(LOB.lob_id.in_(unique_lob_ids))
        )
        all_lobs = {lob.lob_id: lob for lob in all_lobs.scalars().all()}
        
        # Get Data Provider ID phase
        data_provider_phase = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Data Provider ID'
                )
            )
        )
        data_provider_phase = data_provider_phase.scalar_one_or_none()
        
        if not data_provider_phase:
            logger.error(f"Data Provider ID phase not found for cycle {cycle_id}, report {report_id}")
            return
            
        # Import the mapping model
        from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping
        
        # Create mapping records for each attribute/LOB combination
        logger.info(f"Creating attribute LOB mappings for {len(scoped_attributes)} attributes and {len(unique_lob_ids)} LOBs")
        mappings_created = 0
        
        for i, attribute in enumerate(scoped_attributes):
            logger.info(f"Processing attribute {i+1}: {attribute.attribute_name} (ID: {attribute.planning_attribute_id})")
            for lob_id in unique_lob_ids:
                if lob_id in all_lobs:
                    lob = all_lobs[lob_id]
                    
                    # Check if mapping already exists
                    existing = await db.execute(
                        select(DataOwnerLOBAttributeMapping).where(and_(
                            DataOwnerLOBAttributeMapping.phase_id == data_provider_phase.phase_id,
                            DataOwnerLOBAttributeMapping.attribute_id == attribute.planning_attribute_id,
                            DataOwnerLOBAttributeMapping.lob_id == lob_id
                        ))
                    )
                    if not existing.scalar_one_or_none():
                        mapping = DataOwnerLOBAttributeMapping(
                            phase_id=data_provider_phase.phase_id,
                            attribute_id=attribute.planning_attribute_id,
                            lob_id=lob_id,
                            assignment_status='unassigned',
                            created_by_id=created_by,
                            updated_by_id=created_by
                        )
                        db.add(mapping)
                        logger.info(f"Added mapping to session: phase_id={data_provider_phase.phase_id}, attribute_id={attribute.planning_attribute_id}, lob_id={lob_id}")
                        mappings_created += 1
                        
        logger.info(f"Created {mappings_created} attribute LOB mappings")
    
    async def _create_audit_log(
        self,
        db: AsyncSession,
        phase_id: int,
        action: str,
        entity_type: str,
        entity_id: Optional[int],
        performed_by: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ):
        """Create audit log entry"""
        audit_log = DataOwnerPhaseAuditLog(
            phase_id=phase_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=performed_by,
            performed_at=datetime.utcnow(),
            old_values=old_values,
            new_values=new_values,
            notes=notes
        )
        db.add(audit_log)
        await db.commit()


class GetDataProviderPhaseStatusUseCase(UseCase):
    """Get data owner phase status using universal assignments"""
    
    async def _get_total_samples_count(self, cycle_id: int, report_id: int, db: AsyncSession) -> int:
        """Get total samples from approved sample selection version"""
        from app.models.sample_selection import SampleSelectionVersion, SampleSelectionSample
        
        # Get sample selection phase
        sample_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Sample Selection'
            ))
        )
        sample_phase = sample_phase.scalar_one_or_none()
        
        if not sample_phase:
            return 0
            
        # Get approved version
        approved_version = await db.execute(
            select(SampleSelectionVersion)
            .where(and_(
                SampleSelectionVersion.phase_id == sample_phase.phase_id,
                SampleSelectionVersion.version_status == 'approved'
            ))
            .order_by(SampleSelectionVersion.version_number.desc())
            .limit(1)
        )
        approved_version = approved_version.scalar_one_or_none()
        
        if not approved_version:
            return 0
            
        # Count samples in approved version
        samples_count = await db.execute(
            select(func.count(SampleSelectionSample.sample_id))
            .where(SampleSelectionSample.version_id == approved_version.version_id)
        )
        
        return samples_count.scalar() or 0
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> DataProviderPhaseStatusDTO:
        """Get phase status"""
        
        # First check if phase has been started
        phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Data Provider ID'
            ))
        )
        phase = phase.scalar_one_or_none()
        
        # If phase not started, return minimal status
        if not phase or not phase.actual_start_date:
            return DataProviderPhaseStatusDTO(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status="Not Started",
                total_attributes=0,
                scoped_attributes=0,
                total_samples=0,
                attributes_with_lob_assignments=0,
                attributes_with_data_owners=0,
                pending_cdo_assignments=0,
                overdue_assignments=0,
                can_submit_lob_assignments=False,
                can_complete_phase=False,
                completion_requirements=["Phase not started yet"]
            )
        
        # Get scoping phase to find approved non-PK attributes
        from app.models.scoping import ScopingAttribute
        scoping_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Scoping',
                WorkflowPhase.status == 'Complete'
            ))
        )
        scoping_phase = scoping_phase.scalar_one_or_none()
        
        # Default to empty lists if no scoping phase
        scoped_attributes = []
        all_attributes = []
        
        if scoping_phase:
            # Get non-primary key scoped attributes
            scoped_attrs_result = await db.execute(
                select(ScopingAttribute)
                .where(and_(
                    ScopingAttribute.phase_id == scoping_phase.phase_id,
                    ScopingAttribute.is_primary_key == False,
                    ScopingAttribute.report_owner_decision == 'approved'
                ))
            )
            scoped_attributes = scoped_attrs_result.scalars().all()
            
            # Get all attributes from planning phase (for total count)
            planning_phase = await db.execute(
                select(WorkflowPhase)
                .where(and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Planning'
                ))
            )
            planning_phase = planning_phase.scalar_one_or_none()
            
            if planning_phase:
                from app.models.report_attribute import ReportAttribute
                all_attrs_result = await db.execute(
                    select(ReportAttribute)
                    .where(ReportAttribute.phase_id == planning_phase.phase_id)
                )
                all_attributes = all_attrs_result.scalars().all()
            else:
                all_attributes = []
        
        # Get universal assignments for data owner identification
        data_owner_assignments = await db.execute(
            select(UniversalAssignment)
            .where(and_(
                UniversalAssignment.assignment_type == 'LOB Assignment',
                UniversalAssignment.context_type == 'Attribute',
                UniversalAssignment.context_data['cycle_id'].astext == str(cycle_id),
                UniversalAssignment.context_data['report_id'].astext == str(report_id)
            ))
        )
        data_owner_assignments = data_owner_assignments.scalars().all()
        
        # Calculate metrics
        total_attributes = len(all_attributes)
        scoped_attributes_count = len(scoped_attributes)
        
        # Count attributes with assignments
        attributes_with_lob_assignments = len(set(
            assignment.context_data['attribute_id'] if isinstance(assignment.context_data, dict) else json.loads(assignment.context_data)['attribute_id']
            for assignment in data_owner_assignments
        ))
        
        # Count attributes with completed assignments (data owner assigned)
        attributes_with_data_owners = len([
            a for a in data_owner_assignments 
            if a.status == 'Completed'
        ])
        
        # Count pending assignments (assigned but not completed)
        pending_cdo_assignments = len([
            a for a in data_owner_assignments 
            if a.status in ['Assigned', 'Acknowledged', 'In Progress']
        ])
        
        # Get overdue assignments
        overdue_count = 0  # Can be calculated based on due_date if needed
        
        phase_status = phase.status if phase else "Not Started"
        
        # Determine completion requirements
        completion_requirements = []
        can_submit_lob_assignments = True
        can_complete_phase = attributes_with_data_owners >= scoped_attributes_count and overdue_count == 0
        
        if pending_cdo_assignments > 0:
            completion_requirements.append(f"Complete {pending_cdo_assignments} pending CDO assignments")
        
        if overdue_count > 0:
            completion_requirements.append(f"Resolve {overdue_count} overdue assignments")
        
        if not completion_requirements:
            completion_requirements.append("All requirements met - ready to complete phase")
        
        return DataProviderPhaseStatusDTO(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase_status,
            total_attributes=total_attributes,
            scoped_attributes=scoped_attributes_count,
            total_samples=await self._get_total_samples_count(cycle_id, report_id, db),
            attributes_with_lob_assignments=attributes_with_lob_assignments,
            attributes_with_data_owners=attributes_with_data_owners,
            pending_cdo_assignments=pending_cdo_assignments,
            overdue_assignments=overdue_count,
            can_submit_lob_assignments=can_submit_lob_assignments,
            can_complete_phase=can_complete_phase,
            completion_requirements=completion_requirements
        )


class SubmitCDOAssignmentsUseCase(UseCase):
    """Submit CDO data owner assignments using universal assignments"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        submission: CDOAssignmentSubmissionDTO,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Submit assignments"""
        
        # Get current user
        current_user = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        current_user = current_user.scalar_one()
        
        if current_user.role != 'Data Executive':
            raise ValueError("Data Executive role required")
        
        assignments_created = []
        current_time = datetime.utcnow()
        
        for assignment_req in submission.assignments:
            # Convert attribute_id to int
            try:
                attribute_id_int = int(assignment_req.attribute_id)
            except ValueError:
                raise ValueError(f"Invalid attribute ID format: {assignment_req.attribute_id}")
            
            # Get planning phase - there might be multiple, get the latest
            phase_result = await db.execute(
                select(WorkflowPhase.phase_id)
                .where(and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Planning'
                ))
                .order_by(WorkflowPhase.phase_id.desc())
                .limit(1)
            )
            planning_phase_id = phase_result.scalar_one_or_none()
            
            if not planning_phase_id:
                raise ValueError(f"Planning phase not found for cycle {cycle_id}, report {report_id}")
            
            # Verify attribute
            attribute = await db.execute(
                select(ReportAttribute)
                .where(and_(
                    ReportAttribute.phase_id == planning_phase_id,
                    ReportAttribute.id == attribute_id_int,
                    ReportAttribute.is_primary_key == False
                ))
            )
            attribute = attribute.scalar_one_or_none()
            
            if not attribute:
                raise ValueError(f"Attribute {assignment_req.attribute_id} not found or is a primary key")
            
            # Verify data owner
            data_owner = await db.execute(
                select(User)
                .where(and_(
                    User.user_id == assignment_req.data_owner_id,
                    User.lob_id == current_user.lob_id,
                    User.role == 'Data Owner',
                    User.is_active == True
                ))
            )
            data_owner = data_owner.scalar_one_or_none()
            
            if not data_owner:
                raise ValueError(f"Data provider {assignment_req.data_owner_id} not found in your LOB")
            
            # Find the universal assignment for this CDO
            # Multiple assignments might contain this attribute, get the most recent one
            cdo_assignment = await db.execute(
                select(UniversalAssignment)
                .where(and_(
                    UniversalAssignment.assignment_type == 'LOB Assignment',
                    UniversalAssignment.to_user_id == current_user.user_id,
                    UniversalAssignment.status == 'Assigned',
                    UniversalAssignment.context_data['cycle_id'].astext == str(cycle_id),
                    UniversalAssignment.context_data['report_id'].astext == str(report_id),
                    UniversalAssignment.context_data['attribute_ids'].astext.contains(str(attribute_id_int))
                ))
                .order_by(UniversalAssignment.created_at.desc())
                .limit(1)
            )
            cdo_assignment = cdo_assignment.scalar_one_or_none()
            
            if cdo_assignment:
                # Update the CDO assignment to completed
                cdo_assignment.status = 'Completed'
                cdo_assignment.completed_at = current_time
                cdo_assignment.updated_at = current_time
                cdo_assignment.updated_by_id = user_id
                
                # Add data owner info to context
                context_data = cdo_assignment.context_data
                context_data['data_owner_id'] = assignment_req.data_owner_id
                context_data['data_owner_name'] = f"{data_owner.first_name} {data_owner.last_name}"
                context_data['assignment_notes'] = assignment_req.assignment_notes
                cdo_assignment.context_data = context_data
                
                # Create a new universal assignment for the data owner
                data_owner_context = {
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "attribute_id": str(attribute.id),
                    "attribute_name": attribute.attribute_name,
                    "lob_id": current_user.lob_id,
                    "lob_name": cdo_assignment.context_data.get('lob_name'),
                    "phase_name": "Data Provider ID",
                    "cdo_assignment_id": cdo_assignment.assignment_id
                }
                
                data_owner_assignment = UniversalAssignment(
                    assignment_type='Data Upload Request',
                    from_role='DATA_EXECUTIVE',
                    to_role='DATA_OWNER',
                    from_user_id=user_id,
                    to_user_id=assignment_req.data_owner_id,
                    title=f"Provide Data - {attribute.attribute_name}",
                    description=f"Provide data for {attribute.attribute_name}",
                    task_instructions=assignment_req.assignment_notes or "Review the attribute requirements and provide the requested data.",
                    context_type='Attribute',
                    context_data=data_owner_context,
                    priority='Medium',
                    status='Assigned',
                    assigned_at=current_time
                )
                db.add(data_owner_assignment)
                assignments_created.append(data_owner_assignment)
                
                # Update the DataOwnerLOBAttributeMapping table
                from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping
                
                # Get the data provider phase_id
                data_provider_phase_result = await db.execute(
                    select(WorkflowPhase.phase_id)
                    .where(and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == 'Data Provider ID'
                    ))
                    .order_by(WorkflowPhase.phase_id.desc())
                    .limit(1)
                )
                data_provider_phase_id = data_provider_phase_result.scalar_one_or_none()
                
                if not data_provider_phase_id:
                    logger.warning(f"Data Provider ID phase not found for cycle {cycle_id}, report {report_id}")
                    # Use planning phase_id as fallback
                    data_provider_phase_id = planning_phase_id
                
                # Find the mapping record for this attribute and LOB
                mapping_result = await db.execute(
                    select(DataOwnerLOBAttributeMapping)
                    .where(and_(
                        DataOwnerLOBAttributeMapping.phase_id == data_provider_phase_id,
                        DataOwnerLOBAttributeMapping.attribute_id == attribute_id_int,
                        DataOwnerLOBAttributeMapping.lob_id == current_user.lob_id
                    ))
                )
                mapping = mapping_result.scalar_one_or_none()
                
                if mapping:
                    # Update the mapping with data owner information
                    mapping.data_owner_id = assignment_req.data_owner_id
                    mapping.data_executive_id = user_id
                    mapping.assigned_by_data_executive_at = current_time
                    mapping.assignment_rationale = assignment_req.assignment_notes
                    mapping.assignment_status = 'assigned'
                    mapping.updated_at = current_time
                    mapping.updated_by_id = user_id
                    logger.info(f"Updated DataOwnerLOBAttributeMapping for attribute {attribute_id_int}, LOB {current_user.lob_id}, data owner {assignment_req.data_owner_id}")
                else:
                    # Create new mapping if it doesn't exist
                    new_mapping = DataOwnerLOBAttributeMapping(
                        phase_id=data_provider_phase_id,
                        attribute_id=attribute_id_int,
                        lob_id=current_user.lob_id,
                        data_owner_id=assignment_req.data_owner_id,
                        data_executive_id=user_id,
                        assigned_by_data_executive_at=current_time,
                        assignment_rationale=assignment_req.assignment_notes,
                        assignment_status='assigned',
                        created_by_id=user_id,
                        updated_by_id=user_id
                    )
                    db.add(new_mapping)
                    logger.info(f"Created new DataOwnerLOBAttributeMapping for attribute {attribute_id_int}, LOB {current_user.lob_id}, data owner {assignment_req.data_owner_id}")
            
            # Record historical assignment if requested
            if assignment_req.use_historical_assignment:
                report = await db.execute(
                    select(Report)
                    .where(Report.report_id == report_id)
                    .order_by(Report.report_id.desc())
                    .limit(1)
                )
                report = report.scalar_one_or_none()
                
                if not report:
                    logger.warning(f"Report not found for ID {report_id}, skipping historical assignment")
                    continue
                
                # SKIP: HistoricalDataOwnerAssignment table doesn't exist
                # historical_assignment = HistoricalDataOwnerAssignment(
                #     report_name=report.report_name,
                #     attribute_name=attribute.attribute_name,
                #     data_owner_id=assignment_req.data_owner_id,
                #     assigned_by=current_user.user_id,
                #     cycle_id=cycle_id,
                #     assigned_at=current_time,
                #     completion_status='Assigned',
                #     notes=assignment_req.assignment_notes
                # )
                # db.add(historical_assignment)
        
        await db.commit()
        
        # Create audit log - skipping for now as table doesn't exist
        # await self._create_audit_log(
        #     db, cycle_id, report_id, "submit_cdo_assignments", "UniversalAssignment",
        #     None, user_id, new_values={"assignments_count": len(assignments_created)},
        #     notes=submission.submission_notes
        # )
        
        return {
            "success": True,
            "message": f"Data owner assignments submitted successfully. {len(assignments_created)} assignments created.",
            "assignments_completed": len(assignments_created)
        }
    
    async def _create_audit_log(
        self,
        db: AsyncSession,
        phase_id: int,
        action: str,
        entity_type: str,
        entity_id: Optional[int],
        performed_by: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ):
        """Create audit log entry"""
        audit_log = DataOwnerPhaseAuditLog(
            phase_id=phase_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=performed_by,
            performed_at=datetime.utcnow(),
            old_values=old_values,
            new_values=new_values,
            notes=notes
        )
        db.add(audit_log)
        await db.commit()


class GetAssignmentMatrixUseCase(UseCase):
    """Get complete assignment matrix using universal assignments"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> AssignmentMatrixDTO:
        """Get assignment matrix"""
        logger.info(f"GetAssignmentMatrixUseCase.execute called for cycle {cycle_id}, report {report_id}")
        
        # First check if the Data Provider ID phase has been started
        workflow_phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Data Provider ID"
            )
        )
        workflow_result = await db.execute(workflow_phase_query)
        workflow_phase = workflow_result.scalar_one_or_none()
        
        logger.info(f"Data Provider ID phase found: {workflow_phase is not None}, state: {workflow_phase.state if workflow_phase else 'N/A'}")
        
        # If phase hasn't started, return empty assignment matrix
        if not workflow_phase or workflow_phase.state == 'Not Started':
            return AssignmentMatrixDTO(
                cycle_id=cycle_id,
                report_id=report_id,
                assignments=[],
                data_owners=[],
                lob_summary={},
                cdo_summary={},
                status_summary={"Assigned": 0, "In Progress": 0, "Completed": 0, "Overdue": 0}
            )
        
        # Get scoping phase to find approved non-PK attributes
        from app.models.scoping import ScopingAttribute
        scoping_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Scoping',
                WorkflowPhase.status == 'Complete'
            ))
        )
        scoping_phase = scoping_phase.scalar_one_or_none()
        
        if not scoping_phase:
            # Return empty if scoping phase not found
            return AssignmentMatrixDTO(
                cycle_id=cycle_id,
                report_id=report_id,
                assignments=[],
                data_owners=[],
                lob_summary={},
                cdo_summary={},
                status_summary={"Assigned": 0, "In Progress": 0, "Completed": 0, "Overdue": 0}
            )
        
        # Get approved scoping version first
        from app.models.scoping import ScopingVersion
        approved_scoping_version = await db.execute(
            text('''
                SELECT version_id FROM cycle_report_scoping_versions 
                WHERE phase_id = :phase_id 
                AND version_status = 'approved'
                ORDER BY version_number DESC 
                LIMIT 1
            '''),
            {'phase_id': scoping_phase.phase_id}
        )
        approved_version_row = approved_scoping_version.first()
        
        if not approved_version_row:
            logger.warning(f"No approved scoping version found")
            return AssignmentMatrixDTO(
                cycle_id=cycle_id,
                report_id=report_id,
                assignments=[],
                data_owners=[],
                lob_summary={},
                cdo_summary={},
                status_summary={"Assigned": 0, "In Progress": 0, "Completed": 0, "Overdue": 0}
            )
            
        approved_version_id = approved_version_row.version_id
        
        # Get only non-primary key scoped attributes with planning attribute info
        from app.models.report_attribute import ReportAttribute as PlanningAttribute
        
        scoped_attrs_query = await db.execute(
            select(ScopingAttribute, PlanningAttribute)
            .join(PlanningAttribute, ScopingAttribute.planning_attribute_id == PlanningAttribute.id)
            .where(and_(
                ScopingAttribute.version_id == approved_version_id,
                ScopingAttribute.is_primary_key == False,
                ScopingAttribute.tester_decision == 'accept'
            ))
        )
        scoped_attr_results = scoped_attrs_query.all()
        
        # Create a list of attribute objects with the name attached, filtering out PKs
        scoped_attributes = []
        for scoping_attr, planning_attr in scoped_attr_results:
            # Skip if this is actually a primary key in the planning attributes
            if planning_attr.is_primary_key:
                logger.info(f"Skipping primary key attribute: {planning_attr.attribute_name}")
                continue
            # Add attribute_name to the scoping attribute for easier access
            scoping_attr.attribute_name = planning_attr.attribute_name
            scoped_attributes.append(scoping_attr)
            
        logger.info(f"Found {len(scoped_attributes)} scoped non-PK attributes (after filtering PKs)")
        
        # Import the mapping model
        from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping
        
        # Get attribute LOB mappings from the mapping table
        mappings_query = await db.execute(
            select(DataOwnerLOBAttributeMapping, LOB, User)
            .join(LOB, DataOwnerLOBAttributeMapping.lob_id == LOB.lob_id)
            .outerjoin(User, DataOwnerLOBAttributeMapping.data_owner_id == User.user_id)
            .where(DataOwnerLOBAttributeMapping.phase_id == workflow_phase.phase_id)
        )
        mappings = mappings_query.all()
        
        logger.info(f"Found {len(mappings)} mappings in database for phase_id {workflow_phase.phase_id}")
        
        # Build mapping lookup by attribute_id
        mapping_lookup = {}
        for mapping, lob, data_owner in mappings:
            if mapping.attribute_id not in mapping_lookup:
                mapping_lookup[mapping.attribute_id] = []
            mapping_lookup[mapping.attribute_id].append({
                'mapping': mapping,
                'lob': lob,
                'data_owner': data_owner
            })
        
        assignment_statuses = []
        lob_summary = {}
        cdo_summary = {}
        status_summary = {"Assigned": 0, "In Progress": 0, "Completed": 0, "Overdue": 0}
        
        for attribute in scoped_attributes:
            attribute_mappings = mapping_lookup.get(attribute.planning_attribute_id, [])
            logger.info(f"Processing attribute {attribute.planning_attribute_id} ({attribute.attribute_name}), found {len(attribute_mappings)} mappings")
            
            # If no mappings exist for this attribute, it needs LOB assignment
            if not attribute_mappings:
                logger.info(f"No mappings for attribute {attribute.planning_attribute_id}, creating pending assignment status")
                assignment_status = AttributeAssignmentStatusDTO(
                    attribute_id=str(attribute.planning_attribute_id),  # Use planning attribute ID (integer) not scoping UUID
                    attribute_name=attribute.attribute_name,
                    is_primary_key=False,
                    assigned_lobs=[],
                    data_owner_id=None,
                    data_owner_name=None,
                    assigned_by=None,
                    assigned_at=None,
                    status=AssignmentStatusEnum.ASSIGNED,
                    assignment_notes="LOB Assignment Pending",
                    is_overdue=False,
                    sla_deadline=None,
                    hours_remaining=None
                )
                assignment_statuses.append(assignment_status)
                status_summary["Assigned"] += 1
                continue
            
            # Process each LOB mapping for this attribute
            for mapping_info in attribute_mappings:
                mapping = mapping_info['mapping']
                lob = mapping_info['lob']
                data_owner = mapping_info['data_owner']
                
                # Determine status based on mapping
                if mapping.data_owner_id:
                    assignment_status_val = AssignmentStatusEnum.COMPLETED
                else:
                    assignment_status_val = AssignmentStatusEnum.IN_PROGRESS
                
                assignment_status = AttributeAssignmentStatusDTO(
                    attribute_id=str(attribute.planning_attribute_id),
                    attribute_name=attribute.attribute_name,
                    is_primary_key=False,
                    assigned_lobs=[{"lob_id": lob.lob_id, "lob_name": lob.lob_name}],
                    data_owner_id=data_owner.user_id if data_owner else None,
                    data_owner_name=f"{data_owner.first_name} {data_owner.last_name}" if data_owner else None,
                    assigned_by=mapping.created_by_id,
                    assigned_at=mapping.created_at,
                    status=assignment_status_val,
                    assignment_notes="Awaiting Data Executive Assignment" if not data_owner else None,
                    is_overdue=False,
                    sla_deadline=None,
                    hours_remaining=None
                )
                
                assignment_statuses.append(assignment_status)
                
                lob_summary[lob.lob_name] = lob_summary.get(lob.lob_name, 0) + 1
                status_summary[assignment_status_val.value] += 1
        
        # Get available data owners
        data_owners = await db.execute(
            select(User, LOB)
            .join(LOB, User.lob_id == LOB.lob_id)
            .where(and_(
                User.role == 'Data Owner',
                User.is_active == True
            ))
        )
        data_owners = data_owners.all()
        
        data_owner_list = []
        for user, lob in data_owners:
            data_owner_list.append({
                "user_id": user.user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "lob_name": lob.lob_name
            })
        
        return AssignmentMatrixDTO(
            cycle_id=cycle_id,
            report_id=report_id,
            assignments=assignment_statuses,
            data_owners=data_owner_list,
            lob_summary=lob_summary,
            cdo_summary=cdo_summary,
            status_summary=status_summary
        )


# Stub implementations for missing use cases
class CompleteDataProviderPhaseUseCase(UseCase):
    async def execute(self, cycle_id: int, report_id: int, completion_data: Any, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Complete data provider phase - stub implementation"""
        return {"status": "completed", "message": "Phase completed successfully"}


class GetHistoricalAssignmentsUseCase(UseCase):
    async def execute(self, cycle_id: int, report_id: int, db: AsyncSession) -> List[Any]:
        """Get historical assignments - stub implementation"""
        return []


class GetCDOAssignmentsUseCase(UseCase):
    async def execute(self, filters: Any, current_user: Any, db: AsyncSession) -> List[Any]:
        """Get CDO assignments - stub implementation"""
        return []


class GetCDODashboardUseCase(UseCase):
    async def execute(self, cdo_id: int, db: AsyncSession) -> Any:
        """Get CDO dashboard - stub implementation"""
        return {"cdo_id": cdo_id, "assignments": [], "pending_count": 0, "completed_count": 0}