"""
Request for Information use cases for clean architecture
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update, case, text
from sqlalchemy.orm import selectinload
import uuid
import os
import logging
from fastapi import UploadFile

logger = logging.getLogger(__name__)

from app.application.use_cases.base import UseCase
from app.application.dtos.request_info import (
    RequestInfoPhaseStartDTO,
    TestCaseCreateDTO,
    TestCaseResponseDTO,
    TestCaseWithDetailsDTO,
    DocumentSubmissionCreateDTO,
    DocumentSubmissionResponseDTO,
    FileUploadResponseDTO,
    DataOwnerNotificationDTO,
    RequestInfoPhaseStatusDTO,
    DataOwnerPortalDataDTO,
    PhaseProgressSummaryDTO,
    DataOwnerAssignmentSummaryDTO,
    PhaseCompletionRequestDTO,
    ResendTestCaseRequestDTO,
    BulkTestCaseAssignmentDTO,
    TestCaseUpdateDTO,
    SubmissionStatusEnum,
    TestCaseStatusEnum,
    DocumentTypeEnum
)
from app.models import (
    DataProviderNotification,
    User,
    Report,
    WorkflowPhase,
    TestCaseEvidence
)
from app.models.request_info import CycleReportTestCase
from app.models.test_cycle import TestCycle
from app.models.sample_selection import SampleSelectionSample
from app.services.workflow_orchestrator import get_workflow_orchestrator


class StartRequestInfoPhaseUseCase(UseCase):
    """Start request for information phase"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        start_data: RequestInfoPhaseStartDTO,
        user_id: int,
        db: AsyncSession
    ) -> RequestInfoPhaseStatusDTO:
        """Start the phase"""
        
        # Check if phase already exists
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request Info"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if phase:
            if phase.status != 'Not Started':
                raise ValueError("Request Info phase has already been started")
        else:
            # Create new phase
            # Provide default submission deadline if not specified (7 days from now)
            default_deadline = start_data.submission_deadline or (datetime.now(timezone.utc) + timedelta(days=7))
            
            phase = WorkflowPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Request Info",
                assignment_status='assigned',
                phase_metadata={
                    "instructions": start_data.instructions,
                    "submission_deadline": default_deadline.isoformat()
                }
            )
            db.add(phase)
        
        # Update phase
        phase.status = 'In Progress'
        phase.started_by = user_id
        phase.started_at = datetime.now(timezone.utc)
        phase.updated_at = datetime.now(timezone.utc)
        phase.updated_by_id = user_id
        
        if not phase.phase_metadata:
            phase.phase_metadata = {}
        if start_data.instructions:
            phase.phase_metadata["instructions"] = start_data.instructions
        if start_data.submission_deadline:
            phase.phase_metadata["submission_deadline"] = start_data.submission_deadline.isoformat()
        
        # Update the workflow phase as well for consistency
        try:
            workflow_orchestrator = get_workflow_orchestrator()
            await workflow_orchestrator.start_phase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Request Info",
                user_id=user_id
            )
        except Exception as e:
            # Log but don't fail the entire operation
            print(f"Warning: Failed to update workflow phase: {e}")
        
        # Generate test cases automatically (Sample X non-PK Attribute matrix)
        test_cases_created = await self._generate_test_cases(phase, user_id, db)
        print(f"Generated {test_cases_created} test cases for Request Info phase")
        
        await db.commit()
        
        # Return status
        return await self._get_phase_status(phase, db)
    
    async def _get_phase_status(
        self,
        phase: WorkflowPhase,
        db: AsyncSession
    ) -> RequestInfoPhaseStatusDTO:
        """Get phase status"""
        # Get test case statistics
        stats = await db.execute(
            select(
                func.count(CycleReportTestCase.id).label('total'),
                func.sum(case((CycleReportTestCase.status == 'Complete', 1), else_=0)).label('submitted'),
                func.sum(case((CycleReportTestCase.status == 'Not Started', 1), else_=0)).label('pending'),
                func.sum(case((CycleReportTestCase.status == 'In Progress', 1), else_=0)).label('overdue')
            ).where(
                CycleReportTestCase.phase_id == phase.phase_id
            )
        )
        stats_row = stats.first()
        
        # Get data owner count from document submissions
        owner_count = await db.execute(
            select(func.count(func.distinct(TestCaseEvidence.data_owner_id)))
            .join(CycleReportTestCase, TestCaseEvidence.test_case_id == CycleReportTestCase.id)
            .where(
                and_(
                    CycleReportTestCase.phase_id == phase.phase_id,
                    TestCaseEvidence.data_owner_id.isnot(None)
                )
            )
        )
        data_owners = owner_count.scalar() or 0
        
        # Get submission count
        submission_count = await db.execute(
            select(func.count(TestCaseEvidence.id))
            .join(CycleReportTestCase, TestCaseEvidence.test_case_id == CycleReportTestCase.id)
            .where(
                and_(
                    CycleReportTestCase.phase_id == phase.phase_id,
                    TestCaseEvidence.is_current == True
                )
            )
        )
        submissions = submission_count.scalar() or 0
        
        # Handle None values from aggregation functions
        total_cases = stats_row.total or 0
        submitted_cases = stats_row.submitted or 0
        pending_cases = stats_row.pending or 0
        overdue_cases = stats_row.overdue or 0
        
        # Determine if phase can be completed
        can_complete = (
            total_cases > 0 and
            pending_cases == 0 and
            overdue_cases == 0
        )
        
        completion_requirements = []
        if pending_cases > 0:
            completion_requirements.append(f"Submit {pending_cases} pending test cases")
        if overdue_cases > 0:
            completion_requirements.append(f"Resolve {overdue_cases} overdue test cases")
        if total_cases == 0:
            completion_requirements.append("Create test cases for data collection")
        
        if not completion_requirements:
            completion_requirements.append("All requirements met - ready to complete phase")
        
        return RequestInfoPhaseStatusDTO(
            phase_id=str(phase.phase_id),
            cycle_id=phase.cycle_id,
            report_id=phase.report_id,
            phase_status=phase.status,
            total_test_cases=total_cases,
            submitted_test_cases=submitted_cases,
            pending_test_cases=pending_cases,
            overdue_test_cases=overdue_cases,
            data_owners_notified=data_owners,
            total_submissions=submissions,
            can_complete=can_complete,
            completion_requirements=completion_requirements
        )
    
    async def _generate_test_cases(
        self,
        phase: WorkflowPhase,
        user_id: int,
        db: AsyncSession
    ) -> int:
        """Generate test cases from Sample X non-PK Attribute matrix
        
        Flow:
        1. Get approved samples from sample selection phase
        2. Get scoped non-PK attributes approved during scoping
        3. Get data owner assignments from Data Source ID phase
        4. Create one test case for each sample + non-PK attribute combination
        """
        from app.models.sample_selection import SampleSelectionSample, SampleSelectionVersion
        from app.models.scoping import ScopingAttribute, ScopingVersion
        from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping, DataOwnerLOBAttributeVersion
        from app.models.report_attribute import ReportAttribute as PlanningAttribute
        
        # 1. Get approved samples from sample selection phase
        samples_result = await db.execute(
            select(SampleSelectionSample)
            .join(SampleSelectionVersion)
            .where(
                and_(
                    SampleSelectionVersion.cycle_id == phase.cycle_id,
                    SampleSelectionVersion.report_id == phase.report_id,
                    SampleSelectionVersion.status == 'Active',
                    SampleSelectionSample.is_included == True,
                    SampleSelectionSample.decision == 'approved'
                )
            )
        )
        approved_samples = samples_result.scalars().all()
        
        if not approved_samples:
            print(f"Warning: No approved samples found for cycle {phase.cycle_id}, report {phase.report_id}")
            return 0
        
        # 2. Get scoped non-PK attributes approved during scoping
        scoped_attrs_result = await db.execute(
            select(ScopingAttribute)
            .join(ScopingVersion)
            .join(PlanningAttribute, ScopingAttribute.planning_attribute_id == PlanningAttribute.id)
            .where(
                and_(
                    ScopingVersion.cycle_id == phase.cycle_id,
                    ScopingVersion.report_id == phase.report_id,
                    ScopingVersion.status == 'Active',
                    ScopingAttribute.is_in_scope == True,
                    ScopingAttribute.tester_decision == 'include',
                    ScopingAttribute.report_owner_decision == 'approved',
                    PlanningAttribute.is_primary_key == False
                )
            )
        )
        scoped_non_pk_attrs = scoped_attrs_result.scalars().all()
        
        if not scoped_non_pk_attrs:
            print(f"Warning: No scoped non-PK attributes found for cycle {phase.cycle_id}, report {phase.report_id}")
            return 0
        
        # 3. Get data owner assignments from Data Source ID phase
        # Map attribute ID and LOB to data owner
        data_owner_map = {}
        
        for attr in scoped_non_pk_attrs:
            # Get data owner assignment for this attribute and LOB combination
            for sample in approved_samples:
                # Get LOB from sample
                lob_id = sample.metadata.get('lob_id') if sample.metadata else None
                if not lob_id:
                    print(f"Warning: Sample {sample.sample_id} has no LOB ID")
                    continue
                
                # Get data owner assignment
                assignment_result = await db.execute(
                    select(DataOwnerLOBAttributeMapping)
                    .join(DataOwnerLOBAttributeVersion)
                    .where(
                        and_(
                            DataOwnerLOBAttributeVersion.cycle_id == phase.cycle_id,
                            DataOwnerLOBAttributeVersion.report_id == phase.report_id,
                            DataOwnerLOBAttributeVersion.status == 'Active',
                            DataOwnerLOBAttributeMapping.attribute_id == attr.planning_attribute_id,
                            DataOwnerLOBAttributeMapping.lob_id == lob_id,
                            DataOwnerLOBAttributeMapping.status == 'active'
                        )
                    )
                )
                assignment = assignment_result.scalar_one_or_none()
                
                if assignment:
                    key = (attr.planning_attribute_id, lob_id)
                    data_owner_map[key] = assignment.data_owner_id
        
        test_cases_created = 0
        test_case_number = 1
        
        # 4. Create test cases: one per sample + non-PK attribute combination
        for sample in approved_samples:
            lob_id = sample.metadata.get('lob_id') if sample.metadata else None
            if not lob_id:
                continue
                
            for attr in scoped_non_pk_attrs:
                # Get data owner for this attribute/LOB combination
                data_owner_id = data_owner_map.get((attr.planning_attribute_id, lob_id))
                if not data_owner_id:
                    print(f"Warning: No data owner found for attribute {attr.planning_attribute_id} and LOB {lob_id}")
                    continue
                
                # Get attribute details
                attr_details = await db.execute(
                    select(PlanningAttribute).where(PlanningAttribute.id == attr.planning_attribute_id)
                )
                planning_attr = attr_details.scalar_one_or_none()
                
                if not planning_attr:
                    continue
                
                # Create test case
                test_case = CycleReportTestCase(
                    test_case_number=f"TC-{phase.cycle_id}-{phase.report_id}-{test_case_number:04d}",
                    test_case_name=f"Evidence for {planning_attr.attribute_name} - Sample {sample.sample_id}",
                    description=f"Provide source evidence for attribute '{planning_attr.attribute_name}' for the specified sample",
                    expected_outcome="Valid source document or data source evidence provided",
                    test_type="Evidence Collection",
                    phase_id=phase.phase_id,
                    sample_id=sample.sample_id,
                    attribute_id=attr.planning_attribute_id,
                    attribute_name=planning_attr.attribute_name,
                    lob_id=lob_id,
                    data_owner_id=data_owner_id,
                    assigned_by=user_id,
                    assigned_at=datetime.now(timezone.utc),
                    status='Not Started',
                    submission_deadline=datetime.fromisoformat(
                        phase.phase_metadata.get("submission_deadline", 
                        (datetime.now(timezone.utc) + timedelta(days=7)).isoformat())
                    ),
                    special_instructions=phase.phase_metadata.get("instructions", "")
                )
                
                db.add(test_case)
                test_cases_created += 1
                test_case_number += 1
        
        return test_cases_created


class CreateCycleReportTestCaseUseCase(UseCase):
    """Create a test case for data collection"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        test_case_data: TestCaseCreateDTO,
        user_id: int,
        db: AsyncSession
    ) -> TestCaseResponseDTO:
        """Create test case"""
        
        # Get or create phase
        phase = await self._get_or_create_phase(cycle_id, report_id, db)
        
        # Create test case
        test_case = CycleReportTestCase(
            test_case_id=str(uuid.uuid4()),
            phase_id=phase.phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            attribute_id=test_case_data.attribute_id,
            sample_id=test_case_data.sample_id,
            sample_identifier=test_case_data.sample_identifier,
            data_owner_id=test_case_data.data_owner_id,
            assigned_by=user_id,
            assigned_at=datetime.now(timezone.utc),
            attribute_name=test_case_data.attribute_name,
            primary_key_attributes=test_case_data.primary_key_attributes,
            expected_evidence_type=test_case_data.expected_evidence_type,
            special_instructions=test_case_data.special_instructions,
            assignment_status='assigned',
            submission_deadline=test_case_data.submission_deadline or datetime.fromisoformat(phase.phase_metadata.get("submission_deadline", datetime.now(timezone.utc).isoformat()))
        )
        
        db.add(test_case)
        await db.commit()
        await db.refresh(test_case)
        
        return self._to_response_dto(test_case)
    
    async def _get_or_create_phase(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> WorkflowPhase:
        """Get or create request info phase"""
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request Info"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            phase = WorkflowPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Request Info",
                status='Not Started'
            )
            db.add(phase)
            await db.commit()
        
        return phase
    
    def _to_response_dto(self, test_case: CycleReportTestCase) -> TestCaseResponseDTO:
        """Convert test case to response DTO"""
        return TestCaseResponseDTO(
            test_case_id=test_case.test_case_id,
            phase_id=test_case.phase_id,
            cycle_id=test_case.cycle_id,
            report_id=test_case.report_id,
            attribute_id=test_case.attribute_id,
            sample_id=test_case.sample_id,
            sample_identifier=test_case.sample_identifier,
            data_owner_id=test_case.data_owner_id,
            assigned_by=test_case.assigned_by,
            assigned_at=test_case.assigned_at,
            attribute_name=test_case.attribute_name,
            primary_key_attributes=test_case.primary_key_attributes,
            expected_evidence_type=test_case.expected_evidence_type,
            special_instructions=test_case.special_instructions,
            status=test_case.status,
            submission_deadline=test_case.submission_deadline,
            submitted_at=test_case.submitted_at,
            acknowledged_at=test_case.acknowledged_at,
            created_at=test_case.created_at,
            updated_at=test_case.updated_at
        )


class BulkCreateCycleReportTestCasesUseCase(UseCase):
    """Bulk create test cases"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        bulk_data: BulkTestCaseAssignmentDTO,
        user_id: int,
        db: AsyncSession
    ) -> List[TestCaseResponseDTO]:
        """Bulk create test cases"""
        
        # Get or create phase
        phase = await self._get_or_create_phase(cycle_id, report_id, db)
        
        created_test_cases = []
        
        for assignment in bulk_data.assignments:
            test_case = CycleReportTestCase(
                test_case_id=str(uuid.uuid4()),
                phase_id=phase.phase_id,
                cycle_id=cycle_id,
                report_id=report_id,
                attribute_id=assignment.attribute_id,
                sample_id=assignment.sample_id,
                sample_identifier=assignment.sample_identifier,
                data_owner_id=assignment.data_owner_id,
                assigned_by=user_id,
                assigned_at=datetime.now(timezone.utc),
                attribute_name=assignment.attribute_name,
                primary_key_attributes=assignment.primary_key_attributes,
                expected_evidence_type=assignment.expected_evidence_type,
                special_instructions=assignment.special_instructions,
                assignment_status='assigned',
                submission_deadline=assignment.submission_deadline or datetime.fromisoformat(phase.phase_metadata.get("submission_deadline", datetime.now(timezone.utc).isoformat()))
            )
            
            db.add(test_case)
            created_test_cases.append(test_case)
        
        await db.commit()
        
        # Refresh all test cases
        for tc in created_test_cases:
            await db.refresh(tc)
        
        return [self._to_response_dto(tc) for tc in created_test_cases]
    
    async def _get_or_create_phase(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> WorkflowPhase:
        """Get or create request info phase"""
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request Info"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            phase = WorkflowPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Request Info",
                status='Not Started'
            )
            db.add(phase)
            await db.commit()
        
        return phase
    
    def _to_response_dto(self, test_case: CycleReportTestCase) -> TestCaseResponseDTO:
        """Convert test case to response DTO"""
        return TestCaseResponseDTO(
            test_case_id=test_case.test_case_id,
            phase_id=test_case.phase_id,
            cycle_id=test_case.cycle_id,
            report_id=test_case.report_id,
            attribute_id=test_case.attribute_id,
            sample_id=test_case.sample_id,
            sample_identifier=test_case.sample_identifier,
            data_owner_id=test_case.data_owner_id,
            assigned_by=test_case.assigned_by,
            assigned_at=test_case.assigned_at,
            attribute_name=test_case.attribute_name,
            primary_key_attributes=test_case.primary_key_attributes,
            expected_evidence_type=test_case.expected_evidence_type,
            special_instructions=test_case.special_instructions,
            status=test_case.status,
            submission_deadline=test_case.submission_deadline,
            submitted_at=test_case.submitted_at,
            acknowledged_at=test_case.acknowledged_at,
            created_at=test_case.created_at,
            updated_at=test_case.updated_at
        )


class GetDataOwnerCycleReportTestCasesUseCase(UseCase):
    """Get test cases for data owner"""
    
    async def execute(
        self,
        data_owner_id: int,
        cycle_id: Optional[int] = None,
        report_id: Optional[int] = None,
        status: Optional[TestCaseStatusEnum] = None,
        db: AsyncSession = None
    ) -> DataOwnerPortalDataDTO:
        """Get data owner portal data"""
        
        # Build query - get test cases assigned to this data owner
        query = select(CycleReportTestCase).where(
            CycleReportTestCase.data_owner_id == data_owner_id
        ).options(
            selectinload(CycleReportTestCase.phase)
            # Note: Skipping document_submissions eager loading due to model/DB mismatch
        )
        
        # Filter by cycle_id and report_id if provided
        if cycle_id and report_id:
            query = query.join(
                WorkflowPhase,
                CycleReportTestCase.phase_id == WorkflowPhase.phase_id
            ).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id
                )
            )
        
        if status:
            query = query.where(CycleReportTestCase.status == status)
        
        query = query.order_by(CycleReportTestCase.submission_deadline, CycleReportTestCase.created_at)
        
        result = await db.execute(query)
        test_cases = result.scalars().all()
        
        # Load primary key attributes from sample data
        if test_cases:
            # Get the Sample Selection phase for this cycle/report
            phase_info = test_cases[0].phase
            if phase_info:
                sample_phase_result = await db.execute(
                    select(WorkflowPhase.phase_id).where(
                        and_(
                            WorkflowPhase.cycle_id == phase_info.cycle_id,
                            WorkflowPhase.report_id == phase_info.report_id,
                            WorkflowPhase.phase_name == "Sample Selection"
                        )
                    )
                )
                sample_phase_id = sample_phase_result.scalar()
                
                if sample_phase_id:
                    # Get all sample data in one query
                    sample_ids = [tc.sample_id for tc in test_cases if tc.sample_id]
                    if sample_ids:
                        sample_query = """
                            SELECT s.sample_id, s.sample_data
                            FROM cycle_report_sample_selection_samples s
                            WHERE s.phase_id = :phase_id 
                            AND s.sample_id = ANY(:sample_ids)
                        """
                        sample_result = await db.execute(
                            text(sample_query),
                            {
                                "phase_id": sample_phase_id,
                                "sample_ids": sample_ids
                            }
                        )
                        
                        # Create a map of sample_id to sample_data
                        sample_data_map = {}
                        for row in sample_result:
                            sample_data_map[str(row.sample_id)] = row.sample_data
                        
                        # Set primary key attributes for each test case
                        for tc in test_cases:
                            if tc.sample_id and str(tc.sample_id) in sample_data_map:
                                sample_data = sample_data_map[str(tc.sample_id)]
                                primary_key_attributes = {}
                                
                                # Get primary keys from phase_data or use defaults
                                primary_keys = []
                                if tc.phase and hasattr(tc.phase, 'phase_data') and tc.phase.phase_data:
                                    primary_keys = tc.phase.phase_data.get('primary_keys', [])
                                if not primary_keys:
                                    primary_keys = ['Bank ID', 'Period ID', 'Customer ID', 'Reference Number']
                                    
                                if sample_data:
                                    for pk in primary_keys:
                                        if pk in sample_data:
                                            primary_key_attributes[pk] = sample_data[pk]
                                
                                tc._primary_key_attributes = primary_key_attributes
                            else:
                                tc._primary_key_attributes = {}
                else:
                    # No Sample Selection phase found
                    for tc in test_cases:
                        tc._primary_key_attributes = {}
            else:
                # No phase info
                for tc in test_cases:
                    tc._primary_key_attributes = {}
        
        # Get statistics based on evidence submissions
        # Count test cases with evidence submitted
        from app.models.request_info import RFIEvidenceLegacy
        from sqlalchemy import func
        
        # Get test case IDs that have evidence
        test_case_ids = [tc.id for tc in test_cases]
        if test_case_ids:
            evidence_count_result = await db.execute(
                select(
                    RFIEvidenceLegacy.test_case_id,
                    func.count(RFIEvidenceLegacy.id).label('evidence_count')
                ).where(
                    and_(
                        RFIEvidenceLegacy.test_case_id.in_(test_case_ids),
                        RFIEvidenceLegacy.is_current == True
                    )
                ).group_by(RFIEvidenceLegacy.test_case_id)
            )
            evidence_counts = {row[0]: row[1] for row in evidence_count_result}
        else:
            evidence_counts = {}
        
        # Calculate metrics based on evidence
        total_assigned = len(test_cases)
        
        # Get earliest deadline
        deadlines = [tc.submission_deadline for tc in test_cases if tc.submission_deadline]
        submission_deadline = min(deadlines) if deadlines else None
        
        # Get instructions from first test case's phase
        instructions = None
        if test_cases:
            phase_result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.phase_id == test_cases[0].phase_id
                )
            )
            phase = phase_result.scalar_one_or_none()
            if phase and phase.phase_metadata:
                instructions = phase.phase_metadata.get("instructions", "")
        
        # Get cycle and report information
        cycle_result = await db.execute(
            select(TestCycle).where(TestCycle.cycle_id == test_cases[0].cycle_id) if test_cases else select(TestCycle).where(TestCycle.cycle_id == -1)
        )
        cycle = cycle_result.scalar_one_or_none()
        
        report_result = await db.execute(
            select(Report).where(Report.report_id == test_cases[0].report_id) if test_cases else select(Report).where(Report.report_id == -1)
        )
        report = report_result.scalar_one_or_none()
        
        # Get sample data with primary keys
        sample_ids = [tc.sample_id for tc in test_cases]
        sample_result = await db.execute(
            select(SampleSelectionSample).where(
                SampleSelectionSample.sample_id.in_(sample_ids)
            )
        ) if sample_ids else None
        
        samples = sample_result.scalars().all() if sample_result else []
        # Convert UUID keys to strings for consistent lookup
        sample_map = {str(s.sample_id): s for s in samples}
        
        # Get primary key fields from ReportAttribute
        pk_fields = []
        if report:
            # Query for primary key attributes for this report's planning phase
            from app.models.report_attribute import ReportAttribute
            pk_attributes_query = select(ReportAttribute).where(
                and_(
                    ReportAttribute.phase_id.in_(
                        select(WorkflowPhase.phase_id).where(
                            and_(
                                WorkflowPhase.report_id == report.report_id,
                                WorkflowPhase.phase_name == "Planning"
                            )
                        )
                    ),
                    ReportAttribute.is_primary_key == True
                )
            ).order_by(ReportAttribute.primary_key_order)
            
            pk_result = await db.execute(pk_attributes_query)
            pk_attributes = pk_result.scalars().all()
            pk_fields = [attr.attribute_name for attr in pk_attributes]
            
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Found {len(pk_attributes)} primary key attributes for report {report.report_id}")
            logger.info(f"Primary key fields: {pk_fields}")
            
            # If no primary key fields found, try to get them from test case primary_key_attributes
            if not pk_fields and test_cases:
                # Check if any test case has primary_key_attributes stored
                for tc in test_cases:
                    if hasattr(tc, 'primary_key_attributes') and tc.primary_key_attributes:
                        pk_fields = list(tc.primary_key_attributes.keys())
                        logger.info(f"Using primary key fields from test case: {pk_fields}")
                        break
        
        # Convert to DTOs with details
        test_case_dtos = []
        for tc in test_cases:
            # Get data owner details
            user_result = await db.execute(
                select(User).where(User.user_id == tc.data_owner_id)
            )
            data_owner = user_result.scalar_one()
            
            # Count evidence from TestCaseEvidence table (correct table)
            from sqlalchemy import func
            
            evidence_count_result = await db.execute(
                select(func.count(TestCaseEvidence.id)).where(
                    and_(
                        TestCaseEvidence.test_case_id == tc.id,
                        TestCaseEvidence.is_current == True
                    )
                )
            )
            submission_count = evidence_count_result.scalar() or 0
            
            # Get latest submission time
            latest_submission_result = await db.execute(
                select(func.max(TestCaseEvidence.submitted_at)).where(
                    TestCaseEvidence.test_case_id == tc.id
                )
            )
            latest_submission = latest_submission_result.scalar()
            
            # Check if evidence requires revision
            requires_revision = False
            revision_reason = None
            revision_deadline = None
            
            if submission_count > 0:
                # Check if current evidence requires revision
                revision_check_result = await db.execute(
                    select(TestCaseEvidence).where(
                        and_(
                            TestCaseEvidence.test_case_id == tc.id,
                            TestCaseEvidence.is_current == True,
                            TestCaseEvidence.tester_decision == 'requires_revision'
                        )
                    )
                )
                revision_evidence = revision_check_result.scalar_one_or_none()
                if revision_evidence:
                    requires_revision = True
                    revision_reason = revision_evidence.revision_reason if hasattr(revision_evidence, 'revision_reason') else revision_evidence.tester_notes
                    revision_deadline = revision_evidence.revision_deadline if hasattr(revision_evidence, 'revision_deadline') else revision_evidence.resubmission_deadline
            
            # Use the actual test case status from the database
            # Map 'Not Started' to 'Pending' for API compatibility
            dto_status = tc.status
            if not dto_status or dto_status == 'Not Started':
                dto_status = 'Pending'
            
            # Check if overdue (only if not already submitted/complete)
            if dto_status in ['Pending', 'In Progress'] and tc.submission_deadline and tc.submission_deadline < datetime.now(timezone.utc):
                dto_status = 'Overdue'
            
            # Extract primary key values from sample data
            primary_key_attributes = {}
            sample = sample_map.get(tc.sample_id)
            if sample and sample.sample_data:
                for pk_field in pk_fields:
                    if pk_field in sample.sample_data:
                        primary_key_attributes[pk_field] = sample.sample_data[pk_field]
                
            test_case_dtos.append(TestCaseWithDetailsDTO(
                test_case_id=tc.test_case_id,
                phase_id=str(tc.phase_id),  # Convert to string
                cycle_id=tc.cycle_id,
                report_id=tc.report_id,
                attribute_id=tc.attribute_id,
                sample_id=tc.sample_id,
                sample_identifier=tc.sample_id,  # Using sample_id as identifier
                data_owner_id=tc.data_owner_id,
                assigned_by=tc.assigned_by,
                assigned_at=tc.assigned_at,
                attribute_name=tc.attribute_name,
                primary_key_attributes=primary_key_attributes,  # Now populated from sample data
                expected_evidence_type='Document',  # Default value
                special_instructions=tc.special_instructions,
                status=dto_status,  # Use mapped status
                submission_deadline=tc.submission_deadline if not requires_revision else revision_deadline,
                submitted_at=tc.submitted_at,
                acknowledged_at=tc.acknowledged_at,
                created_at=tc.created_at,
                updated_at=tc.updated_at,
                data_owner_name=f"{data_owner.first_name} {data_owner.last_name}",
                data_owner_email=data_owner.email,
                cycle_name=cycle.cycle_name if cycle else f"Cycle {tc.cycle_id}",
                report_name=report.report_name if report else f"Report {tc.report_id}",
                submission_count=submission_count,
                latest_submission_at=latest_submission,
                requires_revision=requires_revision,
                revision_reason=revision_reason,
                revision_deadline=revision_deadline,
                can_resubmit=True  # Data owners can always resubmit
            ))
        
        # Calculate summary statistics based on actual statuses
        # Count both Submitted and Complete as submitted
        total_submitted = sum(1 for tc in test_case_dtos if tc.status in [TestCaseStatusEnum.SUBMITTED, TestCaseStatusEnum.COMPLETE])
        total_pending = sum(1 for tc in test_case_dtos if tc.status == TestCaseStatusEnum.PENDING)
        total_overdue = sum(1 for tc in test_case_dtos if tc.status == TestCaseStatusEnum.OVERDUE)
        
        # Calculate completion percentage
        completion_percentage = (total_submitted / total_assigned * 100) if total_assigned > 0 else 0.0
        
        # Calculate days remaining
        days_remaining = None
        if submission_deadline:
            time_diff = submission_deadline - datetime.now(timezone.utc)
            days_remaining = time_diff.days
        
        # Get cycle and report names (from first test case if available)
        cycle_name = None
        report_name = None
        if test_case_dtos:
            cycle_name = test_case_dtos[0].cycle_name
            report_name = test_case_dtos[0].report_name
        
        return DataOwnerPortalDataDTO(
            test_cases=test_case_dtos,
            total_assigned=total_assigned,
            total_submitted=total_submitted,
            total_pending=total_pending,
            total_overdue=total_overdue,
            submission_deadline=submission_deadline,
            instructions=instructions,
            # Additional fields for frontend compatibility
            cycle_name=cycle_name,
            report_name=report_name,
            days_remaining=days_remaining,
            total_test_cases=total_assigned,  # Alias
            submitted_test_cases=total_submitted,  # Alias
            pending_test_cases=total_pending,  # Alias
            completion_percentage=completion_percentage
        )


class SubmitDocumentUseCase(UseCase):
    """Submit document for test case"""
    
    async def execute(
        self,
        test_case_id: str,
        file: UploadFile,
        document_type: DocumentTypeEnum,
        submission_notes: Optional[str],
        user_id: int,
        db: AsyncSession
    ) -> FileUploadResponseDTO:
        """Submit document"""
        
        # Verify test case exists and user has access
        # Convert test_case_id string to int for query
        try:
            test_case_id_int = int(test_case_id)
        except ValueError:
            raise ValueError(f"Invalid test case ID format: {test_case_id}")
            
        result = await db.execute(
            select(CycleReportTestCase)
            .options(selectinload(CycleReportTestCase.phase))
            .where(CycleReportTestCase.id == test_case_id_int)
        )
        test_case = result.scalar_one_or_none()
        
        if not test_case:
            raise ValueError(f"Test case {test_case_id} not found")
        
        if test_case.data_owner_id != user_id:
            raise ValueError("You don't have permission to submit documents for this test case")
        
        # Save file
        upload_dir = "uploads/request_info"
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        stored_filename = f"{test_case_id}_{timestamp}{file_extension}"
        file_path = os.path.join(upload_dir, stored_filename)
        
        # Save file to disk
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # No need to create TestCaseEvidence anymore - everything goes in TestCaseEvidence
        
        # Create the main evidence record in TestCaseEvidence
        from sqlalchemy import func, update
        
        # Get the next version number
        max_version_result = await db.execute(
            select(func.max(TestCaseEvidence.version_number)).where(
                TestCaseEvidence.test_case_id == test_case.id
            )
        )
        max_version = max_version_result.scalar() or 0
        next_version = max_version + 1
        
        # Mark existing evidence as not current
        if max_version > 0:
            await db.execute(
                update(TestCaseEvidence)
                .where(
                    and_(
                        TestCaseEvidence.test_case_id == test_case.id,
                        TestCaseEvidence.is_current == True
                    )
                )
                .values(is_current=False)
            )
        
        # Get cycle_id and report_id from phase (since they're properties on test_case)
        if not test_case.phase:
            raise ValueError("Test case is missing phase information")
        
        cycle_id = test_case.phase.cycle_id
        report_id = test_case.phase.report_id
        
        # Create unified evidence record
        evidence = TestCaseEvidence(
            test_case_id=test_case.id,
            phase_id=test_case.phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            sample_id=test_case.sample_id,
            evidence_type="document",
            version_number=next_version,
            is_current=True,
            data_owner_id=user_id,
            submission_notes=submission_notes,
            submission_number=next_version,  # Use version as submission number
            validation_status="pending",
            # Document specific fields
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size_bytes=len(content),
            mime_type=file.content_type or 'application/octet-stream',
            document_type=document_type,
            created_by=user_id,
            updated_by=user_id
        )
        
        # Update test case status to Pending Approval (since "Submitted" is not a valid enum value)
        # This should happen for all cases including revisions (In Progress)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Updating test case {test_case.id} status from '{test_case.status}' to 'Pending Approval'")
        test_case.status = 'Pending Approval'
        
        test_case.submitted_at = datetime.now(timezone.utc)
        test_case.updated_at = datetime.now(timezone.utc)
        test_case.updated_by = user_id
        
        db.add(evidence)
        await db.commit()
        
        return FileUploadResponseDTO(
            submission_id=str(evidence.id),  # Use evidence ID as submission ID
            filename=evidence.original_filename,
            file_size=evidence.file_size_bytes,
            mime_type=evidence.mime_type,
            upload_timestamp=evidence.submitted_at,
            storage_path=evidence.file_path
        )


class ReuploadDocumentUseCase(UseCase):
    """Reupload document (create new revision)"""
    
    async def execute(
        self,
        submission_id: str,
        file: UploadFile,
        revision_notes: Optional[str],
        user_id: int,
        db: AsyncSession
    ) -> FileUploadResponseDTO:
        """Reupload document"""
        
        # Get original submission
        result = await db.execute(
            select(TestCaseEvidence).where(
                TestCaseEvidence.id == int(submission_id)
            )
        )
        original_submission = result.scalar_one_or_none()
        
        if not original_submission:
            raise ValueError(f"Submission {submission_id} not found")
        
        if original_submission.data_owner_id != user_id:
            raise ValueError("You don't have permission to reupload this document")
        
        # Save new file
        upload_dir = "uploads/request_info"
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        stored_filename = f"{original_submission.test_case_id}_{timestamp}_rev{original_submission.revision_number + 1}{file_extension}"
        file_path = os.path.join(upload_dir, stored_filename)
        
        # Save file to disk
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Mark original submission as not current
        original_submission.is_current = False
        
        # Create new submission with incremented revision
        new_submission = TestCaseEvidence(
            phase_id=original_submission.phase_id,  # Copy phase_id from original
            cycle_id=original_submission.cycle_id,
            report_id=original_submission.report_id,
            test_case_id=original_submission.test_case_id,
            sample_id=original_submission.sample_id,
            evidence_type="document",
            version_number=original_submission.version_number + 1,
            is_current=True,
            parent_evidence_id=original_submission.id,
            data_owner_id=user_id,     # The user submitting the document
            submission_notes=revision_notes or original_submission.submission_notes,
            submission_number=original_submission.submission_number + 1,
            is_revision=True,
            revision_requested_by=original_submission.revision_requested_by,
            revision_requested_at=original_submission.revision_requested_at,
            revision_reason=original_submission.revision_reason,
            validation_status="pending",
            # Document specific fields
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size_bytes=len(content),
            file_hash=None,  # Could compute hash if needed
            mime_type=file.content_type or 'application/octet-stream',
            document_type=original_submission.document_type,
            created_by=user_id,
            updated_by=user_id
        )
        
        db.add(new_submission)
        await db.commit()
        
        return FileUploadResponseDTO(
            submission_id=str(new_submission.id),
            filename=new_submission.original_filename,
            file_size=new_submission.file_size_bytes,
            mime_type=new_submission.mime_type,
            upload_timestamp=new_submission.submitted_at,
            storage_path=new_submission.file_path
        )


class GetRequestInfoPhaseStatusUseCase(UseCase):
    """Get request info phase status"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> RequestInfoPhaseStatusDTO:
        """Get phase status"""
        
        # Get phase
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request Info"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            # Return default status
            return RequestInfoPhaseStatusDTO(
                phase_id="",
                cycle_id=cycle_id,
                report_id=report_id,
                phase_status="Not Started",
                total_test_cases=0,
                submitted_test_cases=0,
                pending_test_cases=0,
                overdue_test_cases=0,
                data_owners_notified=0,
                total_submissions=0,
                can_complete=False,
                completion_requirements=["Phase not started"]
            )
        
        # Get test case statistics
        stats = await db.execute(
            select(
                func.count(CycleReportTestCase.id).label('total'),
                func.sum(case((CycleReportTestCase.status == 'Complete', 1), else_=0)).label('submitted'),
                func.sum(case((CycleReportTestCase.status == 'Not Started', 1), else_=0)).label('pending'),
                func.sum(case((CycleReportTestCase.status == 'In Progress', 1), else_=0)).label('overdue')
            ).where(
                CycleReportTestCase.phase_id == phase.phase_id
            )
        )
        stats_row = stats.first()
        
        # Get data owner count from document submissions
        owner_count = await db.execute(
            select(func.count(func.distinct(TestCaseEvidence.data_owner_id)))
            .join(CycleReportTestCase, TestCaseEvidence.test_case_id == CycleReportTestCase.id)
            .where(
                and_(
                    CycleReportTestCase.phase_id == phase.phase_id,
                    TestCaseEvidence.data_owner_id.isnot(None)
                )
            )
        )
        data_owners = owner_count.scalar() or 0
        
        # Get submission count
        submission_count = await db.execute(
            select(func.count(TestCaseEvidence.id))
            .join(CycleReportTestCase, TestCaseEvidence.test_case_id == CycleReportTestCase.id)
            .where(
                and_(
                    CycleReportTestCase.phase_id == phase.phase_id,
                    TestCaseEvidence.is_current == True
                )
            )
        )
        submissions = submission_count.scalar() or 0
        
        # Get additional statistics for frontend
        from app.models.report_attribute import ReportAttribute
        from app.models.report import Report
        from app.models.cycle_report import CycleReport
        
        # Total attributes - need to join through WorkflowPhase
        attr_count = await db.execute(
            select(func.count(ReportAttribute.id))
            .join(
                WorkflowPhase,
                ReportAttribute.phase_id == WorkflowPhase.phase_id
            )
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning",
                    ReportAttribute.is_active == True
                )
            )
        )
        total_attributes = attr_count.scalar() or 0
        
        # Scoped attributes - need to join through WorkflowPhase
        scoped_attr_count = await db.execute(
            select(func.count(ReportAttribute.id))
            .join(
                WorkflowPhase,
                ReportAttribute.phase_id == WorkflowPhase.phase_id
            )
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning",
                    ReportAttribute.is_active == True,
                    ReportAttribute.is_scoped == True
                )
            )
        )
        scoped_attributes = scoped_attr_count.scalar() or 0
        
        # Total samples (count unique samples used in test cases for this phase)
        sample_count = await db.execute(
            select(func.count(func.distinct(CycleReportTestCase.sample_id)))
            .where(
                CycleReportTestCase.phase_id == phase.phase_id
            )
        )
        total_samples = sample_count.scalar() or 0
        
        # Total LOBs
        lob_count = await db.execute(
            select(func.count(func.distinct(Report.lob_id)))
            .join(CycleReport)
            .where(
                and_(
                    CycleReport.cycle_id == cycle_id,
                    CycleReport.report_id == report_id
                )
            )
        )
        total_lobs = lob_count.scalar() or 0
        
        # Get workflow phase start date
        workflow_phase = await db.execute(
            select(WorkflowPhase)
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request Info"
                )
            )
        )
        wf_phase = workflow_phase.scalar_one_or_none()
        started_at = wf_phase.actual_start_date if wf_phase else None
        
        # Handle None values from SQL aggregation functions
        total_cases = stats_row.total or 0
        pending_cases = stats_row.pending or 0
        overdue_cases = stats_row.overdue or 0
        
        # Determine if phase can be completed
        can_complete = (
            total_cases > 0 and
            pending_cases == 0 and
            overdue_cases == 0
        )
        
        completion_requirements = []
        if pending_cases > 0:
            completion_requirements.append(f"Submit {pending_cases} pending test cases")
        if overdue_cases > 0:
            completion_requirements.append(f"Resolve {overdue_cases} overdue test cases")
        if total_cases == 0:
            completion_requirements.append("Create test cases for data collection")
        
        if not completion_requirements:
            completion_requirements.append("All requirements met - ready to complete phase")
        
        return RequestInfoPhaseStatusDTO(
            phase_id=str(phase.phase_id),
            cycle_id=cycle_id,
            report_id=report_id,
            phase_status=phase.status,
            total_test_cases=stats_row.total or 0,
            submitted_test_cases=stats_row.submitted or 0,
            pending_test_cases=stats_row.pending or 0,
            overdue_test_cases=stats_row.overdue or 0,
            data_owners_notified=data_owners,
            total_submissions=submissions,
            can_complete=can_complete,
            completion_requirements=completion_requirements,
            # Additional statistics
            total_attributes=total_attributes,
            scoped_attributes=scoped_attributes,
            total_samples=total_samples,
            total_lobs=total_lobs,
            total_data_providers=data_owners,  # Use data_owners as total_data_providers
            uploaded_test_cases=stats_row.submitted or 0,  # Same as submitted_test_cases
            started_at=started_at
        )


class CompleteRequestInfoPhaseUseCase(UseCase):
    """Complete request info phase"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        completion_data: PhaseCompletionRequestDTO,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Complete phase"""
        
        # Get phase
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request Info"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            raise ValueError("Request Info phase not found")
        
        if phase.status == "Complete":
            raise ValueError("Phase is already complete")
        
        # Check completion requirements
        if not completion_data.override_checks:
            status_use_case = GetRequestInfoPhaseStatusUseCase()
            status = await status_use_case.execute(cycle_id, report_id, db)
            
            if not status.can_complete:
                raise ValueError(
                    f"Cannot complete phase: {', '.join(status.completion_requirements)}"
                )
        
        # Update phase status
        phase.status = "Complete"
        phase.completed_by = user_id
        phase.completed_at = datetime.now(timezone.utc)
        phase.updated_at = datetime.now(timezone.utc)
        phase.updated_by_id = user_id
        
        # Update workflow phase
        workflow_orchestrator = await get_workflow_orchestrator(db)
        await workflow_orchestrator.update_phase_state(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name="Request Info",
            new_state="Complete",
            notes=completion_data.completion_notes,
            user_id=user_id
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Request for Information phase completed successfully",
            "phase_id": phase.phase_id,
            "completed_at": phase.completed_at
        }


class ResendCycleReportTestCaseUseCase(UseCase):
    """Resend test case to data owner"""
    
    async def execute(
        self,
        test_case_id: str,
        resend_data: ResendTestCaseRequestDTO,
        user_id: int,
        db: AsyncSession
    ) -> TestCaseResponseDTO:
        """Resend test case"""
        
        # Get test case - convert string ID to int
        test_case_id_int = int(test_case_id)
        result = await db.execute(
            select(CycleReportTestCase)
            .options(selectinload(CycleReportTestCase.phase))
            .where(CycleReportTestCase.id == test_case_id_int)
        )
        test_case = result.scalar_one_or_none()
        
        if not test_case:
            raise ValueError(f"Test case {test_case_id} not found")
        
        # Update test case
        test_case.status = 'In Progress'  # Update status instead of assignment_status
        test_case.submitted_at = None
        
        if resend_data.additional_instructions:
            if test_case.special_instructions:
                test_case.special_instructions += f"\n\nRESENT: {resend_data.additional_instructions}"
            else:
                test_case.special_instructions = f"RESENT: {resend_data.additional_instructions}"
        
        if resend_data.new_deadline:
            test_case.submission_deadline = resend_data.new_deadline
        
        test_case.updated_at = datetime.now(timezone.utc)
        test_case.updated_by = user_id
        
        # Mark existing evidence as requiring revision
        # This handles both document and data source evidence types
        if resend_data.invalidate_previous:
            logger.warning(f"🚨🚨🚨 SETTING REQUIRES_REVISION for test case {test_case_id_int}")
            logger.warning(f"🚨🚨🚨 Called by user {user_id} with reason: {resend_data.reason}")
            logger.warning(f"🚨🚨🚨 This is from resend_to_data_owner function")
            
            # Build the where clause based on evidence type filter
            where_conditions = [
                TestCaseEvidence.test_case_id == test_case_id_int,
                TestCaseEvidence.is_current == True
            ]
            
            # Add evidence type filter if specified
            if resend_data.evidence_type:
                where_conditions.append(TestCaseEvidence.evidence_type == resend_data.evidence_type)
            
            result = await db.execute(
                update(TestCaseEvidence)
                .where(and_(*where_conditions))
                .values(
                    is_revision=True,
                    revision_requested_by=user_id,
                    revision_requested_at=datetime.now(timezone.utc),
                    revision_reason=resend_data.reason,  # Use the reason field
                    revision_deadline=resend_data.new_deadline if resend_data.new_deadline else None,
                    requires_resubmission=True,
                    resubmission_deadline=resend_data.new_deadline if resend_data.new_deadline else None,
                    tester_decision='requires_revision',
                    tester_notes=f"Revision requested: {resend_data.additional_instructions}" if resend_data.additional_instructions else f"Revision requested: {resend_data.reason}",
                    decided_by=user_id,
                    decided_at=datetime.now(timezone.utc)
                )
            )
            logger.warning(f"🚨🚨🚨 Updated {result.rowcount} evidence records to requires_revision")
        
        # TODO: Send notification to data owner
        
        await db.commit()
        await db.refresh(test_case)
        
        return TestCaseResponseDTO(
            test_case_id=test_case.test_case_id,
            phase_id=str(test_case.phase_id) if test_case.phase_id else None,
            cycle_id=test_case.cycle_id,
            report_id=test_case.report_id,
            attribute_id=test_case.attribute_id,
            sample_id=test_case.sample_id,
            sample_identifier=test_case.sample_identifier,
            data_owner_id=test_case.data_owner_id,
            assigned_by=test_case.assigned_by,
            assigned_at=test_case.assigned_at,
            attribute_name=test_case.attribute_name,
            primary_key_attributes=test_case.primary_key_attributes,
            expected_evidence_type=test_case.expected_evidence_type,
            special_instructions=test_case.special_instructions,
            status=TestCaseStatusEnum(test_case.status) if test_case.status else TestCaseStatusEnum.Pending,
            submission_deadline=test_case.submission_deadline,
            submitted_at=test_case.submitted_at,
            acknowledged_at=test_case.acknowledged_at,
            created_at=test_case.created_at,
            updated_at=test_case.updated_at
        )


class GetPhaseProgressSummaryUseCase(UseCase):
    """Get phase progress summary"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> PhaseProgressSummaryDTO:
        """Get progress summary"""
        
        # Get attribute count - need to join through WorkflowPhase
        from app.models.report_attribute import ReportAttribute
        attr_count = await db.execute(
            select(func.count(ReportAttribute.id))
            .join(
                WorkflowPhase,
                ReportAttribute.phase_id == WorkflowPhase.phase_id
            )
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning"
                )
            )
        )
        total_attributes = attr_count.scalar() or 0
        
        # Get test case statistics
        stats = await db.execute(
            select(
                func.count(CycleReportTestCase.id).label('total'),
                CycleReportTestCase.status,
                func.count(func.distinct(TestCaseEvidence.data_owner_id)).label('owners')
            ).select_from(CycleReportTestCase)
            .join(
                WorkflowPhase, 
                CycleReportTestCase.phase_id == WorkflowPhase.phase_id
            )
            .outerjoin(
                TestCaseEvidence, 
                TestCaseEvidence.test_case_id == CycleReportTestCase.id
            )
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request Info"
                )
            ).group_by(CycleReportTestCase.status)
        )
        
        total_test_cases = 0
        test_cases_by_status = {}
        data_owners_assigned = 0
        
        for row in stats:
            total_test_cases += row.total
            test_cases_by_status[row.status] = row.total
            if data_owners_assigned < row.owners:
                data_owners_assigned = row.owners
        
        # Get data owners who have responded (made submissions)
        responded = await db.execute(
            select(func.count(func.distinct(TestCaseEvidence.data_owner_id)))
            .join(CycleReportTestCase, TestCaseEvidence.test_case_id == CycleReportTestCase.id)
            .join(WorkflowPhase, CycleReportTestCase.phase_id == WorkflowPhase.phase_id)
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    TestCaseEvidence.data_owner_id.isnot(None)
                )
            )
        )
        data_owners_responded = responded.scalar() or 0
        
        # Calculate average response time
        response_time = await db.execute(
            select(
                func.avg(
                    func.extract('epoch', TestCaseEvidence.submitted_at - CycleReportTestCase.created_at) / 3600
                ).label('avg_hours')
            ).select_from(TestCaseEvidence)
            .join(CycleReportTestCase, TestCaseEvidence.test_case_id == CycleReportTestCase.id)
            .join(WorkflowPhase, CycleReportTestCase.phase_id == WorkflowPhase.phase_id)
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    TestCaseEvidence.submitted_at.isnot(None)
                )
            )
        )
        avg_response_hours = response_time.scalar()
        
        # Calculate completion percentage
        completion_percentage = (
            (test_cases_by_status.get('completed', 0) / total_test_cases * 100)
            if total_test_cases > 0 else 0
        )
        
        return PhaseProgressSummaryDTO(
            total_attributes=total_attributes,
            total_test_cases=total_test_cases,
            test_cases_by_status=test_cases_by_status,
            data_owners_assigned=data_owners_assigned,
            data_owners_responded=data_owners_responded,
            average_response_time_hours=avg_response_hours,
            completion_percentage=completion_percentage
        )


class GetDataOwnerAssignmentSummaryUseCase(UseCase):
    """Get data owner assignment summary"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> List[DataOwnerAssignmentSummaryDTO]:
        """Get assignment summary by data owner"""
        
        # Get data owners with assignments
        result = await db.execute(
            select(
                TestCaseEvidence.data_owner_id,
                User.first_name,
                User.last_name,
                User.email,
                func.count(CycleReportTestCase.id).label('total'),
                func.sum(case((CycleReportTestCase.status == 'Complete', 1), else_=0)).label('submitted'),
                func.sum(case((CycleReportTestCase.status == 'Not Started', 1), else_=0)).label('pending'),
                func.sum(case((CycleReportTestCase.status == 'In Progress', 1), else_=0)).label('overdue'),
                func.max(TestCaseEvidence.submitted_at).label('last_submission')
            )
            .select_from(TestCaseEvidence)
            .join(CycleReportTestCase, TestCaseEvidence.test_case_id == CycleReportTestCase.id)
            .join(WorkflowPhase, CycleReportTestCase.phase_id == WorkflowPhase.phase_id)
            .join(User, TestCaseEvidence.data_owner_id == User.user_id)
            .where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    TestCaseEvidence.data_owner_id.isnot(None)
                )
            )
            .group_by(
                TestCaseEvidence.data_owner_id,
                User.first_name,
                User.last_name,
                User.email
            )
        )
        
        summaries = []
        
        for row in result:
            # Calculate average submission time for this data owner
            avg_time_result = await db.execute(
                select(
                    func.avg(
                        func.extract('epoch', TestCaseEvidence.submitted_at - CycleReportTestCase.created_at) / 3600
                    ).label('avg_hours')
                ).select_from(TestCaseEvidence)
                .join(CycleReportTestCase, TestCaseEvidence.test_case_id == CycleReportTestCase.id)
                .join(WorkflowPhase, CycleReportTestCase.phase_id == WorkflowPhase.phase_id)
                .where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        TestCaseEvidence.data_owner_id == row.data_owner_id,
                        TestCaseEvidence.submitted_at.isnot(None)
                    )
                )
            )
            avg_submission_hours = avg_time_result.scalar()
            
            summaries.append(DataOwnerAssignmentSummaryDTO(
                data_owner_id=row.data_owner_id,
                data_owner_name=f"{row.first_name} {row.last_name}",
                data_owner_email=row.email,
                assigned_test_cases=row.total,
                submitted_test_cases=row.submitted or 0,
                pending_test_cases=row.pending or 0,
                overdue_test_cases=row.overdue or 0,
                last_submission_at=row.last_submission,
                average_submission_time_hours=avg_submission_hours
            ))
        
        return summaries