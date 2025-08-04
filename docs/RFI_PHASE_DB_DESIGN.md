# Request for Information (RFI) Phase Database Design

## Overview
The RFI phase manages test case creation, evidence collection from data owners, and test execution with tester approval.

## Current Database Schema

### Core Tables

#### 1. `cycle_report_test_cases`
Stores test cases generated from approved attributes and samples.
```sql
- id (PK)
- test_case_number 
- test_case_name
- phase_id (FK -> workflow_phases)
- sample_id: Reference to the sample being tested
- attribute_id (FK -> planning_attributes): The non-PK attribute to test
- attribute_name: Denormalized for performance
- lob_id (FK -> lobs)
- data_owner_id (FK -> users): Assigned data owner
- assigned_by (FK -> users)
- status: Not Started | In Progress | Pending Approval | Complete
- submission_deadline
- special_instructions
```

#### 2. `cycle_report_test_cases_document_submissions` 
Handles document uploads from data owners.
```sql
- submission_id (PK)
- test_case_id (FK -> cycle_report_test_cases)
- phase_id (FK -> workflow_phases)
- submission_number: Version tracking (1, 2, 3...)
- is_current: Boolean flag for latest version
- parent_submission_id: Links to previous version
- file details (path, size, hash, type)
- validation_status
- revision tracking fields
```

#### 3. `cycle_report_request_info_testcase_source_evidence`
Unified evidence storage for both documents and data sources.
```sql
- id (PK)
- test_case_id (FK -> cycle_report_test_cases)
- evidence_type: 'document' | 'data_source'
- Document fields: document_path, document_hash, etc.
- Data source fields: data_source_id, query_text, query_parameters
- validation_status
- version_number, is_current
```

#### 4. `cycle_report_request_info_tester_decisions`
Tester decisions on evidence submissions.
```sql
- id (PK)
- evidence_id (FK -> testcase_source_evidence)
- decision: approved | rejected | requires_revision
- requires_resubmission
- follow_up_instructions
```

## Identified Redundancies

### 1. **Document Storage Duplication**
- `cycle_report_test_cases_document_submissions` AND `cycle_report_request_info_testcase_source_evidence` both store document information
- This creates confusion about which table to use

### 2. **Status Tracking Overlap**
- Test case status in `cycle_report_test_cases`
- Submission status in document submissions
- Validation status in evidence table
- Multiple places tracking similar state

### 3. **Version Management Duplication**
- Both document submissions and evidence tables have version tracking
- Different approaches (submission_number vs version_number)

## Proposed Simplified Design

### Consolidate into Unified Evidence Model

#### 1. Keep `cycle_report_test_cases` (Simplified)
```sql
- id (PK)
- phase_id, sample_id, attribute_id
- data_owner_id, assigned_by
- status: Pending | Submitted | Under Review | Approved | Rejected
- current_evidence_id (FK -> unified evidence table)
```

#### 2. Create `cycle_report_rfi_evidence` (Unified)
```sql
- id (PK)
- test_case_id (FK)
- evidence_type: document | data_source
- version: 1, 2, 3...
- is_current: boolean
- parent_evidence_id: for revision tracking

-- Common fields
- submitted_by, submitted_at
- validation_status
- tester_decision
- tester_notes

-- Document specific (nullable)
- file_path, file_hash, mime_type

-- Data source specific (nullable)
- data_source_id
- query_text
- query_validated: boolean
- query_validation_results: JSONB
```

#### 3. Create `cycle_report_rfi_data_sources` (Reusable)
```sql
- id (PK)
- phase_id (FK)
- data_owner_id (FK)
- source_name
- connection_type
- connection_details (encrypted)
- is_validated
- created_by, created_at
```

#### 4. Add `cycle_report_rfi_query_validations`
```sql
- id (PK)
- evidence_id (FK)
- query_text
- validation_timestamp
- validation_status: pending | success | failed
- row_count
- sample_results: JSONB (first 10 rows)
- error_message
- validated_by (FK -> users)
```

## Benefits of Simplified Design

1. **Single source of truth** for evidence
2. **Clear versioning** with parent-child relationships
3. **Unified status tracking** at test case level
4. **Query validation** properly tracked
5. **Reusable data sources** for efficiency

## Migration Strategy

1. Create new unified tables
2. Migrate existing data
3. Update services to use new structure
4. Deprecate redundant tables