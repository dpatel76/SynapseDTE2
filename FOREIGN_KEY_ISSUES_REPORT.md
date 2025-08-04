# Foreign Key Issues Report for Refactored Tables

## Summary

This report identifies all foreign key reference issues across the refactored `cycle_report_*` tables in the codebase.

## Identified Refactored Tables

Based on the SQL schema analysis, the following `cycle_report_*` tables have been identified:

1. **cycle_report_attributes_planning** (Primary Key: `id`)
2. **cycle_report_attributes_planning_version_history** (Primary Key: `id`)
3. **cycle_report_data_profiling** (Primary Key: `id`)
4. **cycle_report_profiling_results** (Primary Key: `id`)
5. **cycle_report_attributes_scoping** (Primary Key: `id`)
6. **cycle_report_attributes_scoping_version_history** (Primary Key: `id`)
7. **cycle_report_sample_selection** (Primary Key: `id`)
8. **cycle_report_samples** (Primary Key: `id`)
9. **cycle_report_data_owners** (Primary Key: `id`)
10. **cycle_report_test_cases** (Primary Key: `id`)
11. **cycle_report_document_submissions** (Primary Key: `id`)
12. **cycle_report_test_execution** (Primary Key: `id`)
13. **cycle_report_test_failures** (Primary Key: `id`)
14. **cycle_report_observations** (Primary Key: `id`)
15. **cycle_report_observation_failures** (Primary Key: `id`)
16. **cycle_report_final** (Primary Key: `id`)

## Foreign Key Issues Found

### 1. **cycle_report_attributes_planning_version_history** Table

**Issue**: The table has a column `planning_attribute_id` that should reference `cycle_report_attributes_planning.id`, but no foreign key constraint is defined in the SQL schema.

**Locations**:
- `/app/models/cycle_report_planning.py:120` - Defines `planning_attribute_id` column without foreign key
- SQL schema files define the column but missing the foreign key constraint

### 2. **Python Models Using Non-Standard Primary Keys**

Several Python models reference tables using non-standard primary key names:

**cycle_report_test_cases**:
- Models reference it with `test_case_id` instead of `id`
- Found in:
  - `/app/models/request_info.py:203` - `ForeignKey('cycle_report_test_cases.test_case_id')`
  - `/app/models/observation_enhanced.py:42` - `ForeignKey('cycle_report_test_cases.test_case_id')`
  - `/app/models/observation_enhanced.py:137` - `ForeignKey('cycle_report_test_cases.test_case_id')`

**cycle_report_test_executions**:
- Models reference it with `execution_id` instead of `id`
- Found in:
  - `/app/models/versioning_clean.py:309` - `ForeignKey('cycle_report_test_executions.execution_id')`
  - `/app/models/test_execution.py:234` - `ForeignKey('cycle_report_test_executions.execution_id')`
  - `/app/models/observation_enhanced.py:136` - `ForeignKey('cycle_report_test_executions.execution_id')`
  - `/app/models/versioning_complete.py:426` - `ForeignKey('cycle_report_test_executions.execution_id')`
  - `/app/models/observation_management.py:130` - `ForeignKey('cycle_report_test_executions.execution_id')`
  - `/app/models/versioning.py:307` - `ForeignKey('cycle_report_test_executions.execution_id')`

**cycle_report_sample_sets**:
- Models reference it with `set_id` instead of `id`
- Found in multiple places in `/app/models/sample_selection.py`

**cycle_report_sample_records**:
- Models reference it with `record_id` instead of `id`
- Found in:
  - `/app/models/sample_selection.py:213` - `ForeignKey('cycle_report_sample_records.record_id')`
  - `/app/models/observation_enhanced.py:138` - `ForeignKey('cycle_report_sample_records.record_id')`

**cycle_report_observations**:
- Models reference it with `observation_id` instead of `id`
- Found in:
  - `/app/models/versioning_complete.py:492` - `ForeignKey('cycle_report_observations.observation_id')`

**cycle_report_request_info_phases**:
- Models reference it with `phase_id` instead of `id`
- Found in:
  - `/app/models/request_info.py:112` - `ForeignKey('cycle_report_request_info_phases.phase_id')`
  - `/app/models/request_info.py:162` - `ForeignKey('cycle_report_request_info_phases.phase_id')`
  - `/app/models/request_info.py:253` - `ForeignKey('cycle_report_request_info_phases.phase_id')`

**cycle_report_scoping_submissions**:
- Models reference it with `submission_id` instead of `id`
- Found in:
  - `/app/models/scoping.py:113` - `ForeignKey('cycle_report_scoping_submissions.submission_id')`
  - `/app/models/scoping.py:144` - `ForeignKey('cycle_report_scoping_submissions.submission_id')`

### 3. **Correct Foreign Key References**

The following foreign key references are **correct** (using `id` as expected):

- All references to `cycle_report_attributes_planning.id` in various models
- SQL schema foreign key definitions for tables like:
  - `cycle_report_profiling_results` → `cycle_report_data_profiling(id)`
  - `cycle_report_profiling_results` → `cycle_report_attributes_planning(id)`
  - `cycle_report_attributes_scoping` → `cycle_report_attributes_planning(id)`
  - `cycle_report_samples` → `cycle_report_sample_selection(id)`
  - `cycle_report_data_owners` → `cycle_report_attributes_planning(id)`
  - `cycle_report_test_execution` → `cycle_report_test_cases(id)`
  - `cycle_report_test_failures` → `cycle_report_test_execution(id)`
  - `cycle_report_observation_failures` → `cycle_report_observations(id)`
  - `cycle_report_observation_failures` → `cycle_report_test_failures(id)`

### 4. **SQL Query Issues**

Several SQL queries in `/app/services/test_report_service.py` correctly join on `id`:
- Line 895: `JOIN cycle_report_attributes_planning ra ON pr.attribute_id = ra.id`
- Line 915: `JOIN cycle_report_attributes_planning ra ON pr.attribute_id = ra.id`
- Line 938: `JOIN cycle_report_attributes_planning ra ON pr.attribute_id = ra.id`
- Line 1151: `LEFT JOIN cycle_report_attributes_planning ra ON tc.attribute_id = ra.id`
- Line 1201: `LEFT JOIN cycle_report_attributes_planning ra ON te.attribute_id = ra.id`
- Line 1259: `LEFT JOIN cycle_report_attributes_planning ra ON og.attribute_id = ra.id`

These queries appear to be **correct**.

## Recommendations

1. **Verify Table Primary Keys**: Check if tables like `cycle_report_test_cases`, `cycle_report_test_executions`, etc., actually use custom primary key names (`test_case_id`, `execution_id`) instead of `id`. If they use `id`, update all foreign key references.

2. **Add Missing Foreign Key Constraint**: Add the foreign key constraint for `planning_attribute_id` in `cycle_report_attributes_planning_version_history`.

3. **Standardize Primary Key Names**: Consider using consistent `id` naming for all primary keys to avoid confusion.

4. **Update Python Models**: Update all incorrect foreign key references in Python models to use the correct primary key column names.

5. **Create Migration Scripts**: Create migration scripts to fix any incorrect foreign key constraints in the database.

## Action Items

- [ ] Verify actual primary key column names in the database for all `cycle_report_*` tables
- [ ] Update Python models with correct foreign key references
- [ ] Create and run migration scripts to fix database constraints
- [ ] Update any affected SQL queries
- [ ] Test all affected functionality after fixes