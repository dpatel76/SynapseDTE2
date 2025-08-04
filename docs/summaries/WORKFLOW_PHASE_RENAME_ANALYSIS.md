# Workflow Phase Rename Impact Analysis - SynapseDTE

## Executive Summary

This document outlines the comprehensive changes required to rename workflow phases throughout the SynapseDTE system. The changes affect database schemas, backend services, frontend components, and API endpoints.

## Phase Name Changes

### Current → New Phase Names
1. **Planning** → Planning (no change)
2. **Scoping** → Scoping (no change)
3. **Sample Selection** → Sample Selection (no change)
4. **Data Provider ID** → **Data Owner Identification**
5. **Request Info** → **Request Source Information**
6. **Testing** → **Test Execution**
7. **Observations** → Observations (no change)

## Impact Analysis

### 1. Database Changes

#### PostgreSQL Enum Updates
```sql
-- Current enum in workflow_phase_enum
'Data Provider ID' → 'Data Owner Identification'
'Request Info' → 'Request Source Information'
'Testing' → 'Test Execution'
```

#### Table Renames Required
```sql
-- Data Provider → Data Owner tables
ALTER TABLE data_provider_assignments RENAME TO data_owner_assignments;
ALTER TABLE historical_data_provider_assignments RENAME TO historical_data_owner_assignments;
ALTER TABLE data_provider_sla_violations RENAME TO data_owner_sla_violations;
ALTER TABLE data_provider_escalation_log RENAME TO data_owner_escalation_log;
ALTER TABLE data_provider_phase_audit_log RENAME TO data_owner_phase_audit_log;
ALTER TABLE data_provider_notifications RENAME TO data_owner_notifications;

-- Request Info → Request Source Information tables
ALTER TABLE request_info_phases RENAME TO request_source_information_phases;
ALTER TABLE request_info_audit_log RENAME TO request_source_information_audit_log;

-- Testing → Test Execution tables
ALTER TABLE testing_execution_phases RENAME TO test_execution_phases;
ALTER TABLE testing_test_executions RENAME TO test_executions;
ALTER TABLE testing_execution_audit_logs RENAME TO test_execution_audit_logs;
```

### 2. Backend File Renames

#### Model Files
```bash
# Models
mv app/models/data_provider.py app/models/data_owner.py
mv app/models/request_info.py app/models/request_source_information.py
mv app/models/testing_execution.py app/models/test_execution.py

# Schemas
mv app/schemas/data_provider.py app/schemas/data_owner.py
mv app/schemas/request_info.py app/schemas/request_source_information.py
mv app/schemas/testing_execution.py app/schemas/test_execution.py

# API Endpoints
mv app/api/v1/endpoints/data_provider.py app/api/v1/endpoints/data_owner.py
mv app/api/v1/endpoints/request_info.py app/api/v1/endpoints/request_source_information.py
mv app/api/v1/endpoints/testing_execution.py app/api/v1/endpoints/test_execution.py

# Services
mv app/services/data_provider_dashboard_service.py app/services/data_owner_dashboard_service.py
mv app/services/request_info_service.py app/services/request_source_information_service.py
```

### 3. Frontend File Renames

#### Component Files
```bash
# Phase Pages
mv frontend/src/pages/phases/DataProviderPage.tsx frontend/src/pages/phases/DataOwnerPage.tsx
mv frontend/src/pages/phases/NewRequestInfoPage.tsx frontend/src/pages/phases/RequestSourceInformationPage.tsx
mv frontend/src/pages/phases/TestingExecutionPage.tsx frontend/src/pages/phases/TestExecutionPage.tsx

# Dashboard
mv frontend/src/pages/dashboards/DataProviderDashboard.tsx frontend/src/pages/dashboards/DataOwnerDashboard.tsx
```

### 4. Code Updates Required

#### Backend Updates

**app/api/v1/api.py** - Update routes:
```python
# Before
api_router.include_router(data_provider.router, prefix="/data-provider", tags=["data-provider"])
api_router.include_router(request_info.router, prefix="/request-info", tags=["request-info"])
api_router.include_router(testing_execution.router, prefix="/testing-execution", tags=["testing-execution"])

# After
api_router.include_router(data_owner.router, prefix="/data-owner", tags=["data-owner"])
api_router.include_router(request_source_information.router, prefix="/request-source-information", tags=["request-source-information"])
api_router.include_router(test_execution.router, prefix="/test-execution", tags=["test-execution"])
```

**app/services/workflow_orchestrator.py** - Update phase names:
```python
PHASE_DEPENDENCIES = {
    'Planning': [],
    'Scoping': ['Planning'],
    'Sample Selection': ['Scoping'],
    'Data Owner Assignment': ['Sample Selection'],  # Changed
    'Request Source Information': ['Data Owner Assignment'],  # Changed
    'Test Execution': ['Request Source Information'],  # Changed
    'Observations': ['Test Execution']  # Changed
}
```

#### Frontend Updates

**frontend/src/App.tsx** - Update routes:
```typescript
// Before
<Route path="/cycles/:cycleId/reports/:reportId/data-provider" element={<DataProviderPage />} />
<Route path="/cycles/:cycleId/reports/:reportId/request-info" element={<NewRequestInfoPage />} />
<Route path="/cycles/:cycleId/reports/:reportId/testing-execution" element={<TestingExecutionPage />} />

// After
<Route path="/cycles/:cycleId/reports/:reportId/data-owner" element={<DataOwnerPage />} />
<Route path="/cycles/:cycleId/reports/:reportId/request-source-information" element={<RequestSourceInformationPage />} />
<Route path="/cycles/:cycleId/reports/:reportId/test-execution" element={<TestExecutionPage />} />
```

**frontend/src/components/WorkflowProgress.tsx** - Update phase routes:
```typescript
const phaseRoutes: Record<string, string> = {
  'Planning': 'planning',
  'Scoping': 'scoping',
  'Sample Selection': 'sample-selection',
  'Data Owner Assignment': 'data-owner',  // Changed
  'Request Source Information': 'request-source-information',  // Changed
  'Test Execution': 'test-execution',  // Changed
  'Observations': 'observations'
};
```

### 5. Search and Replace Patterns

#### Global Search/Replace Required
```
# Snake case
data_provider → data_owner
request_info → request_source_information
testing_execution → test_execution

# Kebab case
data-provider → data-owner
request-info → request-source-information
testing-execution → test-execution

# Pascal case
DataProvider → DataOwner
RequestInfo → RequestSourceInformation
TestingExecution → TestExecution

# Upper case
DATA_PROVIDER → DATA_OWNER
REQUEST_INFO → REQUEST_SOURCE_INFORMATION
TESTING_EXECUTION → TEST_EXECUTION

# String literals
"Data Provider ID" → "Data Owner Assignment"
"Request Info" → "Request Source Information"
"Testing" → "Test Execution"
```

### 6. Migration Strategy

#### Phase 1: Database Migration (1 day)
1. Create Alembic migration for enum updates
2. Update existing workflow_phases records
3. Rename tables
4. Update foreign key constraints

#### Phase 2: Backend Updates (2-3 days)
1. Update model files and imports
2. Update schema files
3. Update API endpoints and routes
4. Update service files
5. Update workflow orchestrator

#### Phase 3: Frontend Updates (2 days)
1. Update component files and imports
2. Update routing configuration
3. Update API client calls
4. Update TypeScript types

#### Phase 4: Testing and Validation (1 day)
1. Run all unit tests
2. Test workflow progression
3. Validate API endpoints
4. Check UI navigation

### 7. Risks and Considerations

1. **Database Migration Risk**: Enum changes require careful migration to avoid breaking existing data
2. **API Breaking Changes**: External integrations may need updates
3. **Cached Data**: Clear all caches after migration
4. **User Communication**: Notify users of UI changes
5. **Documentation**: Update all documentation and help text

### 8. Rollback Plan

1. Keep backup of database before migration
2. Tag current code version before changes
3. Prepare rollback migration scripts
4. Document old→new mapping for quick reference

## Conclusion

This phase rename requires systematic changes across the entire stack. The migration should be performed in a coordinated manner, preferably during a maintenance window. All changes should be thoroughly tested before deployment to production.