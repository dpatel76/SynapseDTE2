# Role Rename Impact Analysis

## Summary of Role Changes
1. **Test Manager** → **Test Executive**
2. **Data Provider** → **Data Owner**
3. **CDO** → **Data Executive**
4. **Report Owner Executive** → **Report Executive**

Note: "Tester", "Report Owner", and "Admin" roles remain unchanged.

## Backend Files to Update

### 1. Core Models and Enums
- `/app/models/user.py` - Update `user_role_enum` PostgreSQL ENUM type
- `/app/core/auth.py` - Update `UserRoles` class constants
- `/app/core/rbac_config.py` - Update role references in RBAC configuration
- `/app/core/permissions.py` - Update role-based permission checks
- `/app/core/security.py` - Update role references in security functions

### 2. API Endpoints (61 files with "Test Manager", 113 with "Data Provider", 64 with "CDO", 45 with "Report Owner Executive")
Key endpoints to update:
- `/app/api/v1/endpoints/auth.py`
- `/app/api/v1/endpoints/users.py`
- `/app/api/v1/endpoints/dashboards.py`
- `/app/api/v1/endpoints/data_provider.py` (consider renaming to data_owner.py)
- `/app/api/v1/endpoints/cycles.py`
- `/app/api/v1/endpoints/planning.py`
- `/app/api/v1/endpoints/reports.py`
- `/app/api/v1/endpoints/cycle_reports.py`
- `/app/api/v1/endpoints/sla.py`
- `/app/api/v1/endpoints/metrics.py`
- `/app/api/v1/endpoints/observation_management.py`
- `/app/api/v1/endpoints/request_info.py`
- `/app/api/v1/endpoints/sample_selection.py`
- `/app/api/v1/endpoints/testing_execution.py`

### 3. Services
- `/app/services/cdo_dashboard_service.py` (rename to data_executive_dashboard_service.py)
- `/app/services/data_provider_dashboard_service.py` (rename to data_owner_dashboard_service.py)
- `/app/services/executive_dashboard_service.py` (update references)
- `/app/services/metrics_service.py`
- `/app/services/sla_service.py`
- `/app/services/rbac_restrictions.py`
- `/app/services/email_service.py`
- `/app/services/workflow_orchestrator.py`

### 4. Schemas
- `/app/schemas/data_provider.py` (rename to data_owner.py)
- `/app/schemas/sla.py`
- `/app/schemas/cycle.py`
- `/app/schemas/rbac.py`

### 5. Database Migrations
- Create new Alembic migration to update the PostgreSQL enum type
- Update seed data scripts in `/scripts/` directory

### 6. Scripts (multiple references found)
- `/scripts/create_test_users.py`
- `/scripts/seed_rbac_permissions.py`
- `/scripts/create_sample_data.py`
- Various test and migration scripts

## Frontend Files to Update

### 1. Type Definitions
- `/frontend/src/types/api.ts` - Update `UserRole` enum

### 2. Dashboard Components
- `/frontend/src/pages/dashboards/TestManagerDashboard.tsx` (rename to TestExecutiveDashboard.tsx)
- `/frontend/src/pages/dashboards/DataProviderDashboard.tsx` (rename to DataOwnerDashboard.tsx)
- `/frontend/src/pages/dashboards/CDODashboard.tsx` (rename to DataExecutiveDashboard.tsx)
- `/frontend/src/pages/DashboardPage.tsx` - Update role routing

### 3. Phase Components
- `/frontend/src/pages/phases/DataProviderPage.tsx` (rename to DataOwnerPage.tsx)
- `/frontend/src/pages/phases/CDOAssignmentsPage.tsx` (rename to DataExecutiveAssignmentsPage.tsx)
- `/frontend/src/pages/phases/CDOAssignmentInterface.tsx` (rename to DataExecutiveAssignmentInterface.tsx)

### 4. Common Components
- `/frontend/src/components/common/Layout.tsx` - Update role display
- `/frontend/src/components/layout/Sidebar.tsx` - Update navigation based on roles
- `/frontend/src/components/WorkflowProgress.tsx` - Update role references
- `/frontend/src/contexts/PermissionContext.tsx` - Update role checks

### 5. Routing
- `/frontend/src/App.tsx` - Update role-based routing

### 6. Tests
- `/frontend/e2e/global-setup.ts` - Update test user roles
- `/frontend/e2e/test-utils.ts` - Update role utilities
- `/frontend/e2e/role-based-testing.spec.ts` - Update role tests

## Database Issues Found

### Reports vs CycleReports Table Usage
Found incorrect usage of `Report` table in several places where `CycleReport` should be used for cycle-specific data:

1. **`/app/services/cdo_dashboard_service.py`** (line 225):
   ```python
   .join(Report, DataProviderAssignment.report_id == Report.report_id)
   ```
   Should use `CycleReport` for cycle-specific report data.

2. Other services and endpoints may have similar issues where they're joining directly to `Report` table instead of using `CycleReport` for cycle-specific operations.

## Additional Considerations

### 1. File Naming Conventions
- Rename files with old role names (e.g., `data_provider_*` → `data_owner_*`)
- Update import statements accordingly

### 2. UI Display Names
- Add a role label/display name mapping to show user-friendly names in the UI
- Consider creating a `getRoleDisplayName()` utility function

### 3. Database Migration Strategy
1. Create Alembic migration to add new enum values
2. Update existing records to use new role names
3. Remove old enum values
4. Update any foreign key constraints if needed

### 4. API Response Compatibility
- Consider adding a transition period where both old and new role names are accepted
- Add deprecation warnings for old role names
- Update API documentation

### 5. Testing
- Update all test fixtures and test data
- Ensure backward compatibility during transition
- Test role-based access control with new names

## Migration Order
1. Backend enum and model updates
2. Database migration
3. API endpoint updates
4. Service layer updates
5. Frontend type updates
6. Frontend component updates
7. Test updates
8. Documentation updates