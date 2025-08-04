from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Request DTOs
class DocumentAnalysisRequestDTO(BaseModel):
    document_text: str = Field(..., description="Text content of the regulatory document")
    document_type: str = Field(default="regulatory", description="Type of document")


class AttributeGenerationRequestDTO(BaseModel):
    """Request schema for attribute generation"""
    regulatory_context: str = Field(..., description="Regulatory context and requirements")
    report_type: str = Field(default="Compliance Report", description="Type of regulatory report")
    preferred_provider: Optional[str] = Field(None, description="Preferred LLM provider (claude, gemini, auto)")
    discovery_provider: Optional[str] = Field(None, description="Preferred provider for discovery phase")
    details_provider: Optional[str] = Field(None, description="Preferred provider for details phase")
    regulatory_report: Optional[str] = Field(None, description="Regulatory report (e.g., FR Y-14M)")
    schedule: Optional[str] = Field(None, description="Report schedule (e.g., Schedule A)")


class TestRecommendationRequestDTO(BaseModel):
    attribute_name: str = Field(..., description="Name of the attribute to test")
    data_type: str = Field(..., description="Data type (string, numeric, date, boolean)")
    regulatory_context: str = Field(..., description="Regulatory context")
    historical_issues: Optional[List[str]] = Field(default=[], description="Historical issues for this attribute")


class PatternAnalysisRequestDTO(BaseModel):
    historical_issues: List[str] = Field(..., description="List of historical issues to analyze")
    report_context: str = Field(..., description="Context of the report")


class DocumentUploadDTO(BaseModel):
    filename: str
    content_type: str
    size: int
    document_type: str = "regulatory"


# Response DTOs
class DocumentAnalysisResponseDTO(BaseModel):
    key_insights: List[str]
    compliance_requirements: List[str]
    risk_areas: List[str]
    recommendations: List[str]
    analyzed_by: int
    analyzed_at: datetime
    
    class Config:
        from_attributes = True


class AttributeGenerationResponseDTO(BaseModel):
    success: bool
    attributes: List[Dict[str, Any]]
    method: str
    providers_used: Dict[str, str]
    metadata: Dict[str, Any]
    generated_at: datetime
    
    class Config:
        from_attributes = True


class TestRecommendationResponseDTO(BaseModel):
    attribute_name: str
    data_type: str
    recommended_tests: List[Dict[str, Any]]
    risk_level: str
    priority: str
    recommended_by: int
    recommended_at: datetime
    
    class Config:
        from_attributes = True


class PatternAnalysisResponseDTO(BaseModel):
    patterns_identified: List[Dict[str, Any]]
    risk_categories: Dict[str, int]
    recommendations: List[str]
    trend_analysis: Dict[str, Any]
    analyzed_by: int
    analyzed_at: datetime
    
    class Config:
        from_attributes = True


class LLMHealthStatusDTO(BaseModel):
    overall_status: str
    available: bool
    provider_details: Dict[str, Dict[str, Any]]
    last_checked: datetime
    
    class Config:
        from_attributes = True


class LLMProviderInfoDTO(BaseModel):
    available_providers: List[str]
    primary_provider: str
    provider_status: Dict[str, Dict[str, Any]]
    overall_health: str
    
    class Config:
        from_attributes = True


class LLMConnectionTestDTO(BaseModel):
    provider: str
    test_result: Dict[str, Any]
    tested_by: int
    tested_at: datetime
    
    class Config:
        from_attributes = True


class LLMUsageStatsDTO(BaseModel):
    period: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    by_operation: Dict[str, int]
    by_provider: Dict[str, int]
    by_user_role: Dict[str, int]
    average_response_time: str
    peak_usage_hour: str
    generated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUploadResponseDTO(BaseModel):
    file_info: Dict[str, Any]
    analysis_result: DocumentAnalysisResponseDTO
    
    class Config:
        from_attributes = True