"""Dependency injection container for clean architecture"""
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.application.interfaces.repositories import (
    IWorkflowRepository, 
    ISampleSelectionRepository,
    TestCycleRepository,
    ReportRepository,
    UserRepository
)
from app.application.interfaces.external_services import (
    ILLMService, 
    IEmailService, 
    IFileStorageService, 
    ITemporalService
)

# Service instances (singletons)
_llm_service: Optional[ILLMService] = None
_file_storage_service: Optional[IFileStorageService] = None
_temporal_service: Optional[ITemporalService] = None


# Repository factories
async def get_workflow_repository(db: AsyncSession) -> IWorkflowRepository:
    """Get workflow repository instance"""
    from app.infrastructure.repositories.sqlalchemy_workflow_repository import SQLAlchemyWorkflowRepository
    return SQLAlchemyWorkflowRepository(db)


async def get_sample_selection_repository(db: AsyncSession) -> ISampleSelectionRepository:
    """Get sample selection repository instance"""
    from app.infrastructure.repositories.sqlalchemy_sample_selection_repository import SQLAlchemySampleSelectionRepository
    return SQLAlchemySampleSelectionRepository(db)


async def get_test_cycle_repository(db: AsyncSession) -> TestCycleRepository:
    """Get test cycle repository instance"""
    from app.infrastructure.repositories.test_cycle_repository import TestCycleRepositoryImpl
    return TestCycleRepositoryImpl(db)


async def get_report_repository(db: AsyncSession) -> ReportRepository:
    """Get report repository instance"""
    from app.infrastructure.repositories.report_repository import ReportRepositoryImpl
    return ReportRepositoryImpl(db)


async def get_user_repository(db: AsyncSession) -> UserRepository:
    """Get user repository instance"""
    from app.infrastructure.repositories.user_repository import UserRepositoryImpl
    return UserRepositoryImpl(db)


# Service factories
def get_llm_service() -> ILLMService:
    """Get LLM service instance (singleton)"""
    global _llm_service
    if _llm_service is None:
        from app.infrastructure.external_services.llm_service_impl import LLMServiceImpl
        _llm_service = LLMServiceImpl()
    return _llm_service


async def get_email_service(db: Optional[AsyncSession] = None) -> IEmailService:
    """Get email service instance"""
    from app.infrastructure.external_services.email_service_impl import EmailServiceImpl
    return EmailServiceImpl(db)


def get_file_storage_service() -> IFileStorageService:
    """Get file storage service instance (singleton)"""
    global _file_storage_service
    if _file_storage_service is None:
        from app.infrastructure.external_services.file_storage_service_impl import FileStorageServiceImpl
        _file_storage_service = FileStorageServiceImpl()
    return _file_storage_service


def get_temporal_service() -> ITemporalService:
    """Get Temporal service instance (singleton)"""
    global _temporal_service
    if _temporal_service is None:
        from app.infrastructure.external_services.temporal_service_impl import TemporalServiceImpl
        _temporal_service = TemporalServiceImpl()
    return _temporal_service


# Use case factories
def create_sample_selection_use_cases(db: AsyncSession) -> Dict[str, Any]:
    """Create all sample selection use cases with dependencies"""
    from app.application.use_cases.sample_selection import (
        StartSampleSelectionPhaseUseCase,
        CreateSampleSetUseCase,
        AddSampleRecordsUseCase,
        AutoSelectSamplesUseCase,
        ReviewSampleSetUseCase,
        BulkReviewSampleSetsUseCase,
        GetSampleSelectionPhaseStatusUseCase,
        CompleteSampleSelectionPhaseUseCase,
        GetSampleStatisticsUseCase,
        GetSampleSelectionSummaryUseCase,
        GenerateSampleSelectionUseCase,
        ApproveSampleSelectionUseCase,
        UploadSampleDataUseCase
    )
    
    llm_service = get_llm_service()
    
    return {
        'start_phase': StartSampleSelectionPhaseUseCase(),
        'create_sample_set': CreateSampleSetUseCase(),
        'add_sample_records': AddSampleRecordsUseCase(),
        'auto_select_samples': AutoSelectSamplesUseCase(),
        'review_sample_set': ReviewSampleSetUseCase(),
        'bulk_review': BulkReviewSampleSetsUseCase(),
        'get_phase_status': GetSampleSelectionPhaseStatusUseCase(),
        'complete_phase': CompleteSampleSelectionPhaseUseCase(),
        'get_statistics': GetSampleStatisticsUseCase(),
        'get_summary': GetSampleSelectionSummaryUseCase(),
        'generate_samples': GenerateSampleSelectionUseCase(llm_service=llm_service),
        'approve_samples': ApproveSampleSelectionUseCase(),
        'upload_samples': UploadSampleDataUseCase()
    }


def create_workflow_use_cases(db: AsyncSession) -> Dict[str, Any]:
    """Create workflow-related use cases with dependencies"""
    from app.application.use_cases.workflow import (
        StartWorkflowUseCase,
        AdvancePhaseUseCase,
        GetWorkflowStatusUseCase,
        CompletePhaseUseCase,
        GetPhaseDetailsUseCase
    )
    
    temporal_service = get_temporal_service()
    
    return {
        'start_workflow': StartWorkflowUseCase(temporal_service=temporal_service),
        'advance_phase': AdvancePhaseUseCase(),
        'get_workflow_status': GetWorkflowStatusUseCase(),
        'complete_phase': CompletePhaseUseCase(),
        'get_phase_details': GetPhaseDetailsUseCase()
    }


def create_planning_use_cases(db: AsyncSession) -> Dict[str, Any]:
    """Create planning phase use cases"""
    from app.application.use_cases.planning import (
        StartPlanningPhaseUseCase,
        GenerateTestAttributesUseCase,
        SaveTestAttributesUseCase,
        CompletePlanningPhaseUseCase
    )
    
    llm_service = get_llm_service()
    
    return {
        'start_planning': StartPlanningPhaseUseCase(),
        'generate_attributes': GenerateTestAttributesUseCase(llm_service=llm_service),
        'save_attributes': SaveTestAttributesUseCase(),
        'complete_planning': CompletePlanningPhaseUseCase()
    }


def create_scoping_use_cases(db: AsyncSession) -> Dict[str, Any]:
    """Create scoping phase use cases"""
    from app.application.use_cases.scoping import (
        StartScopingPhaseUseCase,
        UpdateScopingDecisionUseCase,
        BulkUpdateScopingUseCase,
        CompleteScopingPhaseUseCase,
        GetScopingStatusUseCase
    )
    
    return {
        'start_scoping': StartScopingPhaseUseCase(),
        'update_scoping': UpdateScopingDecisionUseCase(),
        'bulk_update': BulkUpdateScopingUseCase(),
        'complete_scoping': CompleteScopingPhaseUseCase(),
        'get_status': GetScopingStatusUseCase()
    }


def create_observation_use_cases(db: AsyncSession) -> Dict[str, Any]:
    """Create observation management use cases"""
    from app.application.use_cases.observation_management import (
        CreateObservationUseCase,
        UpdateObservationUseCase,
        ApproveObservationUseCase,
        GetObservationsUseCase,
        GetObservationDetailsUseCase
    )
    
    return {
        'create_observation': CreateObservationUseCase(),
        'update_observation': UpdateObservationUseCase(),
        'approve_observation': ApproveObservationUseCase(),
        'get_observations': GetObservationsUseCase(),
        'get_observation_details': GetObservationDetailsUseCase()
    }


# Dependency container for backward compatibility
_container: Dict[str, Any] = {}


def setup_dependencies():
    """Setup all dependencies in the container"""
    global _container
    
    # Add auth use cases to container
    _container["auth.authenticate_user"] = None  # Will be created on demand
    _container["auth.register_user"] = None  # Will be created on demand
    _container["auth.get_current_user"] = None  # Will be created on demand
    _container["auth.change_password"] = None  # Will be created on demand


def get_container():
    """Get dependency container for backward compatibility"""
    return _container


def get_use_case(name: str):
    """Get specific use case for backward compatibility"""
    return _container.get(name)


def get_repository(name: str):
    """Get specific repository for backward compatibility"""
    return _container.get(name)


def get_service(name: str):
    """Get specific service for backward compatibility"""
    return _container.get(name)