# Evidence Issue Summary - Cycle 58, Report 156

## Issues Found and Fixed

### 1. ✅ FIXED: Evidence Not Showing in Tester View
**Root Cause**: The `evidence_collection_service.py` was querying the wrong table
- Was querying: `cycle_report_request_info_testcase_source_evidence` (empty table)
- Should query: `cycle_report_test_cases_evidence` (contains 7 evidence records)

**Fix Applied**: Updated service to use `TestCaseEvidence` model instead of `TestCaseSourceEvidence`

### 2. ✅ FIXED: Document Evidence API Error
**Root Cause**: The API endpoint was trying to access `.value` on document_type which was already a string
- Error: "'str' object has no attribute 'value'"

**Fix Applied**: Added proper handling in `request_info.py` to check if document_type is an enum or string

### 3. ✅ IDENTIFIED: Status Inconsistency Issue
**Root Cause**: The TestCasesTable component shows "Submitted" for any test case with submission_count > 0
- Actual statuses: 434 (In Progress), 435 (Submitted), 436 (In Progress), 437 (Complete)
- UI shows: All 4 as "Submitted" because they all have evidence

**Fix Needed**: Update TestCasesTable to show actual status from backend

### 4. 🔍 INVESTIGATED: Data Owner Reupload Issue
**Finding**: The upload button is always shown, but the real issue is:
- Test cases 434 & 436 have `tester_decision: requires_revision` 
- They should allow reupload but might be blocked by incorrect status display

## Test Results

### API Testing Results
All 4 test cases now return evidence correctly:
- Test Case 434: Data source evidence (4 versions, current is v4, requires revision)
- Test Case 435: Data source evidence (1 version, pending review)
- Test Case 436: Document evidence (1 version, requires revision) 
- Test Case 437: Document evidence (1 version, pending review)

### Database Analysis
```
Test Case Status Analysis:
ID  | TC Status | Evidence? | Evidence Status | Tester Decision
434 | In Progress | Yes | pending | requires_revision
435 | Submitted | Yes | pending | None
436 | In Progress | Yes | pending | requires_revision  
437 | Complete | Yes | pending | None
```

## Remaining Tasks

1. **Fix TestCasesTable Component**: Update to show actual status instead of determining from submission_count
2. **Fix Data Owner Evidence Icon**: Make it show evidence details like tester view
3. **Verify Reupload Flow**: Ensure data owners can reupload when revision is required

## Code Changes Made

1. **app/services/evidence_collection_service.py**:
   - Changed from `TestCaseSourceEvidence` to `TestCaseEvidence` model
   - Updated query to use correct table relationships

2. **app/api/v1/endpoints/request_info.py**:
   - Added safe handling for document_type (enum vs string)
   - Fixed "'str' object has no attribute 'value'" error

## Verification Commands

```bash
# Test API endpoints
python test_evidence_api_endpoint.py

# Check database status
python investigate_correct_evidence_table.py

# View in browser
open http://localhost:3000/cycles/58/reports/156/request-info
```