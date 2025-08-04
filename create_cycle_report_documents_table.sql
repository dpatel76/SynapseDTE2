-- Create cycle report document management table
-- Generic document management system for all testing phases

-- Drop table if exists (for clean creation)
DROP TABLE IF EXISTS cycle_report_documents CASCADE;

-- Create cycle report documents table
CREATE TABLE cycle_report_documents (
    id SERIAL PRIMARY KEY,
    
    -- Context references
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Document classification
    document_type VARCHAR(100) NOT NULL CHECK (document_type IN (
        'report_sample_data',
        'report_underlying_transaction_data', 
        'report_source_transaction_data',
        'report_source_document'
    )),
    document_category VARCHAR(50) DEFAULT 'general', -- For further subcategorization
    
    -- File information
    original_filename VARCHAR(500) NOT NULL,
    stored_filename VARCHAR(500) NOT NULL, -- UUID-based filename for storage
    file_path VARCHAR(1000) NOT NULL, -- Full path to stored file
    file_size BIGINT NOT NULL, -- Size in bytes
    file_format VARCHAR(20) NOT NULL CHECK (file_format IN (
        'csv', 'pipe', 'excel', 'xlsx', 'xls', 'word', 'docx', 'pdf', 'jpeg', 'jpg', 'png'
    )),
    mime_type VARCHAR(100) NOT NULL,
    file_hash VARCHAR(64), -- SHA-256 hash for integrity verification
    
    -- Document metadata
    document_title VARCHAR(500) NOT NULL,
    document_description TEXT,
    document_version VARCHAR(20) DEFAULT '1.0',
    is_latest_version BOOLEAN DEFAULT TRUE,
    parent_document_id INTEGER REFERENCES cycle_report_documents(id), -- For versioning
    
    -- Access control and security
    access_level VARCHAR(50) DEFAULT 'phase_restricted' CHECK (access_level IN (
        'public', 'phase_restricted', 'role_restricted', 'user_restricted'
    )),
    allowed_roles JSONB, -- Array of role names that can access this document
    allowed_users JSONB, -- Array of user IDs that can access this document
    
    -- Processing status
    upload_status VARCHAR(50) DEFAULT 'pending' CHECK (upload_status IN (
        'pending', 'uploading', 'uploaded', 'processing', 'processed', 'failed', 'quarantined'
    )),
    processing_status VARCHAR(50) DEFAULT 'not_processed' CHECK (processing_status IN (
        'not_processed', 'processing', 'processed', 'failed', 'skipped'
    )),
    validation_status VARCHAR(50) DEFAULT 'not_validated' CHECK (validation_status IN (
        'not_validated', 'validating', 'valid', 'invalid', 'warning'
    )),
    
    -- Document content analysis (for searchable content)
    content_preview TEXT, -- First few lines or extracted text preview
    content_summary TEXT, -- AI-generated summary if applicable
    extracted_metadata JSONB, -- Metadata extracted from file (headers, properties, etc.)
    search_keywords TEXT[], -- Keywords for search functionality
    
    -- Validation and quality checks
    validation_errors JSONB, -- Array of validation error messages
    validation_warnings JSONB, -- Array of validation warnings
    quality_score FLOAT CHECK (quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0)),
    
    -- Usage tracking
    download_count INTEGER DEFAULT 0,
    last_downloaded_at TIMESTAMP WITH TIME ZONE,
    last_downloaded_by INTEGER REFERENCES users(user_id),
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP WITH TIME ZONE,
    last_viewed_by INTEGER REFERENCES users(user_id),
    
    -- Workflow integration
    workflow_stage VARCHAR(100), -- What stage of workflow this document supports
    required_for_completion BOOLEAN DEFAULT FALSE, -- Whether this document is required for phase completion
    approval_required BOOLEAN DEFAULT FALSE, -- Whether document needs approval
    approved_by INTEGER REFERENCES users(user_id),
    approved_at TIMESTAMP WITH TIME ZONE,
    approval_notes TEXT,
    
    -- Retention and lifecycle
    retention_period_days INTEGER, -- How long to keep this document
    archive_date DATE, -- When to archive
    delete_date DATE, -- When to delete
    is_archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP WITH TIME ZONE,
    archived_by INTEGER REFERENCES users(user_id),
    
    -- Audit fields
    uploaded_by INTEGER NOT NULL REFERENCES users(user_id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(stored_filename), -- Ensure unique storage filenames
    UNIQUE(cycle_id, report_id, phase_id, original_filename, document_version) -- Prevent duplicate uploads
);

-- Create indexes for performance
CREATE INDEX idx_cycle_report_documents_cycle_id ON cycle_report_documents(cycle_id);
CREATE INDEX idx_cycle_report_documents_report_id ON cycle_report_documents(report_id);
CREATE INDEX idx_cycle_report_documents_phase_id ON cycle_report_documents(phase_id);
CREATE INDEX idx_cycle_report_documents_document_type ON cycle_report_documents(document_type);
CREATE INDEX idx_cycle_report_documents_file_format ON cycle_report_documents(file_format);
CREATE INDEX idx_cycle_report_documents_upload_status ON cycle_report_documents(upload_status);
CREATE INDEX idx_cycle_report_documents_processing_status ON cycle_report_documents(processing_status);
CREATE INDEX idx_cycle_report_documents_validation_status ON cycle_report_documents(validation_status);
CREATE INDEX idx_cycle_report_documents_uploaded_by ON cycle_report_documents(uploaded_by);
CREATE INDEX idx_cycle_report_documents_uploaded_at ON cycle_report_documents(uploaded_at);
CREATE INDEX idx_cycle_report_documents_is_latest_version ON cycle_report_documents(is_latest_version);
CREATE INDEX idx_cycle_report_documents_access_level ON cycle_report_documents(access_level);
CREATE INDEX idx_cycle_report_documents_required_for_completion ON cycle_report_documents(required_for_completion);
CREATE INDEX idx_cycle_report_documents_file_hash ON cycle_report_documents(file_hash);

-- GIN indexes for JSONB fields
CREATE INDEX idx_cycle_report_documents_allowed_roles_gin ON cycle_report_documents USING GIN (allowed_roles);
CREATE INDEX idx_cycle_report_documents_allowed_users_gin ON cycle_report_documents USING GIN (allowed_users);
CREATE INDEX idx_cycle_report_documents_extracted_metadata_gin ON cycle_report_documents USING GIN (extracted_metadata);
CREATE INDEX idx_cycle_report_documents_validation_errors_gin ON cycle_report_documents USING GIN (validation_errors);

-- GIN index for search keywords array
CREATE INDEX idx_cycle_report_documents_search_keywords_gin ON cycle_report_documents USING GIN (search_keywords);

-- Full text search index for searchable content
CREATE INDEX idx_cycle_report_documents_content_search ON cycle_report_documents USING GIN (
    to_tsvector('english', 
        COALESCE(document_title, '') || ' ' || 
        COALESCE(document_description, '') || ' ' || 
        COALESCE(content_preview, '') || ' ' ||
        COALESCE(content_summary, '')
    )
);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_cycle_report_documents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
CREATE TRIGGER trg_cycle_report_documents_updated_at
    BEFORE UPDATE ON cycle_report_documents
    FOR EACH ROW EXECUTE FUNCTION update_cycle_report_documents_updated_at();

-- Create function to handle document versioning
CREATE OR REPLACE FUNCTION handle_document_versioning()
RETURNS TRIGGER AS $$
BEGIN
    -- If this is a new version of an existing document, mark others as not latest
    IF NEW.parent_document_id IS NOT NULL AND NEW.is_latest_version = TRUE THEN
        UPDATE cycle_report_documents 
        SET is_latest_version = FALSE 
        WHERE parent_document_id = NEW.parent_document_id 
        AND id != NEW.id;
    END IF;
    
    -- If no parent but same filename exists, this is a new version
    IF NEW.parent_document_id IS NULL AND NEW.is_latest_version = TRUE THEN
        UPDATE cycle_report_documents 
        SET is_latest_version = FALSE 
        WHERE cycle_id = NEW.cycle_id 
        AND report_id = NEW.report_id 
        AND phase_id = NEW.phase_id 
        AND original_filename = NEW.original_filename 
        AND id != NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for document versioning
CREATE TRIGGER trg_handle_document_versioning
    BEFORE INSERT OR UPDATE ON cycle_report_documents
    FOR EACH ROW EXECUTE FUNCTION handle_document_versioning();

-- Create function to update download/view counts
CREATE OR REPLACE FUNCTION update_document_access_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- This will be called from application code when tracking access
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add table comments
COMMENT ON TABLE cycle_report_documents IS 'Generic document management system for cycle report testing phases';

-- Add column comments
COMMENT ON COLUMN cycle_report_documents.document_type IS 'Type of document: report_sample_data, report_underlying_transaction_data, report_source_transaction_data, report_source_document';
COMMENT ON COLUMN cycle_report_documents.file_format IS 'Supported formats: csv, pipe, excel, xlsx, xls, word, docx, pdf, jpeg, jpg, png';
COMMENT ON COLUMN cycle_report_documents.access_level IS 'Access control level: public, phase_restricted, role_restricted, user_restricted';
COMMENT ON COLUMN cycle_report_documents.upload_status IS 'Upload progress: pending, uploading, uploaded, processing, processed, failed, quarantined';
COMMENT ON COLUMN cycle_report_documents.processing_status IS 'Document processing status for content extraction and analysis';
COMMENT ON COLUMN cycle_report_documents.validation_status IS 'Document validation status for format and content validation';
COMMENT ON COLUMN cycle_report_documents.file_hash IS 'SHA-256 hash for file integrity verification and duplicate detection';
COMMENT ON COLUMN cycle_report_documents.extracted_metadata IS 'Metadata extracted from the document (headers, properties, etc.)';
COMMENT ON COLUMN cycle_report_documents.search_keywords IS 'Keywords extracted for search functionality';
COMMENT ON COLUMN cycle_report_documents.quality_score IS 'Quality score from 0.0 to 1.0 based on validation and analysis';
COMMENT ON COLUMN cycle_report_documents.required_for_completion IS 'Whether this document is required for phase completion';
COMMENT ON COLUMN cycle_report_documents.is_latest_version IS 'Whether this is the latest version of the document';
COMMENT ON COLUMN cycle_report_documents.parent_document_id IS 'Reference to previous version for document versioning';

-- Create view for latest documents only
CREATE VIEW cycle_report_documents_latest AS
SELECT * FROM cycle_report_documents 
WHERE is_latest_version = TRUE 
AND is_archived = FALSE;

COMMENT ON VIEW cycle_report_documents_latest IS 'View showing only the latest versions of non-archived documents';

-- Create view for required documents by phase
CREATE VIEW cycle_report_required_documents AS
SELECT 
    cycle_id,
    report_id,
    phase_id,
    document_type,
    COUNT(*) as document_count,
    COUNT(CASE WHEN upload_status = 'uploaded' OR upload_status = 'processed' THEN 1 END) as uploaded_count,
    COUNT(CASE WHEN validation_status = 'valid' THEN 1 END) as valid_count,
    CASE 
        WHEN COUNT(*) = COUNT(CASE WHEN upload_status = 'uploaded' OR upload_status = 'processed' THEN 1 END) 
        THEN 'complete'
        ELSE 'incomplete'
    END as completion_status
FROM cycle_report_documents 
WHERE required_for_completion = TRUE 
AND is_latest_version = TRUE 
AND is_archived = FALSE
GROUP BY cycle_id, report_id, phase_id, document_type;

COMMENT ON VIEW cycle_report_required_documents IS 'View showing completion status of required documents by phase and type';