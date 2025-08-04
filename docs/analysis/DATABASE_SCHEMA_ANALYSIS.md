# Database Schema Analysis - SynapseDTE

## Executive Summary

This document provides a comprehensive analysis of the SynapseDTE database schema, identifying key issues, redundancies, and improvement opportunities across the 40+ table schema supporting the 7-phase testing workflow.

## Critical Issues Found

### 1. Missing Indexes on Foreign Keys
**Severity: High**
- Most foreign key columns lack indexes, which will severely impact query performance
- Affected tables: `workflow_phases`, `report_attributes`, `test_executions`, `data_provider_assignments`, etc.
- Impact: Slow joins, poor query performance, especially for reporting and dashboard queries

### 2. Inconsistent Naming Conventions
**Severity: Medium**
- Table names use mix of singular/plural: `users` vs `audit_log`
- Some tables use verbose names: `data_provider_phase_audit_log` could be `dp_phase_audit_log`
- Enum naming inconsistent: some use `_enum` suffix, others don't

### 3. Data Redundancy
**Severity: Medium**
- `cycle_id` and `report_id` are duplicated across many tables where they could be derived through relationships
- Multiple audit log tables with similar structures: `AuditLog`, `LLMAuditLog`, `TestingExecutionAuditLog`, `DataProviderPhaseAuditLog`
- SLA tracking duplicated between generic `SLAViolationTracking` and specific `DataProviderSLAViolation`

### 4. Incomplete Versioning Implementation
**Severity: Medium**
- `ReportAttribute` has comprehensive versioning but other entities that need it don't:
  - `TestExecution` - no versioning for re-runs
  - `Document` - no versioning for document updates
  - `DataProviderAssignment` - no history of reassignments
- Versioning patterns are inconsistent across models

### 5. Hardcoded Values
**Severity: Low-Medium**
- User roles hardcoded in enum instead of configuration table
- Workflow phases hardcoded in enum
- Test types, statuses hardcoded in enums
- This makes adding new roles/phases/types require schema changes

### 6. JSONB Field Overuse
**Severity: Low**
- Some JSONB fields could be normalized:
  - `notification_data` in `CDONotification`
  - `validation_notes` in `DocumentAnalysis`
  - `change_requests` in sample approval
- Makes querying and indexing difficult

### 7. Missing RBAC Implementation Details
**Severity: High**
- RBAC tables exist but aren't properly integrated:
  - No clear mapping between system roles and RBAC roles
  - `ResourcePermission` table exists but no clear resource type definitions
  - Permission strings not standardized
  - No default permissions for roles

### 8. Inefficient Audit Trail Structure
**Severity: Medium**
- Multiple audit tables with different schemas
- No centralized audit trail
- JSONB for old/new values makes querying difficult
- No audit trail for some critical operations

## Detailed Analysis by Domain

### Workflow Management
**Tables:** `workflow_phases`, `test_cycles`, `cycle_reports`

Issues:
- `workflow_phases` stores redundant `cycle_id` and `report_id` (could use composite FK to `cycle_reports`)
- No version tracking for workflow state changes
- Override fields (`state_override`, `status_override`) could be in separate audit table

Recommendations:
1. Add indexes on all foreign keys
2. Create `workflow_phase_history` table for state transitions
3. Move override fields to audit/history table

### Attribute Management
**Tables:** `report_attributes`, `attribute_version_change_logs`, `attribute_version_comparisons`

Strengths:
- Comprehensive versioning implementation
- Good separation of concerns

Issues:
- Very wide table (30+ columns)
- Some fields could be moved to separate tables:
  - LLM-related fields → `attribute_llm_metadata`
  - Risk assessment fields → `attribute_risk_assessment`
- Version comparison table seems unnecessary (can be computed)

### Testing Execution
**Tables:** `testing_test_executions`, `document_analyses`, `database_tests`

Issues:
- No versioning for test re-runs
- `sample_record_id` is string but references could be integer
- Separation between `DocumentAnalysis` and `DatabaseTest` creates complexity
- Missing composite indexes for common queries

Recommendations:
1. Add test execution versioning
2. Unify test results in single table with discriminator
3. Add composite indexes for (cycle_id, report_id, attribute_id)

### SLA Management
**Tables:** `sla_configurations`, `sla_violation_tracking`, `escalation_email_logs`

Strengths:
- Good separation of configuration vs tracking
- Flexible escalation rules

Issues:
- Business hours logic in model instead of configuration
- No holiday calendar support
- Duplicate SLA tracking for data providers

### Data Provider Management
**Tables:** `data_provider_assignments`, `attribute_lob_assignments`, `cdo_notifications`

Issues:
- Complex relationship between LOB assignments and data provider assignments
- Historical assignments in separate table instead of versioning
- No clear assignment workflow tracking

## Recommendations

### Immediate Actions (High Priority)

1. **Add Missing Indexes**
```sql
-- Add indexes on all foreign keys
CREATE INDEX idx_workflow_phases_cycle_id ON workflow_phases(cycle_id);
CREATE INDEX idx_workflow_phases_report_id ON workflow_phases(report_id);
CREATE INDEX idx_report_attributes_cycle_id ON report_attributes(cycle_id);
CREATE INDEX idx_report_attributes_report_id ON report_attributes(report_id);
-- ... continue for all foreign keys
```

2. **Implement Proper RBAC**
- Create seed data for permissions
- Map system roles to RBAC roles
- Add default permissions for each role
- Standardize permission strings

3. **Consolidate Audit Logs**
```sql
CREATE TABLE unified_audit_log (
    audit_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER,
    action VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES users(user_id),
    timestamp TIMESTAMPTZ NOT NULL,
    changes JSONB,
    metadata JSONB,
    INDEX idx_audit_table_record (table_name, record_id),
    INDEX idx_audit_user_timestamp (user_id, timestamp)
);
```

### Medium-Term Improvements

1. **Normalize Wide Tables**
- Split `report_attributes` into core attributes and metadata tables
- Move LLM-specific fields to separate tables
- Create proper configuration tables for enums

2. **Implement Consistent Versioning**
- Create base versioning mixin
- Apply to all entities that need history
- Standardize version number tracking

3. **Optimize JSONB Usage**
- Move frequently queried JSONB fields to columns
- Add GIN indexes where JSONB is necessary
- Consider JSONB → normalized tables for complex structures

### Long-Term Refactoring

1. **Schema Modularization**
- Group related tables into schemas: `workflow`, `testing`, `rbac`, `audit`
- Reduce cross-schema dependencies
- Implement clear boundaries between domains

2. **Performance Optimization**
- Implement table partitioning for large tables (audit logs, test executions)
- Add materialized views for complex reporting queries
- Consider read replicas for reporting workloads

3. **Data Integrity Improvements**
- Add check constraints for business rules
- Implement triggers for complex validations
- Add database-level audit trails

## Migration Strategy

1. **Phase 1: Non-Breaking Changes**
   - Add missing indexes
   - Add new normalized tables alongside existing
   - Implement parallel audit logging

2. **Phase 2: Data Migration**
   - Migrate data to new structures
   - Update application code to use new structures
   - Maintain backward compatibility

3. **Phase 3: Cleanup**
   - Remove deprecated columns
   - Drop redundant tables
   - Update all references

## Performance Impact Analysis

Current schema issues likely cause:
- 10-100x slower queries on foreign key joins without indexes
- Complex queries with multiple JSONB operations
- Table scans instead of index scans
- Lock contention on wide tables

Expected improvements after optimization:
- 50-90% reduction in query time for dashboard queries
- Better concurrent user support
- Reduced database CPU usage
- Improved write performance

## Conclusion

The SynapseDTE schema is comprehensive but needs optimization for performance and maintainability. The most critical issues are missing indexes and incomplete RBAC implementation. With the recommended changes, the system can support better performance, easier maintenance, and future scalability.