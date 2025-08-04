# Assignment Models Audit Report

## Overview
This document provides a comprehensive list of all assignment-related models found in the SynapseDTE codebase and recommendations for migration to the Universal Assignment framework.

## Current Assignment Models

### 1. **UniversalAssignment** (app/models/universal_assignment.py)
- **Status**: ✅ Active - This is the new unified assignment framework
- **Table**: `universal_assignments`
- **Purpose**: Universal assignment model for all role-to-role interactions
- **Action**: Keep as-is

### 2. **ReportOwnerAssignment** (app/models/report_owner_assignment.py)
- **Status**: ⚠️ Legacy - Should be migrated
- **Table**: `report_owner_assignments`
- **Purpose**: Tracking assignments given to report owners across different phases
- **Relationships**: Referenced in TestCycle, Report, and User models
- **Action**: Migrate to UniversalAssignment framework and rename to _backup

### 3. **DataOwnerAssignment** (app/models/testing.py)
- **Status**: ⚠️ Legacy - Should be migrated
- **Table**: `data_owner_assignments`
- **Purpose**: Data owner assignments model
- **Relationships**: Referenced in TestCycle and has SLA violations relationship
- **Note**: Also defined in versioning.py and versioning_complete.py
- **Action**: Migrate to UniversalAssignment framework and rename to _backup

### 4. **AttributeLOBAssignment** (app/models/data_owner.py)
- **Status**: ⚠️ May need evaluation
- **Table**: `attribute_lob_assignments`
- **Purpose**: Attribute to LOB assignments model
- **Relationships**: Referenced in TestCycle, Report, ReportAttribute, and LOB models
- **Action**: Evaluate if this should be migrated or kept as a specialized assignment type

### 5. **HistoricalDataOwnerAssignment** (app/models/data_owner.py)
- **Status**: ✅ Keep - Historical tracking
- **Table**: `historical_data_owner_assignments`
- **Purpose**: Historical data owner assignments for knowledge tracking
- **Action**: Keep as-is for historical data

### 6. **CDONotification** (deprecated)
- **Status**: ❌ Already deprecated
- **Table**: `data_executive_notifications` (renamed)
- **Note**: Already commented out in code and replaced by universal assignments
- **Action**: Ensure table is dropped or renamed to _backup

## Related Models Needing Updates

### Models with Assignment Relationships:
1. **User** (app/models/user.py)
   - Has relationships to multiple assignment types
   - Already has universal assignment relationships configured
   - Need to update/remove legacy assignment relationships

2. **TestCycle** (app/models/test_cycle.py)
   - References: `attribute_lob_assignments`, `data_owner_assignments`, `report_owner_assignments`
   - Need to update relationships to use universal assignments

3. **Report** (app/models/report.py)
   - Has relationships to various assignment types
   - Need to check and update

4. **ReportAttribute** (app/models/report_attribute.py)
   - Has relationships to assignment models
   - Need to check and update

## Migration Strategy

### Phase 1: Immediate Actions
1. Fix the current API errors (500 and 422 errors)
2. Create database backup before any migrations

### Phase 2: Model Migration
1. **ReportOwnerAssignment** → UniversalAssignment
   - Map assignment_type to appropriate universal types
   - Migrate data with proper context_data
   - Update all references in other models

2. **DataOwnerAssignment** → UniversalAssignment
   - Similar migration approach
   - Handle SLA violation relationships

3. **AttributeLOBAssignment** → Evaluate
   - Determine if this needs migration or stays as specialized model

### Phase 3: Cleanup
1. Rename old tables to _backup suffix
2. Remove deprecated model relationships
3. Update all API endpoints to use universal assignments
4. Clean up old import statements

## API Endpoints to Update
- `/reports/` - Fix 500 error
- `/cycles/` - Fix 500 error
- `/universal-assignments/assignments` - Fix 422 error
- `/lobs/active` - Fix 500 error
- `/analytics/` - Fix 500 error

## Next Steps
1. Debug and fix the current API errors
2. Create detailed migration scripts for each assignment type
3. Update frontend to use universal assignment endpoints
4. Test thoroughly before deploying to production