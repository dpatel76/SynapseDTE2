"""Planning phase use cases"""
from typing import List, Optional
from datetime import datetime

from app.application.dto.test_cycle_dto import (
    CreateTestCycleDTO,
    TestCycleDTO,
    AddReportToCycleDTO,
    AssignTesterDTO
)
from app.application.interfaces.repositories import (
    TestCycleRepository,
    ReportRepository,
    UserRepository,
    WorkflowRepository
)
from app.application.interfaces.services import (
    NotificationService,
    AuditService
)
from app.domain.entities.test_cycle import TestCycle
from app.domain.value_objects import CycleStatus
from app.domain.events.test_cycle_events import (
    TestCycleCreated,
    ReportAddedToCycle,
    TesterAssignedToReport,
    CycleStatusChanged
)
from .base import UseCase, UseCaseResult


class CreateTestCycleUseCase(UseCase[CreateTestCycleDTO, TestCycleDTO]):
    """Use case for creating a new test cycle"""
    
    def __init__(
        self,
        cycle_repository: TestCycleRepository,
        user_repository: UserRepository,
        notification_service: NotificationService,
        audit_service: AuditService
    ):
        self.cycle_repository = cycle_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.audit_service = audit_service
    
    async def execute(self, request: CreateTestCycleDTO) -> UseCaseResult[TestCycleDTO]:
        """Create a new test cycle"""
        try:
            # Validate user exists and has permission
            user = await self.user_repository.get(request.created_by)
            if not user:
                return self._failure("User not found")
            
            # Check for duplicate cycle name
            existing = await self.cycle_repository.get_by_name(request.cycle_name)
            if existing:
                return self._failure(f"Test cycle with name '{request.cycle_name}' already exists")
            
            # Create domain entity
            cycle = TestCycle(
                cycle_name=request.cycle_name,
                start_date=request.start_date,
                end_date=request.end_date,
                created_by=request.created_by,
                description=request.description
            )
            
            # Save to repository
            saved_cycle = await self.cycle_repository.save(cycle)
            
            # Create domain event
            event = TestCycleCreated(
                cycle_name=cycle.cycle_name,
                start_date=cycle.start_date,
                end_date=cycle.end_date,
                created_by=cycle.created_by
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=request.created_by,
                action="CREATE_TEST_CYCLE",
                resource_type="test_cycle",
                resource_id=saved_cycle.id,
                details={"cycle_name": cycle.cycle_name}
            )
            
            # Send notifications to Test Executives
            test_executives = await self.user_repository.find_by_role("Test Executive")
            await self.notification_service.send_bulk_notifications(
                user_ids=[u['user_id'] for u in test_executives],
                title="New Test Cycle Created",
                message=f"Test cycle '{cycle.cycle_name}' has been created",
                notification_type="cycle_created",
                priority="high"
            )
            
            # Convert to DTO
            dto = TestCycleDTO(
                cycle_id=saved_cycle.id,
                cycle_name=saved_cycle.cycle_name,
                start_date=saved_cycle.start_date,
                end_date=saved_cycle.end_date,
                status=saved_cycle.status.value,
                created_by=saved_cycle.created_by,
                created_at=saved_cycle.created_at,
                updated_at=saved_cycle.updated_at,
                description=saved_cycle.description,
                reports=[],
                metrics={}
            )
            
            return self._success(dto, [event])
            
        except Exception as e:
            return self._failure(f"Failed to create test cycle: {str(e)}")


class AddReportToCycleUseCase(UseCase[AddReportToCycleDTO, TestCycleDTO]):
    """Use case for adding a report to a test cycle"""
    
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
    
    async def execute(self, request: AddReportToCycleDTO) -> UseCaseResult[TestCycleDTO]:
        """Add a report to a test cycle"""
        try:
            # Get the cycle
            cycle = await self.cycle_repository.get(request.cycle_id)
            if not cycle:
                return self._failure("Test cycle not found")
            
            # Get the report
            report = await self.report_repository.get(request.report_id)
            if not report:
                return self._failure("Report not found")
            
            # Validate tester if provided
            tester = None
            if request.tester_id:
                tester = await self.user_repository.get(request.tester_id)
                if not tester:
                    return self._failure("Tester not found")
                
                # Verify user is a tester
                permissions = await self.user_repository.get_user_permissions(request.tester_id)
                if "testing.execute" not in permissions:
                    return self._failure("User is not a tester")
            
            # Add report to cycle
            try:
                cycle.add_report(
                    report_id=report['report_id'],
                    report_name=report['report_name'],
                    tester_id=request.tester_id
                )
            except Exception as e:
                return self._failure(str(e))
            
            # Save updated cycle
            saved_cycle = await self.cycle_repository.save(cycle)
            
            # Initialize workflow phases for this report
            phases = [
                "Planning", "Scoping", "Sample Selection", "Data Owner Identification",
                "Request for Information", "Test Execution", 
                "Observation Management", "Testing Report"
            ]
            
            for phase in phases:
                await self.workflow_repository.save_phase_status(
                    cycle_id=request.cycle_id,
                    report_id=request.report_id,
                    phase_name=phase,
                    status={
                        "status": "pending" if phase != "Planning" else "in_progress",
                        "started_at": datetime.utcnow().isoformat() if phase == "Planning" else None
                    }
                )
            
            # Create domain event
            event = ReportAddedToCycle(
                cycle_id=cycle.id,
                report_id=report['report_id'],
                report_name=report['report_name'],
                tester_id=request.tester_id
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=request.requested_by,
                action="ADD_REPORT_TO_CYCLE",
                resource_type="cycle_report",
                resource_id=cycle.id,
                details={
                    "report_id": request.report_id,
                    "report_name": report['report_name'],
                    "tester_id": request.tester_id
                }
            )
            
            # Send notifications
            notification_users = [request.requested_by]
            if request.tester_id:
                notification_users.append(request.tester_id)
            
            await self.notification_service.send_bulk_notifications(
                user_ids=notification_users,
                title="Report Added to Cycle",
                message=f"Report '{report['report_name']}' has been added to cycle '{cycle.cycle_name}'",
                notification_type="report_added",
                priority="medium"
            )
            
            # Get updated cycle data with reports
            cycle_reports = []
            for report_assignment in cycle.reports:
                report_data = await self.report_repository.get(report_assignment.report_id)
                if report_data:
                    cycle_reports.append({
                        **report_data,
                        "tester_id": report_assignment.tester_id,
                        "added_at": report_assignment.added_at
                    })
            
            # Convert to DTO
            dto = TestCycleDTO(
                cycle_id=saved_cycle.id,
                cycle_name=saved_cycle.cycle_name,
                start_date=saved_cycle.start_date,
                end_date=saved_cycle.end_date,
                status=saved_cycle.status.value,
                created_by=saved_cycle.created_by,
                created_at=saved_cycle.created_at,
                updated_at=saved_cycle.updated_at,
                description=saved_cycle.description,
                reports=cycle_reports,
                metrics={"total_reports": len(cycle_reports)}
            )
            
            return self._success(dto, [event])
            
        except Exception as e:
            return self._failure(f"Failed to add report to cycle: {str(e)}")


class AssignTesterUseCase(UseCase[AssignTesterDTO, bool]):
    """Use case for assigning a tester to a report"""
    
    def __init__(
        self,
        cycle_repository: TestCycleRepository,
        user_repository: UserRepository,
        notification_service: NotificationService,
        audit_service: AuditService
    ):
        self.cycle_repository = cycle_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.audit_service = audit_service
    
    async def execute(self, request: AssignTesterDTO) -> UseCaseResult[bool]:
        """Assign a tester to a report in a cycle"""
        try:
            # Get the cycle
            cycle = await self.cycle_repository.get(request.cycle_id)
            if not cycle:
                return self._failure("Test cycle not found")
            
            # Validate tester
            tester = await self.user_repository.get(request.tester_id)
            if not tester:
                return self._failure("Tester not found")
            
            # Verify user is a tester
            permissions = await self.user_repository.get_user_permissions(request.tester_id)
            if "testing.execute" not in permissions:
                return self._failure("User is not a tester")
            
            # Assign tester
            try:
                cycle.assign_tester_to_report(
                    report_id=request.report_id,
                    tester_id=request.tester_id,
                    assigned_by=request.assigned_by
                )
            except Exception as e:
                return self._failure(str(e))
            
            # Save updated cycle
            await self.cycle_repository.save(cycle)
            
            # Create domain event
            event = TesterAssignedToReport(
                cycle_id=cycle.id,
                report_id=request.report_id,
                tester_id=request.tester_id,
                assigned_by=request.assigned_by
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=request.assigned_by,
                action="ASSIGN_TESTER",
                resource_type="cycle_report",
                resource_id=cycle.id,
                details={
                    "report_id": request.report_id,
                    "tester_id": request.tester_id,
                    "tester_name": tester.get('full_name', tester.get('username'))
                }
            )
            
            # Send notification to tester
            await self.notification_service.send_notification(
                user_id=request.tester_id,
                title="New Report Assignment",
                message=f"You have been assigned to test a report in cycle '{cycle.cycle_name}'",
                notification_type="assignment",
                priority="high"
            )
            
            return self._success(True, [event])
            
        except Exception as e:
            return self._failure(f"Failed to assign tester: {str(e)}")


class FinalizeTestCycleUseCase(UseCase[int, TestCycleDTO]):
    """Use case for finalizing test cycle planning phase"""
    
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
    
    async def execute(self, cycle_id: int) -> UseCaseResult[TestCycleDTO]:
        """Finalize the planning phase and move to scoping"""
        try:
            # Get the cycle
            cycle = await self.cycle_repository.get(cycle_id)
            if not cycle:
                return self._failure("Test cycle not found")
            
            # Validate cycle has reports
            if not cycle.reports:
                return self._failure("Cannot finalize cycle without any reports")
            
            # Check all reports have testers assigned
            unassigned = [r for r in cycle.reports if not r.tester_id]
            if unassigned:
                return self._failure(f"{len(unassigned)} reports do not have testers assigned")
            
            # Transition to active status
            old_status = cycle.status
            try:
                cycle.transition_to_active()
            except Exception as e:
                return self._failure(str(e))
            
            # Save updated cycle
            saved_cycle = await self.cycle_repository.save(cycle)
            
            # Update workflow phases - complete Planning, start Scoping
            for report in cycle.reports:
                # Complete Planning phase
                await self.workflow_repository.save_phase_status(
                    cycle_id=cycle_id,
                    report_id=report.report_id,
                    phase_name="Planning",
                    status={
                        "status": "completed",
                        "completed_at": datetime.utcnow().isoformat()
                    }
                )
                
                # Start Scoping phase
                await self.workflow_repository.save_phase_status(
                    cycle_id=cycle_id,
                    report_id=report.report_id,
                    phase_name="Scoping",
                    status={
                        "status": "in_progress",
                        "started_at": datetime.utcnow().isoformat()
                    }
                )
            
            # Create domain event
            event = CycleStatusChanged(
                cycle_id=cycle.id,
                old_status=old_status.value,
                new_status=cycle.status.value,
                changed_at=datetime.utcnow()
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=cycle.created_by,
                action="FINALIZE_PLANNING",
                resource_type="test_cycle",
                resource_id=cycle.id,
                details={
                    "old_status": old_status.value,
                    "new_status": cycle.status.value,
                    "total_reports": len(cycle.reports)
                }
            )
            
            # Send notifications to all testers
            tester_ids = [r.tester_id for r in cycle.reports if r.tester_id]
            await self.notification_service.send_bulk_notifications(
                user_ids=tester_ids,
                title="Test Cycle Activated",
                message=f"Test cycle '{cycle.cycle_name}' is now active. Scoping phase has begun.",
                notification_type="cycle_activated",
                priority="high"
            )
            
            # Convert to DTO
            dto = TestCycleDTO(
                cycle_id=saved_cycle.id,
                cycle_name=saved_cycle.cycle_name,
                start_date=saved_cycle.start_date,
                end_date=saved_cycle.end_date,
                status=saved_cycle.status.value,
                created_by=saved_cycle.created_by,
                created_at=saved_cycle.created_at,
                updated_at=saved_cycle.updated_at,
                description=saved_cycle.description,
                reports=[],  # Would be populated by caller if needed
                metrics={
                    "total_reports": len(cycle.reports),
                    "assigned_testers": len(set(r.tester_id for r in cycle.reports if r.tester_id))
                }
            )
            
            return self._success(dto, [event])
            
        except Exception as e:
            return self._failure(f"Failed to finalize test cycle: {str(e)}")