"""
Clean Temporal activities for versioning without backward compatibility
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from temporalio import activity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.versioning import (
    VersionStatus, ApprovalStatus, SampleSource,
    PlanningVersion, AttributeDecision,
    DataProfilingVersion, ProfilingRule,
    ScopingVersion, ScopingDecision,
    SampleSelectionVersion, SampleDecision,
    DataOwnerAssignment, DocumentSubmission,
    TestExecutionAudit, ObservationVersion,
    ObservationDecision, TestReportVersion,
    ReportSection, ReportSignoff
)
from app.core.database import get_async_session
from app.core.logger import logger


class VersioningActivities:
    """Clean versioning activities without compatibility layers"""
    
    def __init__(self):
        self.name = "VersioningActivities"
    
    # Planning Phase Activities
    @activity.defn
    async def create_planning_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        attributes: List[Dict[str, Any]],
        workflow_execution_id: str,
        workflow_run_id: str
    ) -> Dict[str, Any]:
        """Create a new planning version"""
        async with get_async_session() as db:
            try:
                # Get latest version number
                result = await db.execute(
                    select(PlanningVersion.version_number)
                    .where(
                        and_(
                            PlanningVersion.cycle_id == cycle_id,
                            PlanningVersion.report_id == report_id
                        )
                    )
                    .order_by(PlanningVersion.version_number.desc())
                )
                latest_version = result.scalar()
                new_version_number = (latest_version or 0) + 1
                
                # Create version
                version = PlanningVersion(
                    version_number=new_version_number,
                    version_status=VersionStatus.DRAFT,
                    workflow_execution_id=workflow_execution_id,
                    workflow_run_id=workflow_run_id,
                    activity_name="create_planning_version",
                    created_by_id=user_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Planning",
                    total_attributes=len(attributes),
                    included_attributes=sum(1 for a in attributes if a.get('include_in_testing', True))
                )
                
                db.add(version)
                await db.flush()
                
                # Create attribute decisions
                for attr in attributes:
                    decision = AttributeDecision(
                        version_id=version.version_id,
                        attribute_id=attr['attribute_id'],
                        attribute_name=attr['attribute_name'],
                        include_in_testing=attr.get('include_in_testing', True),
                        decision_reason=attr.get('decision_reason'),
                        risk_rating=attr.get('risk_rating')
                    )
                    db.add(decision)
                
                await db.commit()
                
                return {
                    "version_id": str(version.version_id),
                    "version_number": version.version_number,
                    "status": version.version_status.value,
                    "total_attributes": version.total_attributes,
                    "included_attributes": version.included_attributes
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to create planning version: {str(e)}")
                raise

    @activity.defn
    async def approve_planning_version(
        self,
        version_id: str,
        approver_id: int,
        workflow_execution_id: str
    ) -> Dict[str, Any]:
        """Approve planning version"""
        async with get_async_session() as db:
            try:
                # Get version
                result = await db.execute(
                    select(PlanningVersion)
                    .where(PlanningVersion.version_id == uuid.UUID(version_id))
                )
                version = result.scalar_one()
                
                # Update status
                version.version_status = VersionStatus.APPROVED
                version.approved_at = datetime.utcnow()
                version.approved_by_id = approver_id
                
                await db.commit()
                
                return {
                    "version_id": str(version.version_id),
                    "status": "approved",
                    "approved_at": version.approved_at.isoformat()
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to approve planning version: {str(e)}")
                raise

    # Data Profiling Activities
    @activity.defn
    async def create_profiling_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        source_files: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        workflow_execution_id: str,
        workflow_run_id: str
    ) -> Dict[str, Any]:
        """Create data profiling version"""
        async with get_async_session() as db:
            try:
                # Get version number
                result = await db.execute(
                    select(DataProfilingVersion.version_number)
                    .where(
                        and_(
                            DataProfilingVersion.cycle_id == cycle_id,
                            DataProfilingVersion.report_id == report_id
                        )
                    )
                    .order_by(DataProfilingVersion.version_number.desc())
                )
                latest_version = result.scalar()
                new_version_number = (latest_version or 0) + 1
                
                # Create version
                version = DataProfilingVersion(
                    version_number=new_version_number,
                    version_status=VersionStatus.DRAFT,
                    workflow_execution_id=workflow_execution_id,
                    workflow_run_id=workflow_run_id,
                    activity_name="create_profiling_version",
                    created_by_id=user_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Data Profiling",
                    source_files=source_files,
                    total_rules=len(rules),
                    approved_rules=0
                )
                
                db.add(version)
                await db.flush()
                
                # Add rules
                for rule_data in rules:
                    rule = ProfilingRule(
                        version_id=version.version_id,
                        rule_name=rule_data['name'],
                        rule_type=rule_data['type'],
                        rule_definition=rule_data['definition'],
                        approval_status=ApprovalStatus.PENDING
                    )
                    db.add(rule)
                
                await db.commit()
                
                return {
                    "version_id": str(version.version_id),
                    "version_number": version.version_number,
                    "total_rules": version.total_rules
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to create profiling version: {str(e)}")
                raise

    # Scoping Activities
    @activity.defn
    async def create_scoping_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        scoping_decisions: List[Dict[str, Any]],
        workflow_execution_id: str,
        workflow_run_id: str
    ) -> Dict[str, Any]:
        """Create scoping version"""
        async with get_async_session() as db:
            try:
                # Get version number
                result = await db.execute(
                    select(ScopingVersion.version_number)
                    .where(
                        and_(
                            ScopingVersion.cycle_id == cycle_id,
                            ScopingVersion.report_id == report_id
                        )
                    )
                    .order_by(ScopingVersion.version_number.desc())
                )
                latest_version = result.scalar()
                new_version_number = (latest_version or 0) + 1
                
                # Create version
                in_scope_count = sum(1 for d in scoping_decisions if d.get('is_in_scope', False))
                
                version = ScopingVersion(
                    version_number=new_version_number,
                    version_status=VersionStatus.DRAFT,
                    workflow_execution_id=workflow_execution_id,
                    workflow_run_id=workflow_run_id,
                    activity_name="create_scoping_version",
                    created_by_id=user_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Scoping",
                    total_attributes=len(scoping_decisions),
                    in_scope_count=in_scope_count
                )
                
                db.add(version)
                await db.flush()
                
                # Add decisions
                for decision_data in scoping_decisions:
                    decision = ScopingDecision(
                        version_id=version.version_id,
                        attribute_id=decision_data['attribute_id'],
                        is_in_scope=decision_data.get('is_in_scope', False),
                        scoping_rationale=decision_data.get('rationale'),
                        risk_assessment=decision_data.get('risk_assessment'),
                        approval_status=ApprovalStatus.PENDING
                    )
                    db.add(decision)
                
                await db.commit()
                
                return {
                    "version_id": str(version.version_id),
                    "version_number": version.version_number,
                    "in_scope_count": in_scope_count,
                    "total_attributes": len(scoping_decisions)
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to create scoping version: {str(e)}")
                raise

    # Sample Selection Activities
    @activity.defn
    async def create_sample_selection_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        samples: List[Dict[str, Any]],
        selection_criteria: Dict[str, Any],
        workflow_execution_id: str,
        workflow_run_id: str,
        parent_version_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create sample selection version with individual tracking"""
        async with get_async_session() as db:
            try:
                # Get version number
                result = await db.execute(
                    select(SampleSelectionVersion.version_number)
                    .where(
                        and_(
                            SampleSelectionVersion.cycle_id == cycle_id,
                            SampleSelectionVersion.report_id == report_id
                        )
                    )
                    .order_by(SampleSelectionVersion.version_number.desc())
                )
                latest_version = result.scalar()
                new_version_number = (latest_version or 0) + 1
                
                # Create version
                version = SampleSelectionVersion(
                    version_number=new_version_number,
                    version_status=VersionStatus.DRAFT,
                    parent_version_id=uuid.UUID(parent_version_id) if parent_version_id else None,
                    workflow_execution_id=workflow_execution_id,
                    workflow_run_id=workflow_run_id,
                    activity_name="create_sample_selection_version",
                    created_by_id=user_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Sample Selection",
                    selection_criteria=selection_criteria,
                    target_sample_size=selection_criteria.get('target_size', len(samples)),
                    actual_sample_size=len(samples)
                )
                
                db.add(version)
                await db.flush()
                
                # Add sample decisions
                for sample_data in samples:
                    decision = SampleDecision(
                        version_id=version.version_id,
                        sample_identifier=sample_data['identifier'],
                        sample_data=sample_data['data'],
                        sample_type=sample_data.get('type', 'population'),
                        source=SampleSource(sample_data.get('source', 'manual')),
                        source_metadata=sample_data.get('source_metadata'),
                        decision_status=ApprovalStatus(sample_data.get('status', 'pending')),
                        decision_notes=sample_data.get('notes'),
                        carried_from_version_id=uuid.UUID(sample_data['carried_from_version']) if sample_data.get('carried_from_version') else None,
                        carried_from_decision_id=uuid.UUID(sample_data['carried_from_decision']) if sample_data.get('carried_from_decision') else None
                    )
                    db.add(decision)
                
                await db.commit()
                
                return {
                    "version_id": str(version.version_id),
                    "version_number": version.version_number,
                    "sample_count": len(samples),
                    "is_revision": parent_version_id is not None
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to create sample selection version: {str(e)}")
                raise

    @activity.defn
    async def process_sample_review(
        self,
        version_id: str,
        sample_decisions: List[Dict[str, Any]],
        reviewer_id: int
    ) -> Dict[str, Any]:
        """Process sample review decisions"""
        async with get_async_session() as db:
            try:
                approved_count = 0
                rejected_count = 0
                
                for decision_update in sample_decisions:
                    result = await db.execute(
                        select(SampleDecision)
                        .where(SampleDecision.decision_id == uuid.UUID(decision_update['decision_id']))
                    )
                    decision = result.scalar_one()
                    
                    decision.decision_status = ApprovalStatus(decision_update['status'])
                    decision.decision_notes = decision_update.get('notes')
                    
                    if decision.decision_status == ApprovalStatus.APPROVED:
                        approved_count += 1
                    elif decision.decision_status == ApprovalStatus.REJECTED:
                        rejected_count += 1
                
                await db.commit()
                
                return {
                    "version_id": version_id,
                    "approved": approved_count,
                    "rejected": rejected_count,
                    "total_reviewed": len(sample_decisions)
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to process sample review: {str(e)}")
                raise

    @activity.defn
    async def create_sample_revision(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        parent_version_id: str,
        additional_samples: List[Dict[str, Any]],
        workflow_execution_id: str,
        workflow_run_id: str
    ) -> Dict[str, Any]:
        """Create revision with carried forward samples"""
        async with get_async_session() as db:
            try:
                # Get approved samples from parent version
                result = await db.execute(
                    select(SampleDecision)
                    .where(
                        and_(
                            SampleDecision.version_id == uuid.UUID(parent_version_id),
                            SampleDecision.decision_status == ApprovalStatus.APPROVED
                        )
                    )
                )
                approved_samples = result.scalars().all()
                
                # Prepare all samples
                all_samples = []
                
                # Carry forward approved samples
                for sample in approved_samples:
                    all_samples.append({
                        'identifier': sample.sample_identifier,
                        'data': sample.sample_data,
                        'type': sample.sample_type,
                        'source': 'carried_forward',
                        'status': 'approved',
                        'carried_from_version': parent_version_id,
                        'carried_from_decision': str(sample.decision_id)
                    })
                
                # Add new samples
                all_samples.extend(additional_samples)
                
                # Get selection criteria from parent
                parent_result = await db.execute(
                    select(SampleSelectionVersion)
                    .where(SampleSelectionVersion.version_id == uuid.UUID(parent_version_id))
                )
                parent_version = parent_result.scalar_one()
                
                # Create new version
                return await self.create_sample_selection_version(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    user_id=user_id,
                    samples=all_samples,
                    selection_criteria=parent_version.selection_criteria,
                    workflow_execution_id=workflow_execution_id,
                    workflow_run_id=workflow_run_id,
                    parent_version_id=parent_version_id
                )
                
            except Exception as e:
                logger.error(f"Failed to create sample revision: {str(e)}")
                raise

    # Data Owner Assignment Activities
    @activity.defn
    async def assign_data_owner(
        self,
        cycle_id: int,
        report_id: int,
        lob_id: str,
        data_owner_id: int,
        assigned_by_id: int,
        workflow_execution_id: str,
        change_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assign data owner to LOB"""
        async with get_async_session() as db:
            try:
                # Deactivate current assignment if exists
                result = await db.execute(
                    select(DataOwnerAssignment)
                    .where(
                        and_(
                            DataOwnerAssignment.cycle_id == cycle_id,
                            DataOwnerAssignment.report_id == report_id,
                            DataOwnerAssignment.lob_id == uuid.UUID(lob_id),
                            DataOwnerAssignment.is_active == True
                        )
                    )
                )
                current_assignment = result.scalar()
                
                previous_assignment_id = None
                if current_assignment:
                    current_assignment.is_active = False
                    previous_assignment_id = current_assignment.assignment_id
                
                # Create new assignment
                assignment = DataOwnerAssignment(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    workflow_execution_id=workflow_execution_id,
                    lob_id=uuid.UUID(lob_id),
                    data_owner_id=data_owner_id,
                    assigned_by_id=assigned_by_id,
                    previous_assignment_id=previous_assignment_id,
                    change_reason=change_reason
                )
                
                db.add(assignment)
                await db.commit()
                
                return {
                    "assignment_id": str(assignment.assignment_id),
                    "lob_id": lob_id,
                    "data_owner_id": data_owner_id,
                    "is_reassignment": previous_assignment_id is not None
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to assign data owner: {str(e)}")
                raise

    # Document Submission Activities
    @activity.defn
    async def submit_document(
        self,
        cycle_id: int,
        report_id: int,
        lob_id: str,
        document_name: str,
        document_type: str,
        document_path: str,
        submitted_by_id: int,
        workflow_execution_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submit document"""
        async with get_async_session() as db:
            try:
                # Check for existing document of same type
                result = await db.execute(
                    select(DocumentSubmission)
                    .where(
                        and_(
                            DocumentSubmission.cycle_id == cycle_id,
                            DocumentSubmission.report_id == report_id,
                            DocumentSubmission.lob_id == uuid.UUID(lob_id),
                            DocumentSubmission.document_type == document_type,
                            DocumentSubmission.is_current == True
                        )
                    )
                )
                existing = result.scalar()
                
                replaces_id = None
                version_number = 1
                
                if existing:
                    existing.is_current = False
                    replaces_id = existing.submission_id
                    version_number = existing.document_version + 1
                
                # Create submission
                submission = DocumentSubmission(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    lob_id=uuid.UUID(lob_id),
                    workflow_execution_id=workflow_execution_id,
                    document_name=document_name,
                    document_type=document_type,
                    document_path=document_path,
                    document_metadata=metadata,
                    document_version=version_number,
                    replaces_submission_id=replaces_id,
                    submitted_by_id=submitted_by_id
                )
                
                db.add(submission)
                await db.commit()
                
                return {
                    "submission_id": str(submission.submission_id),
                    "document_version": version_number,
                    "is_revision": replaces_id is not None
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to submit document: {str(e)}")
                raise

    # Test Execution Activities
    @activity.defn
    async def record_test_action(
        self,
        cycle_id: int,
        report_id: int,
        test_execution_id: int,
        action_type: str,
        action_details: Dict[str, Any],
        requested_by_id: int,
        workflow_execution_id: str
    ) -> Dict[str, Any]:
        """Record test execution action"""
        async with get_async_session() as db:
            try:
                audit_entry = TestExecutionAudit(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    test_execution_id=test_execution_id,
                    workflow_execution_id=workflow_execution_id,
                    action_type=action_type,
                    action_details=action_details,
                    requested_by_id=requested_by_id
                )
                
                db.add(audit_entry)
                await db.commit()
                
                return {
                    "audit_id": str(audit_entry.audit_id),
                    "action_type": action_type,
                    "requested_at": audit_entry.requested_at.isoformat()
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to record test action: {str(e)}")
                raise

    # Observation Activities
    @activity.defn
    async def create_observation_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        observation_period: Dict[str, Any],
        observations: List[Dict[str, Any]],
        workflow_execution_id: str,
        workflow_run_id: str
    ) -> Dict[str, Any]:
        """Create observation version"""
        async with get_async_session() as db:
            try:
                # Get version number
                result = await db.execute(
                    select(ObservationVersion.version_number)
                    .where(
                        and_(
                            ObservationVersion.cycle_id == cycle_id,
                            ObservationVersion.report_id == report_id
                        )
                    )
                    .order_by(ObservationVersion.version_number.desc())
                )
                latest_version = result.scalar()
                new_version_number = (latest_version or 0) + 1
                
                # Create version
                version = ObservationVersion(
                    version_number=new_version_number,
                    version_status=VersionStatus.DRAFT,
                    workflow_execution_id=workflow_execution_id,
                    workflow_run_id=workflow_run_id,
                    activity_name="create_observation_version",
                    created_by_id=user_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Observation Management",
                    observation_period_start=datetime.fromisoformat(observation_period['start']),
                    observation_period_end=datetime.fromisoformat(observation_period['end']),
                    total_observations=len(observations)
                )
                
                db.add(version)
                await db.flush()
                
                # Add observations
                for obs_data in observations:
                    observation = ObservationDecision(
                        version_id=version.version_id,
                        observation_type=obs_data['type'],
                        severity=obs_data['severity'],
                        title=obs_data['title'],
                        description=obs_data['description'],
                        evidence_references=obs_data.get('evidence'),
                        approval_status=ApprovalStatus.PENDING,
                        requires_remediation=obs_data.get('requires_remediation', False),
                        remediation_deadline=datetime.fromisoformat(obs_data['remediation_deadline']) if obs_data.get('remediation_deadline') else None
                    )
                    db.add(observation)
                
                await db.commit()
                
                return {
                    "version_id": str(version.version_id),
                    "version_number": version.version_number,
                    "observation_count": len(observations)
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to create observation version: {str(e)}")
                raise

    # Test Report Activities
    @activity.defn
    async def create_report_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        report_data: Dict[str, Any],
        workflow_execution_id: str,
        workflow_run_id: str
    ) -> Dict[str, Any]:
        """Create test report version"""
        async with get_async_session() as db:
            try:
                # Get version number
                result = await db.execute(
                    select(TestReportVersion.version_number)
                    .where(
                        and_(
                            TestReportVersion.cycle_id == cycle_id,
                            TestReportVersion.report_id == report_id
                        )
                    )
                    .order_by(TestReportVersion.version_number.desc())
                )
                latest_version = result.scalar()
                new_version_number = (latest_version or 0) + 1
                
                # Create version
                version = TestReportVersion(
                    version_number=new_version_number,
                    version_status=VersionStatus.DRAFT,
                    workflow_execution_id=workflow_execution_id,
                    workflow_run_id=workflow_run_id,
                    activity_name="create_report_version",
                    created_by_id=user_id,
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Finalize Test Report",
                    report_title=report_data['title'],
                    report_period=report_data['period'],
                    executive_summary=report_data.get('executive_summary'),
                    draft_document_path=report_data.get('draft_path')
                )
                
                db.add(version)
                await db.flush()
                
                # Add sections
                for idx, section_data in enumerate(report_data.get('sections', [])):
                    section = ReportSection(
                        version_id=version.version_id,
                        section_type=section_data['type'],
                        section_title=section_data['title'],
                        section_content=section_data.get('content'),
                        section_order=idx + 1
                    )
                    db.add(section)
                
                # Add required signoffs
                for role in ['test_lead', 'test_executive', 'report_owner']:
                    signoff = ReportSignoff(
                        version_id=version.version_id,
                        signoff_role=role,
                        signoff_status='pending'
                    )
                    db.add(signoff)
                
                await db.commit()
                
                return {
                    "version_id": str(version.version_id),
                    "version_number": version.version_number,
                    "requires_signoffs": True
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to create report version: {str(e)}")
                raise

    @activity.defn
    async def submit_report_signoff(
        self,
        version_id: str,
        signoff_role: str,
        user_id: int,
        approved: bool,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit report signoff"""
        async with get_async_session() as db:
            try:
                # Get signoff record
                result = await db.execute(
                    select(ReportSignoff)
                    .where(
                        and_(
                            ReportSignoff.version_id == uuid.UUID(version_id),
                            ReportSignoff.signoff_role == signoff_role
                        )
                    )
                )
                signoff = result.scalar_one()
                
                # Update signoff
                signoff.signoff_user_id = user_id
                signoff.signoff_status = 'signed' if approved else 'rejected'
                signoff.signoff_date = datetime.utcnow()
                signoff.signoff_notes = notes
                
                # Check if all signoffs complete
                all_signoffs_result = await db.execute(
                    select(ReportSignoff)
                    .where(ReportSignoff.version_id == uuid.UUID(version_id))
                )
                all_signoffs = all_signoffs_result.scalars().all()
                
                all_signed = all(s.signoff_status == 'signed' for s in all_signoffs)
                
                # Update version if all signed
                if all_signed:
                    version_result = await db.execute(
                        select(TestReportVersion)
                        .where(TestReportVersion.version_id == uuid.UUID(version_id))
                    )
                    version = version_result.scalar_one()
                    version.executive_signoff_complete = True
                    version.version_status = VersionStatus.APPROVED
                    version.approved_at = datetime.utcnow()
                    version.approved_by_id = user_id
                
                await db.commit()
                
                return {
                    "signoff_role": signoff_role,
                    "status": signoff.signoff_status,
                    "all_signoffs_complete": all_signed
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to submit signoff: {str(e)}")
                raise