"""Test Execution phase use cases"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from app.application.dto.report_dto import TestExecutionDTO, TestResultDTO
from app.application.interfaces.repositories import (
    TestCycleRepository,
    ReportRepository,
    WorkflowRepository
)
from app.application.interfaces.services import (
    LLMService,
    NotificationService,
    AuditService,
    DocumentStorageService,
    UnifiedStatusService
)
from .base import UseCase, UseCaseResult


class TestType(Enum):
    """Types of tests that can be executed"""
    DOCUMENT = "document"
    DATABASE = "database"
    MANUAL = "manual"
    AUTOMATED = "automated"


class ExecuteTestUseCase(UseCase[Dict[str, Any], TestExecutionDTO]):
    """Use case for executing a single test"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        llm_service: LLMService,
        document_storage_service: DocumentStorageService,
        notification_service: NotificationService,
        audit_service: AuditService
    ):
        self.workflow_repository = workflow_repository
        self.llm_service = llm_service
        self.document_storage_service = document_storage_service
        self.notification_service = notification_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[TestExecutionDTO]:
        """Execute a test for an attribute"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            attribute_id = request['attribute_id']
            test_type = request['test_type']
            user_id = request['user_id']
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Test Execution"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Test Execution phase is not active")
            
            # Get attribute details and expected value from RFI phase
            rfi_phase = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Request for Information"
            )
            attribute_data = self._get_attribute_data(rfi_phase, attribute_id)
            
            if not attribute_data:
                return self._failure("Attribute data not found in RFI responses")
            
            # Execute test based on type
            test_result = None
            evidence = []
            
            if test_type == TestType.DOCUMENT.value:
                test_result = await self._execute_document_test(
                    request, attribute_data
                )
            elif test_type == TestType.DATABASE.value:
                test_result = await self._execute_database_test(
                    request, attribute_data
                )
            elif test_type == TestType.MANUAL.value:
                test_result = await self._execute_manual_test(
                    request, attribute_data
                )
            else:
                return self._failure(f"Unsupported test type: {test_type}")
            
            # Store test evidence if provided
            if request.get('evidence_documents'):
                for doc in request['evidence_documents']:
                    doc_id = await self.document_storage_service.store_document(
                        file_content=doc['content'],
                        filename=doc['filename'],
                        content_type=doc['content_type'],
                        metadata={
                            "cycle_id": cycle_id,
                            "report_id": report_id,
                            "attribute_id": attribute_id,
                            "test_type": test_type,
                            "phase": "Test Execution"
                        }
                    )
                    evidence.append({
                        "document_id": doc_id,
                        "filename": doc['filename'],
                        "type": "test_evidence"
                    })
            
            # Create execution record
            execution_dto = TestExecutionDTO(
                execution_id=0,  # Will be assigned by database
                cycle_id=cycle_id,
                report_id=report_id,
                attribute_id=attribute_id,
                test_type=test_type,
                status=test_result['status'],
                executed_by=user_id,
                executed_at=datetime.utcnow(),
                result=test_result.get('result'),
                evidence=evidence,
                comments=test_result.get('comments')
            )
            
            # Update phase metadata with test progress
            metadata = phase_status.get('metadata', {})
            test_executions = metadata.get('test_executions', [])
            test_executions.append({
                "attribute_id": attribute_id,
                "test_type": test_type,
                "status": test_result['status'],
                "executed_at": datetime.utcnow().isoformat(),
                "executed_by": user_id
            })
            metadata['test_executions'] = test_executions
            metadata['tests_completed'] = len(test_executions)
            
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Test Execution",
                status={
                    "status": "in_progress",
                    "metadata": metadata
                }
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="EXECUTE_TEST",
                resource_type="test_execution",
                resource_id=attribute_id,
                details={
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "test_type": test_type,
                    "status": test_result['status']
                }
            )
            
            # Send notification if test failed
            if test_result['status'] == 'fail':
                await self.notification_service.send_notification(
                    user_id=user_id,
                    title="Test Failed",
                    message=f"Test for attribute {attribute_id} failed",
                    notification_type="test_failed",
                    priority="high",
                    metadata={"attribute_id": attribute_id}
                )
            
            return self._success(execution_dto)
            
        except Exception as e:
            return self._failure(f"Failed to execute test: {str(e)}")
    
    def _get_attribute_data(self, rfi_phase: Dict[str, Any], attribute_id: int) -> Optional[Dict[str, Any]]:
        """Extract attribute data from RFI responses"""
        if not rfi_phase:
            return None
        
        metadata = rfi_phase.get('metadata', {})
        rfi_requests = metadata.get('rfi_requests', [])
        
        for rfi in rfi_requests:
            attribute_values = rfi.get('attribute_values', {})
            if str(attribute_id) in attribute_values:
                return {
                    "expected_value": attribute_values[str(attribute_id)],
                    "supporting_documents": rfi.get('supporting_documents', [])
                }
        
        return None
    
    async def _execute_document_test(
        self,
        request: Dict[str, Any],
        attribute_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute document-based test using LLM"""
        document_content = request.get('document_content', '')
        attribute_name = request.get('attribute_name', '')
        expected_value = attribute_data['expected_value']
        
        # Use LLM to analyze document
        llm_result = await self.llm_service.analyze_document(
            document_content=document_content,
            attribute_name=attribute_name,
            expected_value=expected_value,
            analysis_context={
                "test_type": "document_verification",
                "cycle_id": request['cycle_id'],
                "report_id": request['report_id']
            }
        )
        
        if llm_result.get('success'):
            status = 'pass' if llm_result.get('found') else 'fail'
            result = f"Expected: {expected_value}, Found: {llm_result.get('extracted_value')}"
            comments = f"Confidence: {llm_result.get('confidence', 0):.2%}"
        else:
            status = 'error'
            result = llm_result.get('error', 'Unknown error')
            comments = "Failed to analyze document"
        
        return {
            "status": status,
            "result": result,
            "comments": comments,
            "llm_analysis": llm_result
        }
    
    async def _execute_database_test(
        self,
        request: Dict[str, Any],
        attribute_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute database query test"""
        # In a real implementation, this would execute actual database queries
        # For now, we'll simulate the test
        query_result = request.get('query_result')
        expected_value = attribute_data['expected_value']
        
        if query_result is not None:
            status = 'pass' if str(query_result) == str(expected_value) else 'fail'
            result = f"Expected: {expected_value}, Actual: {query_result}"
        else:
            status = 'pending'
            result = "Query execution pending"
        
        return {
            "status": status,
            "result": result,
            "comments": request.get('query', 'No query provided')
        }
    
    async def _execute_manual_test(
        self,
        request: Dict[str, Any],
        attribute_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute manual test"""
        actual_value = request.get('actual_value')
        expected_value = attribute_data['expected_value']
        test_notes = request.get('test_notes', '')
        
        if actual_value is not None:
            status = 'pass' if str(actual_value) == str(expected_value) else 'fail'
            result = f"Expected: {expected_value}, Actual: {actual_value}"
        else:
            status = 'pending'
            result = "Manual verification pending"
        
        return {
            "status": status,
            "result": result,
            "comments": test_notes
        }


class GetTestingProgressUseCase(UseCase[Dict[str, Any], Dict[str, Any]]):
    """Use case for getting testing progress"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        report_repository: ReportRepository
    ):
        self.workflow_repository = workflow_repository
        self.report_repository = report_repository
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[Dict[str, Any]]:
        """Get testing progress for a report"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            
            # Get testing phase status
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Test Execution"
            )
            if not phase_status:
                return self._failure("Test Execution phase not found")
            
            metadata = phase_status.get('metadata', {})
            test_executions = metadata.get('test_executions', [])
            
            # Get total attributes to test from scoping phase
            scoping_phase = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Scoping"
            )
            total_attributes = scoping_phase.get('metadata', {}).get('total_attributes', 0)
            
            # Calculate progress
            tests_completed = len(test_executions)
            tests_passed = sum(1 for t in test_executions if t['status'] == 'pass')
            tests_failed = sum(1 for t in test_executions if t['status'] == 'fail')
            tests_pending = total_attributes - tests_completed
            
            progress = {
                "total_attributes": total_attributes,
                "tests_completed": tests_completed,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "tests_pending": tests_pending,
                "completion_percentage": (tests_completed / total_attributes * 100) if total_attributes > 0 else 0,
                "pass_rate": (tests_passed / tests_completed * 100) if tests_completed > 0 else 0,
                "status": phase_status.get('status'),
                "last_execution": max((t['executed_at'] for t in test_executions), default=None)
            }
            
            return self._success(progress)
            
        except Exception as e:
            return self._failure(f"Failed to get testing progress: {str(e)}")


class CompleteTestingPhaseUseCase(UseCase[Dict[str, Any], bool]):
    """Use case for completing testing phase"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        notification_service: NotificationService,
        audit_service: AuditService,
        unified_status_service: UnifiedStatusService
    ):
        self.workflow_repository = workflow_repository
        self.notification_service = notification_service
        self.audit_service = audit_service
        self.unified_status_service = unified_status_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[bool]:
        """Complete testing phase and advance to Observation Management"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Check workflow phase using unified status
            test_execution_status = await self.unified_status_service.get_phase_status("Test Execution", cycle_id, report_id)
            
            if not test_execution_status.can_proceed_to_next:
                return self._failure("Test Execution phase cannot be completed - requirements not met")
            
            # Get testing progress from unified status metadata
            metadata = test_execution_status.metadata or {}
            total_tests = metadata.get("total_tests", 0)
            completed_tests = metadata.get("completed_tests", 0)
            
            # Verify all tests are completed (this check is redundant since unified status already checks this)
            if completed_tests < total_tests:
                pending = total_tests - completed_tests
                return self._failure(f"{pending} tests are still pending")
            
            # Get test results from metadata
            tests_passed = metadata.get("tests_passed", 0)
            tests_failed = metadata.get("tests_failed", 0)
            
            # Complete Test Execution phase
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Test Execution",
                status={
                    "status": "Complete",
                    "completed_at": datetime.utcnow(),
                    "metadata": {
                        **metadata,
                        "completed_by": user_id,
                        "total_tests": total_tests,
                        "tests_passed": tests_passed,
                        "tests_failed": tests_failed,
                        "pass_rate": (tests_passed / total_tests * 100) if total_tests else 0
                    }
                }
            )
            
            # Start Observation Management phase
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Observation Management",
                status={
                    "status": "In Progress",
                    "started_at": datetime.utcnow(),
                    "metadata": {
                        "failed_tests": tests_failed,
                        "observations_created": 0
                    }
                }
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="COMPLETE_TESTING_PHASE",
                resource_type="workflow_phase",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "phase_completed": "Test Execution",
                    "next_phase": "Observation Management",
                    "tests_passed": tests_passed,
                    "tests_failed": tests_failed
                }
            )
            
            # Send notification
            message = f"Test Execution completed. {tests_passed} passed, {tests_failed} failed."
            if tests_failed > 0:
                message += " Observation Management phase has begun."
            
            await self.notification_service.send_notification(
                user_id=user_id,
                title="Testing Phase Completed",
                message=message,
                notification_type="phase_completed",
                priority="high" if tests_failed > 0 else "medium"
            )
            
            return self._success(True)
            
        except Exception as e:
            return self._failure(f"Failed to complete testing phase: {str(e)}")