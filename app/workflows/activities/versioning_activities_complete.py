"""
Complete Temporal activities for all 9 phases with versioning
"""
from temporalio import activity
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.versioning_complete import (
    PlanningPhaseVersion, AttributeDecision,
    DataProfilingVersion, ProfilingRuleDecision,
    ScopingVersion, ScopingDecision,
    SampleSelectionVersion, SampleDecision,
    DataOwnerAssignment, DataOwnerChangeHistory,
    DocumentSubmission, DocumentRevisionHistory,
    TestExecutionAudit,
    ObservationVersion, ObservationDecision,
    TestReportVersion, TestReportSection, TestReportSignOff,
    WorkflowVersionOperation,
    VersionStatus, ApprovalStatus, SampleSource
)
from app.services.temporal_versioning_service import TemporalVersioningService


class BaseVersioningActivities:
    """Base class for versioning activities"""
    
    @staticmethod
    def get_workflow_context() -> Dict[str, Any]:
        """Get workflow context from activity info"""
        info = activity.info()
        return {
            "workflow_execution_id": info.workflow_id,
            "workflow_run_id": info.workflow_run_id,
            "activity_name": info.activity_type,
            "attempt": info.attempt
        }
    
    @staticmethod
    async def record_operation(
        db: AsyncSession,
        operation_type: str,
        phase_name: str,
        version_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowVersionOperation:
        """Record a version operation"""
        context = BaseVersioningActivities.get_workflow_context()
        
        operation = WorkflowVersionOperation(
            workflow_execution_id=context["workflow_execution_id"],
            operation_type=operation_type,
            phase_name=phase_name,
            version_id=version_id,
            operation_metadata=metadata or {}
        )
        
        db.add(operation)
        await db.flush()
        return operation


# 1. Planning Phase Activities
class PlanningActivities(BaseVersioningActivities):
    """Planning phase activities with versioning"""
    
    @activity.defn
    async def create_planning_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        attributes: List[Dict[str, Any]],
        parent_version_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create planning phase version with attribute decisions"""
        async with get_db() as db:
            try:
                context = self.get_workflow_context()
                
                # Record operation start
                operation = await self.record_operation(
                    db, "create", "Planning", metadata={"attribute_count": len(attributes)}
                )
                
                # Get version number
                existing = await db.execute(
                    select(PlanningPhaseVersion).where(
                        and_(
                            PlanningPhaseVersion.cycle_id == cycle_id,
                            PlanningPhaseVersion.report_id == report_id
                        )
                    ).order_by(PlanningPhaseVersion.version_number.desc())
                )
                latest = existing.scalar_one_or_none()
                version_number = (latest.version_number + 1) if latest else 1
                
                # Create version
                version = PlanningPhaseVersion(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    version_number=version_number,
                    version_status=VersionStatus.DRAFT,
                    parent_version_id=UUID(parent_version_id) if parent_version_id else None,
                    workflow_execution_id=context["workflow_execution_id"],
                    workflow_run_id=context["workflow_run_id"],
                    activity_name=context["activity_name"],
                    version_created_by=user_id,
                    total_attributes=len(attributes),
                    included_attributes=len([a for a in attributes if a.get("include", True)]),
                    excluded_attributes=len([a for a in attributes if not a.get("include", True)])
                )
                
                db.add(version)
                await db.flush()
                
                # Create attribute decisions
                for attr in attributes:
                    decision = AttributeDecision(
                        planning_version_id=version.version_id,
                        attribute_id=attr["attribute_id"],
                        attribute_data=attr.get("data", {}),
                        decision_type=attr.get("decision_type", "include"),
                        decision_reason=attr.get("reason", "Initial selection")
                    )
                    
                    if parent_version_id and attr.get("carried_from_id"):
                        decision.carried_from_version_id = UUID(parent_version_id)
                    
                    db.add(decision)
                
                # Complete operation
                operation.completed_at = datetime.utcnow()
                operation.success = True
                operation.version_id = version.version_id
                
                await db.commit()
                
                return {
                    "version_id": str(version.version_id),
                    "version_number": version.version_number,
                    "attribute_count": len(attributes),
                    "status": "created"
                }
                
            except Exception as e:
                operation.completed_at = datetime.utcnow()
                operation.success = False
                operation.error_message = str(e)
                await db.commit()
                raise
    
    @activity.defn
    async def approve_planning_version(
        self,
        version_id: str,
        user_id: int,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve planning version (auto-approved by tester)"""
        async with get_db() as db:
            operation = await self.record_operation(
                db, "approve", "Planning", UUID(version_id)
            )
            
            try:
                version = await db.get(PlanningPhaseVersion, UUID(version_id))
                if not version:
                    raise ValueError(f"Version {version_id} not found")
                
                version.version_status = VersionStatus.APPROVED
                version.version_reviewed_by = user_id
                version.version_reviewed_at = datetime.utcnow()
                version.version_review_notes = notes or "Auto-approved by tester"
                
                operation.completed_at = datetime.utcnow()
                operation.success = True
                
                await db.commit()
                
                return {
                    "success": True,
                    "approved_at": version.version_reviewed_at.isoformat()
                }
                
            except Exception as e:
                operation.completed_at = datetime.utcnow()
                operation.success = False
                operation.error_message = str(e)
                await db.commit()
                raise


# 2. Data Profiling Activities
class DataProfilingActivities(BaseVersioningActivities):
    """Data profiling activities with versioning"""
    
    @activity.defn
    async def create_profiling_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        profiling_rules: List[Dict[str, Any]],
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create data profiling version with rules"""
        async with get_db() as db:
            context = self.get_workflow_context()
            
            # Create version
            version = DataProfilingVersion(
                cycle_id=cycle_id,
                report_id=report_id,
                version_number=1,
                version_status=VersionStatus.DRAFT,
                workflow_execution_id=context["workflow_execution_id"],
                version_created_by=user_id,
                source_data_reference=source_data,
                total_rules=len(profiling_rules)
            )
            
            db.add(version)
            await db.flush()
            
            # Create rule decisions
            for rule in profiling_rules:
                decision = ProfilingRuleDecision(
                    profiling_version_id=version.version_id,
                    rule_type=rule["type"],
                    rule_definition=rule["definition"],
                    rule_name=rule.get("name", ""),
                    rule_description=rule.get("description", ""),
                    recommended_by_id=user_id,
                    recommendation_reason="Generated from data profiling"
                )
                db.add(decision)
            
            await db.commit()
            
            return {
                "version_id": str(version.version_id),
                "rule_count": len(profiling_rules),
                "status": "created"
            }
    
    @activity.defn
    async def process_profiling_review(
        self,
        version_id: str,
        user_id: int,
        rule_decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process profiling rule reviews"""
        async with get_db() as db:
            approved_count = 0
            rejected_count = 0
            
            for decision_data in rule_decisions:
                decision = await db.get(
                    ProfilingRuleDecision,
                    UUID(decision_data["decision_id"])
                )
                
                if decision:
                    decision.approval_status = ApprovalStatus(decision_data["status"])
                    decision.approved_by_id = user_id
                    decision.approval_timestamp = datetime.utcnow()
                    decision.approval_notes = decision_data.get("notes")
                    
                    if decision_data["status"] == "approved":
                        approved_count += 1
                    else:
                        rejected_count += 1
            
            # Update version status
            version = await db.get(DataProfilingVersion, UUID(version_id))
            if version:
                version.approved_rules = approved_count
                if approved_count > 0:
                    version.version_status = VersionStatus.APPROVED
                    version.version_reviewed_by = user_id
                    version.version_reviewed_at = datetime.utcnow()
            
            await db.commit()
            
            return {
                "version_id": version_id,
                "approved_count": approved_count,
                "rejected_count": rejected_count
            }


# 3. Scoping Activities
class ScopingActivities(BaseVersioningActivities):
    """Scoping activities with versioning"""
    
    @activity.defn
    async def create_scoping_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        scoping_decisions: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create scoping version with decisions"""
        async with get_db() as db:
            context = self.get_workflow_context()
            
            in_scope_count = len([d for d in scoping_decisions if d.get("in_scope", False)])
            
            version = ScopingVersion(
                cycle_id=cycle_id,
                report_id=report_id,
                version_number=1,
                version_status=VersionStatus.DRAFT,
                workflow_execution_id=context["workflow_execution_id"],
                version_created_by=user_id,
                scoping_criteria=criteria,
                total_attributes=len(scoping_decisions),
                scoped_attributes=in_scope_count,
                out_of_scope_attributes=len(scoping_decisions) - in_scope_count
            )
            
            db.add(version)
            await db.flush()
            
            # Create scoping decisions
            for scope_data in scoping_decisions:
                decision = ScopingDecision(
                    scoping_version_id=version.version_id,
                    attribute_id=scope_data["attribute_id"],
                    is_in_scope=scope_data.get("in_scope", False),
                    scoping_rationale=scope_data.get("rationale", ""),
                    risk_rating=scope_data.get("risk_rating", "medium"),
                    recommended_by_id=user_id,
                    recommendation_type="tester"
                )
                db.add(decision)
            
            await db.commit()
            
            return {
                "version_id": str(version.version_id),
                "total_attributes": len(scoping_decisions),
                "in_scope": in_scope_count,
                "status": "created"
            }


# 4. Sample Selection Activities (Complex)
class SampleSelectionActivities(BaseVersioningActivities):
    """Sample selection activities with enhanced versioning"""
    
    @activity.defn
    async def create_sample_selection_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        samples: List[Dict[str, Any]],
        selection_criteria: Dict[str, Any],
        parent_version_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create sample selection version with individual decisions"""
        async with get_db() as db:
            context = self.get_workflow_context()
            operation = await self.record_operation(
                db, "create", "Sample Selection", 
                metadata={"sample_count": len(samples)}
            )
            
            try:
                # Determine version number
                version_number = 1
                if parent_version_id:
                    parent = await db.get(SampleSelectionVersion, UUID(parent_version_id))
                    if parent:
                        version_number = parent.version_number + 1
                
                # Create version
                version = SampleSelectionVersion(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    version_number=version_number,
                    version_status=VersionStatus.DRAFT,
                    parent_version_id=UUID(parent_version_id) if parent_version_id else None,
                    workflow_execution_id=context["workflow_execution_id"],
                    version_created_by=user_id,
                    selection_criteria=selection_criteria,
                    target_sample_size=selection_criteria.get("target_size", len(samples)),
                    actual_sample_size=len(samples),
                    generation_methods=["tester_recommended"]
                )
                
                db.add(version)
                await db.flush()
                
                # Create sample decisions
                for idx, sample in enumerate(samples):
                    source = SampleSource.CARRIED_FORWARD if sample.get("carried_from_id") else SampleSource.TESTER
                    
                    decision = SampleDecision(
                        selection_version_id=version.version_id,
                        sample_identifier=sample.get("id", f"sample_{idx}"),
                        sample_data=sample.get("data", {}),
                        sample_type=sample.get("type", "population"),
                        recommendation_source=source,
                        recommended_by_id=user_id,
                        recommendation_timestamp=datetime.utcnow(),
                        decision_status=ApprovalStatus.PENDING
                    )
                    
                    # Track lineage for carried forward samples
                    if parent_version_id and sample.get("carried_from_id"):
                        decision.carried_from_version_id = UUID(parent_version_id)
                        decision.carried_from_decision_id = UUID(sample["carried_from_id"])
                    
                    db.add(decision)
                
                operation.completed_at = datetime.utcnow()
                operation.success = True
                operation.version_id = version.version_id
                
                await db.commit()
                
                return {
                    "version_id": str(version.version_id),
                    "version_number": version.version_number,
                    "sample_count": len(samples),
                    "status": "created"
                }
                
            except Exception as e:
                operation.completed_at = datetime.utcnow()
                operation.success = False
                operation.error_message = str(e)
                await db.commit()
                raise
    
    @activity.defn
    async def process_sample_review(
        self,
        version_id: str,
        user_id: int,
        decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process individual sample decisions"""
        async with get_db() as db:
            approved_count = 0
            rejected_count = 0
            
            for decision_data in decisions:
                decision = await db.get(
                    SampleDecision,
                    UUID(decision_data["decision_id"])
                )
                
                if decision and str(decision.selection_version_id) == version_id:
                    decision.decision_status = ApprovalStatus(decision_data["status"])
                    decision.decided_by_id = user_id
                    decision.decision_timestamp = datetime.utcnow()
                    decision.decision_notes = decision_data.get("notes")
                    
                    if decision_data["status"] == "approved":
                        approved_count += 1
                    elif decision_data["status"] == "rejected":
                        rejected_count += 1
            
            await db.commit()
            
            return {
                "version_id": version_id,
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "review_complete": True
            }
    
    @activity.defn
    async def create_sample_revision(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        parent_version_id: str,
        additional_samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create revision carrying forward approved samples"""
        async with get_db() as db:
            # Get approved samples from parent
            result = await db.execute(
                select(SampleDecision).where(
                    and_(
                        SampleDecision.selection_version_id == UUID(parent_version_id),
                        SampleDecision.decision_status == ApprovalStatus.APPROVED
                    )
                )
            )
            approved_decisions = result.scalars().all()
            
            # Prepare samples for new version
            samples_for_revision = []
            
            # Carry forward approved samples
            for decision in approved_decisions:
                samples_for_revision.append({
                    "id": decision.sample_identifier,
                    "data": decision.sample_data,
                    "type": decision.sample_type,
                    "carried_from_id": str(decision.decision_id)
                })
            
            # Add new samples
            samples_for_revision.extend(additional_samples)
            
            # Create new version
            return await self.create_sample_selection_version(
                cycle_id=cycle_id,
                report_id=report_id,
                user_id=user_id,
                samples=samples_for_revision,
                selection_criteria={"revision": True, "parent_version": parent_version_id},
                parent_version_id=parent_version_id
            )
    
    @activity.defn
    async def approve_sample_selection(
        self,
        version_id: str,
        user_id: int,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve sample selection version"""
        async with get_db() as db:
            version = await db.get(SampleSelectionVersion, UUID(version_id))
            if not version:
                raise ValueError(f"Version {version_id} not found")
            
            version.version_status = VersionStatus.APPROVED
            version.version_reviewed_by = user_id
            version.version_reviewed_at = datetime.utcnow()
            version.version_review_notes = notes
            
            await db.commit()
            
            return {
                "success": True,
                "approved_at": version.version_reviewed_at.isoformat()
            }


# 5. Data Owner ID Activities (Audit Only)
class DataOwnerActivities(BaseVersioningActivities):
    """Data owner identification activities"""
    
    @activity.defn
    async def assign_data_owner(
        self,
        cycle_id: int,
        report_id: int,
        lob_id: str,
        owner_id: int,
        assigned_by: int,
        assignment_type: str = "primary"
    ) -> Dict[str, Any]:
        """Assign data owner with audit trail"""
        async with get_db() as db:
            context = self.get_workflow_context()
            
            # Check for existing assignment
            result = await db.execute(
                select(DataOwnerAssignment).where(
                    and_(
                        DataOwnerAssignment.cycle_id == cycle_id,
                        DataOwnerAssignment.report_id == report_id,
                        DataOwnerAssignment.lob_id == UUID(lob_id),
                        DataOwnerAssignment.status == "active"
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            # Create new assignment
            assignment = DataOwnerAssignment(
                cycle_id=cycle_id,
                report_id=report_id,
                lob_id=UUID(lob_id),
                data_owner_id=owner_id,
                assignment_type=assignment_type,
                workflow_execution_id=context["workflow_execution_id"],
                workflow_step_id=None,  # Will be set by workflow step tracking
                created_by=assigned_by
            )
            
            if existing:
                # Deactivate existing
                existing.status = "inactive"
                existing.effective_to = datetime.utcnow()
                assignment.previous_assignment_id = existing.assignment_id
                assignment.change_reason = "Reassignment"
            
            db.add(assignment)
            await db.flush()
            
            # Create change history
            history = DataOwnerChangeHistory(
                assignment_id=assignment.assignment_id,
                change_type="created" if not existing else "transferred",
                changed_by_id=assigned_by,
                previous_state={"owner_id": existing.data_owner_id} if existing else None,
                new_state={"owner_id": owner_id}
            )
            db.add(history)
            
            await db.commit()
            
            return {
                "assignment_id": str(assignment.assignment_id),
                "owner_id": owner_id,
                "lob_id": lob_id,
                "status": "assigned"
            }


# 6. Request Info Activities (Audit Only)
class RequestInfoActivities(BaseVersioningActivities):
    """Request for information activities"""
    
    @activity.defn
    async def submit_document(
        self,
        cycle_id: int,
        report_id: int,
        lob_id: str,
        document_id: str,
        submitted_by: int,
        document_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit document with version tracking"""
        async with get_db() as db:
            context = self.get_workflow_context()
            
            # Check for existing submissions
            result = await db.execute(
                select(DocumentSubmission).where(
                    and_(
                        DocumentSubmission.document_id == UUID(document_id),
                        DocumentSubmission.is_current == True
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            submission = DocumentSubmission(
                cycle_id=cycle_id,
                report_id=report_id,
                lob_id=UUID(lob_id),
                document_id=UUID(document_id),
                document_version=(existing.document_version + 1) if existing else 1,
                document_metadata=document_metadata,
                submitted_by_id=submitted_by,
                submission_type="revision" if existing else "initial",
                workflow_execution_id=context["workflow_execution_id"]
            )
            
            if existing:
                existing.is_current = False
                submission.replaces_submission_id = existing.submission_id
            
            db.add(submission)
            await db.flush()
            
            # Create revision history
            if existing:
                history = DocumentRevisionHistory(
                    submission_id=submission.submission_id,
                    revision_type="content_update",
                    revision_reason=document_metadata.get("revision_reason", "Updated document"),
                    changed_fields=["content"],
                    revised_by_id=submitted_by
                )
                db.add(history)
            
            await db.commit()
            
            return {
                "submission_id": str(submission.submission_id),
                "document_version": submission.document_version,
                "status": "submitted"
            }


# 7. Test Execution Activities (Audit Only)
class TestExecutionActivities(BaseVersioningActivities):
    """Test execution audit activities"""
    
    @activity.defn
    async def record_test_action(
        self,
        cycle_id: int,
        report_id: int,
        test_execution_id: int,
        action_type: str,
        requested_by: int,
        action_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record test execution actions for audit"""
        async with get_db() as db:
            context = self.get_workflow_context()
            
            audit = TestExecutionAudit(
                cycle_id=cycle_id,
                report_id=report_id,
                test_execution_id=test_execution_id,
                workflow_execution_id=context["workflow_execution_id"],
                action_type=action_type,
                action_details=action_details,
                requested_by_id=requested_by
            )
            
            db.add(audit)
            await db.commit()
            
            return {
                "audit_id": str(audit.audit_id),
                "action_type": action_type,
                "status": "recorded"
            }
    
    @activity.defn
    async def update_test_response(
        self,
        audit_id: str,
        responded_by: int,
        response_status: str,
        response_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update test action response"""
        async with get_db() as db:
            audit = await db.get(TestExecutionAudit, UUID(audit_id))
            if not audit:
                raise ValueError(f"Audit record {audit_id} not found")
            
            audit.responded_by_id = responded_by
            audit.responded_at = datetime.utcnow()
            audit.response_status = response_status
            audit.response_notes = response_notes
            
            # Calculate turnaround time
            if audit.requested_at:
                delta = audit.responded_at - audit.requested_at
                audit.turnaround_time_hours = delta.total_seconds() / 3600
            
            await db.commit()
            
            return {
                "audit_id": audit_id,
                "response_status": response_status,
                "turnaround_hours": audit.turnaround_time_hours
            }


# 8. Observation Management Activities
class ObservationActivities(BaseVersioningActivities):
    """Observation management activities with versioning"""
    
    @activity.defn
    async def create_observation_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        observations: List[Dict[str, Any]],
        period_start: str,
        period_end: str
    ) -> Dict[str, Any]:
        """Create observation version"""
        async with get_db() as db:
            context = self.get_workflow_context()
            
            version = ObservationVersion(
                cycle_id=cycle_id,
                report_id=report_id,
                version_number=1,
                version_status=VersionStatus.DRAFT,
                workflow_execution_id=context["workflow_execution_id"],
                version_created_by=user_id,
                observation_period_start=datetime.fromisoformat(period_start).date(),
                observation_period_end=datetime.fromisoformat(period_end).date(),
                total_observations=len(observations)
            )
            
            db.add(version)
            await db.flush()
            
            # Create observation decisions
            for obs in observations:
                decision = ObservationDecision(
                    observation_version_id=version.version_id,
                    observation_id=obs.get("observation_id"),
                    observation_type=obs["type"],
                    severity=obs["severity"],
                    observation_data=obs["data"],
                    created_by_id=user_id,
                    creation_timestamp=datetime.utcnow(),
                    evidence_references=obs.get("evidence", [])
                )
                db.add(decision)
            
            await db.commit()
            
            return {
                "version_id": str(version.version_id),
                "observation_count": len(observations),
                "status": "created"
            }
    
    @activity.defn
    async def process_observation_review(
        self,
        version_id: str,
        user_id: int,
        observation_decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process observation reviews"""
        async with get_db() as db:
            approved_count = 0
            
            for decision_data in observation_decisions:
                decision = await db.get(
                    ObservationDecision,
                    UUID(decision_data["decision_id"])
                )
                
                if decision:
                    decision.approval_status = ApprovalStatus(decision_data["status"])
                    decision.approved_by_id = user_id
                    decision.approval_timestamp = datetime.utcnow()
                    decision.approval_notes = decision_data.get("notes")
                    
                    if decision_data["status"] == "approved":
                        approved_count += 1
            
            # Update version
            version = await db.get(ObservationVersion, UUID(version_id))
            if version:
                version.approved_observations = approved_count
                if approved_count == version.total_observations:
                    version.version_status = VersionStatus.APPROVED
                    version.version_reviewed_by = user_id
                    version.version_reviewed_at = datetime.utcnow()
            
            await db.commit()
            
            return {
                "version_id": version_id,
                "approved_count": approved_count,
                "all_approved": approved_count == version.total_observations
            }


# 9. Test Report Activities
class TestReportActivities(BaseVersioningActivities):
    """Test report finalization activities"""
    
    @activity.defn
    async def create_report_version(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create test report version"""
        async with get_db() as db:
            context = self.get_workflow_context()
            
            version = TestReportVersion(
                cycle_id=cycle_id,
                report_id=report_id,
                version_number=1,
                version_status=VersionStatus.DRAFT,
                workflow_execution_id=context["workflow_execution_id"],
                version_created_by=user_id,
                report_title=report_data["title"],
                report_period_start=datetime.fromisoformat(report_data["period_start"]).date(),
                report_period_end=datetime.fromisoformat(report_data["period_end"]).date(),
                executive_summary=report_data.get("executive_summary"),
                included_sections=report_data.get("sections", []),
                generation_method="automated"
            )
            
            db.add(version)
            await db.flush()
            
            # Create report sections
            for idx, section_data in enumerate(report_data.get("sections", [])):
                section = TestReportSection(
                    report_version_id=version.version_id,
                    section_type=section_data["type"],
                    section_title=section_data["title"],
                    section_content=section_data.get("content", ""),
                    section_order=idx + 1,
                    content_source=section_data.get("source", "generated"),
                    source_references=section_data.get("references", [])
                )
                db.add(section)
            
            # Create required sign-offs
            for role in ["test_lead", "test_executive", "report_owner"]:
                signoff = TestReportSignOff(
                    report_version_id=version.version_id,
                    signoff_role=role,
                    signoff_status="pending"
                )
                db.add(signoff)
            
            await db.commit()
            
            return {
                "version_id": str(version.version_id),
                "sections_created": len(report_data.get("sections", [])),
                "status": "created"
            }
    
    @activity.defn
    async def submit_report_signoff(
        self,
        version_id: str,
        user_id: int,
        role: str,
        approved: bool,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit report sign-off"""
        async with get_db() as db:
            # Find the sign-off record
            result = await db.execute(
                select(TestReportSignOff).where(
                    and_(
                        TestReportSignOff.report_version_id == UUID(version_id),
                        TestReportSignOff.signoff_role == role
                    )
                )
            )
            signoff = result.scalar_one_or_none()
            
            if not signoff:
                raise ValueError(f"Sign-off for role {role} not found")
            
            signoff.signoff_user_id = user_id
            signoff.signoff_status = "signed" if approved else "rejected"
            signoff.signoff_date = datetime.utcnow()
            signoff.signoff_comments = comments
            
            # Check if all sign-offs complete
            all_signoffs = await db.execute(
                select(TestReportSignOff).where(
                    TestReportSignOff.report_version_id == UUID(version_id)
                )
            )
            
            all_signed = all(
                s.signoff_status == "signed" 
                for s in all_signoffs.scalars()
            )
            
            if all_signed:
                version = await db.get(TestReportVersion, UUID(version_id))
                version.version_status = VersionStatus.APPROVED
                version.executive_approved_by_id = user_id
                version.executive_approval_date = datetime.utcnow()
            
            await db.commit()
            
            return {
                "signoff_id": str(signoff.signoff_id),
                "status": signoff.signoff_status,
                "all_signed": all_signed
            }


# Consolidated activity registry
ALL_VERSIONING_ACTIVITIES = [
    # Planning
    PlanningActivities.create_planning_version,
    PlanningActivities.approve_planning_version,
    
    # Data Profiling
    DataProfilingActivities.create_profiling_version,
    DataProfilingActivities.process_profiling_review,
    
    # Scoping
    ScopingActivities.create_scoping_version,
    
    # Sample Selection
    SampleSelectionActivities.create_sample_selection_version,
    SampleSelectionActivities.process_sample_review,
    SampleSelectionActivities.create_sample_revision,
    SampleSelectionActivities.approve_sample_selection,
    
    # Data Owner ID
    DataOwnerActivities.assign_data_owner,
    
    # Request Info
    RequestInfoActivities.submit_document,
    
    # Test Execution
    TestExecutionActivities.record_test_action,
    TestExecutionActivities.update_test_response,
    
    # Observations
    ObservationActivities.create_observation_version,
    ObservationActivities.process_observation_review,
    
    # Test Report
    TestReportActivities.create_report_version,
    TestReportActivities.submit_report_signoff
]