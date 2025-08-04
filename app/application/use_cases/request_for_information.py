"""Request for Information phase use cases"""
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
    AuditService,
    DocumentStorageService,
    SLAService
)
from .base import UseCase, UseCaseResult


class CreateRFIUseCase(UseCase[Dict[str, Any], Dict[str, Any]]):
    """Use case for creating request for information"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        user_repository: UserRepository,
        notification_service: NotificationService,
        email_service: EmailService,
        audit_service: AuditService,
        sla_service: SLAService
    ):
        self.workflow_repository = workflow_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.email_service = email_service
        self.audit_service = audit_service
        self.sla_service = sla_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[Dict[str, Any]]:
        """Create RFI for data owners"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Request for Information"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Request for Information phase is not active")
            
            # Get data owners from Data Owner Identification phase
            data_owner_phase = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Data Owner Identification"
            )
            if not data_owner_phase:
                return self._failure("Data Owner Identification phase not found")
            
            data_owners = data_owner_phase.get('metadata', {}).get('data_owners', [])
            if not data_owners:
                return self._failure("No data owners identified")
            
            # Get sample selection info
            sample_phase = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Sample Selection"
            )
            sample_info = sample_phase.get('metadata', {}) if sample_phase else {}
            
            # Create RFI for each data owner
            rfi_requests = []
            for owner in data_owners:
                if owner.get('status') != 'assigned':
                    continue
                
                rfi_id = f"RFI-{cycle_id}-{report_id}-{owner['data_owner_id']}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                
                rfi_request = {
                    "rfi_id": rfi_id,
                    "data_owner_id": owner['data_owner_id'],
                    "data_owner_name": owner['data_owner_name'],
                    "attributes_requested": owner.get('attributes_assigned', []),
                    "sample_size": sample_info.get('sample_size', 25),
                    "due_date": request.get('due_date', (datetime.utcnow() + timedelta(days=7)).isoformat()),
                    "status": "sent",
                    "created_at": datetime.utcnow().isoformat(),
                    "created_by": user_id
                }
                
                rfi_requests.append(rfi_request)
                
                # Send notification to data owner
                await self.notification_service.send_notification(
                    user_id=owner['data_owner_id'],
                    title="New Data Request",
                    message=f"You have a new data request for {len(owner.get('attributes_assigned', []))} attributes",
                    notification_type="rfi_created",
                    priority="high",
                    metadata={"rfi_id": rfi_id}
                )
                
                # Send email notification
                await self.email_service.send_template_email(
                    to_email=owner.get('email'),
                    template_name="rfi_request",
                    context={
                        "data_owner_name": owner['data_owner_name'],
                        "rfi_id": rfi_id,
                        "attribute_count": len(owner.get('attributes_assigned', [])),
                        "due_date": rfi_request['due_date'],
                        "cycle_id": cycle_id,
                        "report_id": report_id
                    }
                )
            
            # Update workflow phase metadata
            metadata = phase_status.get('metadata', {})
            metadata['rfi_requests'] = rfi_requests
            metadata['total_rfis_sent'] = len(rfi_requests)
            metadata['rfi_created_at'] = datetime.utcnow().isoformat()
            
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Request for Information",
                status={
                    "status": "in_progress",
                    "metadata": metadata
                }
            )
            
            # Set up SLA tracking
            for rfi in rfi_requests:
                await self.sla_service.check_sla_compliance(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase="Request for Information"
                )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="CREATE_RFI",
                resource_type="rfi",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "rfis_created": len(rfi_requests),
                    "data_owners": [r['data_owner_id'] for r in rfi_requests]
                }
            )
            
            return self._success({
                "rfi_requests": rfi_requests,
                "total_created": len(rfi_requests)
            })
            
        except Exception as e:
            return self._failure(f"Failed to create RFI: {str(e)}")


class SubmitRFIResponseUseCase(UseCase[Dict[str, Any], Dict[str, Any]]):
    """Use case for data owners to submit RFI responses"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        document_storage_service: DocumentStorageService,
        notification_service: NotificationService,
        audit_service: AuditService
    ):
        self.workflow_repository = workflow_repository
        self.document_storage_service = document_storage_service
        self.notification_service = notification_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[Dict[str, Any]]:
        """Submit RFI response with data"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            rfi_id = request['rfi_id']
            data_owner_id = request['data_owner_id']
            attribute_values = request['attribute_values']
            supporting_documents = request.get('supporting_documents', [])
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Request for Information"
            )
            if not phase_status:
                return self._failure("Request for Information phase not found")
            
            # Find the RFI request
            metadata = phase_status.get('metadata', {})
            rfi_requests = metadata.get('rfi_requests', [])
            
            rfi_request = None
            for rfi in rfi_requests:
                if rfi['rfi_id'] == rfi_id and rfi['data_owner_id'] == data_owner_id:
                    rfi_request = rfi
                    break
            
            if not rfi_request:
                return self._failure("RFI request not found")
            
            # Store supporting documents
            stored_documents = []
            for doc in supporting_documents:
                doc_id = await self.document_storage_service.store_document(
                    file_content=doc['content'],
                    filename=doc['filename'],
                    content_type=doc['content_type'],
                    metadata={
                        "cycle_id": cycle_id,
                        "report_id": report_id,
                        "rfi_id": rfi_id,
                        "data_owner_id": data_owner_id,
                        "phase": "Request for Information"
                    }
                )
                stored_documents.append({
                    "document_id": doc_id,
                    "filename": doc['filename'],
                    "uploaded_at": datetime.utcnow().isoformat()
                })
            
            # Update RFI request with response
            rfi_request['status'] = 'responded'
            rfi_request['responded_at'] = datetime.utcnow().isoformat()
            rfi_request['attribute_values'] = attribute_values
            rfi_request['supporting_documents'] = stored_documents
            
            # Check if all RFIs have been responded to
            all_responded = all(r['status'] == 'responded' for r in rfi_requests)
            
            # Update metadata
            metadata['last_response_at'] = datetime.utcnow().isoformat()
            metadata['responses_received'] = sum(1 for r in rfi_requests if r['status'] == 'responded')
            metadata['all_responses_received'] = all_responded
            
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Request for Information",
                status={
                    "status": "in_progress",
                    "metadata": metadata
                }
            )
            
            # Send notification to tester
            await self.notification_service.send_notification(
                user_id=request.get('tester_id', data_owner_id),
                title="RFI Response Received",
                message=f"Data owner has submitted response for RFI {rfi_id}",
                notification_type="rfi_response",
                priority="medium",
                metadata={"rfi_id": rfi_id}
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=data_owner_id,
                action="SUBMIT_RFI_RESPONSE",
                resource_type="rfi_response",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "rfi_id": rfi_id,
                    "attributes_submitted": len(attribute_values),
                    "documents_uploaded": len(stored_documents)
                }
            )
            
            return self._success({
                "rfi_id": rfi_id,
                "status": "responded",
                "all_responses_received": all_responded,
                "documents_stored": stored_documents
            })
            
        except Exception as e:
            return self._failure(f"Failed to submit RFI response: {str(e)}")


class CompleteRFIPhaseUseCase(UseCase[Dict[str, Any], bool]):
    """Use case for completing RFI phase"""
    
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
        """Complete RFI phase and advance to Test Execution"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Request for Information"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Request for Information phase is not active")
            
            # Verify all RFIs have been responded to
            metadata = phase_status.get('metadata', {})
            if not metadata.get('all_responses_received', False):
                pending_count = metadata.get('total_rfis_sent', 0) - metadata.get('responses_received', 0)
                return self._failure(f"{pending_count} RFI responses are still pending")
            
            # Complete RFI phase
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Request for Information",
                status={
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        **metadata,
                        "completed_by": user_id
                    }
                }
            )
            
            # Start Test Execution phase
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Test Execution",
                status={
                    "status": "in_progress",
                    "started_at": datetime.utcnow().isoformat()
                }
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="COMPLETE_RFI_PHASE",
                resource_type="workflow_phase",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "phase_completed": "Request for Information",
                    "next_phase": "Test Execution",
                    "total_responses": metadata.get('responses_received', 0)
                }
            )
            
            # Send notification
            await self.notification_service.send_notification(
                user_id=user_id,
                title="RFI Phase Completed",
                message="Request for Information phase completed. Test Execution phase has begun.",
                notification_type="phase_completed",
                priority="high"
            )
            
            return self._success(True)
            
        except Exception as e:
            return self._failure(f"Failed to complete RFI phase: {str(e)}")


from datetime import timedelta  # Add this import at the top