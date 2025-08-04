from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import HTTPException, UploadFile, status
import logging

from app.models.user import User
from app.services.llm_service import HybridLLMService
from app.application.dtos.llm import (
    DocumentAnalysisRequestDTO, DocumentAnalysisResponseDTO,
    AttributeGenerationRequestDTO, AttributeGenerationResponseDTO,
    TestRecommendationRequestDTO, TestRecommendationResponseDTO,
    PatternAnalysisRequestDTO, PatternAnalysisResponseDTO,
    LLMHealthStatusDTO, LLMProviderInfoDTO,
    LLMConnectionTestDTO, LLMUsageStatsDTO,
    DocumentUploadDTO, DocumentUploadResponseDTO
)

logger = logging.getLogger(__name__)


class LLMUseCase:
    """Use cases for LLM integration"""
    
    @staticmethod
    async def check_health(
        llm_service: HybridLLMService
    ) -> LLMHealthStatusDTO:
        """Check health status of LLM services"""
        try:
            health_status = await llm_service.health_check()
            return LLMHealthStatusDTO(
                overall_status=health_status["overall_status"],
                available=health_status["available"],
                provider_details=health_status["provider_details"],
                last_checked=datetime.utcnow()
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check LLM health: {str(e)}"
            )
    
    @staticmethod
    async def analyze_document(
        request_dto: DocumentAnalysisRequestDTO,
        current_user: User,
        llm_service: HybridLLMService
    ) -> DocumentAnalysisResponseDTO:
        """Analyze regulatory document for key insights"""
        # Check permissions
        allowed_roles = ["Tester", "Test Executive", "Report Owner", "Admin"]
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Current role: {current_user.role}"
            )
        
        try:
            result = await llm_service.analyze_regulatory_document(
                request_dto.document_text,
                request_dto.document_type
            )
            
            return DocumentAnalysisResponseDTO(
                key_insights=result.get("key_insights", []),
                compliance_requirements=result.get("compliance_requirements", []),
                risk_areas=result.get("risk_areas", []),
                recommendations=result.get("recommendations", []),
                analyzed_by=current_user.user_id,
                analyzed_at=datetime.utcnow()
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze document: {str(e)}"
            )
    
    @staticmethod
    async def generate_attributes(
        request_dto: AttributeGenerationRequestDTO,
        current_user: User,
        llm_service: HybridLLMService
    ) -> AttributeGenerationResponseDTO:
        """Generate test attributes using unified 2-phase strategy"""
        try:
            # Determine which approach to use based on request
            if request_dto.discovery_provider and request_dto.details_provider:
                # Explicit 2-phase with specific providers
                result = await llm_service._generate_attributes_two_phase(
                    regulatory_context=request_dto.regulatory_context,
                    report_type=request_dto.report_type,
                    preferred_discovery=request_dto.discovery_provider,
                    preferred_details=request_dto.details_provider,
                    regulatory_report=request_dto.regulatory_report,
                    schedule=request_dto.schedule
                )
            elif request_dto.preferred_provider == 'hybrid':
                # Legacy hybrid approach (Gemini discovery + Claude details)
                result = await llm_service.generate_test_attributes_hybrid(
                    regulatory_context=request_dto.regulatory_context,
                    report_type=request_dto.report_type,
                    regulatory_report=request_dto.regulatory_report,
                    schedule=request_dto.schedule
                )
            else:
                # Standard 2-phase approach with preferred provider
                result = await llm_service.generate_test_attributes(
                    regulatory_context=request_dto.regulatory_context,
                    report_type=request_dto.report_type,
                    preferred_provider=request_dto.preferred_provider,
                    regulatory_report=request_dto.regulatory_report,
                    schedule=request_dto.schedule
                )
            
            if result.get("success"):
                logger.info(f"Successfully generated {len(result.get('attributes', []))} attributes using {result.get('method', 'unknown')} method")
                
                return AttributeGenerationResponseDTO(
                    success=True,
                    attributes=result.get("attributes", []),
                    method=result.get("method", "unknown"),
                    providers_used=result.get("providers_used", {}),
                    metadata=result.get("metadata", {}),
                    generated_at=datetime.utcnow()
                )
            else:
                logger.error(f"Attribute generation failed: {result.get('error', 'Unknown error')}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Attribute generation failed: {result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            logger.error(f"Attribute generation endpoint error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Attribute generation failed: {str(e)}"
            )
    
    @staticmethod
    async def recommend_tests(
        request_dto: TestRecommendationRequestDTO,
        current_user: User,
        llm_service: HybridLLMService
    ) -> TestRecommendationResponseDTO:
        """Generate test recommendations for a specific attribute"""
        # Check permissions
        allowed_roles = ["Tester", "Test Executive", "Admin"]
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Current role: {current_user.role}"
            )
        
        try:
            result = await llm_service.recommend_tests(
                request_dto.attribute_name,
                request_dto.data_type,
                request_dto.regulatory_context,
                request_dto.historical_issues
            )
            
            return TestRecommendationResponseDTO(
                attribute_name=request_dto.attribute_name,
                data_type=request_dto.data_type,
                recommended_tests=result.get("recommended_tests", []),
                risk_level=result.get("risk_level", "medium"),
                priority=result.get("priority", "normal"),
                recommended_by=current_user.user_id,
                recommended_at=datetime.utcnow()
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate test recommendations: {str(e)}"
            )
    
    @staticmethod
    async def analyze_patterns(
        request_dto: PatternAnalysisRequestDTO,
        current_user: User,
        llm_service: HybridLLMService
    ) -> PatternAnalysisResponseDTO:
        """Analyze historical issues to identify patterns"""
        # Check permissions
        allowed_roles = ["Test Executive", "Report Owner", "Report Owner Executive", "Admin"]
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Current role: {current_user.role}"
            )
        
        try:
            result = await llm_service.analyze_historical_patterns(
                request_dto.historical_issues,
                request_dto.report_context
            )
            
            return PatternAnalysisResponseDTO(
                patterns_identified=result.get("patterns_identified", []),
                risk_categories=result.get("risk_categories", {}),
                recommendations=result.get("recommendations", []),
                trend_analysis=result.get("trend_analysis", {}),
                analyzed_by=current_user.user_id,
                analyzed_at=datetime.utcnow()
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze patterns: {str(e)}"
            )
    
    @staticmethod
    async def upload_and_analyze_document(
        file: UploadFile,
        document_type: str,
        current_user: User,
        llm_service: HybridLLMService
    ) -> DocumentUploadResponseDTO:
        """Upload and analyze a regulatory document file"""
        # Check permissions
        allowed_roles = ["Tester", "Test Executive", "Report Owner", "Admin"]
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Current role: {current_user.role}"
            )
        
        try:
            # Check file type
            allowed_types = [
                "text/plain", "application/pdf", "application/msword", 
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ]
            
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file.content_type} not supported. Allowed types: {allowed_types}"
                )
            
            # Check file size (limit to 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size {file.size} exceeds maximum allowed size of {max_size} bytes"
                )
            
            # Read file content
            content = await file.read()
            
            # Extract text based on file type
            if file.content_type == "text/plain":
                document_text = content.decode("utf-8")
            else:
                # In a full implementation, use PyPDF2, python-docx etc.
                document_text = f"[Extracted text from {file.filename}]\nSimulated document content for testing purposes."
            
            # Analyze the document
            analysis_result = await llm_service.analyze_regulatory_document(document_text, document_type)
            
            file_info = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size,
                "uploaded_by": current_user.user_id,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
            analysis_response = DocumentAnalysisResponseDTO(
                key_insights=analysis_result.get("key_insights", []),
                compliance_requirements=analysis_result.get("compliance_requirements", []),
                risk_areas=analysis_result.get("risk_areas", []),
                recommendations=analysis_result.get("recommendations", []),
                analyzed_by=current_user.user_id,
                analyzed_at=datetime.utcnow()
            )
            
            return DocumentUploadResponseDTO(
                file_info=file_info,
                analysis_result=analysis_response
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload and analyze document: {str(e)}"
            )
    
    @staticmethod
    async def get_provider_info(
        current_user: User,
        llm_service: HybridLLMService
    ) -> LLMProviderInfoDTO:
        """Get information about available LLM providers"""
        # Check permissions
        allowed_roles = ["Admin", "Test Executive"]
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Current role: {current_user.role}"
            )
        
        try:
            health_status = await llm_service.health_check()
            
            return LLMProviderInfoDTO(
                available_providers=list(llm_service.providers.keys()),
                primary_provider="claude" if "claude" in llm_service.providers else (
                    "gemini" if "gemini" in llm_service.providers else "mock"
                ),
                provider_status=health_status["provider_details"],
                overall_health=health_status["overall_status"]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get provider information: {str(e)}"
            )
    
    @staticmethod
    async def test_connection(
        provider: str,
        current_user: User,
        llm_service: HybridLLMService
    ) -> LLMConnectionTestDTO:
        """Test connection to a specific LLM provider"""
        # Check permissions
        if current_user.role != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: Admin. Current role: {current_user.role}"
            )
        
        try:
            if provider == "primary":
                llm_provider = await llm_service.get_primary_provider()
            elif provider in llm_service.providers:
                llm_provider = llm_service.providers[provider]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Provider '{provider}' not available"
                )
            
            # Test the connection
            test_result = await llm_provider.health_check()
            
            return LLMConnectionTestDTO(
                provider=provider,
                test_result=test_result,
                tested_by=current_user.user_id,
                tested_at=datetime.utcnow()
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to test LLM connection: {str(e)}"
            )
    
    @staticmethod
    async def get_usage_statistics(
        days: int,
        current_user: User
    ) -> LLMUsageStatsDTO:
        """Get LLM usage statistics"""
        # Check permissions
        allowed_roles = ["Test Executive", "Admin"]
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Current role: {current_user.role}"
            )
        
        try:
            # In a real implementation, query usage logs from database
            # For now, return simulated statistics
            
            return LLMUsageStatsDTO(
                period=f"Last {days} days",
                total_requests=245,
                successful_requests=238,
                failed_requests=7,
                success_rate=97.1,
                by_operation={
                    "document_analysis": 89,
                    "attribute_generation": 67,
                    "test_recommendations": 54,
                    "pattern_analysis": 35
                },
                by_provider={
                    "claude": 156,
                    "gemini": 82,
                    "mock": 7
                },
                by_user_role={
                    "Tester": 123,
                    "Test Executive": 89,
                    "Report Owner": 33
                },
                average_response_time="2.3 seconds",
                peak_usage_hour="14:00-15:00",
                generated_at=datetime.utcnow()
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get usage statistics: {str(e)}"
            )