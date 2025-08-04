"""Dependency injection container for clean architecture"""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.infrastructure.repositories import (
    SQLAlchemyTestCycleRepository,
    SQLAlchemyReportRepository,
    SQLAlchemyUserRepository,
    SQLAlchemyWorkflowRepository
)
from app.infrastructure.services import (
    NotificationServiceImpl,
    EmailServiceImpl,
    LLMServiceImpl,
    AuditServiceImpl,
    SLAServiceImpl,
    DocumentStorageServiceImpl
)
from app.services.unified_status_service import UnifiedStatusService
from app.application.use_cases.planning import (
    CreateTestCycleUseCase,
    AddReportToCycleUseCase,
    AssignTesterUseCase,
    FinalizeTestCycleUseCase
)
from app.application.use_cases.scoping import (
    GenerateTestAttributesUseCase,
    ReviewAttributesUseCase,
    ApproveAttributesUseCase
)
from app.application.use_cases.workflow import (
    AdvanceWorkflowPhaseUseCase,
    GetWorkflowStatusUseCase,
    OverridePhaseUseCase
)
from app.application.use_cases.test_execution import (
    ExecuteTestUseCase,
    GetTestingProgressUseCase,
    CompleteTestingPhaseUseCase
)
from app.application.use_cases.observation import (
    CreateObservationUseCase,
    GetObservationUseCase,
    ListObservationsUseCase,
    UpdateObservationUseCase,
    SubmitObservationUseCase,
    ReviewObservationUseCase,
    BatchReviewObservationsUseCase,
    CreateImpactAssessmentUseCase,
    CreateResolutionUseCase,
    GetObservationPhaseStatusUseCase,
    CompleteObservationPhaseUseCase,
    GetObservationAnalyticsUseCase,
    AutoDetectObservationsUseCase
)


class Container:
    """Dependency injection container"""
    
    def __init__(self):
        self._session: Optional[AsyncSession] = None
    
    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with AsyncSessionLocal() as session:
            yield session
    
    # Repositories
    
    def get_test_cycle_repository(self, session: AsyncSession) -> SQLAlchemyTestCycleRepository:
        """Get test cycle repository"""
        return SQLAlchemyTestCycleRepository(session)
    
    def get_report_repository(self, session: AsyncSession) -> SQLAlchemyReportRepository:
        """Get report repository"""
        return SQLAlchemyReportRepository(session)
    
    def get_user_repository(self, session: AsyncSession) -> SQLAlchemyUserRepository:
        """Get user repository"""
        return SQLAlchemyUserRepository(session)
    
    def get_workflow_repository(self, session: AsyncSession) -> SQLAlchemyWorkflowRepository:
        """Get workflow repository"""
        return SQLAlchemyWorkflowRepository(session)
    
    # Services
    
    def get_notification_service(self, session: AsyncSession) -> NotificationServiceImpl:
        """Get notification service"""
        return NotificationServiceImpl(session)
    
    def get_email_service(self) -> EmailServiceImpl:
        """Get email service"""
        return EmailServiceImpl()
    
    def get_llm_service(self) -> LLMServiceImpl:
        """Get LLM service"""
        return LLMServiceImpl()
    
    def get_audit_service(self, session: AsyncSession) -> AuditServiceImpl:
        """Get audit service"""
        return AuditServiceImpl(session)
    
    def get_sla_service(self, session: AsyncSession) -> SLAServiceImpl:
        """Get SLA service"""
        return SLAServiceImpl(session)
    
    def get_document_storage_service(self) -> DocumentStorageServiceImpl:
        """Get document storage service"""
        return DocumentStorageServiceImpl()
    
    def get_unified_status_service(self, session: AsyncSession) -> UnifiedStatusService:
        """Get unified status service"""
        return UnifiedStatusService(session)
    
    # Use Cases - Planning
    
    def get_create_test_cycle_use_case(self, session: AsyncSession) -> CreateTestCycleUseCase:
        """Get create test cycle use case"""
        return CreateTestCycleUseCase(
            cycle_repository=self.get_test_cycle_repository(session),
            user_repository=self.get_user_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_add_report_to_cycle_use_case(self, session: AsyncSession) -> AddReportToCycleUseCase:
        """Get add report to cycle use case"""
        return AddReportToCycleUseCase(
            cycle_repository=self.get_test_cycle_repository(session),
            report_repository=self.get_report_repository(session),
            user_repository=self.get_user_repository(session),
            workflow_repository=self.get_workflow_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_assign_tester_use_case(self, session: AsyncSession) -> AssignTesterUseCase:
        """Get assign tester use case"""
        return AssignTesterUseCase(
            cycle_repository=self.get_test_cycle_repository(session),
            user_repository=self.get_user_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_finalize_test_cycle_use_case(self, session: AsyncSession) -> FinalizeTestCycleUseCase:
        """Get finalize test cycle use case"""
        return FinalizeTestCycleUseCase(
            cycle_repository=self.get_test_cycle_repository(session),
            workflow_repository=self.get_workflow_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    # Use Cases - Scoping
    
    def get_generate_test_attributes_use_case(self, session: AsyncSession) -> GenerateTestAttributesUseCase:
        """Get generate test attributes use case"""
        return GenerateTestAttributesUseCase(
            cycle_repository=self.get_test_cycle_repository(session),
            report_repository=self.get_report_repository(session),
            workflow_repository=self.get_workflow_repository(session),
            llm_service=self.get_llm_service(),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_review_attributes_use_case(self, session: AsyncSession) -> ReviewAttributesUseCase:
        """Get review attributes use case"""
        return ReviewAttributesUseCase(
            workflow_repository=self.get_workflow_repository(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_approve_attributes_use_case(self, session: AsyncSession) -> ApproveAttributesUseCase:
        """Get approve attributes use case"""
        return ApproveAttributesUseCase(
            cycle_repository=self.get_test_cycle_repository(session),
            workflow_repository=self.get_workflow_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    # Use Cases - Test Execution
    
    def get_execute_test_use_case(self, session: AsyncSession) -> ExecuteTestUseCase:
        """Get execute test use case"""
        return ExecuteTestUseCase(
            workflow_repository=self.get_workflow_repository(session),
            llm_service=self.get_llm_service(),
            document_storage_service=self.get_document_storage_service(),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_testing_progress_use_case(self, session: AsyncSession) -> GetTestingProgressUseCase:
        """Get testing progress use case"""
        return GetTestingProgressUseCase(
            workflow_repository=self.get_workflow_repository(session),
            report_repository=self.get_report_repository(session)
        )
    
    def get_complete_testing_phase_use_case(self, session: AsyncSession) -> CompleteTestingPhaseUseCase:
        """Get complete testing phase use case"""
        return CompleteTestingPhaseUseCase(
            workflow_repository=self.get_workflow_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session),
            unified_status_service=self.get_unified_status_service(session)
        )
    
    # Use Cases - Observation Management
    
    def get_create_observation_use_case(self, session: AsyncSession) -> CreateObservationUseCase:
        """Get create observation use case"""
        return CreateObservationUseCase(
            workflow_repository=self.get_workflow_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_get_observation_use_case(self, session: AsyncSession) -> GetObservationUseCase:
        """Get get observation use case"""
        return GetObservationUseCase(
            workflow_repository=self.get_workflow_repository(session)
        )
    
    def get_list_observations_use_case(self, session: AsyncSession) -> ListObservationsUseCase:
        """Get list observations use case"""
        return ListObservationsUseCase(
            workflow_repository=self.get_workflow_repository(session)
        )
    
    def get_update_observation_use_case(self, session: AsyncSession) -> UpdateObservationUseCase:
        """Get update observation use case"""
        return UpdateObservationUseCase(
            workflow_repository=self.get_workflow_repository(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_submit_observation_use_case(self, session: AsyncSession) -> SubmitObservationUseCase:
        """Get submit observation use case"""
        return SubmitObservationUseCase(
            workflow_repository=self.get_workflow_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_review_observation_use_case(self, session: AsyncSession) -> ReviewObservationUseCase:
        """Get review observation use case"""
        return ReviewObservationUseCase(
            workflow_repository=self.get_workflow_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_batch_review_observations_use_case(self, session: AsyncSession) -> BatchReviewObservationsUseCase:
        """Get batch review observations use case"""
        return BatchReviewObservationsUseCase(
            workflow_repository=self.get_workflow_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_get_observation_phase_status_use_case(self, session: AsyncSession) -> GetObservationPhaseStatusUseCase:
        """Get observation phase status use case"""
        return GetObservationPhaseStatusUseCase(
            workflow_repository=self.get_workflow_repository(session)
        )
    
    def get_complete_observation_phase_use_case(self, session: AsyncSession) -> CompleteObservationPhaseUseCase:
        """Get complete observation phase use case"""
        return CompleteObservationPhaseUseCase(
            workflow_repository=self.get_workflow_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session)
        )
    
    def get_get_observation_analytics_use_case(self, session: AsyncSession) -> GetObservationAnalyticsUseCase:
        """Get observation analytics use case"""
        return GetObservationAnalyticsUseCase(
            workflow_repository=self.get_workflow_repository(session)
        )
    
    def get_auto_detect_observations_use_case(self, session: AsyncSession) -> AutoDetectObservationsUseCase:
        """Get auto detect observations use case"""
        return AutoDetectObservationsUseCase(
            workflow_repository=self.get_workflow_repository(session),
            llm_service=self.get_llm_service(),
            audit_service=self.get_audit_service(session)
        )
    
    # Use Cases - Workflow
    
    def get_advance_workflow_phase_use_case(self, session: AsyncSession) -> AdvanceWorkflowPhaseUseCase:
        """Get advance workflow phase use case"""
        return AdvanceWorkflowPhaseUseCase(
            workflow_repository=self.get_workflow_repository(session),
            user_repository=self.get_user_repository(session),
            notification_service=self.get_notification_service(session),
            audit_service=self.get_audit_service(session),
            sla_service=self.get_sla_service(session)
        )
    
    def get_workflow_status_use_case(self, session: AsyncSession) -> GetWorkflowStatusUseCase:
        """Get workflow status use case"""
        return GetWorkflowStatusUseCase(
            workflow_repository=self.get_workflow_repository(session),
            sla_service=self.get_sla_service(session)
        )
    
    def get_override_phase_use_case(self, session: AsyncSession) -> OverridePhaseUseCase:
        """Get override phase use case"""
        return OverridePhaseUseCase(
            workflow_repository=self.get_workflow_repository(session),
            user_repository=self.get_user_repository(session),
            audit_service=self.get_audit_service(session),
            notification_service=self.get_notification_service(session)
        )


# Global container instance
container = Container()


# Dependency injection functions for FastAPI

async def get_db():
    """Get database session for FastAPI dependency injection"""
    async for session in container.get_db_session():
        yield session


def get_container() -> Container:
    """Get container instance"""
    return container