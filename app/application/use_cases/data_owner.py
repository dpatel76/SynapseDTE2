"""
Data Owner Identification use cases for clean architecture
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.orm import selectinload
import uuid
import logging

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
    # DataOwnerAssignment replaced with DataOwnerLOBAttributeMapping
    HistoricalDataOwnerAssignment,
    DataOwnerSLAViolation,
    DataOwnerEscalationLog,
    DataOwnerPhaseAuditLog,
    SampleSet,
    SampleRecord,
    TesterScopingDecision
)
from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping as DataOwnerAssignment
from app.services.workflow_orchestrator import get_workflow_orchestrator

logger = logging.getLogger(__name__)


class StartDataProviderPhaseUseCase(UseCase):
    """Start data owner identification phase"""
    
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
        
        # Create DataOwnerAssignment records within the same transaction
        await self._create_data_owner_assignments(db, cycle_id, report_id, user_id)
        
        # Commit the assignments before updating phase state
        await db.commit()
        
        # Use workflow orchestrator to start the phase and create universal assignments
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
        
        # Create audit log
        await self._create_audit_log(
            db, cycle_id, report_id, "start_data_owner_phase", "WorkflowPhase",
            data_owner_phase.phase_id, user_id, notes=start_data.notes
        )
        
        return {
            "success": True,
            "message": "Data owner identification phase started successfully",
            "phase_id": data_owner_phase.phase_id,
            "cycle_id": cycle_id,
            "report_id": report_id,
            "started_at": data_owner_phase.actual_start_date
        }
    
    async def _create_data_owner_assignments(
        self,
        db: AsyncSession,
        cycle_id: int,
        report_id: int,
        created_by: int
    ):
        """Create DataOwnerAssignment records for non-primary key scoped attributes"""
        # Use the new unified sample selection model
        from app.models.sample_selection import SampleSelectionSample, SampleSelectionVersion
        
        # Get the approved sample selection version
        version_query = await db.execute(
            select(SampleSelectionVersion)
            .join(WorkflowPhase, SampleSelectionVersion.phase_id == WorkflowPhase.phase_id)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Sample Selection',
                SampleSelectionVersion.version_status == 'approved'
            ))
            .order_by(SampleSelectionVersion.version_number.desc())
        )
        approved_version = version_query.scalar_one_or_none()
        
        if not approved_version:
            logger.warning(f"No approved sample selection version found for cycle {cycle_id}, report {report_id}")
            return
        
        # Get approved samples with their LOB IDs
        samples_query = await db.execute(
            select(SampleSelectionSample.lob_id)
            .distinct()
            .where(and_(
                SampleSelectionSample.version_id == approved_version.version_id,
                SampleSelectionSample.report_owner_decision == 'approved'
            ))
        )
        unique_lob_ids = [row[0] for row in samples_query.all()]
        
        if not unique_lob_ids:
            logger.warning(f"No LOB IDs found in approved samples for cycle {cycle_id}, report {report_id}")
            return
        
        # Ensure LOB IDs are truly unique
        unique_lob_ids = list(set(unique_lob_ids))
        logger.info(f"Found {len(unique_lob_ids)} unique LOBs from approved samples: {unique_lob_ids}")
        
        # Get non-primary key scoped attributes from planning phase
        from app.models.planning import PlanningAttribute
        planning_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Planning'
            ))
        )
        planning_phase = planning_phase.scalar_one_or_none()
        
        if not planning_phase:
            logger.warning(f"No planning phase found for cycle {cycle_id}, report {report_id}")
            return
        
        # Get scoped non-PK attributes from scoping decisions
        from app.models.scoping import ScopingAttribute, ScopingVersion
        
        # Get approved scoping version
        scoping_version_query = await db.execute(
            select(ScopingVersion)
            .join(WorkflowPhase, ScopingVersion.phase_id == WorkflowPhase.phase_id)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Scoping',
                ScopingVersion.version_status == 'approved'
            ))
            .order_by(ScopingVersion.version_number.desc())
        )
        scoping_version = scoping_version_query.scalar_one_or_none()
        
        if not scoping_version:
            logger.warning(f"No approved scoping version found for cycle {cycle_id}, report {report_id}")
            return
        
        # Get non-PK scoped attributes (accepted by tester)
        scoped_attrs_query = await db.execute(
            select(ScopingAttribute.planning_attribute_id)
            .join(PlanningAttribute, ScopingAttribute.planning_attribute_id == PlanningAttribute.id)
            .where(and_(
                ScopingAttribute.version_id == scoping_version.version_id,
                ScopingAttribute.tester_decision == 'accept',
                PlanningAttribute.is_primary_key == False
            ))
        )
        scoped_attribute_ids = [row[0] for row in scoped_attrs_query.all()]
        
        if not scoped_attribute_ids:
            logger.warning(f"No non-PK scoped attributes found for cycle {cycle_id}, report {report_id}")
            return
        
        # Ensure attribute IDs are unique
        scoped_attribute_ids = list(set(scoped_attribute_ids))
        logger.info(f"Found {len(scoped_attribute_ids)} unique non-PK scoped attributes")
        
        # Get data owner phase
        data_owner_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Data Provider ID'
            ))
        )
        data_owner_phase = data_owner_phase.scalar_one_or_none()
        
        if not data_owner_phase:
            logger.error(f"Data owner phase not found for cycle {cycle_id}, report {report_id}")
            return
        
        # Get Data Executives for each LOB
        lob_executives = await db.execute(
            select(User.lob_id, User.user_id)
            .where(and_(
                User.lob_id.in_(unique_lob_ids),
                User.role == 'Data Executive',
                User.is_active == True
            ))
        )
        lob_executive_map = {row[0]: row[1] for row in lob_executives.all()}
        
        # Create assignment records for each unique attribute/LOB combination
        from app.models.data_owner_lob_assignment import (
            DataOwnerLOBAttributeVersion, 
            DataOwnerLOBAttributeMapping
        )
        
        # Create a version for the data owner assignments
        # Use the system data executive (first available) or created_by user
        system_executive_id = created_by
        if lob_executive_map:
            # Use the first data executive as the system executive
            system_executive_id = next(iter(lob_executive_map.values()))
        
        # Check if a version already exists
        existing_version = await db.execute(
            select(DataOwnerLOBAttributeVersion)
            .where(and_(
                DataOwnerLOBAttributeVersion.phase_id == data_owner_phase.phase_id,
                DataOwnerLOBAttributeVersion.version_status == 'active'
            ))
        )
        version = existing_version.scalar_one_or_none()
        
        if not version:
            # Create new version
            version = DataOwnerLOBAttributeVersion(
                phase_id=data_owner_phase.phase_id,
                version_number=1,
                version_status='active',
                data_executive_id=system_executive_id,
                assignment_notes="Initial data owner assignments created during phase start",
                created_by_id=created_by,
                updated_by_id=created_by
            )
            db.add(version)
            await db.flush()  # Get the version_id
            logger.info(f"Created new assignment version with ID: {version.version_id}")
        else:
            logger.info(f"Using existing assignment version with ID: {version.version_id}")
            # If version already exists, check if assignments also exist and return early
            existing_assignments = await db.execute(
                select(func.count(DataOwnerLOBAttributeMapping.mapping_id))
                .where(DataOwnerLOBAttributeMapping.version_id == version.version_id)
            )
            assignment_count = existing_assignments.scalar()
            if assignment_count > 0:
                logger.info(f"Assignments already exist for version {version.version_id} (count: {assignment_count}), skipping creation")
                return
        
        # Get samples to link assignments to
        samples_for_assignments = await db.execute(
            select(SampleSelectionSample.sample_id, SampleSelectionSample.lob_id)
            .where(and_(
                SampleSelectionSample.version_id == approved_version.version_id,
                SampleSelectionSample.report_owner_decision == 'approved'
            ))
        )
        sample_lob_map = {}
        for sample_id, lob_id in samples_for_assignments:
            if lob_id not in sample_lob_map:
                sample_lob_map[lob_id] = []
            sample_lob_map[lob_id].append(sample_id)
        
        # Create assignments
        created_count = 0
        assignments_to_create = []
        created_combinations = set()  # Track combinations to avoid duplicates
        
        logger.info(f"Creating assignments for {len(scoped_attribute_ids)} attributes and {len(unique_lob_ids)} LOBs")
        
        for attribute_id in scoped_attribute_ids:
            for lob_id in unique_lob_ids:
                # Check if we already created this combination
                combination_key = (attribute_id, lob_id)
                if combination_key in created_combinations:
                    logger.warning(f"Skipping duplicate combination: attribute {attribute_id}, LOB {lob_id}")
                    continue
                
                # Get a sample for this LOB (use first available)
                sample_ids = sample_lob_map.get(lob_id, [])
                if not sample_ids:
                    logger.warning(f"No sample found for LOB {lob_id}, skipping assignment")
                    continue
                
                sample_id = sample_ids[0]  # Use first sample for this LOB
                executive_id = lob_executive_map.get(lob_id, system_executive_id)
                
                # Check if assignment already exists in database (including pending inserts)
                existing = await db.execute(
                    select(DataOwnerLOBAttributeMapping).where(and_(
                        DataOwnerLOBAttributeMapping.phase_id == data_owner_phase.phase_id,
                        DataOwnerLOBAttributeMapping.attribute_id == attribute_id,
                        DataOwnerLOBAttributeMapping.lob_id == lob_id
                    ))
                )
                if existing.scalar_one_or_none():
                    logger.info(f"Assignment already exists for attribute {attribute_id}, LOB {lob_id} - skipping")
                    continue
                
                # Double-check in the pending assignments list
                already_pending = any(
                    a.attribute_id == attribute_id and a.lob_id == lob_id 
                    for a in assignments_to_create
                )
                if already_pending:
                    logger.warning(f"Assignment already pending for attribute {attribute_id}, LOB {lob_id} - skipping")
                    continue
                
                if True:  # Keep indentation for the assignment creation
                    assignment = DataOwnerLOBAttributeMapping(
                        version_id=version.version_id,
                        phase_id=data_owner_phase.phase_id,
                        sample_id=sample_id,
                        attribute_id=attribute_id,
                        lob_id=lob_id,
                        data_owner_id=None,  # Will be assigned by Data Executive later
                        data_executive_id=executive_id,
                        assignment_rationale="Initial assignment - pending data owner selection",
                        assignment_status='unassigned',
                        created_by_id=created_by,
                        updated_by_id=created_by
                    )
                    assignments_to_create.append(assignment)
                    created_combinations.add(combination_key)
                    created_count += 1
                    logger.debug(f"Created assignment for attribute {attribute_id}, LOB {lob_id}")
        
        # Bulk insert assignments
        if assignments_to_create:
            db.add_all(assignments_to_create)
            
            # Update version summary
            version.total_lob_attributes = created_count
            version.assigned_lob_attributes = 0  # None assigned yet
            version.unassigned_lob_attributes = created_count
            
            # Create universal assignments for each LOB
            await self._create_universal_assignments_for_lobs(
                db, data_owner_phase, unique_lob_ids, 
                lob_executive_map, scoped_attribute_ids, created_by
            )
        
        logger.info(f"Created {created_count} unique data owner assignments for cycle {cycle_id}, report {report_id}")
    
    async def _create_universal_assignments_for_lobs(
        self,
        db: AsyncSession,
        data_owner_phase: WorkflowPhase,
        unique_lob_ids: List[int],
        lob_executive_map: Dict[int, int],
        scoped_attribute_ids: List[int],
        created_by: int
    ):
        """Create universal assignments for each LOB's Data Executive"""
        from app.models.universal_assignment import UniversalAssignment
        from datetime import timedelta
        import uuid
        
        # Get LOB details
        lob_details = await db.execute(
            select(LOB).where(LOB.lob_id.in_(unique_lob_ids))
        )
        lobs = {lob.lob_id: lob for lob in lob_details.scalars().all()}
        
        assignments_created = []
        
        for lob_id in unique_lob_ids:
            lob = lobs.get(lob_id)
            if not lob:
                continue
                
            # Get the Data Executive for this LOB
            data_executive_id = lob_executive_map.get(lob_id)
            
            # Count attributes for this LOB
            attr_count_query = await db.execute(
                select(func.count(DataOwnerLOBAttributeMapping.mapping_id))
                .where(and_(
                    DataOwnerLOBAttributeMapping.phase_id == data_owner_phase.phase_id,
                    DataOwnerLOBAttributeMapping.lob_id == lob_id
                ))
            )
            attribute_count = attr_count_query.scalar() or len(scoped_attribute_ids)
            
            # Check if assignment already exists for this LOB
            existing_assignment = await db.execute(
                select(UniversalAssignment).where(and_(
                    UniversalAssignment.context_type == 'Phase',
                    UniversalAssignment.context_data['phase_id'].astext == str(data_owner_phase.phase_id),
                    UniversalAssignment.context_data['lob_id'].astext == str(lob_id),
                    UniversalAssignment.assignment_type == 'LOB Assignment'
                ))
            )
            if existing_assignment.scalar_one_or_none():
                logger.info(f"Universal assignment already exists for LOB {lob.lob_name}")
                continue
            
            # Create universal assignment for this LOB
            new_assignment = UniversalAssignment(
                assignment_id=str(uuid.uuid4()),
                assignment_type='LOB Assignment',
                from_role='System',
                to_role='Data Executive',
                from_user_id=created_by,
                to_user_id=data_executive_id if data_executive_id else None,
                title=f'Assign Data Owners for {lob.lob_name}',
                description=f'Assign data owners to {attribute_count} attributes for {lob.lob_name}',
                task_instructions=f'''Please assign data owners to all attributes in {lob.lob_name}:
1. Review the {attribute_count} attributes requiring data owner assignment
2. Select appropriate data owners from the {lob.lob_name} team
3. Ensure all attributes have assigned data owners before marking complete
4. Use the Data Provider ID interface to make assignments''',
                context_type='Report',  # Changed from 'Phase' to match frontend expectations
                priority='High',
                assigned_at=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=3),
                status='Assigned',
                context_data={
                    'phase_id': data_owner_phase.phase_id,
                    'lob_id': lob_id,
                    'lob_name': lob.lob_name,
                    'attribute_count': attribute_count,
                    'cycle_id': data_owner_phase.cycle_id,
                    'report_id': data_owner_phase.report_id,
                    'phase_name': 'Data Provider ID',
                    'mapping_version_id': str(lob_executive_map.get('version_id', ''))  # Link to mapping version
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(new_assignment)
            assignments_created.append(new_assignment)
            
            if data_executive_id:
                logger.info(f"Created universal assignment for {lob.lob_name} assigned to user {data_executive_id}")
            else:
                logger.info(f"Created universal assignment for {lob.lob_name} with role-based assignment")
        
        if assignments_created:
            logger.info(f"Created {len(assignments_created)} universal assignments for LOBs")
    
    async def _create_audit_log(
        self,
        db: AsyncSession,
        cycle_id: int,
        report_id: int,
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
            cycle_id=cycle_id,
            report_id=report_id,
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
    """Get data owner phase status"""
    
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
        
        # Get approved samples from Sample Selection phase using actual tables
        try:
            from app.models.sample_selection import SampleRecord, SampleSet
            
            sample_records = await db.execute(
                select(SampleRecord)
                .join(SampleSet, SampleRecord.set_id == SampleSet.set_id)
                .where(and_(
                    SampleSet.cycle_id == cycle_id,
                    SampleSet.report_id == report_id,
                    SampleRecord.approval_status == 'Approved'
                ))
            )
            sample_records = sample_records.scalars().all()
            
        except ImportError:
            # Fallback if SampleRecord doesn't exist - try phase_data approach
            sample_phase = await db.execute(
                select(WorkflowPhase)
                .where(and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Sample Selection'
                ))
            )
            sample_phase = sample_phase.scalar_one_or_none()
            sample_records = []
            
            if sample_phase and sample_phase.phase_data:
                submissions = sample_phase.phase_data.get('submissions', [])
                for submission in submissions:
                    if submission.get('status') == 'approved':
                        approved_samples_data = submission.get('samples', [])
                        # Convert to sample record-like objects
                        for sample_data in approved_samples_data:
                            if sample_data.get('tester_decision') == 'include':
                                sample_records.append(type('SampleRecord', (), {
                                    'lob_assignment': sample_data.get('lob_assignment'),
                                    'sample_id': sample_data.get('sample_id')
                                })())
        
        # Get unique LOBs from approved samples
        unique_lobs = set()
        for sample in sample_records:
            # LOB assignment might be in sample_data JSONB field
            if hasattr(sample, 'sample_data') and sample.sample_data:
                lob_assignment = sample.sample_data.get('lob_assignment')
                if lob_assignment:
                    unique_lobs.add(lob_assignment)
            # Or check if there's a direct lob_assignment field
            elif hasattr(sample, 'lob_assignment') and sample.lob_assignment:
                unique_lobs.add(sample.lob_assignment)
        
        # Get all active attributes first
        all_attributes = await db.execute(
            select(ReportAttribute)
            .where(and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_active == True
            ))
        )
        all_attributes = all_attributes.scalars().all()
        
        # Filter scoped attributes (non-primary key only)
        scoped_attributes = [attr for attr in all_attributes if attr.is_scoped and not attr.is_primary_key]
        
        # Get primary key attributes
        pk_attributes = [attr for attr in all_attributes if attr.is_primary_key]
        
        # Combine for data owner assignment (scoped + primary key attributes)
        attributes = list(scoped_attributes) + list(pk_attributes)
        total_attributes = len(all_attributes)
        
        if total_attributes == 0:
            phase = await db.execute(
                select(WorkflowPhase)
                .where(and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Data Provider ID'
                ))
            )
            phase = phase.scalar_one_or_none()
            phase_status = phase.status if phase else "Not Started"
            
            return DataProviderPhaseStatusDTO(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status=phase_status,
                total_attributes=0,
                scoped_attributes=0,
                total_samples=0,
                attributes_with_lob_assignments=0,
                attributes_with_data_owners=0,
                pending_cdo_assignments=0,
                overdue_assignments=0,
                can_submit_lob_assignments=True,
                can_complete_phase=True,
                completion_requirements=["No attributes require data owner assignment yet - complete scoping phase first"]
            )
        
        # Get overdue assignments
        overdue_assignments = await db.execute(
            select(DataOwnerSLAViolation)
            .where(and_(
                DataOwnerSLAViolation.cycle_id == cycle_id,
                DataOwnerSLAViolation.report_id == report_id,
                DataOwnerSLAViolation.is_resolved == False
            ))
        )
        overdue_assignments = overdue_assignments.scalars().all()
        
        # Get data owner assignments
        data_owner_assignments = await db.execute(
            select(DataOwnerAssignment)
            .where(and_(
                DataOwnerAssignment.cycle_id == cycle_id,
                DataOwnerAssignment.report_id == report_id
            ))
        )
        data_owner_assignments = data_owner_assignments.scalars().all()
        
        # Calculate metrics
        non_pk_attributes = [attr for attr in attributes if not attr.is_primary_key]
        total_non_pk_attributes = len(non_pk_attributes)
        
        attributes_with_lob_assignments = total_non_pk_attributes
        attributes_with_data_owners = len(set(
            assignment.attribute_id for assignment in data_owner_assignments
            if assignment.data_owner_id
        ))
        
        pending_cdo_assignments = len([
            a for a in data_owner_assignments if not a.data_owner_id
        ])
        
        assigned_attribute_ids = set(assignment.attribute_id for assignment in data_owner_assignments)
        non_pk_attribute_ids = set(attr.attribute_id for attr in non_pk_attributes)
        unassigned_attributes = non_pk_attribute_ids - assigned_attribute_ids
        pending_cdo_assignments += len(unassigned_attributes)
        
        overdue_count = len(overdue_assignments)
        
        # Get phase status
        phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Data Provider ID'
            ))
        )
        phase = phase.scalar_one_or_none()
        phase_status = phase.status if phase else "Not Started"
        
        # Determine completion requirements
        completion_requirements = []
        can_submit_lob_assignments = True
        can_complete_phase = attributes_with_data_owners >= total_non_pk_attributes and overdue_count == 0
        
        if pending_cdo_assignments > 0:
            completion_requirements.append(f"Complete {pending_cdo_assignments} pending CDO assignments")
        
        if overdue_count > 0:
            completion_requirements.append(f"Resolve {overdue_count} overdue assignments")
        
        if not completion_requirements:
            completion_requirements.append("All requirements met - ready to complete phase")
        
        # Use Universal Metrics Service for consistent metrics
        from app.services.universal_metrics_service import get_universal_metrics_service, MetricsContext
        
        metrics_service = get_universal_metrics_service(db)
        metrics_context = MetricsContext(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name="Data Provider ID"
        )
        
        # Get universal metrics
        universal_metrics = await metrics_service.get_metrics(metrics_context)
        
        # Extract the metrics we need
        approved_samples_count = universal_metrics.approved_samples
        total_lobs = universal_metrics.lobs_count
        assigned_data_providers = universal_metrics.data_providers_count
        
        # Get total available data owners (not included in universal metrics by default)
        try:
            data_owners_result = await db.execute(
                select(User).where(User.role == 'Data Owner')
            )
            data_owners = data_owners_result.scalars().all()
            total_data_providers = len(data_owners)
        except Exception as e:
            logger.warning(f"Error counting total data providers: {e}")
            total_data_providers = 0
        
        return DataProviderPhaseStatusDTO(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase_status,
            total_attributes=universal_metrics.total_attributes,
            scoped_attributes=universal_metrics.scoped_attributes_non_pk,  # Non-PK only for data owner
            total_samples=approved_samples_count,  # From universal metrics
            total_lobs=total_lobs,  # From universal metrics
            assigned_data_providers=assigned_data_providers,  # From universal metrics
            total_data_providers=total_data_providers,
            attributes_with_lob_assignments=attributes_with_lob_assignments,
            attributes_with_data_owners=attributes_with_data_owners,
            pending_cdo_assignments=pending_cdo_assignments,
            overdue_assignments=overdue_count,
            can_submit_lob_assignments=can_submit_lob_assignments,
            can_complete_phase=can_complete_phase,
            completion_requirements=completion_requirements,
            started_at=phase.actual_start_date if phase and phase.actual_start_date else None
        )


class GetHistoricalAssignmentsUseCase(UseCase):
    """Get historical data owner assignments"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> HistoricalAssignmentResponseDTO:
        """Get historical assignments"""
        
        # Get report name
        report = await db.execute(
            select(Report).where(Report.report_id == report_id)
        )
        report = report.scalar_one_or_none()
        
        if not report:
            raise ValueError("Report not found")
        
        # Get scoped attributes
        scoped_attributes = await db.execute(
            select(ReportAttribute)
            .where(and_(
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_scoped == True
            ))
        )
        scoped_attributes = scoped_attributes.scalars().all()
        
        suggestions = []
        
        for attribute in scoped_attributes:
            # Find historical assignments
            historical = await db.execute(
                select(HistoricalDataOwnerAssignment, User)
                .join(User, HistoricalDataOwnerAssignment.data_owner_id == User.user_id)
                .where(and_(
                    HistoricalDataOwnerAssignment.report_name == report.report_name,
                    HistoricalDataOwnerAssignment.attribute_name == attribute.attribute_name
                ))
                .order_by(HistoricalDataOwnerAssignment.assigned_at.desc())
                .limit(3)
            )
            historical = historical.all()
            
            for hist_assignment, data_owner in historical:
                # Calculate assignment frequency
                frequency = await db.execute(
                    select(func.count(HistoricalDataOwnerAssignment.history_id))
                    .where(and_(
                        HistoricalDataOwnerAssignment.report_name == report.report_name,
                        HistoricalDataOwnerAssignment.attribute_name == attribute.attribute_name,
                        HistoricalDataOwnerAssignment.data_owner_id == hist_assignment.data_owner_id
                    ))
                )
                frequency = frequency.scalar() or 0
                
                success_rate = hist_assignment.success_rating or 0.8
                
                suggestions.append(HistoricalAssignmentSuggestionDTO(
                    attribute_name=attribute.attribute_name,
                    data_owner_id=hist_assignment.data_owner_id,
                    data_owner_name=data_owner.full_name,
                    last_assigned_date=hist_assignment.assigned_at,
                    assignment_frequency=frequency,
                    success_rate=success_rate
                ))
        
        return HistoricalAssignmentResponseDTO(
            cycle_id=cycle_id,
            report_id=report_id,
            suggestions=suggestions,
            total_suggestions=len(suggestions)
        )


class SubmitCDOAssignmentsUseCase(UseCase):
    """Submit CDO data owner assignments"""
    
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
            # First, try to find by attribute name if UUID doesn't match
            attribute = None
            
            # Try to convert attribute_id to int if it's a string number
            try:
                attribute_id_int = int(assignment_req.attribute_id)
                # Verify attribute by ID
                # Query by phase_id instead of cycle_id/report_id for better performance
                phase_result = await db.execute(
                    select(WorkflowPhase.phase_id)
                    .where(and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == 'Planning'
                    ))
                )
                phase_id = phase_result.scalar_one_or_none()
                
                if not phase_id:
                    raise ValueError(f"Planning phase not found for cycle {cycle_id}, report {report_id}")
                
                attribute = await db.execute(
                    select(ReportAttribute)
                    .where(and_(
                        ReportAttribute.phase_id == phase_id,
                        ReportAttribute.id == attribute_id_int,
                        ReportAttribute.is_primary_key == False
                    ))
                )
                attribute = attribute.scalar_one_or_none()
            except ValueError:
                # attribute_id is not a valid integer, it might be a UUID
                # Let's find the attribute by other means
                logger.warning(f"Received non-numeric attribute_id: {assignment_req.attribute_id}")
                
                # Since we have the assignment data, let's match by attribute from the pending assignments
                # The frontend should be sending assignments that were loaded from the assignment matrix
                # For now, we'll need to find a workaround
                pass
            
            if not attribute:
                # Try to find by matching the context - this is a workaround
                # Get all attributes for this report and find the one that needs assignment
                all_attrs = await db.execute(
                    select(ReportAttribute)
                    .where(and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.is_scoped == True,
                        ReportAttribute.is_primary_key == False
                    ))
                )
                attrs_list = all_attrs.scalars().all()
                
                # Log available attributes
                logger.info(f"Available attributes for cycle {cycle_id}, report {report_id}: {[(a.id, a.attribute_name) for a in attrs_list]}")
                
                raise ValueError(f"Attribute {assignment_req.attribute_id} not found. Please ensure valid attribute IDs are sent.")
            
            # Skip scoping verification for now - the attribute exists in planning phase
            # which means it should be available for data owner assignment
            logger.info(f"Processing assignment for attribute {attribute_id_int}: {attribute.attribute_name}")
            
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
            
            # Check existing assignment
            existing_assignment = await db.execute(
                select(DataOwnerAssignment)
                .where(and_(
                    DataOwnerAssignment.cycle_id == cycle_id,
                    DataOwnerAssignment.report_id == report_id,
                    DataOwnerAssignment.attribute_id == attribute_id_int
                ))
            )
            existing_assignment = existing_assignment.scalar_one_or_none()
            
            if existing_assignment:
                existing_assignment.data_owner_id = assignment_req.data_owner_id
                existing_assignment.cdo_id = current_user.user_id
                existing_assignment.assigned_by = current_user.user_id
                existing_assignment.assigned_at = current_time
                existing_assignment.status = 'Completed'
                assignments_created.append(existing_assignment)
            else:
                new_assignment = DataOwnerAssignment(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    attribute_id=attribute_id_int,
                    lob_id=current_user.lob_id,
                    cdo_id=current_user.user_id,
                    data_owner_id=assignment_req.data_owner_id,
                    assigned_by=current_user.user_id,
                    assigned_at=current_time,
                    status='Completed'
                )
                db.add(new_assignment)
                assignments_created.append(new_assignment)
            
            # Record historical assignment if requested
            if assignment_req.use_historical_assignment:
                report = await db.execute(select(Report).where(Report.report_id == report_id))
                report = report.scalar_one()
                
                historical_assignment = HistoricalDataOwnerAssignment(
                    report_name=report.report_name,
                    attribute_name=attribute.attribute_name,
                    data_owner_id=assignment_req.data_owner_id,
                    assigned_by=current_user.user_id,
                    cycle_id=cycle_id,
                    assigned_at=current_time,
                    completion_status='Assigned',
                    notes=assignment_req.assignment_notes
                )
                db.add(historical_assignment)
        
        await db.commit()
        
        # Create audit log
        await self._create_audit_log(
            db, cycle_id, report_id, "submit_cdo_assignments", "DataOwnerAssignment",
            None, user_id, new_values={"assignments_count": len(assignments_created)},
            notes=submission.submission_notes
        )
        
        return {
            "success": True,
            "message": f"Data owner assignments submitted successfully. {len(assignments_created)} assignments completed.",
            "assignments_completed": len(assignments_created)
        }
    
    async def _create_audit_log(
        self,
        db: AsyncSession,
        cycle_id: int,
        report_id: int,
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
            cycle_id=cycle_id,
            report_id=report_id,
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
    """Get complete assignment matrix"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession,
        current_user: Optional[User] = None  # Add current user parameter
    ) -> AssignmentMatrixDTO:
        """Get assignment matrix"""
        
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
        
        # If phase hasn't started, return empty assignment matrix
        if not workflow_phase or workflow_phase.state == 'Not Started':
            logger.warning(f"Returning empty matrix - phase not started. Phase exists: {workflow_phase is not None}, State: {workflow_phase.state if workflow_phase else 'N/A'}")
            return AssignmentMatrixDTO(
                cycle_id=cycle_id,
                report_id=report_id,
                assignments=[],
                data_owners=[],
                lob_summary={},
                cdo_summary={},
                status_summary={"Assigned": 0, "In Progress": 0, "Completed": 0, "Overdue": 0}
            )
        
        # Get planning attributes from the Planning phase that are approved and not primary keys
        # We use planning attributes as the source of truth for CDE, PK, and issue information
        from app.models.report_attribute import ReportAttribute as PlanningAttribute
        
        # Get the planning phase for this cycle/report
        planning_phase = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning"
                )
            )
        )
        planning_phase = planning_phase.scalar_one_or_none()
        
        if not planning_phase:
            logger.warning(f"No Planning phase found for cycle {cycle_id}, report {report_id}")
            scoped_attributes = []
        else:
            # Get attributes from planning that are approved (approval_status='approved') and not primary keys
            scoped_attributes = await db.execute(
                select(PlanningAttribute)
                .where(and_(
                    PlanningAttribute.phase_id == planning_phase.phase_id,
                    PlanningAttribute.approval_status == 'approved',
                    PlanningAttribute.is_primary_key == False
                ))
            )
            scoped_attributes = scoped_attributes.scalars().all()
            logger.info(f"Found {len(scoped_attributes)} approved non-PK planning attributes for phase_id={planning_phase.phase_id}")
        
        # Get unique scoped attributes to avoid duplicates
        unique_attributes = {}
        for attr in scoped_attributes:
            if attr.attribute_name not in unique_attributes:
                unique_attributes[attr.attribute_name] = attr
        
        attributes = list(unique_attributes.values())
        
        assignment_statuses = []
        lob_summary = {}
        cdo_summary = {}
        status_summary = {"Assigned": 0, "In Progress": 0, "Completed": 0, "Overdue": 0}
        
        # Get approved samples from Sample Selection phase to find LOBs
        sample_phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Sample Selection'
            ))
        )
        sample_phase = sample_phase.scalar_one_or_none()
        
        # Extract unique LOBs from approved samples by querying the database directly
        unique_lob_ids = set()
        unique_lob_names = set()
        
        if sample_phase:
            logger.info(f"Found Sample Selection phase for cycle {cycle_id}, report {report_id}")
            
            # Import the sample model
            from app.models.sample_selection import SampleSelectionSample
            from app.models.lob import LOB
            
            # Query approved samples with their LOBs
            approved_samples_query = select(
                SampleSelectionSample.lob_id,
                LOB.lob_name
            ).join(
                LOB, SampleSelectionSample.lob_id == LOB.lob_id, isouter=True
            ).where(
                and_(
                    SampleSelectionSample.phase_id == sample_phase.phase_id,
                    SampleSelectionSample.tester_decision == 'include',
                    SampleSelectionSample.report_owner_decision == 'approved',
                    SampleSelectionSample.lob_id.isnot(None)
                )
            ).distinct()
            
            approved_samples_result = await db.execute(approved_samples_query)
            lob_data = approved_samples_result.all()
            
            for lob_id, lob_name in lob_data:
                if lob_id:
                    unique_lob_ids.add(lob_id)
                if lob_name:
                    unique_lob_names.add(lob_name)
            
            logger.info(f"Found {len(unique_lob_ids)} unique LOBs from approved samples")
            logger.info(f"LOB names: {list(unique_lob_names)}")
        
        # Filter LOBs if current user is a Data Executive
        if current_user and current_user.role == 'Data Executive' and current_user.lob_id:
            logger.info(f"Data Executive {current_user.email} with LOB {current_user.lob_id} - filtering assignments")
            # Only keep the Data Executive's LOB
            if current_user.lob_id in unique_lob_ids:
                unique_lob_ids = {current_user.lob_id}
                # Also filter LOB names to match
                user_lob = await db.execute(
                    select(LOB).where(LOB.lob_id == current_user.lob_id)
                )
                user_lob_obj = user_lob.scalar_one_or_none()
                if user_lob_obj:
                    unique_lob_names = {user_lob_obj.lob_name}
                    logger.info(f"Filtered to LOB: {user_lob_obj.lob_name} (ID: {current_user.lob_id})")
            else:
                logger.warning(f"Data Executive's LOB {current_user.lob_id} not found in approved samples")
                # No assignments for this Data Executive
                unique_lob_ids = set()
                unique_lob_names = set()
        
        for attribute in attributes:
            
            # Get data owner LOB assignments for this attribute
            # We need to get all LOB assignments for this attribute
            from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping
            from app.models.lob import LOB as LOBModel
            
            # Build query for LOB assignments
            lob_assignment_query = select(DataOwnerLOBAttributeMapping, User).outerjoin(
                User, DataOwnerLOBAttributeMapping.data_owner_id == User.user_id
            ).where(and_(
                DataOwnerLOBAttributeMapping.phase_id == workflow_phase.phase_id,
                DataOwnerLOBAttributeMapping.attribute_id == attribute.id  # Use attribute.id not attribute_id
            ))
            
            # Filter by LOB if current user is a Data Executive
            if current_user and current_user.role == 'Data Executive' and current_user.lob_id:
                lob_assignment_query = lob_assignment_query.where(
                    DataOwnerLOBAttributeMapping.lob_id == current_user.lob_id
                )
            
            lob_assignments = await db.execute(lob_assignment_query)
            lob_assignments_list = lob_assignments.all()
            
            # Build assigned_lobs with assignment details
            assigned_lobs = []
            if lob_assignments_list:
                # Get LOB details for all assignments
                lob_ids = [assignment[0].lob_id for assignment in lob_assignments_list]
                lob_objects = await db.execute(
                    select(LOBModel).where(LOBModel.lob_id.in_(lob_ids))
                )
                lob_dict = {lob.lob_id: lob for lob in lob_objects.scalars().all()}
                
                # Build LOB assignment details
                for assignment, data_owner in lob_assignments_list:
                    lob = lob_dict.get(assignment.lob_id)
                    if lob:
                        assigned_lobs.append({
                            "lob_id": lob.lob_id,
                            "lob_name": lob.lob_name,
                            "data_owner_id": assignment.data_owner_id,
                            "data_owner_name": data_owner.full_name if data_owner else None,
                            "data_executive_id": assignment.data_executive_id,
                            "can_assign": current_user and current_user.user_id == assignment.data_executive_id if assignment.data_executive_id else False
                        })
            elif unique_lob_ids:
                # Fallback: If no assignments exist yet, create empty ones for the LOBs
                lob_objects = await db.execute(
                    select(LOBModel).where(LOBModel.lob_id.in_(list(unique_lob_ids)))
                )
                lob_objects = lob_objects.scalars().all()
                for lob in lob_objects:
                    # For Data Executives, only include their LOB
                    if current_user and current_user.role == 'Data Executive' and current_user.lob_id:
                        if lob.lob_id == current_user.lob_id:
                            assigned_lobs.append({
                                "lob_id": lob.lob_id,
                                "lob_name": lob.lob_name,
                                "data_owner_id": None,
                                "data_owner_name": None,
                                "data_executive_id": current_user.user_id,
                                "can_assign": True
                            })
                    else:
                        assigned_lobs.append({
                            "lob_id": lob.lob_id,
                            "lob_name": lob.lob_name,
                            "data_owner_id": None,
                            "data_owner_name": None,
                            "data_executive_id": None,
                            "can_assign": False
                        })
            
            # For backward compatibility, pick first assignment as the primary one
            data_owner_assignment = lob_assignments_list[0] if lob_assignments_list else None
            
            # Check for SLA violations
            sla_violation = await db.execute(
                select(DataOwnerSLAViolation)
                .where(and_(
                    DataOwnerSLAViolation.cycle_id == cycle_id,
                    DataOwnerSLAViolation.report_id == report_id,
                    DataOwnerSLAViolation.attribute_id == attribute.id,  # Use attribute.id not attribute_id
                    DataOwnerSLAViolation.is_resolved == False
                ))
            )
            sla_violation = sla_violation.scalar_one_or_none()
            
            # Determine status
            if data_owner_assignment:
                dp_assignment, data_owner = data_owner_assignment
                if dp_assignment.data_owner_id:
                    assignment_status_val = AssignmentStatusEnum.COMPLETED
                else:
                    assignment_status_val = AssignmentStatusEnum.ASSIGNED
            else:
                assignment_status_val = AssignmentStatusEnum.ASSIGNED
            
            is_overdue = sla_violation is not None
            
            # Log the attribute ID for debugging
            logger.info(f"Creating assignment status for attribute: id={attribute.id}, name={attribute.attribute_name}")
            
            # Generate a unique identifier for frontend tracking while preserving the actual ID
            frontend_id = str(attribute.id)
            
            assignment_status = AttributeAssignmentStatusDTO(
                attribute_id=frontend_id,  # Use actual ID as string
                attribute_name=attribute.attribute_name,
                is_primary_key=False,
                assigned_lobs=assigned_lobs,
                data_owner_id=data_owner_assignment[0].data_owner_id if data_owner_assignment and data_owner_assignment[0].data_owner_id else None,
                data_owner_name=data_owner_assignment[1].full_name if data_owner_assignment and data_owner_assignment[1] else None,
                assigned_by=data_owner_assignment[0].assigned_by if data_owner_assignment else None,
                assigned_at=data_owner_assignment[0].assigned_at if data_owner_assignment else None,
                status=assignment_status_val,
                assignment_notes=None,
                is_overdue=is_overdue,
                sla_deadline=None,
                hours_remaining=None
            )
            
            assignment_statuses.append(assignment_status)
            
            for lob in assigned_lobs:
                lob_name = lob["lob_name"]
                lob_summary[lob_name] = lob_summary.get(lob_name, 0) + 1
            
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


class GetCDOAssignmentsUseCase(UseCase):
    """Get CDO assignments"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        db: AsyncSession
    ) -> List[DataOwnerAssignmentDTO]:
        """Get assignments made by CDO"""
        
        assignments = await db.execute(
            select(DataOwnerAssignment, ReportAttribute, User, LOB)
            .join(ReportAttribute, DataOwnerAssignment.attribute_id == ReportAttribute.attribute_id)
            .join(User, DataOwnerAssignment.data_owner_id == User.user_id)
            .join(LOB, DataOwnerAssignment.lob_id == LOB.lob_id)
            .where(and_(
                DataOwnerAssignment.cycle_id == cycle_id,
                DataOwnerAssignment.report_id == report_id,
                DataOwnerAssignment.assigned_by == user_id
            ))
            .order_by(DataOwnerAssignment.assigned_at.desc())
        )
        assignments = assignments.all()
        
        assignment_list = []
        for dp_assignment, attribute, data_owner, lob in assignments:
            assignment_list.append(DataOwnerAssignmentDTO(
                assignment_id=dp_assignment.assignment_id,
                cycle_id=cycle_id,
                report_id=report_id,
                attribute_id=attribute.attribute_id,
                attribute_name=attribute.attribute_name,
                attribute_description=attribute.description,
                data_owner_id=data_owner.user_id,
                data_owner_name=f"{data_owner.first_name} {data_owner.last_name}",
                data_owner_email=data_owner.email,
                lob_name=lob.lob_name,
                assigned_at=dp_assignment.assigned_at,
                status=dp_assignment.status
            ))
        
        return assignment_list


class GetCDODashboardUseCase(UseCase):
    """Get CDO dashboard"""
    
    async def execute(
        self,
        user_id: int,
        time_filter: str,
        db: AsyncSession
    ) -> CDODashboardResponseDTO:
        """Get dashboard data"""
        
        from app.services.cdo_dashboard_service import get_cdo_dashboard_service
        
        # Get dashboard service
        dashboard_service = get_cdo_dashboard_service()
        
        # Get comprehensive dashboard data
        dashboard_data = await dashboard_service.get_cdo_dashboard_metrics(
            user_id,
            db,
            time_filter
        )
        
        # Convert to DTOs
        lob_summary = dashboard_data.get('lob_overview', {}).get('summary', {})
        overview_metrics = CDODashboardMetricsDTO(
            total_assignments=lob_summary.get('total_assignments', 0),
            completed_assignments=lob_summary.get('completed_assignments', 0),
            pending_assignments=lob_summary.get('total_assignments', 0) - lob_summary.get('completed_assignments', 0),
            overdue_assignments=0,  # TODO: Calculate from test cases
            compliance_rate=lob_summary.get('sla_compliance_rate', 0)
        )
        
        workflow_status = []
        for ws in dashboard_data.get('workflow_status', []):
            workflow_status.append(CDOWorkflowStatusDTO(
                cycle_id=ws['cycle_id'],
                cycle_name=ws['cycle_name'],
                report_id=ws['report_id'],
                report_name=ws['report_name'],
                phase_status=ws.get('phase_status', 'Not Started'),
                attributes_pending=ws.get('pending_assignments', 0),
                attributes_completed=ws.get('completed_assignments', 0),
                last_updated=datetime.utcnow()
            ))
        
        recent_activity = []
        for activity in dashboard_data.get('assignment_analytics', {}).get('recent_activity', []):
            recent_activity.append(CDOAssignmentActivityDTO(
                activity_date=activity.get('assigned_at', datetime.utcnow().isoformat()),
                activity_type='Assignment Created',
                attribute_name=activity.get('attribute_name', ''),
                data_owner_name=activity.get('data_provider_name', 'Not Assigned'),
                cycle_name=activity.get('cycle_name', ''),
                report_name=activity.get('report_name', '')
            ))
        
        return CDODashboardResponseDTO(
            overview_metrics=overview_metrics,
            workflow_status=workflow_status,
            recent_activity=recent_activity,
            assignment_analytics=dashboard_data.get('assignment_analytics', {}),
            lob_overview=dashboard_data.get('lob_overview', {})
        )


class CompleteDataProviderPhaseUseCase(UseCase):
    """Complete data owner phase"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        completion_data: DataProviderPhaseCompleteDTO,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Complete phase"""
        
        # Verify requirements
        status_use_case = GetDataProviderPhaseStatusUseCase()
        status = await status_use_case.execute(cycle_id, report_id, db)
        
        if not status.can_complete_phase:
            raise ValueError(f"Cannot complete phase. Requirements: {', '.join(status.completion_requirements)}")
        
        if not completion_data.confirm_completion:
            raise ValueError("Completion must be confirmed")
        
        # Update workflow phase
        phase = await db.execute(
            select(WorkflowPhase)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Data Provider ID'
            ))
        )
        phase = phase.scalar_one_or_none()
        
        if not phase:
            raise ValueError("Data owner phase not found")
        
        phase.status = 'Complete'
        phase.completed_at = datetime.utcnow()
        phase.completed_by = user_id
        
        await db.commit()
        
        # Create audit log
        await self._create_audit_log(
            db, cycle_id, report_id, "complete_data_owner_phase", "WorkflowPhase",
            phase.phase_id, user_id, notes=completion_data.completion_notes
        )
        
        return {
            "success": True,
            "message": "Data owner identification phase completed successfully",
            "phase_id": phase.phase_id,
            "completed_at": phase.completed_at,
            "total_attributes": status.total_attributes
        }
    
    async def _create_audit_log(
        self,
        db: AsyncSession,
        cycle_id: int,
        report_id: int,
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
            cycle_id=cycle_id,
            report_id=report_id,
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