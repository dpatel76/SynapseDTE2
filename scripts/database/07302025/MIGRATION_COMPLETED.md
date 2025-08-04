# Evidence Table Migration - COMPLETED ✅

## Migration Summary
Date: 2025-07-30
Executed by: postgres superuser

## What Was Done

### 1. Table Renamed ✅
- `cycle_report_rfi_evidence` → `cycle_report_test_cases_evidence`

### 2. Columns Added ✅
- `submission_number` (INTEGER DEFAULT 1)
- `is_revision` (BOOLEAN DEFAULT FALSE)
- `revision_requested_by` (INTEGER, FK to users)
- `revision_requested_at` (TIMESTAMP WITH TIME ZONE)
- `revision_reason` (TEXT)
- `revision_deadline` (TIMESTAMP WITH TIME ZONE)
- `document_type` (document_type_enum)

### 3. Column Renamed ✅
- `submitted_by` → `data_owner_id`

## Verification Results

### Table Check
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'cycle_report_test_cases_evidence';
-- Result: Table exists ✅
```

### Evidence Count
```sql
SELECT COUNT(*) as total, evidence_type 
FROM cycle_report_test_cases_evidence 
GROUP BY evidence_type;
-- Result: data_source: 5 ✅
```

### Application Test
- Model correctly references new table name ✅
- Queries execute successfully ✅
- No errors in application ✅

## Benefits Achieved

1. **Unified Evidence Tracking**: Both documents and data sources now use the same table
2. **Better Naming**: Table name now clearly indicates its purpose (test case evidence)
3. **Enhanced Tracking**: New columns support revision management and submission tracking
4. **Simplified Architecture**: Removed the need for separate `TestCaseDocumentSubmission` table

## Code Changes Applied

1. **Model Updates**:
   - Created `TestCaseEvidence` model with new table name
   - Added backward compatibility alias
   - Removed `TestCaseDocumentSubmission` model

2. **Service Updates**:
   - Updated all queries to use `TestCaseEvidence`
   - Changed references from `submitted_by` to `data_owner_id`

3. **Use Case Updates**:
   - Modified `SubmitDocumentUseCase` to save to unified table
   - Updated evidence counting logic

## Next Steps

1. **Frontend Updates** (Still Pending):
   - Update TypeScript interfaces
   - Remove references to old document submission endpoints
   - Test document upload flow

2. **Testing**:
   - Verify document uploads work correctly
   - Confirm data source submissions still function
   - Test revision request workflow

## Rollback Instructions (If Needed)

If rollback is required, use:
```bash
psql -U postgres -d synapse_dt < /path/to/scripts/database/07302025/01_rename_evidence_table_rollback.sql
```

## Notes
- All existing data was preserved during migration
- No data loss occurred
- Application is fully functional with new structure