# Data Profiling Database Schema Comparison

## Overview

This document provides a detailed comparison between the **old data profiling tables** and the **new unified data profiling architecture**.

## Table Architecture Changes

### Old Architecture (23+ tables)
- Multiple separate tables for different aspects of data profiling
- Direct cycle_id and report_id references
- Separate phases, files, rules, results, and scores tables

### New Architecture (2 main tables + supporting tables)
- Unified 2-table pattern matching sample selection and scoping
- Phase-based integration using phase_id
- Version management with parent-child relationships
- Background job execution tracking

## Detailed Table Comparison

### 1. Phase Management Tables

#### Old: `data_profiling_phases`
```sql
Table: data_profiling_phases
- phase_id (Integer, PK)
- cycle_id (Integer, FK → test_cycles.cycle_id)
- report_id (Integer, FK → reports.report_id)
- status (String)
- data_requested_at (DateTime)
- data_received_at (DateTime)
- rules_generated_at (DateTime)
- profiling_executed_at (DateTime)
- phase_completed_at (DateTime)
- started_by (Integer, FK → users.user_id)
- data_requested_by (Integer, FK → users.user_id)
- completed_by (Integer, FK → users.user_id)
- created_at, updated_at, created_by, updated_by
```

#### New: Integrated into `workflow_phases`
- No separate phase table needed
- Phase management handled by universal workflow system
- Status tracking via workflow_activities

### 2. Rule Management Tables

#### Old: `profiling_rules`
```sql
Table: profiling_rules
- rule_id (Integer, PK)
- phase_id (Integer, FK → data_profiling_phases.phase_id)
- attribute_id (Integer, FK → report_attributes.attribute_id)
- rule_name (String)
- rule_type (ENUM: completeness, validity, accuracy, consistency, uniqueness, timeliness, regulatory)
- rule_description (Text)
- rule_code (Text)
- rule_parameters (JSON)
- llm_provider (String)
- llm_rationale (Text)
- regulatory_reference (Text)
- status (ENUM: pending, approved, rejected)
- approved_by (Integer, FK → users.user_id)
- approved_at (DateTime)
- approval_notes (Text)
- is_executable (Boolean)
- execution_order (Integer)
- created_at, updated_at, created_by, updated_by
```

#### New: `cycle_report_data_profiling_rule_versions` + `cycle_report_data_profiling_rules`

**Version Table:**
```sql
Table: cycle_report_data_profiling_rule_versions
- version_id (UUID, PK)
- phase_id (Integer, FK → workflow_phases.phase_id)  # Changed from cycle_id/report_id
- workflow_activity_id (Integer, FK → workflow_activities.activity_id)
- version_number (Integer)
- version_status (ENUM: draft, pending_approval, approved, rejected, superseded)
- parent_version_id (UUID, FK → self)
- workflow_execution_id (String)
- workflow_run_id (String)
- total_rules (Integer)
- approved_rules (Integer)
- rejected_rules (Integer)
- data_source_type (ENUM: file_upload, database_source)
- planning_data_source_id (Integer)
- source_table_name (String)
- source_file_path (String)
- total_records_processed (Integer)
- overall_quality_score (DECIMAL)
- execution_job_id (String)
- submitted_by_id, submitted_at, approved_by_id, approved_at
- rejection_reason (Text)
- created_at, created_by_id, updated_at, updated_by_id
```

**Rules Table:**
```sql
Table: cycle_report_data_profiling_rules
- rule_id (UUID, PK)
- version_id (UUID, FK → cycle_report_data_profiling_rule_versions.version_id)
- phase_id (Integer, FK → workflow_phases.phase_id)
- attribute_id (UUID, FK → cycle_report_planning_attributes.id)  # Changed from Integer
- rule_name (String)
- rule_type (ENUM: completeness, validity, accuracy, consistency, uniqueness)  # Removed timeliness, regulatory
- rule_description (Text)
- rule_code (Text)
- rule_parameters (JSONB)
- llm_provider (String)
- llm_rationale (Text)
- llm_confidence_score (DECIMAL)  # New field
- regulatory_reference (Text)
- is_executable (Boolean)
- execution_order (Integer)
- severity (ENUM: low, medium, high)  # New field
- tester_decision (ENUM: approve, reject, request_changes)  # New dual decision model
- tester_decided_by (Integer, FK → users.user_id)
- tester_decided_at (DateTime)
- tester_notes (Text)
- report_owner_decision (ENUM: approve, reject, request_changes)  # New
- report_owner_decided_by (Integer, FK → users.user_id)
- report_owner_decided_at (DateTime)
- report_owner_notes (Text)
- status (ENUM: pending, submitted, approved, rejected)  # Added 'submitted'
- created_at, created_by_id, updated_at, updated_by_id
```

### 3. File Management Tables

#### Old: `data_profiling_files`
```sql
Table: data_profiling_files
- file_id (Integer, PK)
- phase_id (Integer, FK → data_profiling_phases.phase_id)
- file_name (String)
- file_path (Text)
- file_size (Integer)
- file_format (String)
- delimiter (String)
- row_count (Integer)
- column_count (Integer)
- columns_metadata (JSON)
- is_validated (Boolean)
- validation_errors (JSON)
- missing_attributes (JSON)
- uploaded_by (Integer, FK → users.user_id)
- uploaded_at (DateTime)
- created_at, updated_at, created_by, updated_by
```

#### New: `cycle_report_data_profiling_uploads`
```sql
Table: cycle_report_data_profiling_uploads
- id (Integer, PK)
- phase_id (Integer, FK → workflow_phases.phase_id)  # Simplified relationship
- file_name (String)
- file_path (Text)
- file_size (Integer)
- upload_status (String)  # Simplified from multiple validation fields
- created_at, created_by_id, updated_at, updated_by_id
```

### 4. Execution Results Tables

#### Old: `profiling_results`
```sql
Table: profiling_results
- result_id (Integer, PK)
- phase_id (Integer, FK → data_profiling_phases.phase_id)
- rule_id (Integer, FK → profiling_rules.rule_id)
- attribute_id (Integer, FK → report_attributes.attribute_id)
- execution_status (String)
- execution_time_ms (Integer)
- executed_at (DateTime)
- passed_count (Integer)
- failed_count (Integer)
- total_count (Integer)
- pass_rate (Float)
- result_summary (JSON)
- failed_records (JSON)
- result_details (Text)
- quality_impact (Float)
- severity (String)
- has_anomaly (Boolean)
- anomaly_description (Text)
- anomaly_marked_by (Integer, FK → users.user_id)
- anomaly_marked_at (DateTime)
- created_at, updated_at, created_by, updated_by
```

#### New: Results tracked via background job system
- No direct results table in the unified architecture
- Execution tracked through `cycle_report_data_profiling_jobs`
- Detailed results in `cycle_report_data_profiling_attribute_results`

### 5. Scoring Tables

#### Old: `attribute_profiling_scores`
```sql
Table: attribute_profiling_scores
- score_id (Integer, PK)
- phase_id (Integer, FK → data_profiling_phases.phase_id)
- attribute_id (Integer, FK → report_attributes.attribute_id)
- overall_quality_score (Float)
- completeness_score (Float)
- validity_score (Float)
- accuracy_score (Float)
- consistency_score (Float)
- uniqueness_score (Float)
- total_rules_executed (Integer)
- rules_passed (Integer)
- rules_failed (Integer)
- total_values (Integer)
- null_count (Integer)
- unique_count (Integer)
- data_type_detected (String)
- pattern_detected (String)
- distribution_type (String)
- has_anomalies (Boolean)
- anomaly_count (Integer)
- anomaly_types (JSON)
- testing_recommendation (Text)
- risk_assessment (Text)
- calculated_at (DateTime)
- created_at, updated_at, created_by, updated_by
```

#### New: `cycle_report_data_profiling_attribute_results`
```sql
Table: cycle_report_data_profiling_attribute_results
- id (Integer, PK)
- profiling_job_id (Integer, FK → cycle_report_data_profiling_jobs.id)
- attribute_id (UUID, FK → cycle_report_planning_attributes.id)
- attribute_name (String)
- total_values (BigInteger)
- null_count (BigInteger)
- null_percentage (Float)
- distinct_count (BigInteger)
- distinct_percentage (Float)
- detected_data_type (String)
- type_consistency (Float)
- min_value, max_value, mean_value, median_value, std_deviation (Float)
- percentile_25, percentile_75 (Float)
- min_length, max_length (Integer)
- avg_length (Float)
- common_patterns (JSONB)
- pattern_coverage (Float)
- top_values (JSONB)
- value_distribution (JSONB)
- completeness_score, validity_score, consistency_score, uniqueness_score (Float)
- overall_quality_score (Float)
- anomaly_count (Integer)
- anomaly_examples (JSONB)
- anomaly_rules_triggered (JSONB)
- outliers_detected (Integer)
- outlier_examples (JSONB)
- profiling_duration_ms (Integer)
- sampling_applied (Boolean)
- sample_size_used (Integer)
- created_at, created_by_id, updated_at, updated_by_id
```

## Key Differences Summary

### 1. **Architecture Pattern**
- **Old**: Multiple interconnected tables with direct relationships
- **New**: Unified 2-table pattern with version management

### 2. **Primary Keys**
- **Old**: Integer-based primary keys
- **New**: UUID-based primary keys for version and rule tables

### 3. **Foreign Key Relationships**
- **Old**: Direct cycle_id and report_id references
- **New**: Single phase_id reference to workflow_phases

### 4. **Approval Workflow**
- **Old**: Single approver model
- **New**: Dual decision model (tester + report owner)

### 5. **Version Management**
- **Old**: No versioning support
- **New**: Full version lifecycle (draft → pending → approved/rejected → superseded)

### 6. **Execution Tracking**
- **Old**: Results stored directly in profiling_results table
- **New**: Background job system with separate job and result tables

### 7. **Data Types**
- **Old**: Mixed use of JSON and specific columns
- **New**: JSONB for complex data, more structured approach

### 8. **Audit Fields**
- **Old**: String-based created_by/updated_by
- **New**: Integer FK references to users table

### 9. **Status Enums**
- **Old**: Simple pending/approved/rejected
- **New**: Extended status options with submission state

### 10. **LLM Integration**
- **Old**: Basic LLM provider and rationale
- **New**: Added LLM confidence score for better tracking

## Migration Considerations

1. **Data Migration**: Need to map old integer PKs to new UUIDs
2. **Phase Mapping**: Convert cycle_id/report_id pairs to phase_id
3. **Approval Model**: Migrate single approvals to dual decision model
4. **Status Mapping**: Map old status values to new extended options
5. **Execution Results**: Move from direct storage to job-based tracking