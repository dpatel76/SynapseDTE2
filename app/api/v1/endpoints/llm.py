from typing import Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Query
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.llm_service import HybridLLMService, get_llm_service
from app.application.dtos.llm import (
    DocumentAnalysisRequestDTO, DocumentAnalysisResponseDTO,
    AttributeGenerationRequestDTO, AttributeGenerationResponseDTO,
    TestRecommendationRequestDTO, TestRecommendationResponseDTO,
    PatternAnalysisRequestDTO, PatternAnalysisResponseDTO,
    LLMHealthStatusDTO, LLMProviderInfoDTO,
    LLMConnectionTestDTO, LLMUsageStatsDTO,
    DocumentUploadResponseDTO
)
from app.application.use_cases.llm import LLMUseCase

router = APIRouter(prefix="/llm", tags=["LLM Integration"])


@router.get("/health", response_model=LLMHealthStatusDTO)
async def llm_health_check(
    llm_service: HybridLLMService = Depends(get_llm_service)
):
    """
    Check health status of LLM services.
    
    Returns the overall health status and details for each provider.
    """
    return await LLMUseCase.check_health(llm_service)


@router.post("/analyze-document", response_model=DocumentAnalysisResponseDTO)
async def analyze_document(
    request: DocumentAnalysisRequestDTO,
    current_user: User = Depends(get_current_user),
    llm_service: HybridLLMService = Depends(get_llm_service)
):
    """
    Analyze regulatory document for key insights.
    
    Required roles: Tester, Test Executive, Report Owner, Admin
    """
    return await LLMUseCase.analyze_document(request, current_user, llm_service)


@router.post("/generate-attributes", response_model=AttributeGenerationResponseDTO)
async def generate_attributes(
    request: AttributeGenerationRequestDTO,
    current_user: User = Depends(get_current_user),
    llm_service: HybridLLMService = Depends(get_llm_service)
):
    """
    Generate test attributes using unified 2-phase strategy.
    
    Supports multiple generation strategies:
    - Standard 2-phase with preferred provider
    - Explicit 2-phase with specific providers for each phase
    - Legacy hybrid approach (Gemini discovery + Claude details)
    """
    return await LLMUseCase.generate_attributes(request, current_user, llm_service)


@router.post("/recommend-tests", response_model=TestRecommendationResponseDTO)
async def recommend_tests(
    request: TestRecommendationRequestDTO,
    current_user: User = Depends(get_current_user),
    llm_service: HybridLLMService = Depends(get_llm_service)
):
    """
    Generate test recommendations for a specific attribute.
    
    Required roles: Tester, Test Executive, Admin
    """
    return await LLMUseCase.recommend_tests(request, current_user, llm_service)


@router.post("/analyze-patterns", response_model=PatternAnalysisResponseDTO)
async def analyze_patterns(
    request: PatternAnalysisRequestDTO,
    current_user: User = Depends(get_current_user),
    llm_service: HybridLLMService = Depends(get_llm_service)
):
    """
    Analyze historical issues to identify patterns.
    
    Required roles: Test Executive, Report Owner, Report Owner Executive, Admin
    """
    return await LLMUseCase.analyze_patterns(request, current_user, llm_service)


@router.post("/upload-document", response_model=DocumentUploadResponseDTO)
async def upload_and_analyze_document(
    file: UploadFile = File(...),
    document_type: str = Query("regulatory", description="Type of document"),
    current_user: User = Depends(get_current_user),
    llm_service: HybridLLMService = Depends(get_llm_service)
):
    """
    Upload and analyze a regulatory document file.
    
    Supported file types:
    - Text files (.txt)
    - PDF files (.pdf)
    - Word documents (.doc, .docx)
    
    Maximum file size: 10MB
    
    Required roles: Tester, Test Executive, Report Owner, Admin
    """
    return await LLMUseCase.upload_and_analyze_document(
        file, document_type, current_user, llm_service
    )


@router.get("/providers", response_model=LLMProviderInfoDTO)
async def get_llm_providers(
    current_user: User = Depends(get_current_user),
    llm_service: HybridLLMService = Depends(get_llm_service)
):
    """
    Get information about available LLM providers.
    
    Required roles: Admin, Test Executive
    """
    return await LLMUseCase.get_provider_info(current_user, llm_service)


@router.post("/test-connection", response_model=LLMConnectionTestDTO)
async def test_llm_connection(
    provider: str = Query("primary", description="Provider to test (primary, claude, gemini, mock)"),
    current_user: User = Depends(get_current_user),
    llm_service: HybridLLMService = Depends(get_llm_service)
):
    """
    Test connection to a specific LLM provider.
    
    Required role: Admin
    """
    return await LLMUseCase.test_connection(provider, current_user, llm_service)


@router.get("/usage-stats", response_model=LLMUsageStatsDTO)
async def get_usage_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in statistics"),
    current_user: User = Depends(get_current_user)
):
    """
    Get LLM usage statistics.
    
    Returns usage metrics including:
    - Total requests and success rate
    - Breakdown by operation type
    - Breakdown by provider
    - Breakdown by user role
    - Response time metrics
    
    Required roles: Test Executive, Admin
    """
    return await LLMUseCase.get_usage_statistics(days, current_user)