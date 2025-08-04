"""Observation Management phase use cases"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.application.dto.report_dto import CreateObservationDTO, ObservationDTO
from app.application.interfaces.repositories import (
    TestCycleRepository,
    WorkflowRepository,
    UserRepository
)
from app.application.interfaces.services import (
    NotificationService,
    EmailService,
    AuditService,
    LLMService
)
from .base import UseCase, UseCaseResult


class CreateObservationUseCase(UseCase[CreateObservationDTO, ObservationDTO]):
    """Use case for creating an observation from failed tests"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        notification_service: NotificationService,
        audit_service: AuditService,
        llm_service: LLMService
    ):
        self.workflow_repository = workflow_repository
        self.notification_service = notification_service
        self.audit_service = audit_service
        self.llm_service = llm_service
    
    async def execute(self, request: CreateObservationDTO) -> UseCaseResult[ObservationDTO]:
        """Create an observation"""
        try:
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                request.cycle_id, request.report_id, "Observation Management"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Observation Management phase is not active")
            
            # Get test execution details from Testing phase
            testing_phase = await self.workflow_repository.get_phase_status(
                request.cycle_id, request.report_id, "Test Execution"
            )
            if not testing_phase:
                return self._failure("Test Execution phase not found")
            
            # Generate observation ID
            observation_id = self._generate_observation_id(request.cycle_id, request.report_id)
            
            # Use LLM to enhance observation description if needed
            enhanced_description = request.description
            if request.test_executions:
                # Get details of failed tests to provide context
                test_details = self._get_test_details(testing_phase, request.test_executions)
                
                llm_result = await self.llm_service.generate_report_summary(
                    test_results=test_details,
                    observations=[],  # No observations yet
                    cycle_context={
                        "observation_type": request.observation_type,
                        "severity": request.severity,
                        "title": request.title
                    }
                )
                
                if llm_result and not llm_result.startswith("Error"):
                    enhanced_description = f"{request.description}\n\nAnalysis:\n{llm_result}"
            
            # Create observation DTO
            observation_dto = ObservationDTO(
                observation_id=observation_id,
                cycle_id=request.cycle_id,
                report_id=request.report_id,
                observation_type=request.observation_type,
                severity=request.severity,
                title=request.title,
                description=enhanced_description,
                status="open",
                created_by=request.created_by,
                created_at=datetime.utcnow(),
                test_executions=request.test_executions,
                recommendations=request.recommendations,
                management_response=None,
                target_date=None
            )
            
            # Update phase metadata
            metadata = phase_status.get('metadata', {})
            observations = metadata.get('observations', [])
            observations.append({
                "observation_id": observation_id,
                "title": request.title,
                "severity": request.severity,
                "status": "open",
                "created_at": datetime.utcnow().isoformat(),
                "cycle_report_test_execution_test_executions": request.test_executions
            })
            metadata['observations'] = observations
            metadata['observations_created'] = len(observations)
            metadata['open_observations'] = sum(1 for o in observations if o['status'] == 'open')
            
            await self.workflow_repository.save_phase_status(
                cycle_id=request.cycle_id,
                report_id=request.report_id,
                phase_name="Observation Management",
                status={
                    "status": "in_progress",
                    "metadata": metadata
                }
            )
            
            # Send notifications based on severity
            priority = "critical" if request.severity == "critical" else "high"
            await self.notification_service.send_notification(
                user_id=request.created_by,
                title=f"New {request.severity.upper()} Observation Created",
                message=f"Observation: {request.title}",
                notification_type="observation_created",
                priority=priority,
                metadata={"observation_id": observation_id}
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=request.created_by,
                action="CREATE_OBSERVATION",
                resource_type="observation",
                resource_id=request.report_id,
                details={
                    "cycle_id": request.cycle_id,
                    "observation_id": observation_id,
                    "severity": request.severity,
                    "type": request.observation_type,
                    "cycle_report_test_execution_test_executions": len(request.test_executions)
                }
            )
            
            return self._success(observation_dto)
            
        except Exception as e:
            return self._failure(f"Failed to create observation: {str(e)}")
    
    def _generate_observation_id(self, cycle_id: int, report_id: int) -> int:
        """Generate a unique observation ID"""
        # In a real implementation, this would be handled by the database
        import random
        return random.randint(100000, 999999)
    
    def _get_test_details(self, testing_phase: Dict[str, Any], execution_ids: List[int]) -> List[Dict[str, Any]]:
        """Extract test details for specific execution IDs"""
        metadata = testing_phase.get('metadata', {})
        test_executions = metadata.get('test_executions', [])
        
        return [
            t for t in test_executions 
            if t.get('attribute_id') in execution_ids
        ]


class UpdateObservationUseCase(UseCase[Dict[str, Any], ObservationDTO]):
    """Use case for updating an observation"""
    
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
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[ObservationDTO]:
        """Update an observation with management response"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            observation_id = request['observation_id']
            user_id = request['user_id']
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Observation Management"
            )
            if not phase_status:
                return self._failure("Observation Management phase not found")
            
            # Find the observation
            metadata = phase_status.get('metadata', {})
            observations = metadata.get('observations', [])
            
            observation = None
            for idx, obs in enumerate(observations):
                if obs['observation_id'] == observation_id:
                    observation = obs
                    obs_index = idx
                    break
            
            if not observation:
                return self._failure("Observation not found")
            
            # Update observation fields
            if 'management_response' in request:
                observation['management_response'] = request['management_response']
                observation['response_date'] = datetime.utcnow().isoformat()
                observation['responded_by'] = user_id
            
            if 'target_date' in request:
                observation['target_date'] = request['target_date']
            
            if 'status' in request:
                old_status = observation['status']
                observation['status'] = request['status']
                observation['status_updated_at'] = datetime.utcnow().isoformat()
                
                # Update open observation count
                if old_status == 'open' and request['status'] != 'open':
                    metadata['open_observations'] = metadata.get('open_observations', 1) - 1
                elif old_status != 'open' and request['status'] == 'open':
                    metadata['open_observations'] = metadata.get('open_observations', 0) + 1
            
            # Update in metadata
            observations[obs_index] = observation
            metadata['observations'] = observations
            metadata['last_updated'] = datetime.utcnow().isoformat()
            
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Observation Management",
                status={
                    "status": phase_status.get('status'),
                    "metadata": metadata
                }
            )
            
            # Create updated DTO
            observation_dto = ObservationDTO(
                observation_id=observation_id,
                cycle_id=cycle_id,
                report_id=report_id,
                observation_type=observation['observation_type'],
                severity=observation['severity'],
                title=observation['title'],
                description=observation['description'],
                status=observation['status'],
                created_by=observation['created_by'],
                created_at=datetime.fromisoformat(observation['created_at']),
                test_executions=observation['test_executions'],
                recommendations=observation.get('recommendations'),
                management_response=observation.get('management_response'),
                target_date=datetime.fromisoformat(observation['target_date']) if observation.get('target_date') else None
            )
            
            # Send notifications
            if 'management_response' in request:
                # Notify the observation creator
                await self.notification_service.send_notification(
                    user_id=observation['created_by'],
                    title="Management Response Received",
                    message=f"Management has responded to observation: {observation['title']}",
                    notification_type="observation_response",
                    priority="medium",
                    metadata={"observation_id": observation_id}
                )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="UPDATE_OBSERVATION",
                resource_type="observation",
                resource_id=observation_id,
                details={
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "updates": list(request.keys())
                }
            )
            
            return self._success(observation_dto)
            
        except Exception as e:
            return self._failure(f"Failed to update observation: {str(e)}")


class CompleteObservationPhaseUseCase(UseCase[Dict[str, Any], bool]):
    """Use case for completing observation management phase"""
    
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
        """Complete observation phase and advance to Testing Report"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Observation Management"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Observation Management phase is not active")
            
            # Check if there are open observations
            metadata = phase_status.get('metadata', {})
            open_observations = metadata.get('open_observations', 0)
            
            if open_observations > 0 and not request.get('force_complete', False):
                return self._failure(f"{open_observations} observations are still open. Use force_complete=True to proceed.")
            
            # Get observation statistics
            observations = metadata.get('observations', [])
            total_observations = len(observations)
            critical_count = sum(1 for o in observations if o['severity'] == 'critical')
            high_count = sum(1 for o in observations if o['severity'] == 'high')
            
            # Complete Observation Management phase
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Observation Management",
                status={
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        **metadata,
                        "completed_by": user_id,
                        "total_observations": total_observations,
                        "critical_observations": critical_count,
                        "high_observations": high_count,
                        "forced_completion": request.get('force_complete', False)
                    }
                }
            )
            
            # Start Testing Report phase
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Testing Report",
                status={
                    "status": "in_progress",
                    "started_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "report_status": "draft",
                        "sections_completed": []
                    }
                }
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="COMPLETE_OBSERVATION_PHASE",
                resource_type="workflow_phase",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "phase_completed": "Observation Management",
                    "next_phase": "Testing Report",
                    "total_observations": total_observations,
                    "open_observations": open_observations,
                    "forced": request.get('force_complete', False)
                }
            )
            
            # Send notification
            message = f"Observation Management completed with {total_observations} observations."
            if critical_count > 0:
                message += f" {critical_count} critical issues identified."
            message += " Testing Report phase has begun."
            
            await self.notification_service.send_notification(
                user_id=user_id,
                title="Observation Phase Completed",
                message=message,
                notification_type="phase_completed",
                priority="high"
            )
            
            return self._success(True)
            
        except Exception as e:
            return self._failure(f"Failed to complete observation phase: {str(e)}")


class GroupObservationsUseCase(UseCase[Dict[str, Any], Dict[str, Any]]):
    """Use case for grouping similar observations"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        llm_service: LLMService,
        audit_service: AuditService
    ):
        self.workflow_repository = workflow_repository
        self.llm_service = llm_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[Dict[str, Any]]:
        """Group similar observations using LLM"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Get all observations
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Observation Management"
            )
            if not phase_status:
                return self._failure("Observation Management phase not found")
            
            metadata = phase_status.get('metadata', {})
            observations = metadata.get('observations', [])
            
            if len(observations) < 2:
                return self._failure("Not enough observations to group")
            
            # Use LLM to identify similar observations
            observation_texts = [
                f"{o['title']}: {o['description']}" 
                for o in observations
            ]
            
            llm_result = await self.llm_service.extract_data_from_document(
                document_content="\n".join(observation_texts),
                extraction_schema={
                    "groups": [
                        {
                            "group_name": "string",
                            "observation_indices": "array of integers",
                            "common_theme": "string",
                            "recommended_action": "string"
                        }
                    ]
                }
            )
            
            if not llm_result.get('success'):
                return self._failure(f"Failed to group observations: {llm_result.get('error')}")
            
            groups = llm_result.get('data', {}).get('groups', [])
            
            # Update metadata with groupings
            metadata['observation_groups'] = groups
            metadata['grouping_performed_at'] = datetime.utcnow().isoformat()
            metadata['grouping_performed_by'] = user_id
            
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Observation Management",
                status={
                    "status": phase_status.get('status'),
                    "metadata": metadata
                }
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="GROUP_OBSERVATIONS",
                resource_type="observation_grouping",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "total_observations": len(observations),
                    "groups_created": len(groups)
                }
            )
            
            return self._success({
                "groups": groups,
                "total_groups": len(groups),
                "ungrouped_observations": self._find_ungrouped_observations(observations, groups)
            })
            
        except Exception as e:
            return self._failure(f"Failed to group observations: {str(e)}")
    
    def _find_ungrouped_observations(self, observations: List[Dict], groups: List[Dict]) -> List[int]:
        """Find observations that weren't grouped"""
        all_indices = set(range(len(observations)))
        grouped_indices = set()
        
        for group in groups:
            grouped_indices.update(group.get('observation_indices', []))
        
        return list(all_indices - grouped_indices)