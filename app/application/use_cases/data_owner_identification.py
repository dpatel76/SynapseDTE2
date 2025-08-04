"""Data Owner Identification phase use cases"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.application.interfaces.repositories import (
    TestCycleRepository,
    ReportRepository,
    UserRepository,
    WorkflowRepository
)
from app.application.interfaces.services import (
    NotificationService,
    EmailService,
    AuditService
)
from .base import UseCase, UseCaseResult


class IdentifyDataOwnersUseCase(UseCase[Dict[str, Any], List[Dict[str, Any]]]):
    """Use case for identifying data owners for report attributes"""
    
    def __init__(
        self,
        cycle_repository: TestCycleRepository,
        report_repository: ReportRepository,
        user_repository: UserRepository,
        workflow_repository: WorkflowRepository,
        notification_service: NotificationService,
        audit_service: AuditService
    ):
        self.cycle_repository = cycle_repository
        self.report_repository = report_repository
        self.user_repository = user_repository
        self.workflow_repository = workflow_repository
        self.notification_service = notification_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[List[Dict[str, Any]]]:
        """Identify data owners for test attributes"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Validate cycle and report
            cycle = await self.cycle_repository.get(cycle_id)
            if not cycle:
                return self._failure("Test cycle not found")
            
            report = await self.report_repository.get(report_id)
            if not report:
                return self._failure("Report not found")
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Data Owner Identification"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Data Owner Identification phase is not active")
            
            # Get all data owners
            data_owners = await self.user_repository.find_by_role("Data Owner")
            
            # Get report attributes to determine appropriate data owners
            # In real implementation, this would involve complex business logic
            # to match attributes with data owners based on their LOB/expertise
            attribute_owners = []
            
            for owner in data_owners:
                # Simple assignment logic - in production this would be more sophisticated
                attribute_owners.append({
                    "data_owner_id": owner['user_id'],
                    "data_owner_name": owner.get('full_name', owner['username']),
                    "email": owner.get('email'),
                    "lob": owner.get('lob', 'General'),
                    "attributes_assigned": [],  # Would be populated based on attribute matching
                    "status": "pending"
                })
            
            # Update workflow phase metadata
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Data Owner Identification",
                status={
                    "status": "in_progress",
                    "metadata": {
                        "data_owners_identified": len(attribute_owners),
                        "identification_date": datetime.utcnow().isoformat(),
                        "identified_by": user_id,
                        "data_owners": attribute_owners
                    }
                }
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="IDENTIFY_DATA_OWNERS",
                resource_type="data_owner_assignment",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "data_owners_identified": len(attribute_owners)
                }
            )
            
            # Send notification
            await self.notification_service.send_notification(
                user_id=user_id,
                title="Data Owners Identified",
                message=f"Identified {len(attribute_owners)} data owners for {report.get('report_name')}",
                notification_type="data_owners_identified",
                priority="medium"
            )
            
            return self._success(attribute_owners)
            
        except Exception as e:
            return self._failure(f"Failed to identify data owners: {str(e)}")


class AssignDataOwnerUseCase(UseCase[Dict[str, Any], bool]):
    """Use case for assigning data owner to specific attributes"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        user_repository: UserRepository,
        notification_service: NotificationService,
        email_service: EmailService,
        audit_service: AuditService
    ):
        self.workflow_repository = workflow_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.email_service = email_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[bool]:
        """Assign data owner to attributes"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            data_owner_id = request['data_owner_id']
            attribute_ids = request['attribute_ids']
            assigned_by = request['assigned_by']
            
            # Validate data owner
            data_owner = await self.user_repository.get(data_owner_id)
            if not data_owner:
                return self._failure("Data owner not found")
            
            # Verify user is a data owner
            permissions = await self.user_repository.get_user_permissions(data_owner_id)
            if "data.provide" not in permissions:
                return self._failure("User is not a data owner")
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Data Owner Identification"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Data Owner Identification phase is not active")
            
            # Update data owner assignments in metadata
            metadata = phase_status.get('metadata', {})
            data_owners = metadata.get('data_owners', [])
            
            # Find and update the data owner's assignment
            owner_found = False
            for owner in data_owners:
                if owner['data_owner_id'] == data_owner_id:
                    owner['attributes_assigned'] = attribute_ids
                    owner['status'] = 'assigned'
                    owner['assigned_at'] = datetime.utcnow().isoformat()
                    owner['assigned_by'] = assigned_by
                    owner_found = True
                    break
            
            if not owner_found:
                # Add new data owner assignment
                data_owners.append({
                    "data_owner_id": data_owner_id,
                    "data_owner_name": data_owner.get('full_name', data_owner['username']),
                    "email": data_owner.get('email'),
                    "lob": data_owner.get('lob', 'General'),
                    "attributes_assigned": attribute_ids,
                    "status": "assigned",
                    "assigned_at": datetime.utcnow().isoformat(),
                    "assigned_by": assigned_by
                })
            
            metadata['data_owners'] = data_owners
            
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Data Owner Identification",
                status={
                    "status": "in_progress",
                    "metadata": metadata
                }
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=assigned_by,
                action="ASSIGN_DATA_OWNER",
                resource_type="data_owner_assignment",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "data_owner_id": data_owner_id,
                    "attributes_assigned": len(attribute_ids)
                }
            )
            
            # Send notification to data owner
            await self.notification_service.send_notification(
                user_id=data_owner_id,
                title="New Data Request Assignment",
                message=f"You have been assigned to provide data for {len(attribute_ids)} attributes",
                notification_type="data_assignment",
                priority="high"
            )
            
            # Send email notification
            await self.email_service.send_template_email(
                to_email=data_owner.get('email'),
                template_name="data_owner_assignment",
                context={
                    "data_owner_name": data_owner.get('full_name', data_owner['username']),
                    "attribute_count": len(attribute_ids),
                    "cycle_id": cycle_id,
                    "report_id": report_id
                }
            )
            
            return self._success(True)
            
        except Exception as e:
            return self._failure(f"Failed to assign data owner: {str(e)}")


class CompleteDataOwnerIdentificationUseCase(UseCase[Dict[str, Any], bool]):
    """Use case for completing data owner identification phase"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        notification_service: NotificationService,
        audit_service: AuditService
    ):
        self.workflow_repository = workflow_repository
        self.notification_service = notification_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[bool]:
        """Complete data owner identification phase"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Data Owner Identification"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Data Owner Identification phase is not active")
            
            # Verify all attributes have data owners assigned
            metadata = phase_status.get('metadata', {})
            data_owners = metadata.get('data_owners', [])
            
            unassigned_count = sum(1 for owner in data_owners if owner.get('status') != 'assigned')
            if unassigned_count > 0:
                return self._failure(f"{unassigned_count} data owners have not been assigned yet")
            
            # Complete Data Owner Identification phase
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Data Owner Identification",
                status={
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        **metadata,
                        "completed_by": user_id,
                        "completion_date": datetime.utcnow().isoformat()
                    }
                }
            )
            
            # Check if Sample Selection is also complete
            sample_selection_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Sample Selection"
            )
            
            # If both parallel phases are complete, start Request for Information
            if sample_selection_status and sample_selection_status.get('status') == 'completed':
                await self.workflow_repository.save_phase_status(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Request for Information",
                    status={
                        "status": "in_progress",
                        "started_at": datetime.utcnow().isoformat()
                    }
                )
                
                next_phase = "Request for Information"
                
                # Notify all assigned data owners
                for owner in data_owners:
                    if owner.get('status') == 'assigned':
                        await self.notification_service.send_notification(
                            user_id=owner['data_owner_id'],
                            title="Request for Information Phase Started",
                            message="The Request for Information phase has begun. Please prepare to submit your data.",
                            notification_type="phase_started",
                            priority="high"
                        )
            else:
                next_phase = None
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="COMPLETE_DATA_OWNER_IDENTIFICATION",
                resource_type="workflow_phase",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "phase_completed": "Data Owner Identification",
                    "data_owners_assigned": len(data_owners),
                    "next_phase": next_phase
                }
            )
            
            return self._success(True)
            
        except Exception as e:
            return self._failure(f"Failed to complete data owner identification: {str(e)}")