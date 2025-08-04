"""Workflow management use cases"""
from typing import Dict, Any, List
from datetime import datetime

from app.application.dto.workflow_dto import (
    WorkflowTransitionDTO,
    WorkflowStateDTO,
    PhaseStatusDTO
)
from app.application.interfaces.repositories import (
    WorkflowRepository,
    UserRepository
)
from app.application.interfaces.services import (
    NotificationService,
    AuditService,
    SLAService
)
from .base import UseCase, UseCaseResult


class AdvanceWorkflowPhaseUseCase(UseCase[WorkflowTransitionDTO, WorkflowStateDTO]):
    """Use case for advancing workflow to next phase"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        user_repository: UserRepository,
        notification_service: NotificationService,
        audit_service: AuditService,
        sla_service: SLAService
    ):
        self.workflow_repository = workflow_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.audit_service = audit_service
        self.sla_service = sla_service
    
    async def execute(self, request: WorkflowTransitionDTO) -> UseCaseResult[WorkflowStateDTO]:
        """Advance workflow to next phase"""
        try:
            # Validate user has permission
            user_permissions = await self.user_repository.get_user_permissions(request.requested_by)
            if "workflow.advance" not in user_permissions and not request.override_dependencies:
                return self._failure("User does not have permission to advance workflow")
            
            if request.override_dependencies and "workflow.override" not in user_permissions:
                return self._failure("User does not have permission to override workflow dependencies")
            
            # Check if transition is allowed
            if not request.override_dependencies:
                can_advance = await self.workflow_repository.can_advance_to_phase(
                    request.cycle_id,
                    request.report_id,
                    request.to_phase
                )
                if not can_advance:
                    return self._failure(f"Cannot advance to {request.to_phase}. Prerequisites not met.")
            
            # Get current phase status
            from_phase_status = await self.workflow_repository.get_phase_status(
                request.cycle_id,
                request.report_id,
                request.from_phase
            )
            
            if not from_phase_status:
                return self._failure(f"Phase {request.from_phase} not found")
            
            if from_phase_status.get('status') != 'in_progress':
                return self._failure(f"Phase {request.from_phase} is not in progress")
            
            # Complete current phase
            await self.workflow_repository.save_phase_status(
                cycle_id=request.cycle_id,
                report_id=request.report_id,
                phase_name=request.from_phase,
                status={
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "completed_by": request.requested_by
                }
            )
            
            # Start new phase
            await self.workflow_repository.save_phase_status(
                cycle_id=request.cycle_id,
                report_id=request.report_id,
                phase_name=request.to_phase,
                status={
                    "status": "in_progress",
                    "started_at": datetime.utcnow().isoformat(),
                    "started_by": request.requested_by
                }
            )
            
            # Check SLA compliance
            sla_status = await self.sla_service.check_sla_compliance(
                request.cycle_id,
                request.report_id,
                request.to_phase
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=request.requested_by,
                action="ADVANCE_WORKFLOW_PHASE",
                resource_type="workflow",
                resource_id=request.report_id,
                details={
                    "cycle_id": request.cycle_id,
                    "from_phase": request.from_phase,
                    "to_phase": request.to_phase,
                    "override_used": request.override_dependencies,
                    "reason": request.reason
                }
            )
            
            # Send notifications
            await self.notification_service.send_notification(
                user_id=request.requested_by,
                title="Workflow Phase Advanced",
                message=f"Workflow advanced from {request.from_phase} to {request.to_phase}",
                notification_type="workflow_advanced",
                priority="medium"
            )
            
            # Get updated workflow state
            all_phases = await self.workflow_repository.get_all_phases(
                request.cycle_id,
                request.report_id
            )
            
            # Convert to DTOs
            phase_dtos = [
                PhaseStatusDTO(
                    cycle_id=request.cycle_id,
                    report_id=request.report_id,
                    phase_name=phase['phase_name'],
                    status=phase['status'],
                    started_at=phase.get('started_at'),
                    completed_at=phase.get('completed_at'),
                    updated_by=phase.get('updated_by'),
                    metadata=phase.get('metadata')
                )
                for phase in all_phases
            ]
            
            # Determine next available phases
            next_available = await self._get_next_available_phases(
                request.cycle_id,
                request.report_id,
                request.to_phase
            )
            
            workflow_state = WorkflowStateDTO(
                cycle_id=request.cycle_id,
                report_id=request.report_id,
                current_phase=request.to_phase,
                phases=phase_dtos,
                can_advance=len(next_available) > 0,
                next_available_phases=next_available,
                sla_status=sla_status
            )
            
            return self._success(workflow_state)
            
        except Exception as e:
            return self._failure(f"Failed to advance workflow: {str(e)}")
    
    async def _get_next_available_phases(
        self,
        cycle_id: int,
        report_id: int,
        current_phase: str
    ) -> List[str]:
        """Determine next available phases based on workflow rules"""
        # Define workflow dependencies
        workflow_rules = {
            "Planning": ["Scoping"],
            "Scoping": ["Sample Selection", "Data Owner Identification"],
            "Sample Selection": ["Request for Information"],
            "Data Owner Identification": ["Request for Information"],
            "Request for Information": ["Test Execution"],
            "Test Execution": ["Observation Management"],
            "Observation Management": ["Testing Report"],
            "Testing Report": []
        }
        
        next_phases = workflow_rules.get(current_phase, [])
        available_phases = []
        
        for phase in next_phases:
            can_advance = await self.workflow_repository.can_advance_to_phase(
                cycle_id, report_id, phase
            )
            if can_advance:
                available_phases.append(phase)
        
        return available_phases


class GetWorkflowStatusUseCase(UseCase[Dict[str, Any], WorkflowStateDTO]):
    """Use case for getting current workflow status"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        sla_service: SLAService
    ):
        self.workflow_repository = workflow_repository
        self.sla_service = sla_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[WorkflowStateDTO]:
        """Get current workflow status"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            
            # Get all phases
            all_phases = await self.workflow_repository.get_all_phases(cycle_id, report_id)
            
            if not all_phases:
                return self._failure("No workflow phases found for this report")
            
            # Find current phase (in_progress)
            current_phase = None
            for phase in all_phases:
                if phase.get('status') == 'in_progress':
                    current_phase = phase['phase_name']
                    break
            
            # If no phase is in progress, find the last completed
            if not current_phase:
                completed_phases = [p for p in all_phases if p.get('status') == 'completed']
                if completed_phases:
                    # Sort by completed_at and get the latest
                    completed_phases.sort(key=lambda x: x.get('completed_at', ''), reverse=True)
                    current_phase = completed_phases[0]['phase_name']
                else:
                    current_phase = "Planning"  # Default to first phase
            
            # Check SLA status for current phase
            sla_status = await self.sla_service.check_sla_compliance(
                cycle_id, report_id, current_phase
            )
            
            # Convert to DTOs
            phase_dtos = [
                PhaseStatusDTO(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name=phase['phase_name'],
                    status=phase['status'],
                    started_at=phase.get('started_at'),
                    completed_at=phase.get('completed_at'),
                    updated_by=phase.get('updated_by'),
                    metadata=phase.get('metadata')
                )
                for phase in all_phases
            ]
            
            # Determine next available phases
            next_available = await self._get_next_available_phases(
                cycle_id, report_id, current_phase
            )
            
            workflow_state = WorkflowStateDTO(
                cycle_id=cycle_id,
                report_id=report_id,
                current_phase=current_phase,
                phases=phase_dtos,
                can_advance=len(next_available) > 0,
                next_available_phases=next_available,
                sla_status=sla_status
            )
            
            return self._success(workflow_state)
            
        except Exception as e:
            return self._failure(f"Failed to get workflow status: {str(e)}")
    
    async def _get_next_available_phases(
        self,
        cycle_id: int,
        report_id: int,
        current_phase: str
    ) -> List[str]:
        """Determine next available phases based on workflow rules"""
        # Same implementation as in AdvanceWorkflowPhaseUseCase
        workflow_rules = {
            "Planning": ["Scoping"],
            "Scoping": ["Sample Selection", "Data Owner Identification"],
            "Sample Selection": ["Request for Information"],
            "Data Owner Identification": ["Request for Information"],
            "Request for Information": ["Test Execution"],
            "Test Execution": ["Observation Management"],
            "Observation Management": ["Testing Report"],
            "Testing Report": []
        }
        
        next_phases = workflow_rules.get(current_phase, [])
        available_phases = []
        
        for phase in next_phases:
            can_advance = await self.workflow_repository.can_advance_to_phase(
                cycle_id, report_id, phase
            )
            if can_advance:
                available_phases.append(phase)
        
        return available_phases


class OverridePhaseUseCase(UseCase[Dict[str, Any], bool]):
    """Use case for overriding workflow phase status"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        user_repository: UserRepository,
        audit_service: AuditService,
        notification_service: NotificationService
    ):
        self.workflow_repository = workflow_repository
        self.user_repository = user_repository
        self.audit_service = audit_service
        self.notification_service = notification_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[bool]:
        """Override phase status (admin function)"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            phase_name = request['phase_name']
            new_status = request['new_status']
            user_id = request['user_id']
            reason = request['reason']
            
            # Validate user has override permission
            user_permissions = await self.user_repository.get_user_permissions(user_id)
            if "workflow.override" not in user_permissions:
                return self._failure("User does not have permission to override workflow")
            
            # Get current phase status
            current_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, phase_name
            )
            
            if not current_status:
                return self._failure(f"Phase {phase_name} not found")
            
            old_status = current_status.get('status')
            
            # Update phase status
            status_update = {
                "status": new_status,
                "override_by": user_id,
                "override_at": datetime.utcnow().isoformat(),
                "override_reason": reason
            }
            
            if new_status == "completed" and old_status != "completed":
                status_update["completed_at"] = datetime.utcnow().isoformat()
            elif new_status == "in_progress" and old_status != "in_progress":
                status_update["started_at"] = datetime.utcnow().isoformat()
            
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name=phase_name,
                status=status_update
            )
            
            # Audit log with detailed information
            await self.audit_service.log_action(
                user_id=user_id,
                action="OVERRIDE_WORKFLOW_PHASE",
                resource_type="workflow",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "phase_name": phase_name,
                    "old_status": old_status,
                    "new_status": new_status,
                    "reason": reason
                }
            )
            
            # Send notification to admins
            admins = await self.user_repository.find_by_role("Test Executive")
            await self.notification_service.send_bulk_notifications(
                user_ids=[admin['user_id'] for admin in admins],
                title="Workflow Override Applied",
                message=f"Phase {phase_name} status overridden from {old_status} to {new_status}",
                notification_type="workflow_override",
                priority="high"
            )
            
            return self._success(True)
            
        except Exception as e:
            return self._failure(f"Failed to override phase: {str(e)}")