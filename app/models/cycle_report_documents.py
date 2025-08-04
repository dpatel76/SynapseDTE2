"""
Cycle Report Document Management Models
Generic document management system for all testing phases
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, BigInteger, Float, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin
from enum import Enum


# Enums for document management
class DocumentType(str, Enum):
    REPORT_SAMPLE_DATA = "report_sample_data"
    REPORT_UNDERLYING_TRANSACTION_DATA = "report_underlying_transaction_data"
    REPORT_SOURCE_TRANSACTION_DATA = "report_source_transaction_data"
    REPORT_SOURCE_DOCUMENT = "report_source_document"


class FileFormat(str, Enum):
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


class AccessLevel(str, Enum):
    PUBLIC = "public"
    PHASE_RESTRICTED = "phase_restricted"
    ROLE_RESTRICTED = "role_restricted"
    USER_RESTRICTED = "user_restricted"


class UploadStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    QUARANTINED = "quarantined"


class ProcessingStatus(str, Enum):
    NOT_PROCESSED = "not_processed"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ValidationStatus(str, Enum):
    NOT_VALIDATED = "not_validated"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


class CycleReportDocument(CustomPKModel):
    """
    Generic document management for cycle report testing phases
    Supports versioning, access control, validation, and full-text search
    """
    
    __tablename__ = "cycle_report_documents"
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Primary context reference - use phase_id for all relationships
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    test_case_id = Column(String(255), nullable=True)  # Optional test case ID for granular document tracking
    
    # Document classification
    document_type = Column(String(100), nullable=False)
    document_category = Column(String(50), default='general', nullable=True)
    
    # File information
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)  # UUID-based filename for storage
    file_path = Column(String(1000), nullable=False)  # Full path to stored file
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    file_format = Column(String(20), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash for integrity verification
    
    # Advanced security features (from legacy documents)
    is_encrypted = Column(Boolean, default=False, nullable=False)
    encryption_key_id = Column(String(100), nullable=True)
    is_confidential = Column(Boolean, default=False, nullable=False)
    
    # Enhanced metadata
    document_tags = Column(JSONB, nullable=True)
    business_date = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Integrity verification
    last_integrity_check = Column(DateTime, nullable=True)
    integrity_verified = Column(Boolean, default=True, nullable=False)
    
    # Enhanced access tracking
    last_access_session_id = Column(String(100), nullable=True)
    last_access_ip = Column(String(45), nullable=True)
    last_access_user_agent = Column(Text, nullable=True)
    
    # Document metadata
    document_title = Column(String(500), nullable=False)
    document_description = Column(Text, nullable=True)
    document_version = Column(String(20), default='1.0', nullable=False)
    is_latest_version = Column(Boolean, default=True, nullable=False)
    parent_document_id = Column(Integer, ForeignKey('cycle_report_documents.id'), nullable=True)
    
    # Access control and security
    access_level = Column(String(50), default='phase_restricted', nullable=False)
    allowed_roles = Column(JSONB, nullable=True)  # Array of role names that can access this document
    allowed_users = Column(JSONB, nullable=True)  # Array of user IDs that can access this document
    
    # Processing status
    upload_status = Column(String(50), default='pending', nullable=False)
    processing_status = Column(String(50), default='not_processed', nullable=False)
    validation_status = Column(String(50), default='not_validated', nullable=False)
    
    # Document content analysis (for searchable content)
    content_preview = Column(Text, nullable=True)  # First few lines or extracted text preview
    content_summary = Column(Text, nullable=True)  # AI-generated summary if applicable
    extracted_metadata = Column(JSONB, nullable=True)  # Metadata extracted from file (headers, properties, etc.)
    search_keywords = Column(JSONB, nullable=True)  # Keywords for search functionality (stored as array)
    
    # Validation and quality checks
    validation_errors = Column(JSONB, nullable=True)  # Array of validation error messages
    validation_warnings = Column(JSONB, nullable=True)  # Array of validation warnings
    quality_score = Column(Float, nullable=True)  # Quality score from 0.0 to 1.0
    
    # Usage tracking
    download_count = Column(Integer, default=0, nullable=False)
    last_downloaded_at = Column(DateTime(timezone=True), nullable=True)
    last_downloaded_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    view_count = Column(Integer, default=0, nullable=False)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    last_viewed_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    # Workflow integration
    workflow_stage = Column(String(100), nullable=True)  # What stage of workflow this document supports
    required_for_completion = Column(Boolean, default=False, nullable=False)  # Whether this document is required for phase completion
    approval_required = Column(Boolean, default=False, nullable=False)  # Whether document needs approval
    approved_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Retention and lifecycle
    retention_period_days = Column(Integer, nullable=True)  # How long to keep this document
    archive_date = Column(DateTime(timezone=True).with_variant(DateTime(timezone=False), 'sqlite'), nullable=True)  # When to archive
    delete_date = Column(DateTime(timezone=True).with_variant(DateTime(timezone=False), 'sqlite'), nullable=True)  # When to delete
    is_archived = Column(Boolean, default=False, nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archived_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    # Audit fields
    uploaded_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    workflow_phase = relationship("WorkflowPhase", foreign_keys=[phase_id])
    parent_document = relationship("CycleReportDocument", remote_side=[id])
    
    # Hybrid properties to access cycle_id and report_id through phase relationship
    @hybrid_property
    def cycle_id(self):
        """Get cycle_id from phase relationship for UI compatibility"""
        return self.workflow_phase.cycle_id if self.workflow_phase else None
    
    @hybrid_property
    def report_id(self):
        """Get report_id from phase relationship for UI compatibility"""
        return self.workflow_phase.report_id if self.workflow_phase else None
    
    @hybrid_property
    def test_cycle(self):
        """Get test cycle through phase relationship"""
        return self.workflow_phase.cycle if self.workflow_phase else None
    
    @hybrid_property
    def report(self):
        """Get report through phase relationship"""
        return self.workflow_phase.report if self.workflow_phase else None
    
    # User relationships
    uploader = relationship("User", foreign_keys=[uploaded_by])
    last_downloader = relationship("User", foreign_keys=[last_downloaded_by])
    last_viewer = relationship("User", foreign_keys=[last_viewed_by])
    approver = relationship("User", foreign_keys=[approved_by])
    archiver = relationship("User", foreign_keys=[archived_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Enhanced relationships to new tables
    access_logs = relationship("CycleReportDocumentAccessLog", back_populates="document", cascade="all, delete-orphan")
    extractions = relationship("CycleReportDocumentExtraction", back_populates="document", cascade="all, delete-orphan")
    revisions = relationship("CycleReportDocumentRevision", foreign_keys="CycleReportDocumentRevision.document_id", back_populates="document", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('report_sample_data', 'report_underlying_transaction_data', 'report_source_transaction_data', 'report_source_document')",
            name='ck_cycle_report_document_type'
        ),
        CheckConstraint(
            "file_format IN ('csv', 'pipe', 'excel', 'xlsx', 'xls', 'word', 'docx', 'pdf', 'jpeg', 'jpg', 'png')",
            name='ck_cycle_report_document_file_format'
        ),
        CheckConstraint(
            "access_level IN ('public', 'phase_restricted', 'role_restricted', 'user_restricted')",
            name='ck_cycle_report_document_access_level'
        ),
        CheckConstraint(
            "upload_status IN ('pending', 'uploading', 'uploaded', 'processing', 'processed', 'failed', 'quarantined')",
            name='ck_cycle_report_document_upload_status'
        ),
        CheckConstraint(
            "processing_status IN ('not_processed', 'processing', 'processed', 'failed', 'skipped')",
            name='ck_cycle_report_document_processing_status'
        ),
        CheckConstraint(
            "validation_status IN ('not_validated', 'validating', 'valid', 'invalid', 'warning')",
            name='ck_cycle_report_document_validation_status'
        ),
        CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0)",
            name='ck_cycle_report_document_quality_score'
        ),
        UniqueConstraint(
            'stored_filename',
            name='uq_cycle_report_document_stored_filename'
        ),
        UniqueConstraint(
            'phase_id', 'test_case_id', 'original_filename', 'document_version',
            name='uq_cycle_report_document_phase_testcase_filename_version'
        ),
    )
    
    def __repr__(self):
        return f"<CycleReportDocument(id={self.id}, document_title='{self.document_title}', document_type='{self.document_type}', file_format='{self.file_format}', upload_status='{self.upload_status}')>"


# Helper classes for type hints and validation
class DocumentSummary:
    """Summary data for documents"""
    def __init__(self, document: CycleReportDocument):
        self.id = document.id
        self.document_title = document.document_title
        self.document_type = document.document_type
        self.file_format = document.file_format
        self.file_size = document.file_size
        self.upload_status = document.upload_status
        self.validation_status = document.validation_status
        self.uploaded_at = document.uploaded_at
        self.is_latest_version = document.is_latest_version


class DocumentMetrics:
    """Document metrics and statistics"""
    def __init__(self, total_documents: int = 0, total_size: int = 0, 
                 by_type: dict = None, by_status: dict = None, by_format: dict = None):
        self.total_documents = total_documents
        self.total_size = total_size
        self.by_type = by_type or {}
        self.by_status = by_status or {}
        self.by_format = by_format or {}


class DocumentSearchResult:
    """Document search result with relevance scoring"""
    def __init__(self, document: CycleReportDocument, relevance_score: float = 0.0):
        self.document = document
        self.relevance_score = relevance_score
        self.matched_fields = []  # Fields that matched the search query


class DocumentVersionInfo:
    """Document version information"""
    def __init__(self, current_version: str, total_versions: int, 
                 has_newer_version: bool = False, parent_id: int = None):
        self.current_version = current_version
        self.total_versions = total_versions
        self.has_newer_version = has_newer_version
        self.parent_id = parent_id


class CycleReportDocumentAccessLog(CustomPKModel):
    """Document access logging for audit trails"""
    
    __tablename__ = "cycle_report_document_access_logs"
    
    log_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('cycle_report_documents.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    access_type = Column(String(20), nullable=False)  # view, download, edit, delete
    accessed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Relationships
    document = relationship("CycleReportDocument", back_populates="access_logs")
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<CycleReportDocumentAccessLog(id={self.log_id}, document_id={self.document_id}, access_type='{self.access_type}')>"


class CycleReportDocumentExtraction(CustomPKModel):
    """AI-powered document data extraction results"""
    
    __tablename__ = "cycle_report_document_extractions"
    
    extraction_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('cycle_report_documents.id'), nullable=False)
    attribute_name = Column(String(255), nullable=False)
    extracted_value = Column(Text, nullable=True)
    confidence_score = Column(Integer, nullable=True)  # 0-100
    extraction_method = Column(String(50), nullable=True)  # direct_match, pattern_recognition, contextual_inference
    source_location = Column(Text, nullable=True)  # Where in document the value was found
    supporting_context = Column(Text, nullable=True)  # Surrounding text
    data_quality_flags = Column(JSONB, nullable=True)  # Array of quality concerns
    alternative_values = Column(JSONB, nullable=True)  # Other possible values if ambiguous
    is_validated = Column(Boolean, default=False, nullable=False)
    validated_by_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    validation_notes = Column(Text, nullable=True)
    extracted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    llm_provider = Column(String(50), nullable=True)  # claude, gemini, gpt
    llm_model = Column(String(100), nullable=True)  # Model version used
    processing_time_ms = Column(Integer, nullable=True)  # Processing time in milliseconds
    
    # Relationships
    document = relationship("CycleReportDocument", back_populates="extractions")
    validated_by_user = relationship("User", foreign_keys=[validated_by_user_id])
    
    def __repr__(self):
        return f"<CycleReportDocumentExtraction(id={self.extraction_id}, document_id={self.document_id}, attribute='{self.attribute_name}')>"


class CycleReportDocumentRevision(CustomPKModel):
    """Document revision tracking and management"""
    
    __tablename__ = "cycle_report_document_revisions"
    
    revision_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('cycle_report_documents.id'), nullable=False)
    test_case_id = Column(String(255), nullable=True)
    revision_number = Column(Integer, nullable=False)
    revision_reason = Column(Text, nullable=False)
    requested_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=True)
    uploaded_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    upload_notes = Column(Text, nullable=True)
    previous_document_id = Column(Integer, ForeignKey('cycle_report_documents.id'), nullable=True)
    status = Column(String(50), nullable=True)
    reviewed_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Relationships
    document = relationship("CycleReportDocument", back_populates="revisions", foreign_keys=[document_id])
    previous_document = relationship("CycleReportDocument", foreign_keys=[previous_document_id])
    requested_by_user = relationship("User", foreign_keys=[requested_by])
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<CycleReportDocumentRevision(id={self.revision_id}, document_id={self.document_id}, revision_number={self.revision_number})>"