# Summary of Changes - Evidence Architecture Refactoring

## Overview
Successfully refactored the evidence tracking system to use a unified table structure, combining document and data source evidence into a single `cycle_report_test_cases_evidence` table.

## Database Changes

### 1. Table Renamed
- **From**: `cycle_report_rfi_evidence`
- **To**: `cycle_report_test_cases_evidence`

### 2. New Columns Added
- `submission_number` (INTEGER, default 1)
- `is_revision` (BOOLEAN, default false)
- `revision_requested_by` (INTEGER, FK to users)
- `revision_requested_at` (TIMESTAMP)
- `revision_reason` (TEXT)
- `revision_deadline` (TIMESTAMP)
- `original_filename` (VARCHAR(255))
- `stored_filename` (VARCHAR(255))
- `file_path` (VARCHAR(500))
- `file_size_bytes` (INTEGER)
- `file_hash` (VARCHAR(64))
- `mime_type` (VARCHAR(100))
- `document_type` (document_type_enum)
- `tester_decision` (VARCHAR(50))
- `tester_notes` (TEXT)
- `decided_by` (INTEGER, FK to users)
- `decided_at` (TIMESTAMP)
- `requires_resubmission` (BOOLEAN, default false)
- `resubmission_deadline` (TIMESTAMP)

### 3. Table Removed
- `cycle_report_test_cases_document_submissions` - No longer needed, all functionality merged into evidence table

## Model Changes

### 1. TestCaseEvidence Model
- Renamed from `RFIEvidenceLegacy` to `TestCaseEvidence`
- Added backward compatibility alias: `RFIEvidenceLegacy = TestCaseEvidence`
- Enhanced with document submission fields
- Located in: `/app/models/request_info.py`

### 2. Removed Model
- `TestCaseDocumentSubmission` - Functionality merged into `TestCaseEvidence`

## API Changes

### New Endpoints Added

1. **Get Test Case Evidence** (for testers and data owners)
   - `GET /api/v1/request-info/test-cases/{test_case_id}/evidence`
   - Returns all evidence (documents and data sources) for a test case
   - Includes submission details, validation status, and tester decisions
   - Shows `can_resend` flag for testers

2. **Get Test Case Evidence Details** (identical view for testers as data owners)
   - `GET /api/v1/request-info/test-cases/{test_case_id}/evidence-details`
   - Returns the same detailed structure that data owners see
   - Includes:
     - Complete test case information with data owner details
     - Current evidence with validation results
     - Tester decisions history
     - Available data sources for the report
     - Permission flags: `can_submit_evidence`, `can_resubmit`, `can_review`, `can_resend`
   - Shows revision status and requirements

3. **Download Evidence File**
   - `GET /api/v1/request-info/evidence/{evidence_id}/download`
   - Downloads document evidence files
   - Returns 404 if evidence is not a document type

### Updated Endpoints

1. **Resend Test Case** (Enhanced for both document and data source evidence)
   - `POST /api/v1/request-info/test-cases/{test_case_id}/resend`
   - Fixed to use correct use case class: `ResendCycleReportTestCaseUseCase`
   - Enhanced request body:
     ```json
     {
       "reason": "Required field - reason for resend",
       "additional_instructions": "Optional additional instructions",
       "new_deadline": "2025-02-01T00:00:00",
       "evidence_type": "document",  // or "data_source" or null for all
       "invalidate_previous": true   // Whether to mark previous evidence as requiring revision
     }
     ```
   - Features:
     - Can target specific evidence type (document OR data_source)
     - Updates test case status to "In Progress"
     - Marks targeted evidence as requiring revision
     - Sets tester decision to 'requires_revision'
     - Tracks who requested the revision and when
     - Supports setting new submission deadline

2. **Get Test Case Submissions**
   - `GET /api/v1/request-info/test-cases/{test_case_id}/submissions`
   - Updated to query from `TestCaseEvidence` table

## Service Changes

### Updated Use Cases
1. `SubmitDocumentUseCase` - Now saves to unified `TestCaseEvidence` table
2. `ResendCycleReportTestCaseUseCase` - Fixed to handle integer test case IDs correctly
3. Evidence counting queries updated to use new table structure

## Key Benefits

1. **Simplified Architecture**: Single table for all evidence types reduces complexity
2. **Better Tracking**: Submission numbers, revisions, and tester decisions all in one place
3. **Unified Queries**: No need to join multiple tables to get complete evidence information
4. **Backward Compatibility**: Model alias ensures existing code continues to work

## Frontend Requirements

The frontend needs to be updated to:
1. Use the new `/api/v1/request-info/test-cases/{id}/evidence` endpoint for testers
2. Display evidence with download links for documents
3. Show tester decision status and notes
4. Enable resend functionality based on `can_resend` flag
5. Update any references from `submission_id` to `id` (evidence ID)

## Testing

Created test script at `/test_evidence_endpoint.py` that verifies:
- Test cases with evidence are properly stored
- Evidence types (document vs data_source) are correctly tracked
- Validation status and tester decisions are preserved

## Migration Status
✅ Database migration executed successfully
✅ Backend APIs updated and tested
✅ Model refactoring complete
⏳ Frontend updates pending