# Evidence Table Migration Guide

## Overview
This migration unifies the evidence tracking system by renaming `cycle_report_rfi_evidence` to `cycle_report_test_cases_evidence` and consolidating all evidence-related fields into a single table.

## Migration Purpose
- **Simplify Architecture**: Remove the need for separate `TestCaseDocumentSubmission` table
- **Unified Evidence**: Store both document and data source evidence in one table
- **Better Tracking**: Include submission tracking fields directly in the evidence table
- **Consistent Naming**: Align table name with its actual purpose (test case evidence)

## Changes Made

### 1. Table Rename
- `cycle_report_rfi_evidence` → `cycle_report_test_cases_evidence`

### 2. New Columns Added
- `submission_number` (INTEGER) - Track submission versions
- `is_revision` (BOOLEAN) - Flag for revision submissions
- `revision_requested_by` (INTEGER) - User who requested revision
- `revision_requested_at` (TIMESTAMP) - When revision was requested
- `revision_reason` (TEXT) - Reason for revision request
- `revision_deadline` (TIMESTAMP) - Deadline for revision
- `document_type` (ENUM) - Type of document submitted

### 3. Column Rename
- `submitted_by` → `data_owner_id` (for consistency)

### 4. Model Updates
- Created `TestCaseEvidence` model
- Added backward compatibility alias: `RFIEvidenceLegacy = TestCaseEvidence`
- Removed `TestCaseDocumentSubmission` model

## Running the Migration

### Prerequisites
- Database admin/owner privileges
- Backup of current database
- All active connections closed

### Execute Migration
```bash
# Connect to database as admin/owner
psql -U postgres -d your_database_name

# Run migration script
\i /path/to/scripts/database/07302025/01_rename_evidence_table.sql

# Verify migration
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'cycle_report_test_cases_evidence';
```

### Rollback (if needed)
```bash
# Run rollback script
\i /path/to/scripts/database/07302025/01_rename_evidence_table_rollback.sql
```

## Application Changes Required

### Backend
1. ✅ Updated `app/models/request_info.py`:
   - Renamed `RFIEvidenceLegacy` class to `TestCaseEvidence`
   - Added backward compatibility alias
   - Removed `TestCaseDocumentSubmission` class

2. ✅ Updated `app/application/use_cases/request_info.py`:
   - Modified `SubmitDocumentUseCase` to use unified table
   - Updated field mappings

3. ✅ Updated `app/services/request_info_service.py`:
   - Updated query references
   - Changed field names (e.g., `submitted_by` → `data_owner_id`)

### Frontend Updates Still Needed
- Update API response handling for evidence data
- Remove references to separate document submission endpoints
- Update type definitions for unified evidence structure

## Testing Checklist
- [ ] Document uploads work correctly
- [ ] Data source submissions work correctly
- [ ] Evidence appears in Data Owner Dashboard
- [ ] Evidence links are functional
- [ ] Revision requests work properly
- [ ] All existing evidence is preserved

## Benefits
1. **Simpler Code**: One model instead of two
2. **Better Performance**: Single table queries
3. **Easier Maintenance**: Less complex relationships
4. **Consistent Data**: All evidence in one place

## Notes
- The migration preserves all existing data
- Foreign key relationships are maintained
- Indexes are added for performance
- The old table name is completely removed