"""
Pydantic schemas for document management
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


# Enums
class DocumentTypeEnum(str, Enum):
    REPORT_SAMPLE_DATA = "report_sample_data"
    REPORT_UNDERLYING_TRANSACTION_DATA = "report_underlying_transaction_data"
    REPORT_SOURCE_TRANSACTION_DATA = "report_source_transaction_data"
    REPORT_SOURCE_DOCUMENT = "report_source_document"


class FileFormatEnum(str, Enum):
    CSV = "csv"
    PIPE = "pipe"
    EXCEL = "excel"
    XLSX = "xlsx"
    XLS = "xls"
    WORD = "word"
    DOCX = "docx"
    PDF = "pdf"
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"


class AccessLevelEnum(str, Enum):
    PUBLIC = "public"
    PHASE_RESTRICTED = "phase_restricted"
    ROLE_RESTRICTED = "role_restricted"
    USER_RESTRICTED = "user_restricted"


class UploadStatusEnum(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    QUARANTINED = "quarantined"


class ProcessingStatusEnum(str, Enum):
    NOT_PROCESSED = "not_processed"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ValidationStatusEnum(str, Enum):
    NOT_VALIDATED = "not_validated"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


# Request schemas
class DocumentUploadRequest(BaseModel):
    """Request schema for document upload"""
    cycle_id: int = Field(..., description="Test cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_id: int = Field(..., description="Workflow phase ID")
    test_case_id: Optional[str] = Field(None, max_length=255, description="Optional test case ID for granular tracking")
    document_type: DocumentTypeEnum = Field(..., description="Type of document")
    document_title: str = Field(..., min_length=1, max_length=500, description="Document title")
    document_description: Optional[str] = Field(None, max_length=2000, description="Document description")
    document_category: str = Field("general", max_length=50, description="Document category")
    access_level: AccessLevelEnum = Field(AccessLevelEnum.PHASE_RESTRICTED, description="Access control level")
    allowed_roles: Optional[List[str]] = Field(None, description="Allowed role names")
    allowed_users: Optional[List[int]] = Field(None, description="Allowed user IDs")
    required_for_completion: bool = Field(False, description="Whether document is required for phase completion")
    approval_required: bool = Field(False, description="Whether document requires approval")
    workflow_stage: Optional[str] = Field(None, max_length=100, description="Workflow stage this document supports")


class DocumentUpdateRequest(BaseModel):
    """Request schema for document metadata update"""
    document_title: Optional[str] = Field(None, min_length=1, max_length=500, description="Document title")
    document_description: Optional[str] = Field(None, max_length=2000, description="Document description")
    document_category: Optional[str] = Field(None, max_length=50, description="Document category")
    access_level: Optional[AccessLevelEnum] = Field(None, description="Access control level")
    allowed_roles: Optional[List[str]] = Field(None, description="Allowed role names")
    allowed_users: Optional[List[int]] = Field(None, description="Allowed user IDs")
    required_for_completion: Optional[bool] = Field(None, description="Whether document is required for phase completion")
    approval_required: Optional[bool] = Field(None, description="Whether document requires approval")
    workflow_stage: Optional[str] = Field(None, max_length=100, description="Workflow stage this document supports")


class DocumentSearchRequest(BaseModel):
    """Request schema for document search"""
    search_query: str = Field(..., min_length=1, max_length=500, description="Search query")
    cycle_id: Optional[int] = Field(None, description="Filter by cycle ID")
    report_id: Optional[int] = Field(None, description="Filter by report ID")
    phase_id: Optional[int] = Field(None, description="Filter by phase ID")
    document_type: Optional[DocumentTypeEnum] = Field(None, description="Filter by document type")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=200, description="Items per page")


class DocumentListRequest(BaseModel):
    """Request schema for document listing"""
    cycle_id: Optional[int] = Field(None, description="Filter by cycle ID")
    report_id: Optional[int] = Field(None, description="Filter by report ID")
    phase_id: Optional[int] = Field(None, description="Filter by phase ID")
    test_case_id: Optional[str] = Field(None, description="Filter by test case ID")
    document_type: Optional[DocumentTypeEnum] = Field(None, description="Filter by document type")
    include_archived: bool = Field(False, description="Include archived documents")
    latest_only: bool = Field(True, description="Show only latest versions")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=200, description="Items per page")


class DocumentApprovalRequest(BaseModel):
    """Request schema for document approval"""
    approval_decision: str = Field(..., pattern="^(approved|rejected)$", description="Approval decision")
    approval_notes: Optional[str] = Field(None, max_length=2000, description="Approval notes")


# Document versioning schemas
class DocumentVersionCreateRequest(BaseModel):
    """Request schema for creating a new document version"""
    parent_document_id: int = Field(..., description="ID of the parent document to version")
    document_title: str = Field(..., min_length=1, max_length=500, description="Document title for new version")
    document_description: Optional[str] = Field(None, max_length=2000, description="Document description for new version")
    version_notes: Optional[str] = Field(None, max_length=2000, description="Notes about this version")


class DocumentVersionRestoreRequest(BaseModel):
    """Request schema for restoring a document version"""
    version_document_id: int = Field(..., description="ID of the version to restore as latest")


class DocumentVersionCompareRequest(BaseModel):
    """Request schema for comparing document versions"""
    version1_id: int = Field(..., description="ID of first version to compare")
    version2_id: int = Field(..., description="ID of second version to compare")


# Response schemas
class DocumentResponse(BaseModel):
    """Response schema for document details"""
    id: int
    cycle_id: int
    report_id: int
    phase_id: int
    test_case_id: Optional[str]
    document_type: str
    document_category: str
    original_filename: str
    file_size: int
    file_format: str
    mime_type: str
    document_title: str
    document_description: Optional[str]
    document_version: str
    is_latest_version: bool
    access_level: str
    upload_status: str
    processing_status: str
    validation_status: str
    content_preview: Optional[str]
    quality_score: Optional[float]
    download_count: int
    view_count: int
    required_for_completion: bool
    approval_required: bool
    workflow_stage: Optional[str]
    uploaded_by: int
    uploaded_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_archived: bool

    class Config:
        from_attributes = True


class DocumentSummaryResponse(BaseModel):
    """Response schema for document summary"""
    id: int
    document_title: str
    document_type: str
    file_format: str
    file_size: int
    upload_status: str
    validation_status: str
    uploaded_at: Optional[datetime]
    is_latest_version: bool

    class Config:
        from_attributes = True


class DocumentSearchResultResponse(BaseModel):
    """Response schema for document search result"""
    document: DocumentResponse
    relevance_score: float
    matched_fields: Optional[List[str]] = []


class DocumentVersionInfoResponse(BaseModel):
    """Response schema for document version information"""
    current_version: str
    total_versions: int
    has_newer_version: bool
    parent_id: Optional[int]


class DocumentMetricsResponse(BaseModel):
    """Response schema for document metrics"""
    total_documents: int
    total_size_bytes: int
    total_size_mb: float
    by_document_type: Dict[str, Dict[str, Union[int, float]]]
    by_upload_status: Dict[str, int]
    by_file_format: Dict[str, Dict[str, Union[int, float]]]


class PaginationResponse(BaseModel):
    """Response schema for pagination metadata"""
    page: int
    page_size: int
    total_count: int
    total_pages: int


class DocumentListResponse(BaseModel):
    """Response schema for document listing"""
    documents: List[DocumentResponse]
    pagination: PaginationResponse


class DocumentSearchResponse(BaseModel):
    """Response schema for document search"""
    search_results: List[DocumentSearchResultResponse]
    search_query: str
    pagination: PaginationResponse


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload"""
    success: bool
    document_id: Optional[int] = None
    document: Optional[DocumentResponse] = None
    error: Optional[str] = None
    existing_document_id: Optional[int] = None


class DocumentUpdateResponse(BaseModel):
    """Response schema for document update"""
    success: bool
    document: Optional[DocumentResponse] = None
    error: Optional[str] = None


class DocumentDeleteResponse(BaseModel):
    """Response schema for document deletion"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class DocumentDownloadResponse(BaseModel):
    """Response schema for document download metadata"""
    filename: str
    mime_type: str
    file_size: int


class ErrorResponse(BaseModel):
    """Response schema for errors"""
    error: str
    details: Optional[Dict[str, Any]] = None


# Validation schemas
class DocumentValidationResult(BaseModel):
    """Schema for document validation result"""
    is_valid: bool
    validation_status: ValidationStatusEnum
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    quality_score: Optional[float] = None


class DocumentProcessingResult(BaseModel):
    """Schema for document processing result"""
    processing_status: ProcessingStatusEnum
    content_preview: Optional[str] = None
    content_summary: Optional[str] = None
    extracted_metadata: Optional[Dict[str, Any]] = None
    search_keywords: Optional[List[str]] = None
    error_message: Optional[str] = None


# Batch operation schemas
class BulkDocumentUploadRequest(BaseModel):
    """Request schema for bulk document upload"""
    cycle_id: int = Field(..., description="Test cycle ID")
    report_id: int = Field(..., description="Report ID")
    phase_id: int = Field(..., description="Workflow phase ID")
    document_type: DocumentTypeEnum = Field(..., description="Type of document")
    access_level: AccessLevelEnum = Field(AccessLevelEnum.PHASE_RESTRICTED, description="Access control level")
    required_for_completion: bool = Field(False, description="Whether documents are required for phase completion")
    approval_required: bool = Field(False, description="Whether documents require approval")


class BulkDocumentDeleteRequest(BaseModel):
    """Request schema for bulk document deletion"""
    document_ids: List[int] = Field(..., min_items=1, max_items=100, description="Document IDs to delete")
    permanent: bool = Field(False, description="Whether to permanently delete (vs archive)")


class BulkOperationResponse(BaseModel):
    """Response schema for bulk operations"""
    success_count: int
    failure_count: int
    total_count: int
    successes: List[int] = []  # Document IDs that succeeded
    failures: List[Dict[str, Any]] = []  # Document IDs that failed with error messages


# Access control schemas
class DocumentAccessRequest(BaseModel):
    """Request schema for document access check"""
    document_id: int = Field(..., description="Document ID")
    user_id: int = Field(..., description="User ID")
    access_type: str = Field("read", pattern="^(read|write|delete)$", description="Type of access")


class DocumentAccessResponse(BaseModel):
    """Response schema for document access check"""
    has_access: bool
    access_level: Optional[str] = None
    reason: Optional[str] = None


# Statistics schemas
class DocumentStatisticsRequest(BaseModel):
    """Request schema for document statistics"""
    cycle_id: Optional[int] = Field(None, description="Filter by cycle ID")
    report_id: Optional[int] = Field(None, description="Filter by report ID")
    phase_id: Optional[int] = Field(None, description="Filter by phase ID")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")


class PhaseDocumentCompletionResponse(BaseModel):
    """Response schema for phase document completion status"""
    phase_id: int
    phase_name: Optional[str] = None
    required_document_types: List[str]
    uploaded_document_types: List[str]
    missing_document_types: List[str]
    completion_percentage: float
    is_complete: bool


class CycleDocumentSummaryResponse(BaseModel):
    """Response schema for cycle document summary"""
    cycle_id: int
    report_id: int
    total_documents: int
    documents_by_phase: Dict[int, int]
    completion_by_phase: Dict[int, PhaseDocumentCompletionResponse]
    overall_completion_percentage: float


# Document versioning response schemas
class DocumentVersionCreateResponse(BaseModel):
    """Response schema for document version creation"""
    success: bool
    document_id: Optional[int] = None
    document: Optional[DocumentResponse] = None
    parent_document_id: Optional[int] = None
    version: Optional[str] = None
    error: Optional[str] = None


class DocumentVersionListResponse(BaseModel):
    """Response schema for document version listing"""
    versions: List[DocumentResponse]
    total_versions: int
    latest_version: Optional[DocumentResponse] = None


class DocumentVersionRestoreResponse(BaseModel):
    """Response schema for document version restoration"""
    success: bool
    message: Optional[str] = None
    document: Optional[DocumentResponse] = None
    error: Optional[str] = None


class DocumentVersionCompareResponse(BaseModel):
    """Response schema for document version comparison"""
    version1: DocumentResponse
    version2: DocumentResponse
    differences: Dict[str, Dict[str, Any]]
    has_differences: bool


class DocumentVersionDifference(BaseModel):
    """Schema for version differences"""
    field_name: str
    version1_value: Any
    version2_value: Any
    difference_type: str  # 'modified', 'added', 'removed'