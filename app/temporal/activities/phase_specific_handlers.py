"""
Phase-Specific Activity Handlers
Implements business logic for each phase's activities
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.temporal.activities.activity_handler import (
    BaseActivityHandler, ActivityDependency, DependencyType,
    ActivityHandlerRegistry, ActivityContext
)
from app.temporal.shared import ActivityResult
from app.models.report_attribute import ReportAttribute
from app.models.scoping import ScopingSubmission
from app.models.sample_selection import SampleSelection
from app.models.data_owner import DataOwner
from app.models.request_info import RequestInfo
from app.models.test_execution import TestExecution
# Observation enhanced models removed - use observation_management models

logger = logging.getLogger(__name__)


# Planning Phase Handlers

class GenerateAttributesHandler(BaseActivityHandler):
    """Handler for generating test attributes using LLM"""
    
    async def can_execute(self, context: ActivityContext) -> bool:
        """Can execute if planning phase has started"""
        return True
    
    async def execute(self, context: ActivityContext) -> ActivityResult:
        """Generate attributes using LLM"""
        try:
            # Import LLM service
            from app.services.llm_service import LLMService
            from app.models.report import Report
            
            # Get report details
            result = await self.db.execute(
                select(Report).where(Report.report_id == context.report_id)
            )
            report = result.scalar_one_or_none()
            
            if not report:
                return ActivityResult(success=False, error="Report not found")
            
            # Generate attributes using LLM
            llm_service = LLMService()
            attributes = await llm_service.generate_test_attributes(
                report_name=report.report_name,
                report_description=report.description,
                metadata=context.metadata
            )
            
            # Save generated attributes
            for attr_data in attributes:
                attribute = ReportAttribute(
                    report_id=context.report_id,
                    attribute_name=attr_data["name"],
                    attribute_label=attr_data["label"],
                    attribute_type=attr_data["type"],
                    is_mandatory=attr_data.get("is_mandatory", True),
                    llm_suggested=True,
                    validation_rules=attr_data.get("validation_rules", {})
                )
                self.db.add(attribute)
            
            await self.db.commit()
            
            return ActivityResult(
                success=True,
                data={
                    "attributes_generated": len(attributes),
                    "status": "completed"
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating attributes: {str(e)}")
            return ActivityResult(success=False, error=str(e))
    
    async def compensate(self, context: ActivityContext, result: ActivityResult) -> None:
        """Remove generated attributes"""
        await self.db.execute(
            ReportAttribute.__table__.delete().where(
                and_(
                    ReportAttribute.report_id == context.report_id,
                    ReportAttribute.llm_suggested == True
                )
            )
        )
        await self.db.commit()
    
    def get_dependencies(self) -> List[ActivityDependency]:
        """No dependencies for attribute generation"""
        return []


# Scoping Phase Handlers

class ExecuteScopingHandler(BaseActivityHandler):
    """Handler for executing scoping logic"""
    
    async def can_execute(self, context: ActivityContext) -> bool:
        """Can execute if attributes exist"""
        result = await self.db.execute(
            select(func.count(ReportAttribute.attribute_id))
            .where(ReportAttribute.report_id == context.report_id)
        )
        count = result.scalar()
        return count > 0
    
    async def execute(self, context: ActivityContext) -> ActivityResult:
        """Execute scoping for attributes"""
        try:
            # Get all attributes
            result = await self.db.execute(
                select(ReportAttribute)
                .where(ReportAttribute.report_id == context.report_id)
            )
            attributes = result.scalars().all()
            
            # Apply scoping logic
            scoped_count = 0
            for attribute in attributes:
                # Default scoping logic - can be enhanced
                if attribute.is_mandatory or context.metadata.get("include_optional", False):
                    attribute.is_scoped = True
                    scoped_count += 1
                
                # Create scoping result
                scoping_result = ScopingResult(
                    cycle_id=context.cycle_id,
                    report_id=context.report_id,
                    attribute_id=attribute.attribute_id,
                    is_scoped=attribute.is_scoped,
                    scoping_rationale=f"{'Mandatory' if attribute.is_mandatory else 'Optional'} attribute",
                    confidence_score=0.9 if attribute.is_mandatory else 0.7
                )
                self.db.add(scoping_result)
            
            await self.db.commit()
            
            return ActivityResult(
                success=True,
                data={
                    "total_attributes": len(attributes),
                    "scoped_attributes": scoped_count,
                    "status": "completed"
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing scoping: {str(e)}")
            return ActivityResult(success=False, error=str(e))
    
    async def compensate(self, context: ActivityContext, result: ActivityResult) -> None:
        """Reset scoping results"""
        await self.db.execute(
            ReportAttribute.__table__.update()
            .where(ReportAttribute.report_id == context.report_id)
            .values(is_scoped=False)
        )
        await self.db.commit()
    
    def get_dependencies(self) -> List[ActivityDependency]:
        """Depends on planning phase completion"""
        return [
            ActivityDependency(
                depends_on_phase="Planning",
                depends_on_activity="Complete Planning Phase",
                dependency_type=DependencyType.COMPLETION
            )
        ]


# Sample Selection Phase Handlers

class GenerateSamplesHandler(BaseActivityHandler):
    """Handler for generating test samples"""
    
    async def can_execute(self, context: ActivityContext) -> bool:
        """Can execute if scoped attributes exist"""
        result = await self.db.execute(
            select(func.count(ReportAttribute.attribute_id))
            .where(
                and_(
                    ReportAttribute.report_id == context.report_id,
                    ReportAttribute.is_scoped == True
                )
            )
        )
        count = result.scalar()
        return count > 0
    
    async def execute(self, context: ActivityContext) -> ActivityResult:
        """Generate samples for testing"""
        try:
            # Get LOBs for tagging samples
            from app.models.lob import LOB
            result = await self.db.execute(select(LOB).where(LOB.is_active == True))
            lobs = result.scalars().all()
            
            # Generate samples based on configuration
            sample_count = context.metadata.get("target_sample_size", 25)
            samples_created = 0
            
            for i in range(sample_count):
                # Assign LOB in round-robin fashion
                lob = lobs[i % len(lobs)] if lobs else None
                
                sample = SampleSelection(
                    cycle_id=context.cycle_id,
                    report_id=context.report_id,
                    sample_identifier=f"SAMPLE_{context.cycle_id}_{context.report_id}_{i+1}",
                    sample_period_start=datetime.utcnow().replace(day=1),
                    sample_period_end=datetime.utcnow(),
                    lob_id=lob.lob_id if lob else None,
                    selection_criteria={"method": "random", "index": i},
                    created_by=1  # System user
                )
                self.db.add(sample)
                samples_created += 1
            
            await self.db.commit()
            
            return ActivityResult(
                success=True,
                data={
                    "samples_created": samples_created,
                    "lobs_assigned": len(lobs),
                    "status": "completed"
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating samples: {str(e)}")
            return ActivityResult(success=False, error=str(e))
    
    async def compensate(self, context: ActivityContext, result: ActivityResult) -> None:
        """Remove generated samples"""
        await self.db.execute(
            SampleSelection.__table__.delete().where(
                and_(
                    SampleSelection.cycle_id == context.cycle_id,
                    SampleSelection.report_id == context.report_id
                )
            )
        )
        await self.db.commit()
    
    def get_dependencies(self) -> List[ActivityDependency]:
        """Depends on scoping completion"""
        return [
            ActivityDependency(
                depends_on_phase="Scoping",
                depends_on_activity="Complete Scoping Phase",
                dependency_type=DependencyType.COMPLETION
            )
        ]


# Request for Information Phase Handlers (Parallel)

class SendDataRequestHandler(BaseActivityHandler):
    """Handler for sending data requests to data owners"""
    
    async def can_execute(self, context: ActivityContext) -> bool:
        """Can execute if data owner is assigned"""
        if not context.instance_id:
            return False
        
        # Extract data owner ID from instance
        data_owner_id = context.metadata.get("instance_data", {}).get("data_owner_id")
        if not data_owner_id:
            return False
        
        # Check if assignments exist for this data owner
        result = await self.db.execute(
            select(func.count(DataProviderAssignment.assignment_id))
            .where(
                and_(
                    DataProviderAssignment.cycle_id == context.cycle_id,
                    DataProviderAssignment.report_id == context.report_id,
                    DataProviderAssignment.data_provider_id == data_owner_id
                )
            )
        )
        count = result.scalar()
        return count > 0
    
    async def execute(self, context: ActivityContext) -> ActivityResult:
        """Send data request to specific data owner"""
        try:
            data_owner_id = context.metadata.get("instance_data", {}).get("data_owner_id")
            
            # Create notification for data owner
            from app.services.notification_service import NotificationService
            notification_service = NotificationService(self.db)
            
            await notification_service.send_notification(
                user_id=data_owner_id,
                notification_type="data_request",
                title="Data Upload Request",
                message=f"Please upload data for cycle {context.cycle_id}, report {context.report_id}",
                metadata={
                    "cycle_id": context.cycle_id,
                    "report_id": context.report_id,
                    "phase": "Request for Information"
                }
            )
            
            return ActivityResult(
                success=True,
                data={
                    "data_owner_id": data_owner_id,
                    "notification_sent": True,
                    "status": "pending_data_upload"
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending data request: {str(e)}")
            return ActivityResult(success=False, error=str(e))
    
    async def compensate(self, context: ActivityContext, result: ActivityResult) -> None:
        """No compensation needed for notifications"""
        pass
    
    def get_dependencies(self) -> List[ActivityDependency]:
        """Depends on data owner identification"""
        return [
            ActivityDependency(
                depends_on_phase="Data Owner Identification",
                depends_on_activity="Complete Provider ID",
                dependency_type=DependencyType.COMPLETION,
                wait_for_all_instances=False  # Can start as soon as any data owner is assigned
            )
        ]


# Test Execution Phase Handlers (Parallel)

class ExecuteTestsHandler(BaseActivityHandler):
    """Handler for executing tests on uploaded documents"""
    
    async def can_execute(self, context: ActivityContext) -> bool:
        """Can execute if document exists and test cases are created"""
        if not context.instance_id:
            return False
        
        document_id = context.metadata.get("instance_data", {}).get("document_id")
        if not document_id:
            return False
        
        # Check if test cases exist
        result = await self.db.execute(
            select(func.count(TestCase.test_case_id))
            .where(
                and_(
                    TestCase.cycle_id == context.cycle_id,
                    TestCase.report_id == context.report_id
                )
            )
        )
        count = result.scalar()
        return count > 0
    
    async def execute(self, context: ActivityContext) -> ActivityResult:
        """Execute tests for specific document"""
        try:
            document_id = context.metadata.get("instance_data", {}).get("document_id")
            
            # Get test cases
            result = await self.db.execute(
                select(TestCase)
                .where(
                    and_(
                        TestCase.cycle_id == context.cycle_id,
                        TestCase.report_id == context.report_id
                    )
                )
                .limit(10)  # Process in batches
            )
            test_cases = result.scalars().all()
            
            executed_count = 0
            for test_case in test_cases:
                # Create test execution record
                test_execution = TestExecution(
                    cycle_id=context.cycle_id,
                    report_id=context.report_id,
                    test_case_id=test_case.test_case_id,
                    document_id=document_id,
                    execution_date=datetime.utcnow(),
                    status="Completed",
                    test_result="Pass" if executed_count % 3 != 0 else "Fail",  # Simulate results
                    executed_by=1  # System user
                )
                self.db.add(test_execution)
                executed_count += 1
            
            await self.db.commit()
            
            return ActivityResult(
                success=True,
                data={
                    "document_id": document_id,
                    "tests_executed": executed_count,
                    "status": "completed"
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing tests: {str(e)}")
            return ActivityResult(success=False, error=str(e))
    
    async def compensate(self, context: ActivityContext, result: ActivityResult) -> None:
        """Remove test execution records"""
        document_id = context.metadata.get("instance_data", {}).get("document_id")
        if document_id:
            await self.db.execute(
                TestExecution.__table__.delete().where(
                    and_(
                        TestExecution.cycle_id == context.cycle_id,
                        TestExecution.report_id == context.report_id,
                        TestExecution.document_id == document_id
                    )
                )
            )
            await self.db.commit()
    
    def get_dependencies(self) -> List[ActivityDependency]:
        """Depends on data upload for specific data owner"""
        return [
            ActivityDependency(
                depends_on_phase="Request for Information",
                depends_on_activity="Data Upload Complete",
                dependency_type=DependencyType.DATA_READY,
                wait_for_all_instances=False  # Can start as soon as any document is uploaded
            )
        ]


# Data Profiling Phase Handlers

class ReportOwnerRuleApprovalHandler(BaseActivityHandler):
    """Handler for Report Owner approval of data profiling rules"""
    
    async def can_execute(self, context: ActivityContext) -> bool:
        """Check if rules have been sent for approval"""
        # Check if there's an assignment for Report Owner
        from app.models.universal_assignment import UniversalAssignment
        result = await self.db.execute(
            select(UniversalAssignment)
            .where(
                and_(
                    UniversalAssignment.assignment_type == 'Rule Approval',
                    UniversalAssignment.to_role == 'Report Owner',
                    UniversalAssignment.context_type == 'Report',
                    UniversalAssignment.context_data['cycle_id'].astext == str(context.cycle_id),
                    UniversalAssignment.context_data['report_id'].astext == str(context.report_id),
                    UniversalAssignment.context_data['phase'].astext == 'data_profiling',
                    UniversalAssignment.status.in_([
                        'Created',
                        'Assigned',
                        'Acknowledged',
                        'In Progress'
                    ])
                )
            )
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            return False
        
        # Check if assignment has version_id and approved rules exist
        version_id = assignment.context_data.get('version_id')
        if not version_id:
            return False
            
        # Check if there are approved rules in this version
        from app.models.data_profiling import ProfilingRule, Decision
        from sqlalchemy import func
        approved_count_query = await self.db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                and_(
                    ProfilingRule.version_id == version_id,
                    ProfilingRule.tester_decision == Decision.APPROVED
                )
            )
        )
        approved_count = approved_count_query.scalar() or 0
        return approved_count > 0
    
    async def execute(self, context: ActivityContext) -> ActivityResult:
        """Monitor Report Owner approval status"""
        try:
            from app.models.universal_assignment import UniversalAssignment
            from app.models.data_profiling import ProfilingRule, ProfilingRuleStatus
            from app.models.versioning import create_version
            from app.services.workflow_service import WorkflowService
            
            # Find the assignment
            result = await self.db.execute(
                select(UniversalAssignment)
                .where(
                    and_(
                        UniversalAssignment.assignment_type == 'Rule Approval',
                        UniversalAssignment.to_role == 'Report Owner',
                        UniversalAssignment.context_type == 'Report',
                        UniversalAssignment.context_data['cycle_id'].astext == str(context.cycle_id),
                        UniversalAssignment.context_data['report_id'].astext == str(context.report_id),
                        UniversalAssignment.context_data['phase'].astext == 'data_profiling'
                    )
                )
                .order_by(UniversalAssignment.created_at.desc())
            )
            assignment = result.scalar_one_or_none()
            
            if not assignment:
                return ActivityResult(
                    success=False,
                    data={
                        "status": "waiting",
                        "message": "Waiting for Tester to send rules for approval"
                    }
                )
            
            # Get version_id from assignment
            version_id = assignment.context_data.get('version_id')
            if not version_id:
                return ActivityResult(
                    success=False,
                    data={
                        "status": "error",
                        "message": "No version_id found in assignment"
                    }
                )
            
            # Get rules statistics from database
            from app.models.data_profiling import Decision
            from sqlalchemy import func
            
            # Count total tester-approved rules
            total_rules_query = await self.db.execute(
                select(func.count(ProfilingRule.rule_id))
                .where(
                    and_(
                        ProfilingRule.version_id == version_id,
                        ProfilingRule.tester_decision == Decision.APPROVED
                    )
                )
            )
            total_rules = total_rules_query.scalar() or 0
            
            # Count rules with report owner decisions
            decided_rules_query = await self.db.execute(
                select(func.count(ProfilingRule.rule_id))
                .where(
                    and_(
                        ProfilingRule.version_id == version_id,
                        ProfilingRule.tester_decision == Decision.APPROVED,
                        ProfilingRule.report_owner_decision.isnot(None)
                    )
                )
            )
            decided_rules = decided_rules_query.scalar() or 0
            
            # Count approved by report owner
            approved_by_owner_query = await self.db.execute(
                select(func.count(ProfilingRule.rule_id))
                .where(
                    and_(
                        ProfilingRule.version_id == version_id,
                        ProfilingRule.tester_decision == Decision.APPROVED,
                        ProfilingRule.report_owner_decision == Decision.APPROVED
                    )
                )
            )
            approved_by_owner = approved_by_owner_query.scalar() or 0
            
            # Count rejected by report owner
            rejected_by_owner_query = await self.db.execute(
                select(func.count(ProfilingRule.rule_id))
                .where(
                    and_(
                        ProfilingRule.version_id == version_id,
                        ProfilingRule.tester_decision == Decision.APPROVED,
                        ProfilingRule.report_owner_decision == Decision.REJECTED
                    )
                )
            )
            rejected_by_owner = rejected_by_owner_query.scalar() or 0
            
            # Check if all rules have been decided
            if decided_rules == total_rules:
                if rejected_by_owner == 0:
                    # All approved - complete the activity
                    assignment.status = 'Completed'
                    assignment.completed_at = datetime.utcnow()
                    
                    # Update all tester-approved rules that are also report-owner-approved to final approved status
                    if version_id:
                        await self.db.execute(
                            ProfilingRule.__table__.update()
                            .where(
                                and_(
                                    ProfilingRule.version_id == version_id,
                                    ProfilingRule.tester_decision == Decision.APPROVED,
                                    ProfilingRule.report_owner_decision == Decision.APPROVED
                                )
                            )
                            .values(
                                status=ProfilingRuleStatus.APPROVED,
                                updated_at=datetime.utcnow(),
                                updated_by_id=assignment.to_user_id
                            )
                        )
                    
                    await self.db.commit()
                    
                    return ActivityResult(
                        success=True,
                        data={
                            "status": "completed",
                            "message": f"All {approved_by_owner} rules approved by Report Owner"
                        }
                    )
                else:
                    # Some rejected - create feedback assignment
                    # Get rejected rules from database
                    rejected_rules_query = await self.db.execute(
                        select(ProfilingRule)
                        .where(
                            and_(
                                ProfilingRule.version_id == version_id,
                                ProfilingRule.tester_decision == Decision.APPROVED,
                                ProfilingRule.report_owner_decision == Decision.REJECTED
                            )
                        )
                    )
                    rejected_rules = rejected_rules_query.scalars().all()
                    
                    # Create new versions for rejected rules
                    for rule in rejected_rules:
                        # Create new version
                        new_version = await create_version(
                            self.db,
                            ProfilingRule,
                            rule,
                            reason_for_change=rule.report_owner_notes or 'Rejected by Report Owner',
                            changed_by=assignment.to_user_id
                        )
                        
                        # Update status to indicate revision needed
                        new_version.status = ProfilingRuleStatus.NEEDS_REVISION
                        new_version.revision_notes = rule.report_owner_notes or ''
                    
                    # No need to create feedback assignment - Tester will see the rejected rules with feedback
                    # in the Data Profiling page when they check the status of rules
                    
                    # Update original assignment
                    assignment.status = 'Rejected'
                    assignment.rejection_reason = f"{rejected_by_owner} rules rejected"
                    
                    await self.db.commit()
                    
                    return ActivityResult(
                        success=False,
                        data={
                            "status": "needs_revision",
                            "message": f"{rejected_by_owner} rules rejected and need revision",
                            "rejected_rules": rejected_by_owner
                        }
                    )
            
            # Still in progress
            progress_percentage = (decided_rules / total_rules * 100) if total_rules > 0 else 0
            
            return ActivityResult(
                success=False,
                data={
                    "status": "in_progress",
                    "message": f"Report Owner review in progress: {decided_rules}/{total_rules} rules decided",
                    "progress": progress_percentage,
                    "approved": approved_by_owner,
                    "rejected": rejected_by_owner,
                    "pending": total_rules - decided_rules
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Report Owner rule approval: {str(e)}")
            return ActivityResult(success=False, error=str(e))
    
    async def compensate(self, context: ActivityContext, result: ActivityResult) -> None:
        """Reset approval status if needed"""
        pass
    
    def get_dependencies(self) -> List[ActivityDependency]:
        """Depends on Tester review completion"""
        return [
            ActivityDependency(
                depends_on_phase="Data Profiling",
                depends_on_activity="Review Profiling Results",
                dependency_type=DependencyType.COMPLETION
            )
        ]


# Register all handlers
def register_phase_handlers():
    """Register all phase-specific handlers"""
    
    # Planning Phase
    ActivityHandlerRegistry.register("Planning", "generate_attributes", GenerateAttributesHandler)
    
    # Scoping Phase
    ActivityHandlerRegistry.register("Scoping", "execute_scoping", ExecuteScopingHandler)
    
    # Sample Selection Phase
    ActivityHandlerRegistry.register("Sample Selection", "generate_samples", GenerateSamplesHandler)
    
    # Request for Information Phase
    ActivityHandlerRegistry.register("Request for Information", "send_data_request", SendDataRequestHandler)
    
    # Test Execution Phase
    ActivityHandlerRegistry.register("Test Execution", "execute_tests", ExecuteTestsHandler)
    
    # Data Profiling Phase
    ActivityHandlerRegistry.register("Data Profiling", "APPROVAL", ReportOwnerRuleApprovalHandler)
    
    logger.info("Registered all phase-specific handlers")


# Auto-register on import
register_phase_handlers()