# CDO References Report

This report identifies all references to "CDO" (Chief Data Officer) in the SynapseDTE codebase. These references need to be updated to "Data Executive" as the role has been renamed.

## Summary

Total files with CDO references: 240+ files across the codebase

## Key Areas Requiring Updates

### 1. Backend Python Files

#### Models
- **`app/models/user.py`**
  - Line 94: `cdo_notifications = relationship("CDONotification", back_populates="cdo")`
  - Line 191-193: Property `is_cdo()` that checks if user role is 'Data Executive'
  - Comment on line 192: "Check if user is a CDO"

- **`app/models/data_owner.py`**
  - Line 45: Class `CDONotification` - entire class needs renaming
  - Line 48: Table name `"cdo_notifications"`

#### Services
- **`app/services/cdo_dashboard_service.py`**
  - Line 2-3: Comments refer to "CDO Dashboard Service" and "Chief Data Officers"
  - Line 29: Class `CDOMetrics` - comment refers to "CDO dashboard"
  - Line 41: Class `CDOWorkflowStatus` - comment refers to "CDO workflow status"
  - Line 51: Class `CDODashboardService` - entire class name
  - Line 65-66: Class docstring refers to "CDO dashboard analytics"
  - Line 69: Log message "CDO dashboard service initialized"
  - Line 71-77: Method `get_cdo_dashboard_metrics()`
  - Line 78-88: Comments and error messages referring to CDO
  - Line 141-144: Error response with "cdo" dashboard type
  - Line 308-409: Method `_get_cdo_workflow_status()`
  - Line 783: Global instance `cdo_dashboard_service`
  - Line 786-788: Function `get_cdo_dashboard_service()`
  - Multiple references throughout in variable names, comments, and logic

- **`app/services/notification_adapter.py`**
  - CDO notification references

- **`app/services/activity_state_manager.py`**
  - CDO related activity state management

#### API Endpoints
- **`app/api/v1/endpoints/data_owner.py`**
  - CDO assignment endpoints

- **`app/api/v1/endpoints/dashboards.py`**
  - CDO dashboard endpoints

#### Other Backend Files
- **`app/core/config.py`**
  - CDO configuration settings

- **`app/schemas/data_owner.py`**
  - CDO related schemas

- **`app/temporal/activities/data_owner_activities.py`**
  - CDO temporal workflow activities

### 2. Frontend TypeScript/React Files

#### Types
- **`frontend/src/types/api.ts`**
  - Line 21: `CDO = 'CDO'` in UserRole enum

#### Components
- **`frontend/src/pages/dashboards/DataExecutiveDashboard.tsx`**
  - Dashboard component for CDO role (file already renamed but may contain internal CDO references)

- **`frontend/src/components/dashboards/RoleDashboardRouter.tsx`**
  - Role routing logic that includes CDO

#### Pages
- **`frontend/src/pages/phases/DataOwnerPage.tsx`**
  - CDO assignment UI

- **`frontend/src/pages/phases/DataExecutiveAssignmentInterface.tsx`**
  - CDO assignment interface (file renamed but may contain internal references)

### 3. Database Files

#### Seed Data
- **`scripts/database/schema/seed_data.sql`**
  - Line 44: Role description "Chief Data Officer - Manage LOBs and data providers"

#### Migrations
- Various migration files contain CDO references

### 4. Documentation

- **`CLAUDE.md`**
  - Line 167: Lists "CDO" as one of the 6 user roles
  - Line 169: "LOB-based assignment for CDO role"

- **`docs/README.md`**
  - CDO references in documentation

### 5. Test Files

- Multiple test files contain CDO references for testing CDO-specific functionality

## Recommendations

1. **Database Migration**: Create a migration to:
   - Rename `cdo_notifications` table to `data_executive_notifications`
   - Update any stored procedures or functions that reference CDO
   - Update role descriptions in seed data

2. **Backend Code Updates**:
   - Rename `CDONotification` class to `DataExecutiveNotification`
   - Rename `CDODashboardService` to `DataExecutiveDashboardService`
   - Update all method names from `cdo_*` to `data_executive_*`
   - Update all variable names and comments

3. **Frontend Code Updates**:
   - Update UserRole enum to remove CDO
   - Update all component references
   - Update routing logic

4. **Documentation Updates**:
   - Update all documentation files to reflect the new role name
   - Update API documentation

5. **Testing**:
   - Update all test files to use the new role name
   - Ensure all tests pass after updates

## Search Commands for Verification

To find all CDO references:
```bash
# Case-sensitive search for CDO
grep -r "CDO" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.sql" --include="*.md" .

# Search for cdo (lowercase) in variable names
grep -r "cdo" --include="*.py" --include="*.ts" --include="*.tsx" .

# Search for specific patterns
grep -r "is_cdo" --include="*.py" .
grep -r "CDONotification" --include="*.py" .
grep -r "cdo_dashboard" --include="*.py" .
```