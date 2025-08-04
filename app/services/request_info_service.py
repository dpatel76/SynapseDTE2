"""
Request for Information phase service
"""

import os
import uuid
import shutil
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import and_, or_, func, case, desc, select, cast, String, literal_column, update
from fastapi import HTTPException, UploadFile
import mimetypes

logger = logging.getLogger(__name__)

from app.models.request_info import (
    CycleReportTestCase,
    DataProviderNotification, RequestInfoAuditLog,
    TestCaseEvidence, RFIDataSource, RFIQueryValidation
)
from app.models.workflow import WorkflowPhase
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.report_attribute import ReportAttribute
from app.models.sample_selection import SampleSelectionVersion, SampleSelectionSample
from app.models.scoping import ScopingVersion, ScopingAttribute
from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeVersion, DataOwnerLOBAttributeMapping
from app.models.user import User
from app.schemas.request_info import (
    RequestInfoPhaseCreate, RequestInfoPhaseUpdate, RequestInfoPhaseResponse,
    TestCaseCreate, TestCaseResponse, TestCaseWithDetails,
    DocumentSubmissionCreate, DocumentSubmissionResponse,
    DataProviderNotificationCreate, DataProviderNotificationResponse,
    StartPhaseRequest, PhaseProgressSummary, DataProviderAssignmentSummary,
    TesterPhaseView, DataProviderPortalData, FileUploadResponse,
    PhaseCompletionRequest, TestCaseListResponse,
    QueryValidationRequest, QueryValidationResult, DataSourceCreateRequest,
    DataSourceResponse, SaveQueryRequest, QueryExecutionRequest
)


def convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj


class RequestInfoService:
    """Service for managing Request for Information phase"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.upload_dir = "uploads/request_info"
        self._ensure_upload_directory()
    
    def _ensure_upload_directory(self):
        """Ensure upload directory exists"""
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def _log_audit(self, action: str, entity_type: str, entity_id: str, 
                   user_id: int, cycle_id: int, report_id: int, 
                   phase_id: Optional[str] = None, old_values: Optional[Dict] = None, 
                   new_values: Optional[Dict] = None, notes: Optional[str] = None):
        """Log audit trail"""
        audit_log = RequestInfoAuditLog(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_id=phase_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=user_id,
            old_values=old_values,
            new_values=new_values,
            notes=notes
        )
        self.db.add(audit_log)
    
    # Phase Management
    async def create_phase(self, phase_data: RequestInfoPhaseCreate, user_id: int) -> RequestInfoPhaseResponse:
        """Create a new Request for Information phase"""
        
        # Validate cycle and report exist
        cycle_result = await self.db.execute(
            select(TestCycle).where(TestCycle.cycle_id == phase_data.cycle_id)
        )
        cycle = cycle_result.scalar_one_or_none()
        if not cycle:
            raise HTTPException(status_code=404, detail="Test cycle not found")
        
        report_result = await self.db.execute(
            select(Report).where(Report.report_id == phase_data.report_id)
        )
        report = report_result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Check if phase already exists for this cycle/report
        existing_phase_result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == phase_data.cycle_id,
                    WorkflowPhase.report_id == phase_data.report_id,
                    WorkflowPhase.phase_name == "Request for Information"
                )
            )
        )
        existing_phase = existing_phase_result.scalar_one_or_none()
        
        if existing_phase:
            raise HTTPException(
                status_code=400, 
                detail="Request for Information phase already exists for this cycle and report"
            )
        
        # Create phase
        phase = WorkflowPhase(
            cycle_id=phase_data.cycle_id,
            report_id=phase_data.report_id,
            phase_name=phase_data.phase_name,
            instructions=phase_data.instructions,
            auto_notify_data_owners=phase_data.auto_notify_data_owners,
            require_all_submissions=phase_data.require_all_submissions,
            submission_deadline=phase_data.submission_deadline
        )
        
        self.db.add(phase)
        await self.db.commit()
        await self.db.refresh(phase)
        
        # Log audit
        self._log_audit(
            action="CREATE_PHASE",
            entity_type="WorkflowPhase",
            entity_id=phase.phase_id,
            user_id=user_id,
            cycle_id=phase_data.cycle_id,
            report_id=phase_data.report_id,
            phase_id=phase.phase_id,
            notes="Created Request for Information phase"
        )
        
        return RequestInfoPhaseResponse.from_orm(phase)
    
    async def start_phase(self, phase_id: str, start_request: StartPhaseRequest, user_id: int) -> RequestInfoPhaseResponse:
        """Start the Request for Information phase"""
        
        phase_result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.phase_id == phase_id,
                    WorkflowPhase.phase_name == "Request for Information"
                )
            )
        )
        phase = phase_result.scalar_one_or_none()
        if not phase:
            raise HTTPException(status_code=404, detail="Phase not found")
        
        if phase.status != "Not Started":
            raise HTTPException(status_code=400, detail="Phase has already been started")
        
        # Update phase - NOTE: Test cases are now created via the "Create Test Cases" activity
        phase.status = "In Progress"
        phase.started_by = user_id
        phase.started_at = datetime.now(timezone.utc)
        phase.instructions = start_request.instructions or phase.instructions
        phase.submission_deadline = start_request.submission_deadline
        # Don't set total_test_cases here - it will be set when test cases are created
        
        await self.db.commit()
        
        # Send notifications if requested
        if start_request.auto_notify_data_owners and start_request.notify_immediately:
            await self._send_data_owner_notifications(phase)
        
        # Log audit
        self._log_audit(
            action="START_PHASE",
            entity_type="WorkflowPhase",
            entity_id=phase.phase_id,
            user_id=user_id,
            cycle_id=phase.cycle_id,
            report_id=phase.report_id,
            phase_id=phase.phase_id,
            notes="Started Request Info phase"
        )
        
        return RequestInfoPhaseResponse.from_orm(phase)
    
    async def _generate_test_cases(self, phase: WorkflowPhase, user_id: int) -> int:
        """Generate test cases from Sample X non-PK Attribute matrix
        
        Flow:
        1. Get approved samples from sample selection phase (approved version)
        2. Get scoped non-PK attributes approved during scoping (approved version)
        3. Get data owner assignments from Data Owner LOB Assignment
        4. Create one test case for each sample + non-PK attribute combination
        """
        
        # 1. Get the approved/active sample selection version
        sample_version_result = await self.db.execute(
            select(SampleSelectionVersion).where(
                and_(
                    SampleSelectionVersion.phase_id == select(WorkflowPhase.phase_id).where(
                        and_(
                            WorkflowPhase.cycle_id == phase.cycle_id,
                            WorkflowPhase.report_id == phase.report_id,
                            WorkflowPhase.phase_name == "Sample Selection"
                        )
                    ).scalar_subquery(),
                    cast(SampleSelectionVersion.version_status, String).in_(['approved', 'pending_approval'])
                )
            ).order_by(SampleSelectionVersion.version_number.desc())
        )
        sample_version = sample_version_result.scalar_one_or_none()
        
        if not sample_version:
            raise HTTPException(
                status_code=400,
                detail="No approved sample selection version found"
            )
        
        # Get approved samples from the version
        approved_samples_result = await self.db.execute(
            select(SampleSelectionSample).where(
                and_(
                    SampleSelectionSample.version_id == sample_version.version_id,
                    SampleSelectionSample.report_owner_decision == 'approved'
                )
            )
        )
        approved_samples = approved_samples_result.scalars().all()
        logger.info(f"Found {len(approved_samples)} approved samples")
        
        if not approved_samples:
            raise HTTPException(
                status_code=400,
                detail="No approved samples found in sample selection"
            )
        
        # 2. Get the approved/active scoping version
        scoping_version_result = await self.db.execute(
            select(ScopingVersion).where(
                and_(
                    ScopingVersion.phase_id == select(WorkflowPhase.phase_id).where(
                        and_(
                            WorkflowPhase.cycle_id == phase.cycle_id,
                            WorkflowPhase.report_id == phase.report_id,
                            WorkflowPhase.phase_name == "Scoping"
                        )
                    ).scalar_subquery(),
                    literal_column("cycle_report_scoping_versions.version_status::text").in_(['approved', 'pending_approval'])
                )
            ).order_by(ScopingVersion.version_number.desc())
        )
        scoping_version = scoping_version_result.scalar_one_or_none()
        
        if not scoping_version:
            raise HTTPException(
                status_code=400,
                detail="No approved scoping version found"
            )
        
        # Get approved non-PK attributes from the version
        from app.models.report_attribute import ReportAttribute
        scoped_attrs_result = await self.db.execute(
            select(ScopingAttribute)
            .join(
                ReportAttribute,
                ScopingAttribute.planning_attribute_id == ReportAttribute.id
            )
            .where(
                and_(
                    ScopingAttribute.version_id == scoping_version.version_id,
                    ScopingAttribute.report_owner_decision == 'approved',
                    ScopingAttribute.final_scoping == True,
                    ReportAttribute.is_primary_key == False
                )
            )
        )
        scoped_non_pk_attrs = scoped_attrs_result.scalars().all()
        logger.info(f"Found {len(scoped_non_pk_attrs)} approved non-PK attributes")
        
        if not scoped_non_pk_attrs:
            raise HTTPException(
                status_code=400,
                detail="No approved non-PK attributes found in scoping"
            )
        
        # 3. Get the active data owner LOB assignment version
        data_owner_version_result = await self.db.execute(
            select(DataOwnerLOBAttributeVersion).where(
                and_(
                    DataOwnerLOBAttributeVersion.phase_id == select(WorkflowPhase.phase_id).where(
                        and_(
                            WorkflowPhase.cycle_id == phase.cycle_id,
                            WorkflowPhase.report_id == phase.report_id,
                            WorkflowPhase.phase_name == "Data Provider ID"
                        )
                    ).scalar_subquery(),
                    DataOwnerLOBAttributeVersion.version_status == 'active'
                )
            ).order_by(DataOwnerLOBAttributeVersion.version_number.desc())
        )
        data_owner_version = data_owner_version_result.scalar_one_or_none()
        logger.info(f"Data owner version found: {data_owner_version is not None}")
        
        # Get primary key attributes for context
        pk_attrs_result = await self.db.execute(
            select(ScopingAttribute)
            .join(
                ReportAttribute,
                ScopingAttribute.planning_attribute_id == ReportAttribute.id
            )
            .where(
                and_(
                    ScopingAttribute.version_id == scoping_version.version_id,
                    ReportAttribute.is_primary_key == True
                )
            )
        )
        pk_attributes = pk_attrs_result.scalars().all()
        
        test_cases_created = 0
        test_case_number = 1
        
        # 4. Create test cases: one per sample + non-PK attribute combination
        logger.info(f"Starting test case creation: {len(approved_samples)} samples x {len(scoped_non_pk_attrs)} attributes")
        for sample in approved_samples:
            # Get LOB from sample
            lob_id = sample.lob_id
            logger.info(f"Processing sample {sample.sample_id} with LOB {lob_id}")
            if not lob_id:
                continue
            
            for attr in scoped_non_pk_attrs:
                logger.info(f"  Processing attribute {attr.planning_attribute_id}")
                # Get data owner assignment for this attribute/LOB combination
                data_owner_id = None
                
                # First try with version if available
                if data_owner_version:
                    assignment_result = await self.db.execute(
                        select(DataOwnerLOBAttributeMapping).where(
                            and_(
                                DataOwnerLOBAttributeMapping.version_id == data_owner_version.version_id,
                                DataOwnerLOBAttributeMapping.attribute_id == attr.planning_attribute_id,
                                DataOwnerLOBAttributeMapping.lob_id == lob_id,
                                DataOwnerLOBAttributeMapping.assignment_status == 'assigned'
                            )
                        )
                    )
                    assignment = assignment_result.scalar_one_or_none()
                    if assignment:
                        data_owner_id = assignment.data_owner_id
                        logger.info(f"    Found data owner assignment (with version): {data_owner_id}")
                
                # If no version or no assignment found with version, try without version
                if not data_owner_id:
                    # Get Data Provider ID phase_id for this cycle/report
                    data_provider_phase_result = await self.db.execute(
                        select(WorkflowPhase.phase_id).where(
                            and_(
                                WorkflowPhase.cycle_id == phase.cycle_id,
                                WorkflowPhase.report_id == phase.report_id,
                                WorkflowPhase.phase_order < phase.phase_order,  # Data Provider ID comes before Request Info
                                WorkflowPhase.phase_name == 'Data Provider ID'  # Exact match for enum
                            )
                        )
                    )
                    data_provider_phase_id = data_provider_phase_result.scalar_one_or_none()
                    logger.info(f"    Data Provider ID phase_id: {data_provider_phase_id}")
                    
                    if data_provider_phase_id:
                        assignment_result = await self.db.execute(
                            select(DataOwnerLOBAttributeMapping).where(
                                and_(
                                    DataOwnerLOBAttributeMapping.phase_id == data_provider_phase_id,
                                    DataOwnerLOBAttributeMapping.attribute_id == attr.planning_attribute_id,
                                    DataOwnerLOBAttributeMapping.lob_id == lob_id,
                                    DataOwnerLOBAttributeMapping.assignment_status == 'assigned'
                                )
                            )
                        )
                        assignment = assignment_result.scalar_one_or_none()
                        if assignment:
                            data_owner_id = assignment.data_owner_id
                            logger.info(f"    Found data owner assignment (without version): {data_owner_id}")
                        else:
                            logger.info(f"    No data owner assignment found for attribute {attr.planning_attribute_id} and LOB {lob_id}")
                
                if not data_owner_id:
                    # If no data owner assigned yet, create test case without assignment
                    logger.info(f"    No data owner assigned - creating unassigned test case")
                    data_owner_id = None
                
                # Build primary key context for this sample
                pk_context = {}
                sample_data = sample.sample_data or {}
                for pk_attr in pk_attributes:
                    # Get the attribute name from planning attributes
                    attr_name_result = await self.db.execute(
                        select(ReportAttribute.attribute_name).where(
                            ReportAttribute.attribute_id == pk_attr.planning_attribute_id
                        )
                    )
                    attr_name = attr_name_result.scalar_one_or_none()
                    if attr_name:
                        pk_context[attr_name] = sample_data.get(attr_name, "N/A")
                
                # Get attribute name from planning attributes table
                from app.models.planning import ReportAttribute as PlanningAttribute
                attr_name_result = await self.db.execute(
                    select(PlanningAttribute.attribute_name).where(
                        PlanningAttribute.id == attr.planning_attribute_id
                    )
                )
                attribute_name = attr_name_result.scalar_one_or_none() or "Unknown"
                
                test_case = CycleReportTestCase(
                    test_case_number=f"TC-{phase.cycle_id}-{phase.report_id}-{test_case_number:04d}",
                    test_case_name=f"Evidence for {attribute_name} - Sample {sample.sample_id}",
                    phase_id=phase.phase_id,
                    # cycle_id and report_id are computed properties from phase
                    attribute_id=attr.planning_attribute_id,
                    sample_id=str(sample.sample_id),  # Convert UUID to string
                    # sample_identifier and primary_key_attributes are properties
                    lob_id=lob_id,
                    data_owner_id=data_owner_id,
                    assigned_by=user_id,
                    assigned_at=datetime.now(timezone.utc),
                    attribute_name=attribute_name,
                    submission_deadline=phase.sla_deadline,
                    # expected_evidence_type="Document",
                    special_instructions=f"Please provide evidence for {attribute_name} for the sample identified by: {', '.join([f'{k}: {v}' for k, v in pk_context.items()])}"
                )
                
                self.db.add(test_case)
                test_cases_created += 1
                test_case_number += 1
        
        await self.db.commit()
        return test_cases_created
    
    async def _create_test_cases_for_phase(self, cycle_id: int, report_id: int, user_id: int) -> dict:
        """Create test cases for the Request Info phase - called by Create Test Cases activity
        
        This method is called when the "Create Test Cases" activity is executed, 
        NOT when the phase is started.
        """
        
        # Get the phase
        phase_result = await self.db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request Info"
                )
            )
        )
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            return {"success": False, "error": "Request Info phase not found"}
        
        if phase.state != "In Progress":
            return {"success": False, "error": "Request Info phase must be started first"}
        
        # Check if test cases already exist
        existing_count_result = await self.db.execute(
            select(func.count(CycleReportTestCase.id)).where(
                CycleReportTestCase.phase_id == phase.phase_id
            )
        )
        existing_count = existing_count_result.scalar()
        
        if existing_count > 0:
            return {"success": True, "count": existing_count, "message": "Test cases already exist"}
        
        # Generate test cases
        try:
            test_cases_created = await self._generate_test_cases(phase, user_id)
            
            # Update phase with test case count
            phase.total_test_cases = test_cases_created
            phase.updated_at = datetime.utcnow()
            phase.updated_by_id = user_id
            
            await self.db.commit()
            
            # Log audit - temporarily disabled due to schema mismatch
            # self._log_audit(
            #     action="CREATE_TEST_CASES",
            #     entity_type="WorkflowPhase",
            #     entity_id=phase.phase_id,
            #     phase_id=phase.phase_id,
            #     user_id=user_id,
            #     cycle_id=cycle_id,
            #     report_id=report_id,
            #     new_values={
            #         "test_cases_created": test_cases_created
            #     }
            # )
            
            return {
                "success": True, 
                "count": test_cases_created,
                "message": f"Successfully created {test_cases_created} test cases"
            }
            
        except Exception as e:
            logger.error(f"Error creating test cases: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _send_data_owner_notifications(self, phase: WorkflowPhase):
        """Send notifications to data providers"""
        
        # Get unique data providers and their assignments
        data_owners_result = await self.db.execute(
            select(
                CycleReportTestCase.data_owner_id,
                func.array_agg(CycleReportTestCase.attribute_name.distinct()).label('attributes'),
                func.count(CycleReportTestCase.test_case_id).label('test_case_count')
            ).where(
                CycleReportTestCase.phase_id == phase.phase_id
            ).group_by(CycleReportTestCase.data_owner_id)
        )
        data_owners = data_owners_result.all()
        
        for dp_id, attributes, test_case_count in data_owners:
            # Create notification
            notification = DataProviderNotification(
                phase_id=phase.phase_id,
                cycle_id=phase.cycle_id,
                report_id=phase.report_id,
                data_owner_id=dp_id,
                assigned_attributes=attributes,
                sample_count=test_case_count,
                submission_deadline=phase.submission_deadline,
                portal_access_url=f"/data-owner/request-info/{phase.phase_id}",
                custom_instructions=phase.instructions
            )
            
            self.db.add(notification)
        
        await self.db.commit()
    
    def get_phase(self, phase_id: str) -> RequestInfoPhaseResponse:
        """Get phase details"""
        phase = self.db.query(WorkflowPhase).filter(WorkflowPhase.phase_id == phase_id).first()
        if not phase:
            raise HTTPException(status_code=404, detail="Phase not found")
        
        return RequestInfoPhaseResponse.from_orm(phase)
    
    def get_tester_phase_view(self, phase_id: str, user_id: int) -> TesterPhaseView:
        """Get comprehensive phase view for testers"""
        
        phase = self.db.query(WorkflowPhase).options(
            selectinload(WorkflowPhase.cycle),
            selectinload(WorkflowPhase.report)
        ).filter(WorkflowPhase.phase_id == phase_id).first()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Phase not found")
        
        # Get progress summary
        progress_summary = self._get_phase_progress_summary(phase)
        
        # Get data provider summaries
        data_owner_summaries = self._get_data_owner_summaries(phase_id)
        
        # Get recent submissions
        recent_submissions = self.db.query(DocumentSubmission).options(
            selectinload(DocumentSubmission.test_case),
            selectinload(DocumentSubmission.data_owner)
        ).join(CycleReportTestCase).filter(
            CycleReportTestCase.phase_id == phase_id
        ).order_by(desc(DocumentSubmission.submitted_at)).limit(10).all()
        
        # Get overdue test cases
        overdue_test_cases = self.db.query(CycleReportTestCase).options(
            selectinload(CycleReportTestCase.data_owner),
            selectinload(CycleReportTestCase.attribute)
        ).filter(
            and_(
                CycleReportTestCase.phase_id == phase_id,
                CycleReportTestCase.status == "Pending",
                CycleReportTestCase.submission_deadline < datetime.now(timezone.utc)
            )
        ).all()
        
        # Determine available actions
        can_start_phase = phase.status == "Not Started"
        can_complete_phase = (
            phase.status == "In Progress" and 
            progress_summary.completion_percentage >= 100.0
        )
        can_send_reminders = phase.status == "In Progress"
        
        return TesterPhaseView(
            phase=RequestInfoPhaseResponse.from_orm(phase),
            cycle_name=phase.cycle.cycle_name,
            report_name=phase.report.report_name,
            progress_summary=progress_summary,
            data_owner_summaries=data_owner_summaries,
            recent_submissions=[DocumentSubmissionResponse.from_orm(sub) for sub in recent_submissions],
            overdue_test_cases=[self._test_case_with_details(tc) for tc in overdue_test_cases],
            can_start_phase=can_start_phase,
            can_complete_phase=can_complete_phase,
            can_send_reminders=can_send_reminders
        )
    
    def _get_phase_progress_summary(self, phase: WorkflowPhase) -> PhaseProgressSummary:
        """Get phase progress summary"""
        
        # Get test case counts
        test_case_stats = self.db.query(
            func.count(CycleReportTestCase.test_case_id).label('total'),
            func.sum(case((CycleReportTestCase.status == 'Submitted', 1), else_=0)).label('submitted'),
            func.sum(case((CycleReportTestCase.status == 'Pending', 1), else_=0)).label('pending'),
            func.sum(case((and_(CycleReportTestCase.status == 'Pending', CycleReportTestCase.submission_deadline < datetime.now(timezone.utc)), 1), else_=0)).label('overdue')
        ).filter(CycleReportTestCase.phase_id == phase.phase_id).first()
        
        total = test_case_stats.total or 0
        submitted = test_case_stats.submitted or 0
        pending = test_case_stats.pending or 0
        overdue = test_case_stats.overdue or 0
        
        completion_percentage = (submitted / total * 100) if total > 0 else 0
        
        # Get data provider counts
        dp_stats = self.db.query(
            func.count(func.distinct(CycleReportTestCase.data_owner_id)).label('total_dps'),
            func.count(func.distinct(DataProviderNotification.data_owner_id)).label('notified_dps'),
            func.count(func.distinct(case((DataProviderNotification.first_access_at.isnot(None), DataProviderNotification.data_owner_id)))).label('active_dps')
        ).select_from(CycleReportTestCase).outerjoin(
            DataProviderNotification,
            and_(
                DataProviderNotification.phase_id == CycleReportTestCase.phase_id,
                DataProviderNotification.data_owner_id == CycleReportTestCase.data_owner_id
            )
        ).filter(CycleReportTestCase.phase_id == phase.phase_id).first()
        
        # Calculate days remaining
        days_remaining = None
        if phase.submission_deadline:
            days_remaining = (phase.submission_deadline - datetime.now(timezone.utc)).days
        
        return PhaseProgressSummary(
            phase_id=phase.phase_id,
            phase_name=phase.phase_name,
            status=phase.status,
            cycle_name=phase.cycle.cycle_name,
            report_name=phase.report.report_name,
            total_test_cases=total,
            submitted_test_cases=submitted,
            pending_test_cases=pending,
            overdue_test_cases=overdue,
            completion_percentage=completion_percentage,
            started_at=phase.started_at,
            submission_deadline=phase.submission_deadline,
            days_remaining=days_remaining,
            total_data_owners=dp_stats.total_dps or 0,
            notified_data_owners=dp_stats.notified_dps or 0,
            active_data_owners=dp_stats.active_dps or 0
        )
    
    def _get_data_owner_summaries(self, phase_id: str) -> List[DataProviderAssignmentSummary]:
        """Get data provider assignment summaries"""
        
        summaries = []
        
        # Get data providers with their test case statistics
        dp_data = self.db.query(
            CycleReportTestCase.data_owner_id,
            User.first_name,
            User.last_name,
            User.email,
            func.array_agg(CycleReportTestCase.attribute_name.distinct()).label('attributes'),
            func.count(CycleReportTestCase.test_case_id).label('total_cases'),
            func.sum(case((CycleReportTestCase.status == 'Submitted', 1), else_=0)).label('submitted_cases'),
            func.sum(case((CycleReportTestCase.status == 'Pending', 1), else_=0)).label('pending_cases'),
            func.sum(case((and_(CycleReportTestCase.status == 'Pending', CycleReportTestCase.submission_deadline < datetime.now(timezone.utc)), 1), else_=0)).label('overdue_cases'),
            func.max(DocumentSubmission.submitted_at).label('last_activity')
        ).select_from(CycleReportTestCase).join(User, User.user_id == CycleReportTestCase.data_owner_id).outerjoin(
            DocumentSubmission, DocumentSubmission.test_case_id == CycleReportTestCase.test_case_id
        ).filter(CycleReportTestCase.phase_id == phase_id).group_by(
            CycleReportTestCase.data_owner_id, User.first_name, User.last_name, User.email
        ).all()
        
        for dp in dp_data:
            # Check notification status
            notification = self.db.query(DataProviderNotification).filter(
                and_(
                    DataProviderNotification.phase_id == phase_id,
                    DataProviderNotification.data_owner_id == dp.data_owner_id
                )
            ).first()
            
            # Determine overall status
            if dp.overdue_cases > 0:
                overall_status = "Overdue"
            elif dp.submitted_cases == dp.total_cases:
                overall_status = "Submitted"
            elif dp.submitted_cases > 0:
                overall_status = "In Progress"
            else:
                overall_status = "Pending"
            
            summaries.append(DataProviderAssignmentSummary(
                data_owner_id=dp.data_owner_id,
                data_owner_name=f"{dp.first_name} {dp.last_name}",
                data_owner_email=dp.email,
                assigned_attributes=dp.attributes or [],
                total_test_cases=dp.total_cases,
                submitted_test_cases=dp.submitted_cases or 0,
                pending_test_cases=dp.pending_cases or 0,
                overdue_test_cases=dp.overdue_cases or 0,
                overall_status=overall_status,
                last_activity=dp.last_activity,
                notification_sent=notification is not None and notification.notification_sent_at is not None,
                portal_accessed=notification is not None and notification.first_access_at is not None
            ))
        
        return summaries
    
    def _test_case_with_details(self, test_case: CycleReportTestCase) -> TestCaseWithDetails:
        """Convert CycleReportTestCase to TestCaseWithDetails"""
        
        try:
            # Get document count from legacy DocumentSubmission table
            print(f"[_test_case_with_details] Getting document count for test case ID: {test_case.id}")
            doc_count = self.db.query(func.count(DocumentSubmission.submission_id)).filter(
                DocumentSubmission.test_case_id == test_case.id
            ).scalar() or 0
            print(f"[_test_case_with_details] Document count: {doc_count}")
            
            # Get evidence count from new RFI evidence table
            from app.models.request_info import TestCaseEvidence
            print(f"[_test_case_with_details] Getting evidence count for test case ID: {test_case.id}")
            evidence_count = self.db.query(func.count(TestCaseEvidence.id)).filter(
                and_(
                    TestCaseEvidence.test_case_id == test_case.id,
                    TestCaseEvidence.is_current == True
                )
            ).scalar() or 0
            print(f"[_test_case_with_details] Evidence count: {evidence_count}")
            
            # Total count includes both legacy documents and new evidence
            total_evidence_count = doc_count + evidence_count
            print(f"[_test_case_with_details] Total evidence count: {total_evidence_count}")
            
            # Safely access relationships
            data_owner_name = None
            data_owner_email = None
            assigned_by_name = None
            
            try:
                if test_case.data_owner:
                    data_owner_name = f"{test_case.data_owner.first_name} {test_case.data_owner.last_name}"
                    data_owner_email = test_case.data_owner.email
            except Exception as e:
                print(f"[_test_case_with_details] Error accessing data_owner: {e}")
                
            try:
                if test_case.assigned_by_user:
                    assigned_by_name = f"{test_case.assigned_by_user.first_name} {test_case.assigned_by_user.last_name}"
            except Exception as e:
                print(f"[_test_case_with_details] Error accessing assigned_by_user: {e}")
            
            # Get cycle_id and report_id from phase if not directly available
            if hasattr(test_case, 'cycle_id'):
                cycle_id = test_case.cycle_id
                report_id = test_case.report_id
            else:
                # These fields might be in the phase relationship
                cycle_id = test_case.phase.cycle_id if hasattr(test_case, 'phase') and test_case.phase else 0
                report_id = test_case.phase.report_id if hasattr(test_case, 'phase') and test_case.phase else 0
            
            return TestCaseWithDetails(
                test_case_id=str(test_case.id),
                phase_id=test_case.phase_id,
                cycle_id=cycle_id,
                report_id=report_id,
                attribute_id=test_case.attribute_id,
                sample_id=test_case.sample_id,
                data_owner_id=test_case.data_owner_id,
                assigned_by=test_case.assigned_by,
                assigned_at=test_case.assigned_at,
                attribute_name=test_case.attribute_name,
                sample_identifier=test_case.sample_identifier,
                primary_key_attributes=test_case.primary_key_attributes,
                expected_evidence_type=test_case.expected_evidence_type,
                special_instructions=test_case.special_instructions,
                submission_deadline=test_case.submission_deadline,
                status=test_case.status,
                submitted_at=test_case.submitted_at,
                acknowledged_at=test_case.acknowledged_at,
                created_at=test_case.created_at,
                updated_at=test_case.updated_at,
                data_owner_name=data_owner_name,
                data_owner_email=data_owner_email,
                assigned_by_name=assigned_by_name,
                document_count=total_evidence_count,
                has_submissions=total_evidence_count > 0
            )
        except Exception as e:
            print(f"[_test_case_with_details] Error processing test case {test_case.id}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    # Data Provider Portal Methods
    def get_data_owner_portal_data(self, phase_id: str, data_owner_id: int) -> DataProviderPortalData:
        """Get data for data provider portal"""
        
        # Get test cases for this data provider first
        test_cases = self.db.query(CycleReportTestCase).filter(
            and_(
                CycleReportTestCase.phase_id == phase_id,
                CycleReportTestCase.data_owner_id == data_owner_id
            )
        ).all()
        
        if not test_cases:
            raise HTTPException(status_code=404, detail="No test cases found for this data provider")
        
        # Get phase details
        phase = self.db.query(WorkflowPhase).options(
            selectinload(WorkflowPhase.cycle),
            selectinload(WorkflowPhase.report)
        ).filter(WorkflowPhase.phase_id == phase_id).first()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Phase not found")
        
        # Try to get notification (optional)
        notification = self.db.query(DataProviderNotification).filter(
            and_(
                DataProviderNotification.phase_id == phase_id,
                DataProviderNotification.data_owner_id == data_owner_id
            )
        ).first()
        
        # Update access tracking if notification exists
        if notification:
            if not notification.first_access_at:
                notification.first_access_at = datetime.now(timezone.utc)
            notification.last_access_at = datetime.now(timezone.utc)
            notification.access_count += 1
        
        # Calculate progress
        total_cases = len(test_cases)
        submitted_cases = len([tc for tc in test_cases if tc.status == "Submitted"])
        pending_cases = total_cases - submitted_cases
        completion_percentage = (submitted_cases / total_cases * 100) if total_cases > 0 else 0
        
        # Calculate days remaining
        days_remaining = 0
        submission_deadline = None
        
        if notification and notification.submission_deadline:
            submission_deadline = notification.submission_deadline
            if submission_deadline.tzinfo is None:
                # If deadline is naive, assume UTC
                submission_deadline = submission_deadline.replace(tzinfo=timezone.utc)
            days_remaining = max(0, (submission_deadline - datetime.now(timezone.utc)).days)
        elif phase.submission_deadline:
            submission_deadline = phase.submission_deadline
            if submission_deadline.tzinfo is None:
                # If deadline is naive, assume UTC
                submission_deadline = submission_deadline.replace(tzinfo=timezone.utc)
            days_remaining = max(0, (submission_deadline - datetime.now(timezone.utc)).days)
        
        # Get unique attributes assigned to this data provider
        assigned_attributes = list(set([tc.attribute_name for tc in test_cases]))
        
        # Create virtual notification response if no notification exists
        if notification:
            notification_response = DataProviderNotificationResponse.from_orm(notification)
        else:
            # Create a virtual notification response
            notification_response = DataProviderNotificationResponse(
                notification_id="virtual",
                phase_id=phase_id,
                cycle_id=phase.cycle_id,
                report_id=phase.report_id,
                data_owner_id=data_owner_id,
                assigned_attributes=assigned_attributes,
                sample_count=len(set([tc.sample_identifier for tc in test_cases])),
                submission_deadline=submission_deadline,
                portal_access_url=f"/request-info/phases/{phase_id}/data-owner-portal",
                custom_instructions=phase.instructions,
                notification_sent_at=None,
                first_access_at=datetime.now(timezone.utc),
                last_access_at=datetime.now(timezone.utc),
                access_count=1,
                is_acknowledged=False,
                acknowledged_at=None,
                status="Pending",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        
        self.db.commit()
        
        return DataProviderPortalData(
            notification=notification_response,
            test_cases=[TestCaseResponse.from_orm(tc) for tc in test_cases],
            cycle_name=phase.cycle.cycle_name,
            report_name=phase.report.report_name,
            phase_instructions=phase.instructions,
            submission_deadline=submission_deadline,
            days_remaining=days_remaining,
            total_test_cases=total_cases,
            submitted_test_cases=submitted_cases,
            pending_test_cases=pending_cases,
            completion_percentage=completion_percentage
        )
    
    # Document Upload Methods
    def upload_document(self, test_case_id: str, file: UploadFile, 
                       data_owner_id: int, submission_notes: Optional[str] = None) -> FileUploadResponse:
        """Upload document for a test case"""
        
        # Validate test case
        test_case = self.db.query(CycleReportTestCase).filter(CycleReportTestCase.test_case_id == test_case_id).first()
        if not test_case:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        if test_case.data_owner_id != data_owner_id:
            raise HTTPException(status_code=403, detail="Not authorized for this test case")
        
        if test_case.status == "Submitted":
            raise HTTPException(status_code=400, detail="Test case already has submissions")
        
        try:
            # Validate file
            if not file.filename:
                raise HTTPException(status_code=400, detail="No file provided")
            
            # Determine document type and validate
            mime_type, _ = mimetypes.guess_type(file.filename)
            document_type = self._determine_document_type(file.filename, mime_type)
            
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            stored_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(self.upload_dir, stored_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create document submission record
            submission = DocumentSubmission(
                test_case_id=test_case_id,
                data_owner_id=data_owner_id,
                original_filename=file.filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size_bytes=file_size,
                document_type=document_type,
                mime_type=mime_type or "application/octet-stream",
                submission_notes=submission_notes
            )
            
            self.db.add(submission)
            
            # Update test case status
            test_case.status = "Submitted"
            test_case.submitted_at = datetime.now(timezone.utc)
            
            # Update phase progress
            phase = self.db.query(WorkflowPhase).filter(
                WorkflowPhase.phase_id == test_case.phase_id
            ).first()
            if phase:
                submitted_count = self.db.query(func.count(CycleReportTestCase.test_case_id)).filter(
                    and_(
                        CycleReportTestCase.phase_id == test_case.phase_id,
                        CycleReportTestCase.status == "Submitted"
                    )
                ).scalar()
                phase.submitted_test_cases = submitted_count
            
            self.db.commit()
            self.db.refresh(submission)
            
            # Log audit
            self._log_audit(
                action="UPLOAD_DOCUMENT",
                entity_type="DocumentSubmission",
                entity_id=submission.submission_id,
                user_id=data_owner_id,
                cycle_id=test_case.cycle_id,
                report_id=test_case.report_id,
                phase_id=test_case.phase_id,
                notes=f"Uploaded document for test case {test_case_id}"
            )
            
            return FileUploadResponse(
                success=True,
                message="Document uploaded successfully",
                submission_id=submission.submission_id,
                file_info={
                    "original_filename": file.filename,
                    "file_size": file_size,
                    "document_type": document_type
                }
            )
            
        except Exception as e:
            # Clean up file if it was created
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            
            return FileUploadResponse(
                success=False,
                message="Failed to upload document",
                errors=[str(e)]
            )
    
    def _determine_document_type(self, filename: str, mime_type: Optional[str]) -> str:
        """Determine document type from filename and mime type"""
        
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf') or (mime_type and 'pdf' in mime_type):
            return "PDF"
        elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')) or (mime_type and 'image' in mime_type):
            return "Image"
        elif filename_lower.endswith(('.xls', '.xlsx')) or (mime_type and 'excel' in mime_type):
            return "Excel"
        elif filename_lower.endswith(('.doc', '.docx')) or (mime_type and 'word' in mime_type):
            return "Word"
        else:
            return "Other"
    
    # Phase Completion
    def complete_phase(self, phase_id: str, completion_request: PhaseCompletionRequest, 
                      user_id: int) -> RequestInfoPhaseResponse:
        """Complete the Request for Information phase"""
        
        phase = self.db.query(WorkflowPhase).filter(WorkflowPhase.phase_id == phase_id).first()
        if not phase:
            raise HTTPException(status_code=404, detail="Phase not found")
        
        if phase.status != "In Progress":
            raise HTTPException(status_code=400, detail="Phase is not in progress")
        
        # Check completion requirements
        if not completion_request.force_complete:
            pending_count = self.db.query(func.count(CycleReportTestCase.test_case_id)).filter(
                and_(
                    CycleReportTestCase.phase_id == phase_id,
                    CycleReportTestCase.status == "Pending"
                )
            ).scalar()
            
            if pending_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot complete phase: {pending_count} test cases still pending"
                )
        
        # Update phase
        phase.status = "Complete"
        phase.completed_by = user_id
        phase.completed_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        # Log audit
        self._log_audit(
            action="COMPLETE_PHASE",
            entity_type="WorkflowPhase",
            entity_id=phase.phase_id,
            user_id=user_id,
            cycle_id=phase.cycle_id,
            report_id=phase.report_id,
            phase_id=phase.phase_id,
            notes=completion_request.completion_notes or "Completed Request for Information phase"
        )
        
        return RequestInfoPhaseResponse.from_orm(phase)
    
    # Test Case Management
    def get_test_cases(self, phase_id: str, data_owner_id: Optional[int] = None, 
                      status_filter: Optional[str] = None) -> TestCaseListResponse:
        """Get test cases for a phase"""
        
        query = self.db.query(CycleReportTestCase).options(
            selectinload(CycleReportTestCase.data_owner),
            selectinload(CycleReportTestCase.assigned_by_user),
            selectinload(CycleReportTestCase.attribute)
        ).filter(CycleReportTestCase.phase_id == phase_id)
        
        if data_owner_id:
            query = query.filter(CycleReportTestCase.data_owner_id == data_owner_id)
        
        if status_filter:
            query = query.filter(CycleReportTestCase.status == status_filter)
        
        test_cases = query.all()
        
        # Convert to detailed test cases
        detailed_test_cases = [self._test_case_with_details(tc) for tc in test_cases]
        
        # Calculate counts
        total_count = len(detailed_test_cases)
        submitted_count = len([tc for tc in detailed_test_cases if tc.status == "Submitted"])
        pending_count = len([tc for tc in detailed_test_cases if tc.status == "Pending"])
        overdue_count = len([tc for tc in detailed_test_cases if tc.status == "Overdue"])
        
        return TestCaseListResponse(
            test_cases=detailed_test_cases,
            total_count=total_count,
            submitted_count=submitted_count,
            pending_count=pending_count,
            overdue_count=overdue_count,
            data_owner_id=data_owner_id,
            status_filter=status_filter
        )
    
    # Query Validation Methods
    async def validate_query(self, request: QueryValidationRequest, user_id: int) -> QueryValidationResult:
        """Validate a query before final submission"""
        import time
        import asyncio
        from app.services.database_connection_service import DatabaseConnectionService
        
        start_time = time.time()
        validation_id = str(uuid.uuid4())
        
        try:
            # Get test case to verify ownership
            test_case_result = await self.db.execute(
                select(CycleReportTestCase).where(CycleReportTestCase.id == request.test_case_id)
            )
            test_case = test_case_result.scalar_one_or_none()
            
            if not test_case:
                raise HTTPException(status_code=404, detail="Test case not found")
                
            # Log for debugging
            logger.info(f"Authorization check - Test case data_owner_id: {test_case.data_owner_id}, User ID: {user_id}")
            
            if test_case.data_owner_id != user_id:
                # Check if user has admin or tester role as fallback
                from app.models.user import User
                user_result = await self.db.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if user and user.user_role in ['Admin', 'Tester', 'Test Executive']:
                    logger.info(f"User {user_id} has {user.user_role} role, allowing access")
                else:
                    logger.warning(f"User {user_id} not authorized for test case {test_case.id} owned by {test_case.data_owner_id}")
                    raise HTTPException(status_code=403, detail=f"Not authorized for this test case. Test case is assigned to data owner {test_case.data_owner_id}, but you are user {user_id}")
            
            # Get data source configuration
            data_source = await self._get_data_source(request.data_source_id)
            if not data_source:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Data source not found. Please ensure you have created a data source first. Invalid ID: {request.data_source_id}"
                )
            
            # Get expected columns (PK attributes + target attribute)
            expected_columns = await self._get_expected_columns(test_case)
            
            # Execute query with timeout
            db_service = DatabaseConnectionService()
            try:
                # Add LIMIT to query for validation
                limited_query = f"{request.query_text.rstrip(';')} LIMIT {request.sample_size_limit}"
                
                # Execute query
                result = await asyncio.wait_for(
                    db_service.execute_query(
                        connection_type=data_source['connection_type'],
                        connection_details=data_source['connection_details'],
                        query=limited_query,
                        parameters=request.query_parameters
                    ),
                    timeout=30.0  # 30 second timeout
                )
                
                # Process results and convert Decimal values
                rows = convert_decimals(result.get('rows', []))
                columns = result.get('columns', [])
                total_count = result.get('total_count', len(rows))
                
                # Check for required columns - more flexible validation
                column_names_lower = [col.lower() for col in columns]
                
                # For primary keys, check if at least one is present (not all required)
                # This allows for partial primary key queries
                found_primary_keys = [
                    pk for pk in expected_columns['primary_keys']
                    if pk.lower() in column_names_lower
                ]
                has_primary_keys = len(found_primary_keys) > 0 if expected_columns['primary_keys'] else True
                
                # For target attribute, check exact match or suggest using alias
                has_target_attribute = test_case.attribute_name.lower() in column_names_lower
                
                # Provide helpful feedback about missing columns
                missing_columns = []
                validation_warnings = []
                
                if expected_columns['primary_keys'] and not found_primary_keys:
                    missing_pks = expected_columns['primary_keys']
                    missing_columns.extend(missing_pks)
                    validation_warnings.append(
                        f"No primary key columns found. Expected at least one of: {', '.join(missing_pks)}. "
                        f"You may need to use column aliases (e.g., SELECT your_column AS {missing_pks[0]})"
                    )
                elif expected_columns['primary_keys'] and len(found_primary_keys) < len(expected_columns['primary_keys']):
                    # Some but not all PKs found - this is OK
                    validation_warnings.append(
                        f"Found {len(found_primary_keys)} of {len(expected_columns['primary_keys'])} primary key columns. "
                        f"This is acceptable for validation."
                    )
                
                if not has_target_attribute:
                    missing_columns.append(test_case.attribute_name)
                    validation_warnings.append(
                        f"Target attribute '{test_case.attribute_name}' not found in query results. "
                        f"Please use a column alias (e.g., SELECT your_column AS {test_case.attribute_name})"
                    )
                
                execution_time = int((time.time() - start_time) * 1000)
                
                # Save validation result to database
                validation_record = RFIQueryValidation(
                    validation_id=validation_id,
                    test_case_id=request.test_case_id,
                    data_source_id=request.data_source_id,
                    query_text=request.query_text,
                    query_parameters=request.query_parameters,
                    validation_status="success",
                    execution_time_ms=execution_time,
                    row_count=total_count,
                    column_names=columns,
                    sample_rows=rows[:request.sample_size_limit],
                    has_primary_keys=has_primary_keys,
                    has_target_attribute=has_target_attribute,
                    missing_columns=missing_columns,
                    validation_warnings=validation_warnings,
                    validated_by=user_id
                )
                
                self.db.add(validation_record)
                await self.db.commit()
                
                return QueryValidationResult(
                    validation_id=validation_id,
                    test_case_id=request.test_case_id,
                    validation_status="success",
                    executed_at=datetime.now(timezone.utc),
                    execution_time_ms=execution_time,
                    row_count=total_count,
                    column_names=columns,
                    sample_rows=rows[:request.sample_size_limit],
                    has_primary_keys=has_primary_keys,
                    has_target_attribute=has_target_attribute,
                    missing_columns=missing_columns,
                    validation_warnings=validation_warnings
                )
                
            except asyncio.TimeoutError:
                return QueryValidationResult(
                    validation_id=validation_id,
                    test_case_id=request.test_case_id,
                    validation_status="timeout",
                    executed_at=datetime.now(timezone.utc),
                    execution_time_ms=30000,
                    row_count=0,
                    column_names=[],
                    sample_rows=[],
                    error_message="Query execution timed out after 30 seconds",
                    has_primary_keys=False,
                    has_target_attribute=False
                )
                
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return QueryValidationResult(
                validation_id=validation_id,
                test_case_id=request.test_case_id,
                validation_status="failed",
                executed_at=datetime.now(timezone.utc),
                execution_time_ms=execution_time,
                row_count=0,
                column_names=[],
                sample_rows=[],
                error_message=str(e),
                has_primary_keys=False,
                has_target_attribute=False
            )
    
    async def create_data_source(self, request: DataSourceCreateRequest, user_id: int) -> DataSourceResponse:
        """Create a reusable data source"""
        
        # Encrypt sensitive connection details
        encrypted_details = await self._encrypt_connection_details(request.connection_details)
        
        # Create data source
        data_source = RFIDataSource(
            source_name=request.source_name,
            connection_type=request.connection_type,
            connection_details=encrypted_details,
            is_active=request.is_active,
            test_query=request.test_query,
            created_by=user_id,
            data_owner_id=user_id
        )
        
        self.db.add(data_source)
        
        # Test connection if test query provided
        if request.test_query:
            try:
                db_service = DatabaseConnectionService()
                await db_service.test_connection(
                    connection_type=request.connection_type,
                    connection_details=request.connection_details,
                    test_query=request.test_query
                )
                data_source.last_validated_at = datetime.now(timezone.utc)
                data_source.validation_status = "valid"
            except Exception as e:
                data_source.validation_status = "invalid"
                data_source.validation_error = str(e)
        
        await self.db.commit()
        await self.db.refresh(data_source)
        
        return DataSourceResponse(
            data_source_id=str(data_source.data_source_id),
            source_name=data_source.source_name,
            connection_type=data_source.connection_type,
            connection_details=request.connection_details,  # Return unencrypted for response
            is_active=data_source.is_active,
            test_query=data_source.test_query,
            created_by=data_source.created_by,
            created_at=data_source.created_at,
            updated_at=data_source.updated_at,
            last_validated_at=data_source.last_validated_at,
            validation_status=data_source.validation_status,
            usage_count=data_source.usage_count
        )
    
    async def save_validated_query(self, request: SaveQueryRequest, user_id: int):
        """Save a validated query as evidence"""
        from app.models.request_info import TestCaseEvidence, RFIQueryValidation, CycleReportTestCase
        from sqlalchemy import func
        
        # Verify test case ownership and get phase data
        from app.models.workflow import WorkflowPhase
        
        test_case_query = select(CycleReportTestCase, WorkflowPhase).join(
            WorkflowPhase, CycleReportTestCase.phase_id == WorkflowPhase.phase_id
        ).where(CycleReportTestCase.id == request.test_case_id)
        
        test_case_result = await self.db.execute(test_case_query)
        result = test_case_result.first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Test case not found")
            
        test_case, phase = result
        
        if test_case.data_owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized for this test case")
        
        # Get the next version number
        max_version_result = await self.db.execute(
            select(func.max(TestCaseEvidence.version_number)).where(
                TestCaseEvidence.test_case_id == request.test_case_id
            )
        )
        max_version = max_version_result.scalar() or 0
        next_version = max_version + 1
        
        # Mark existing evidence as not current
        if max_version > 0:
            update_stmt = (
                update(TestCaseEvidence)
                .where(
                    and_(
                        TestCaseEvidence.test_case_id == request.test_case_id,
                        TestCaseEvidence.is_current == True
                    )
                )
                .values(is_current=False)
            )
            await self.db.execute(update_stmt)
        
        # Create unified evidence record
        evidence = TestCaseEvidence(
            test_case_id=request.test_case_id,
            phase_id=test_case.phase_id,
            cycle_id=phase.cycle_id,
            report_id=phase.report_id,
            sample_id=test_case.sample_id,
            evidence_type="data_source",
            version_number=next_version,
            is_current=True,
            data_owner_id=user_id,
            submission_notes=request.submission_notes,
            submission_number=next_version,  # Use version as submission number
            validation_status="pending",
            rfi_data_source_id=request.data_source_id,  # Now supports UUID
            query_text=request.query_text,
            query_parameters={},  # Empty for now
            query_validation_id=None,  # We're not tracking validation ID for now
            created_by=user_id,
            updated_by=user_id
        )
        
        self.db.add(evidence)
        
        # Update test case status to Submitted
        # This should happen for all cases including revisions (In Progress)
        logger.info(f"Updating test case {test_case.id} status from '{test_case.status}' to 'Submitted'")
        test_case.status = 'Submitted'
        
        test_case.submitted_at = datetime.now(timezone.utc)
        test_case.updated_by = user_id
        test_case.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        logger.info(f"Successfully committed test case {test_case.id} with status 'Submitted'")
        
        # Log audit
        self._log_audit(
            action="SUBMIT_QUERY_EVIDENCE",
            entity_type="TestCaseEvidence",
            entity_id=str(evidence.id),
            user_id=user_id,
            cycle_id=test_case.cycle_id,
            report_id=test_case.report_id,
            phase_id=test_case.phase_id,
            notes=f"Submitted query evidence for test case {request.test_case_id}"
        )
    
    async def _get_data_source(self, data_source_id: str) -> Optional[Dict[str, Any]]:
        """Get data source configuration"""
        
        # Validate UUID format
        try:
            # Try to parse as UUID to validate format
            import uuid
            uuid.UUID(data_source_id)
        except ValueError:
            logger.error(f"Invalid data source ID format: {data_source_id}")
            return None
        
        result = await self.db.execute(
            select(RFIDataSource).where(RFIDataSource.data_source_id == data_source_id)
        )
        data_source = result.scalar_one_or_none()
        
        if not data_source:
            return None
            
        # Decrypt connection details for use
        decrypted_details = await self._decrypt_connection_details(data_source.connection_details)
        
        return {
            'data_source_id': str(data_source.data_source_id),
            'connection_type': data_source.connection_type,
            'connection_details': decrypted_details
        }
    
    async def _decrypt_connection_details(self, encrypted_details: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt connection details"""
        from app.core.encryption import decrypt_connection_details
        try:
            return decrypt_connection_details(encrypted_details)
        except Exception:
            # If decryption fails, assume it's already decrypted (backwards compatibility)
            return encrypted_details
    
    async def _get_expected_columns(self, test_case) -> Dict[str, List[str]]:
        """Get expected columns for validation"""
        # Get primary key attributes from the test case
        pk_attributes = []
        if hasattr(test_case, 'primary_key_attributes') and test_case.primary_key_attributes:
            pk_attributes = list(test_case.primary_key_attributes.keys())
        
        return {
            'primary_keys': pk_attributes,
            'target_attribute': test_case.attribute_name
        }
    
    async def _encrypt_connection_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive connection details"""
        from app.core.encryption import encrypt_connection_details
        try:
            return encrypt_connection_details(details)
        except Exception:
            # If encryption fails, return as-is (development mode fallback)
            return details 