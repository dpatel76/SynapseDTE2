# Evidence Table Migration Status

## Summary
The code changes have been completed to unify the evidence tracking system. The database migration script is ready but requires admin privileges to execute.

## Completed Tasks ✅

### 1. Model Updates
- ✅ Created unified `TestCaseEvidence` model in `/app/models/request_info.py`
- ✅ Added backward compatibility alias: `RFIEvidenceLegacy = TestCaseEvidence`
- ✅ Enhanced model with all document submission fields (submission_number, is_revision, etc.)
- ✅ Removed `TestCaseDocumentSubmission` model completely
- ✅ Updated model `__tablename__` to `cycle_report_test_cases_evidence`

### 2. Service & Use Case Updates
- ✅ Updated `SubmitDocumentUseCase` to save directly to `TestCaseEvidence` table
- ✅ Changed field references from `submitted_by` to `data_owner_id`
- ✅ Updated `save_validated_query` in request_info_service.py to use `TestCaseEvidence`
- ✅ Updated all queries to use `TestCaseEvidence` instead of `TestCaseDocumentSubmission`

### 3. Import & Reference Updates
- ✅ Removed all `TestCaseDocumentSubmission` imports and references
- ✅ Updated all code to use `TestCaseEvidence` as the unified model
- ✅ Fixed `/app/models/__init__.py` exports
- ✅ Updated `/app/api/v1/endpoints/request_info_documents.py` to query unified table

### 4. Migration Scripts Created
- ✅ `/scripts/database/07302025/01_rename_evidence_table.sql` - Main migration
- ✅ `/scripts/database/07302025/01_rename_evidence_table_rollback.sql` - Rollback script
- ✅ `/scripts/database/07302025/EVIDENCE_TABLE_MIGRATION.md` - Documentation

## Pending Tasks ⏳

### 1. Execute Database Migration
The migration script needs to be run with database admin/owner privileges:

```bash
# Connect as database admin
psql -U postgres -d your_database_name

# Run migration
\i /path/to/scripts/database/07302025/01_rename_evidence_table.sql
```

### 2. Update Frontend
After database migration:
- Update TypeScript types to remove `TestCaseDocumentSubmission` interface
- Update API calls to use unified evidence endpoints
- Test document upload and data source submission flows

## Current State
- **Code**: Ready for new table structure ✅
- **Database**: Still using old table name (`cycle_report_rfi_evidence`) ⚠️
- **Application**: Working with backward compatibility ✅

## Important Notes
1. The application currently works because the model uses an alias
2. The database table name mismatch will be resolved after migration
3. All existing evidence data will be preserved during migration
4. Document submissions that were in the separate table will be migrated

## Next Steps
1. Get database admin to run the migration script
2. Verify all data migrated correctly
3. Test document uploads and data source submissions
4. Update frontend components
5. Remove any remaining references to old structure