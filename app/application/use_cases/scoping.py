"""Scoping phase use cases"""
from typing import List, Dict, Any
from datetime import datetime

from app.application.dto.report_dto import ReportAttributeDTO
from app.application.interfaces.repositories import (
    TestCycleRepository,
    ReportRepository,
    WorkflowRepository
)
from app.application.interfaces.services import (
    LLMService,
    NotificationService,
    AuditService
)
from app.domain.events.base import DomainEvent
from .base import UseCase, UseCaseResult


class GenerateTestAttributesUseCase(UseCase[Dict[str, Any], List[ReportAttributeDTO]]):
    """Use case for generating test attributes using LLM"""
    
    def __init__(
        self,
        cycle_repository: TestCycleRepository,
        report_repository: ReportRepository,
        workflow_repository: WorkflowRepository,
        llm_service: LLMService,
        notification_service: NotificationService,
        audit_service: AuditService
    ):
        self.cycle_repository = cycle_repository
        self.report_repository = report_repository
        self.workflow_repository = workflow_repository
        self.llm_service = llm_service
        self.notification_service = notification_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[List[ReportAttributeDTO]]:
        """Generate test attributes for a report"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Validate cycle exists
            cycle = await self.cycle_repository.get(cycle_id)
            if not cycle:
                return self._failure("Test cycle not found")
            
            # Validate report exists and is in cycle
            report = await self.report_repository.get(report_id)
            if not report:
                return self._failure("Report not found")
            
            report_in_cycle = any(r.report_id == report_id for r in cycle.reports)
            if not report_in_cycle:
                return self._failure("Report is not in this test cycle")
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Scoping"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Scoping phase is not active for this report")
            
            # Generate attributes using LLM
            llm_result = await self.llm_service.generate_test_attributes(
                regulatory_context=report.get('regulation', ''),
                report_type=report.get('report_type', ''),
                sample_size=request.get('sample_size', 25),
                existing_attributes=request.get('existing_attributes'),
                preferred_provider=request.get('preferred_provider', 'claude')
            )
            
            if not llm_result.get('success'):
                return self._failure(f"LLM generation failed: {llm_result.get('error')}")
            
            # Convert to DTOs
            attribute_dtos = []
            for idx, attr in enumerate(llm_result.get('attributes', [])):
                dto = ReportAttributeDTO(
                    attribute_id=0,  # Will be assigned when saved
                    cycle_id=cycle_id,
                    report_id=report_id,
                    attribute_name=attr.get('name'),
                    description=attr.get('description'),
                    data_type=attr.get('data_type', 'string'),
                    is_critical=attr.get('is_critical', False),
                    validation_rules=attr.get('validation_rules'),
                    expected_value=attr.get('expected_value'),
                    test_approach=attr.get('test_approach'),
                    risk_score=attr.get('risk_score', 5)
                )
                attribute_dtos.append(dto)
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="GENERATE_TEST_ATTRIBUTES",
                resource_type="report_attributes",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "report_name": report.get('report_name'),
                    "attributes_generated": len(attribute_dtos),
                    "provider_used": llm_result.get('provider_used')
                }
            )
            
            # Send notification
            await self.notification_service.send_notification(
                user_id=user_id,
                title="Test Attributes Generated",
                message=f"Generated {len(attribute_dtos)} test attributes for {report.get('report_name')}",
                notification_type="attributes_generated",
                priority="medium"
            )
            
            return self._success(attribute_dtos)
            
        except Exception as e:
            return self._failure(f"Failed to generate test attributes: {str(e)}")


class ReviewAttributesUseCase(UseCase[Dict[str, Any], bool]):
    """Use case for reviewing and modifying test attributes"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        audit_service: AuditService
    ):
        self.workflow_repository = workflow_repository
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[bool]:
        """Review and update test attributes"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            updates = request['attribute_updates']
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Scoping"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Scoping phase is not active for this report")
            
            # Update phase metadata with review status
            current_metadata = phase_status.get('metadata', {})
            current_metadata['attributes_reviewed'] = True
            current_metadata['reviewed_by'] = user_id
            current_metadata['reviewed_at'] = datetime.utcnow().isoformat()
            current_metadata['total_attributes'] = len(updates)
            
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Scoping",
                status={
                    "status": "in_progress",
                    "metadata": current_metadata
                }
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="REVIEW_TEST_ATTRIBUTES",
                resource_type="report_attributes",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "attributes_reviewed": len(updates)
                }
            )
            
            return self._success(True)
            
        except Exception as e:
            return self._failure(f"Failed to review attributes: {str(e)}")


class ApproveAttributesUseCase(UseCase[Dict[str, Any], bool]):
    """Use case for approving test attributes and completing scoping phase"""
    
    def __init__(
        self,
        cycle_repository: TestCycleRepository,
        workflow_repository: WorkflowRepository,
        notification_service: NotificationService,
        audit_service: AuditService
    ):
        self.cycle_repository = cycle_repository
        self.workflow_repository = workflow_repository
        self.notification_service = notification_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[bool]:
        """Approve attributes and complete scoping phase"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Get cycle for notification purposes
            cycle = await self.cycle_repository.get(cycle_id)
            if not cycle:
                return self._failure("Test cycle not found")
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Scoping"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Scoping phase is not active for this report")
            
            # Verify attributes have been reviewed
            metadata = phase_status.get('metadata', {})
            if not metadata.get('attributes_reviewed'):
                return self._failure("Attributes must be reviewed before approval")
            
            # Complete scoping phase
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Scoping",
                status={
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        **metadata,
                        "approved_by": user_id,
                        "approved_at": datetime.utcnow().isoformat()
                    }
                }
            )
            
            # Start parallel phases: Sample Selection and Data Owner Identification
            for phase_name in ["Sample Selection", "Data Owner Identification"]:
                await self.workflow_repository.save_phase_status(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name=phase_name,
                    status={
                        "status": "in_progress",
                        "started_at": datetime.utcnow().isoformat()
                    }
                )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="APPROVE_TEST_ATTRIBUTES",
                resource_type="workflow_phase",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "phase_completed": "Scoping",
                    "next_phases": ["Sample Selection", "Data Owner Identification"]
                }
            )
            
            # Find tester for this report
            report_assignment = next((r for r in cycle.reports if r.report_id == report_id), None)
            if report_assignment and report_assignment.tester_id:
                # Send notification to tester
                await self.notification_service.send_notification(
                    user_id=report_assignment.tester_id,
                    title="Scoping Phase Completed",
                    message=f"Scoping phase completed for report in cycle '{cycle.cycle_name}'. Sample Selection and Data Owner Identification phases are now active.",
                    notification_type="phase_completed",
                    priority="high"
                )
            
            return self._success(True)
            
        except Exception as e:
            return self._failure(f"Failed to approve attributes: {str(e)}")