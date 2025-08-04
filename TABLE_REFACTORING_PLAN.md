# Table Refactoring Plan - First Principles Approach

## Core Principles
1. **Universal frameworks over phase-specific**: Use universal status, SLA, escalation, and assignment frameworks
2. **Consistent naming**: `cycle_report_<phase>_<entity/action>`
3. **No redundancy**: Remove duplicate functionality
4. **Clear phase boundaries**: Each table belongs to exactly one phase

## Phase 1: Analysis and Discovery

### 1.1 Identify All Dependencies
- [ ] Find all foreign key references to tables being renamed
- [ ] Find all relationship definitions in SQLAlchemy models
- [ ] Find all raw SQL queries referencing these tables
- [ ] Find all API endpoints using these models
- [ ] Find all migration scripts referencing old names

### 1.2 Identify Tables to Remove
Based on clarifications:
- All `*_phases` tables (use universal phase status)
- All sample set related tables
- Data owner SLA/escalation tables (use universal)
- Data owner notifications (use universal assignments)

### 1.3 Create Dependency Graph
Map out which tables depend on which others to determine correct order of changes

## Phase 2: Design Final State

### Final Table Structure by Phase

#### Planning Phase
```
cycle_report_planning_attributes (from cycle_report_attributes_planning)
cycle_report_planning_attribute_version_history
cycle_report_planning_attribute_change_logs
cycle_report_planning_attribute_comparisons
cycle_report_planning_data_sources (from cycle_report_data_sources)
cycle_report_planning_pde_mappings (from cycle_report_pde_mappings)
cycle_report_planning_pde_classifications (from cycle_report_pde_classifications)
cycle_report_planning_pde_mapping_reviews (NEW - moved from data profiling)
cycle_report_planning_pde_mapping_review_history (NEW - moved from data profiling)
cycle_report_planning_pde_mapping_approval_rules (NEW - moved from data profiling)
```

#### Scoping Phase
```
cycle_report_scoping_attribute_recommendations
cycle_report_scoping_tester_decisions
cycle_report_scoping_submissions
cycle_report_scoping_report_owner_reviews
cycle_report_scoping_audit_logs
```

#### Data Profiling Phase
```
cycle_report_data_profiling_configurations
cycle_report_data_profiling_jobs
cycle_report_data_profiling_files
cycle_report_data_profiling_dq_rules
cycle_report_data_profiling_dq_results
cycle_report_data_profiling_attribute_dq_scores
cycle_report_data_profiling_attribute_results
cycle_report_data_profiling_anomaly_patterns
```

#### Data Owner Phase
```
cycle_report_data_owner_attribute_lob_assignments
cycle_report_data_owner_assignments
cycle_report_data_owner_assignments_history
cycle_report_data_owner_activity_logs (from audit log)
```

#### Sample Selection Phase
```
cycle_report_sample_selection_records (individual samples only)
cycle_report_sample_selection_validation_results
cycle_report_sample_selection_validation_issues
cycle_report_sample_selection_approval_history
cycle_report_sample_selection_llm_generations
cycle_report_sample_selection_upload_history
cycle_report_sample_selection_audit_logs
```

#### Request Info Phase
```
cycle_report_request_info_test_cases
cycle_report_request_info_document_submissions
cycle_report_request_info_document_versions (NEW)
cycle_report_request_info_audit_logs
```

#### Test Execution Phase
```
cycle_report_test_execution_executions
cycle_report_test_execution_sample_data
cycle_report_test_execution_document_analyses
cycle_report_test_execution_database_tests
cycle_report_test_execution_result_reviews
cycle_report_test_execution_comparisons
cycle_report_test_execution_bulk_executions
cycle_report_test_execution_audit_logs
```

#### Observation Management Phase
```
cycle_report_observation_mgmt_observations
cycle_report_observation_mgmt_groups
cycle_report_observation_mgmt_preliminary_findings (NEW)
cycle_report_observation_mgmt_clarifications
cycle_report_observation_mgmt_impact_assessments
cycle_report_observation_mgmt_approvals
cycle_report_observation_mgmt_resolutions
cycle_report_observation_mgmt_audit_logs
```

#### Test Report Phase
```
cycle_report_test_report_sections
cycle_report_test_report_document_revisions
```

### Tables to Remove Completely
```
# Phase status tables (replaced by universal status)
- data_profiling_phases
- sample_selection_phases
- test_execution_phases
- observation_management_phases
- test_report_phases
- cycle_report_request_info_phases (already exists but remove)

# Sample set tables (no longer used)
- cycle_report_sample_sets
- Any references to sample_set_id

# Data owner redundant tables (use universal frameworks)
- data_owner_sla_violations
- data_owner_escalation_log
- data_owner_notifications

# Observation tables that were in wrong phase
- Move all observation tables from test_report to observation_mgmt
```

## Phase 3: Implementation Strategy

### 3.1 Create Comprehensive Scripts
1. **Analysis Script**: Finds all occurrences of table names
2. **Model Update Script**: Updates all SQLAlchemy models
3. **Migration Script**: Renames tables in database
4. **Verification Script**: Ensures all references updated

### 3.2 Order of Operations
1. Create new tables (document_versions, preliminary_findings)
2. Move PDE review tables from data_profiling to planning
3. Rename tables in dependency order (least dependent first)
4. Remove deprecated tables
5. Update all foreign keys
6. Update all relationships
7. Update all queries

### 3.3 Testing Strategy
1. Create test database with sample data
2. Run migration on test database
3. Verify all relationships intact
4. Test all API endpoints
5. Run full integration tests

## Phase 4: Execution Steps

### Step 1: Backup Current State
- Backup database
- Create git branch
- Document current table structure

### Step 2: Create Analysis Report
```python
# Script to find all table references
# Output: JSON file with all occurrences
```

### Step 3: Generate Update Scripts
```python
# Script to generate all SQL and Python changes
# Output: Multiple update scripts
```

### Step 4: Execute in Test Environment
- Run on test database
- Verify all changes
- Run test suite

### Step 5: Execute in Production
- Schedule maintenance window
- Run migration
- Verify application

## Risk Mitigation

### Risks Identified
1. **Circular dependencies**: Tables referencing each other
2. **Hidden references**: Raw SQL, stored procedures
3. **Cache invalidation**: ORM caches with old names
4. **Migration rollback**: Need clean rollback plan

### Mitigation Strategies
1. Map all dependencies before starting
2. Search entire codebase for string references
3. Restart all services after migration
4. Create reverse migration script

## Success Criteria
1. All tables follow naming convention
2. No duplicate functionality
3. All tests pass
4. No performance degradation
5. Clean rollback possible

## Timeline Estimate
- Analysis: 2-3 hours
- Script Development: 4-6 hours
- Testing: 2-3 hours
- Execution: 1-2 hours
- Total: ~12-14 hours of focused work