# Database Foreign Key Redundancy Analysis

## 🎯 Issue Identified
Many tables contain redundant foreign key relationships by having all three identifiers (phase_id, cycle_id, report_id) when phase_id alone would suffice.

## 📊 Current State Analysis

### 🔴 REDUNDANT TABLES (18 tables with ALL THREE IDs)
These tables have unnecessary cycle_id and report_id columns since phase_id can provide access to both:

1. **cycle_report_data_profiling_rules**
2. **cycle_report_documents**  
3. **cycle_report_observation_groups**
4. **cycle_report_observation_mgmt_audit_logs**
5. **cycle_report_observation_mgmt_observation_records**
6. **cycle_report_observation_mgmt_preliminary_findings**
7. **cycle_report_planning_attributes**
8. **cycle_report_request_info_audit_logs**
9. **cycle_report_request_info_testcase_source_evidence**
10. **cycle_report_sample_selection_audit_logs**
11. **cycle_report_sample_selection_samples**
12. **cycle_report_scoping_attribute_recommendations_backup**
13. **cycle_report_scoping_decision_versions**
14. **cycle_report_scoping_decisions**
15. **cycle_report_scoping_submissions**
16. **cycle_report_test_execution_results**
17. **workflow_activities** 
18. **workflow_phases** (main table - exception)

### ✅ IDEAL PATTERN (9 tables with PHASE_ID ONLY)
These tables follow the correct pattern:

1. **cycle_report_data_owner_lob_attribute_assignments**
2. **cycle_report_data_owner_lob_attribute_versions**
3. **cycle_report_observation_mgmt_approvals**
4. **cycle_report_observation_mgmt_impact_assessments** 
5. **cycle_report_observation_mgmt_resolutions**
6. **cycle_report_planning_attribute_version_history**
7. **cycle_report_request_info_document_versions**
8. **cycle_report_test_execution_reviews**
9. **cycle_report_test_report_sections**

### 🟡 PARTIAL REDUNDANCY (17 tables with CYCLE + REPORT)
These tables have cycle_id and report_id but could potentially use phase_id:

1. **activity_states**
2. **cycle_report_data_profiling_rule_versions**
3. **cycle_report_document_submissions**
4. **cycle_report_planning_data_sources** 
5. **cycle_report_planning_pde_mappings**
6. **cycle_report_test_cases**
7. **cycle_reports** (main junction table - exception)
8. **data_owner_phase_audit_logs_legacy**
9. **llm_audit_logs**
10. **metrics_execution**
11. **metrics_phases**
12. **profiling_executions**
13. **profiling_jobs**
14. **universal_sla_violation_trackings**
15. **universal_version_histories**
16. **workflow_activity_histories**
17. **workflow_executions**

## 🔧 Recommended Refactoring

### Phase 1: Remove Redundant Columns from RED Category Tables

For the 17 tables (excluding workflow_phases) that have all three IDs:

**Remove columns:**
- `cycle_id` 
- `report_id`

**Keep only:**
- `phase_id` (provides access to both cycle and report via workflow_phases table)

**Relationship chain:**
```
table → phase_id → workflow_phases → (cycle_id, report_id) → cycle_reports → test_cycles
```

### Phase 2: Evaluate Yellow Category Tables

Tables with cycle_id + report_id should be evaluated case by case:
- If they are phase-specific data, add phase_id and remove cycle_id/report_id
- If they are truly cycle/report level data (not phase-specific), keep current structure

## 🎁 Benefits of Refactoring

1. **Reduced Storage**: Eliminate duplicate foreign key columns
2. **Simplified Queries**: Single join path through phase_id
3. **Data Integrity**: Impossible to have mismatched cycle_id/report_id/phase_id combinations
4. **Cleaner Schema**: Clear hierarchy and relationships
5. **Easier Maintenance**: Single source of truth for relationships

## 🔄 Migration Strategy

1. **Add phase_id columns** to tables that need them
2. **Populate phase_id** based on existing cycle_id/report_id combinations
3. **Update application code** to use phase_id relationships
4. **Add foreign key constraints** for phase_id
5. **Remove redundant columns** (cycle_id, report_id)
6. **Remove old foreign key constraints**

## 🚨 Exceptions (Keep Current Structure)

- **workflow_phases**: Main table that defines the relationship
- **cycle_reports**: Junction table between cycles and reports
- **test_cycles**: Root table

## 📝 Example Migration SQL

```sql
-- Example for cycle_report_data_profiling_rules
-- Step 1: Add phase_id column
ALTER TABLE cycle_report_data_profiling_rules ADD COLUMN phase_id_new UUID;

-- Step 2: Populate phase_id from existing cycle_id/report_id
UPDATE cycle_report_data_profiling_rules 
SET phase_id_new = wp.phase_id
FROM workflow_phases wp
WHERE wp.cycle_id = cycle_report_data_profiling_rules.cycle_id 
    AND wp.report_id = cycle_report_data_profiling_rules.report_id
    AND wp.phase_name = 'Data Profiling';  -- or appropriate phase

-- Step 3: Add foreign key constraint
ALTER TABLE cycle_report_data_profiling_rules 
ADD CONSTRAINT fk_data_profiling_rules_phase 
FOREIGN KEY (phase_id_new) REFERENCES workflow_phases(phase_id);

-- Step 4: Remove old columns (after code update)
ALTER TABLE cycle_report_data_profiling_rules 
DROP COLUMN cycle_id,
DROP COLUMN report_id,
RENAME COLUMN phase_id_new TO phase_id;
```

This refactoring will significantly improve the database schema's clarity and efficiency while maintaining all necessary relationships.