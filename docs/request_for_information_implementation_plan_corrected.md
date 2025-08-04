# Request for Information Phase - Corrected Implementation Plan

## Overview

This document outlines the correct implementation of the Request for Information (RFI) phase database architecture, focusing on collecting source evidence at the test case level.

## Understanding the Business Requirements

### What Request for Information Actually Does
- **Collects source evidence** for each test case
- **Test case level granularity** - one row per test case
- **Source evidence types**: Data source + query OR document
- **Evidence collection** from data owners for specific test cases

### Key Insight
The request for information phase is NOT about bulk assignments - it's about collecting specific evidence for individual test cases that were created from the Sample × Attribute matrix.

## Corrected Architecture

### Existing Foundation: Test Cases Table
The `cycle_report_test_cases` table already exists and contains:
```sql
-- Already exists
CREATE TABLE cycle_report_test_cases (
    test_case_id VARCHAR(255) PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    sample_id VARCHAR(255) NOT NULL,
    sample_identifier VARCHAR(255) NOT NULL,
    attribute_name VARCHAR(255) NOT NULL,
    data_owner_id INTEGER NOT NULL REFERENCES users(user_id),
    primary_key_attributes JSONB,
    status VARCHAR(50) DEFAULT 'Pending',
    submission_deadline TIMESTAMP WITH TIME ZONE,
    expected_evidence_type VARCHAR(100),
    special_instructions TEXT,
    assigned_by INTEGER REFERENCES users(user_id),
    assigned_at TIMESTAMP WITH TIME ZONE,
    submitted_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### New Table: Test Case Source Evidence
```sql
CREATE TABLE cycle_report_request_info_testcase_source_evidence (
    id SERIAL PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    test_case_id VARCHAR(255) NOT NULL REFERENCES cycle_report_test_cases(test_case_id),
    sample_id VARCHAR(255) NOT NULL,
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    
    -- Evidence type and source
    evidence_type VARCHAR(50) NOT NULL, -- 'document' or 'data_source'
    
    -- Document evidence fields
    document_name VARCHAR(255),
    document_path VARCHAR(500),
    document_size INTEGER,
    mime_type VARCHAR(100),
    document_hash VARCHAR(128),
    
    -- Data source evidence fields  
    data_source_id INTEGER REFERENCES cycle_report_planning_data_sources(id),
    query_text TEXT,
    query_parameters JSONB,
    query_result_sample JSONB, -- Sample of query results for verification
    
    -- Submission metadata
    submitted_by INTEGER NOT NULL REFERENCES users(user_id),
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    submission_notes TEXT,
    
    -- Validation and review
    validation_status VARCHAR(50) DEFAULT 'pending', -- pending, valid, invalid, requires_review
    validation_notes TEXT,
    validated_by INTEGER REFERENCES users(user_id),
    validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Version tracking (for resubmissions)
    version_number INTEGER DEFAULT 1,
    is_current BOOLEAN DEFAULT TRUE,
    replaced_by INTEGER REFERENCES cycle_report_request_info_testcase_source_evidence(id),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(test_case_id, version_number),
    
    -- Ensure either document or data source evidence is provided
    CONSTRAINT check_evidence_type CHECK (
        (evidence_type = 'document' AND document_name IS NOT NULL) OR
        (evidence_type = 'data_source' AND data_source_id IS NOT NULL AND query_text IS NOT NULL)
    )
);
```

### Supporting Tables

#### Evidence Validation Results
```sql
CREATE TABLE cycle_report_request_info_evidence_validation (
    id SERIAL PRIMARY KEY,
    evidence_id INTEGER NOT NULL REFERENCES cycle_report_request_info_testcase_source_evidence(id),
    validation_rule VARCHAR(255) NOT NULL,
    validation_result VARCHAR(50) NOT NULL, -- passed, failed, warning
    validation_message TEXT,
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    validated_by INTEGER NOT NULL REFERENCES users(user_id)
);
```

#### Tester Review and Decisions
```sql
CREATE TABLE cycle_report_request_info_tester_decisions (
    id SERIAL PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    evidence_id INTEGER NOT NULL REFERENCES cycle_report_request_info_testcase_source_evidence(id),
    test_case_id VARCHAR(255) NOT NULL REFERENCES cycle_report_test_cases(test_case_id),
    
    -- Decision details
    decision VARCHAR(50) NOT NULL, -- approved, rejected, requires_revision
    decision_notes TEXT,
    decision_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    decided_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Follow-up actions
    requires_resubmission BOOLEAN DEFAULT FALSE,
    resubmission_deadline TIMESTAMP WITH TIME ZONE,
    follow_up_instructions TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(evidence_id, decided_by)
);
```

## Business Logic Implementation

### 1. Test Case Creation (Already Exists)
- Test cases are created during phase initialization
- One test case per non-PK attribute per sample per data owner
- Stored in existing `cycle_report_test_cases` table

### 2. Evidence Collection Workflow

#### Data Owner Portal Flow:
1. **View Test Cases**: Data owner sees their assigned test cases
2. **Provide Evidence**: For each test case, submit either:
   - **Document Evidence**: Upload file(s) with evidence
   - **Data Source Evidence**: Provide query and data source reference
3. **Validation**: System validates evidence completeness and format
4. **Resubmission**: If rejected, data owner can resubmit with new version

#### Tester Review Flow:
1. **Review Evidence**: Tester examines submitted evidence per test case
2. **Validation**: Verify evidence meets requirements
3. **Decision**: Approve, reject, or request revision for each test case
4. **Phase Completion**: All test cases must be approved to complete phase

### 3. Evidence Types

#### Document Evidence
- **Purpose**: Traditional document uploads (PDFs, spreadsheets, etc.)
- **Storage**: Files stored on disk, metadata in database
- **Validation**: File type, size, readability checks
- **Use Cases**: Compliance documents, reports, certificates

#### Data Source Evidence  
- **Purpose**: Query-based evidence from data sources
- **Storage**: Query text and sample results in database
- **Validation**: Query syntax, data source connectivity, result samples
- **Use Cases**: Database queries, API calls, data extracts

### 4. Validation Framework

#### Automatic Validation
- **File Validation**: Check file integrity, format, size
- **Query Validation**: Verify query syntax and connectivity
- **Completeness**: Ensure required fields are populated

#### Manual Review
- **Tester Review**: Business logic validation of evidence
- **Approval Workflow**: Formal approval/rejection process
- **Revision Requests**: Structured feedback for resubmission

## Data Relationships

### Primary Relationships
```
cycle_report_test_cases (1) ←→ (1..n) cycle_report_request_info_testcase_source_evidence
workflow_phases (1) ←→ (n) cycle_report_request_info_testcase_source_evidence
users (1) ←→ (n) cycle_report_request_info_testcase_source_evidence [submitted_by]
cycle_report_planning_data_sources (1) ←→ (n) cycle_report_request_info_testcase_source_evidence
```

### Supporting Relationships
```
cycle_report_request_info_testcase_source_evidence (1) ←→ (n) cycle_report_request_info_evidence_validation
cycle_report_request_info_testcase_source_evidence (1) ←→ (n) cycle_report_request_info_tester_decisions
```

## API Endpoints Design

### Data Owner Portal
```
GET /api/v1/request-info/{cycle_id}/reports/{report_id}/my-test-cases
- Returns test cases assigned to current data owner

POST /api/v1/request-info/test-cases/{test_case_id}/evidence
- Submit evidence for a specific test case
- Body: { evidence_type, document_file?, data_source_id?, query_text?, notes }

GET /api/v1/request-info/test-cases/{test_case_id}/evidence
- Get current evidence for a test case

PUT /api/v1/request-info/test-cases/{test_case_id}/evidence/{evidence_id}
- Update/resubmit evidence for a test case
```

### Tester Review Interface
```
GET /api/v1/request-info/{cycle_id}/reports/{report_id}/evidence/pending-review
- Get all evidence pending tester review

POST /api/v1/request-info/evidence/{evidence_id}/review
- Submit tester decision for evidence
- Body: { decision, notes, requires_resubmission?, resubmission_deadline? }

GET /api/v1/request-info/{cycle_id}/reports/{report_id}/progress
- Get phase progress and completion status
```

### Evidence Management
```
GET /api/v1/request-info/evidence/{evidence_id}/download
- Download document evidence file

POST /api/v1/request-info/evidence/{evidence_id}/validate
- Trigger validation for evidence

GET /api/v1/request-info/evidence/{evidence_id}/validation-results
- Get validation results for evidence
```

## Migration Strategy

### Phase 1: Create New Tables
```sql
-- Create the new evidence table
CREATE TABLE cycle_report_request_info_testcase_source_evidence (...);

-- Create supporting tables
CREATE TABLE cycle_report_request_info_evidence_validation (...);
CREATE TABLE cycle_report_request_info_tester_decisions (...);

-- Create indexes
CREATE INDEX idx_evidence_test_case ON cycle_report_request_info_testcase_source_evidence(test_case_id);
CREATE INDEX idx_evidence_phase ON cycle_report_request_info_testcase_source_evidence(phase_id);
CREATE INDEX idx_evidence_current ON cycle_report_request_info_testcase_source_evidence(test_case_id, is_current);
```

### Phase 2: Migrate Existing Data
```sql
-- Migrate existing document submissions to new evidence table
INSERT INTO cycle_report_request_info_testcase_source_evidence (
    phase_id, cycle_id, report_id, test_case_id, sample_id, attribute_id,
    evidence_type, document_name, document_path, document_size, mime_type,
    submitted_by, submitted_at, submission_notes, validation_status,
    created_by, updated_by
)
SELECT 
    ds.phase_id, ds.cycle_id, ds.report_id, ds.test_case_id, 
    tc.sample_id, tc.attribute_id,
    'document', ds.document_name, ds.file_path, ds.file_size, ds.mime_type,
    ds.submitted_by, ds.submitted_at, ds.comments, ds.validation_status,
    ds.created_by, ds.updated_by
FROM document_submissions ds
JOIN cycle_report_test_cases tc ON ds.test_case_id = tc.test_case_id;
```

### Phase 3: Update Application Code
1. **Update Models**: Create new SQLAlchemy models for evidence tables
2. **Update Services**: Implement evidence collection and validation logic
3. **Update APIs**: Create new endpoints for evidence management
4. **Update UI**: Modify data owner portal and tester interface

### Phase 4: Testing and Deployment
1. **Integration Testing**: Test evidence collection workflows
2. **Performance Testing**: Verify query performance with evidence data
3. **User Testing**: Validate data owner and tester interfaces
4. **Production Deployment**: Deploy with rollback capability

## Key Benefits

### 1. Granular Evidence Tracking
- **Test Case Level**: Evidence collected for each specific test case
- **Multiple Evidence Types**: Support both document and data source evidence
- **Version Control**: Track evidence revisions and updates

### 2. Flexible Evidence Types
- **Document Evidence**: Traditional file uploads for compliance
- **Data Source Evidence**: Query-based evidence for data validation
- **Extensible**: Easy to add new evidence types in the future

### 3. Robust Validation
- **Automatic Validation**: File integrity and query syntax checks
- **Manual Review**: Tester approval workflow for business validation
- **Audit Trail**: Complete history of evidence submissions and decisions

### 4. Improved User Experience
- **Data Owner Portal**: Clear view of evidence requirements per test case
- **Tester Interface**: Efficient review and approval workflow
- **Progress Tracking**: Real-time visibility into evidence collection progress

## Conclusion

The corrected implementation focuses on the actual business requirement: collecting source evidence at the test case level. This approach:

1. **Respects existing structure** - Works with the existing test cases table
2. **Provides granular tracking** - One row per test case evidence
3. **Supports multiple evidence types** - Documents and data source queries
4. **Enables validation workflows** - Automatic and manual validation
5. **Maintains audit trail** - Complete history of evidence collection

This design correctly implements the request for information phase as an evidence collection system rather than a bulk assignment system.