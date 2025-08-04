# Table Refactoring - Phased Implementation Approach

## Reality Check
- **52 tables to rename**
- **10 tables to remove**  
- **102 foreign key references**
- **872 relationship references**
- **22,365 string references** (includes false positives)
- **100 migration references**

This is too large to do in one go. We need a phased approach.

## Revised Strategy: Phase by Phase Implementation

### Phase 1: Remove Deprecated Tables (Lowest Risk)
Start by removing tables that should use universal frameworks:

#### 1.1 Remove Phase Status Tables
These have the least dependencies and clear replacement (universal status):
- `data_profiling_phases`
- `sample_selection_phases`
- `test_execution_phases`
- `observation_management_phases`
- `test_report_phases`
- `cycle_report_request_info_phases`

#### 1.2 Remove Sample Set Tables
- `cycle_report_sample_sets`
- Update all references to remove sample_set_id

#### 1.3 Remove Data Owner Redundant Tables
- `data_owner_sla_violations` (use universal SLA)
- `data_owner_escalation_log` (use universal escalation)
- `data_owner_notifications` (use universal assignments)

### Phase 2: Create New Tables
Before renaming, create the new tables we need:
- `cycle_report_request_info_document_versions`
- `cycle_report_observation_mgmt_preliminary_findings`

### Phase 3: Rename by Workflow Phase (One Phase at a Time)

#### 3.1 Start with Planning Phase (Critical Path)
Tables with most dependencies first:
1. `cycle_report_attributes_planning` → `cycle_report_planning_attributes`
2. Move PDE tables from data_profiling to planning
3. Update all related tables

#### 3.2 Data Owner Phase
High dependency tables:
1. `data_owner_assignments` (1,187 dependencies)
2. Related tables

#### 3.3 Test Execution Phase  
1. `samples` (3,562 dependencies!)
2. Related tables

#### 3.4 Continue with Other Phases
In order of dependency count

## Implementation Plan for Each Table

### Step 1: Create Migration Script Template
```python
def rename_table_safely(old_name: str, new_name: str):
    """
    1. Create new table with new name (copy structure)
    2. Copy all data
    3. Update all foreign keys
    4. Update all indexes
    5. Drop old table
    """
```

### Step 2: Update Models Script
```python
def update_model_references(old_name: str, new_name: str):
    """
    1. Update __tablename__
    2. Update ForeignKey references
    3. Update relationship back_populates
    4. Update any string references
    """
```

### Step 3: Testing Protocol
1. Test on single table first
2. Verify all relationships work
3. Run full test suite
4. Check performance

## Immediate First Steps

### 1. Create Helper Scripts
```bash
# Script to update a single table and all its references
python scripts/rename_single_table.py --old-name "table_name" --new-name "new_table_name"
```

### 2. Start with Least Dependent Table
Find table with fewest dependencies to test process:
- Good candidate: `pde_mapping_approval_rules` (likely few dependencies)

### 3. Create Rollback Scripts
For each change, create immediate rollback

## Risk Mitigation for High-Dependency Tables

### For `samples` table (3,562 dependencies):
1. Create detailed dependency map
2. Consider creating a view with old name during transition
3. Update in smaller batches

### For `data_owner_assignments` (1,187 dependencies):
1. Coordinate with universal assignments migration
2. May need compatibility layer

## Recommended Order of Implementation

### Week 1: Foundation
1. Remove deprecated tables (phase status, sample sets)
2. Create new required tables
3. Test migration scripts on low-dependency tables

### Week 2: Planning Phase
1. Rename planning tables
2. Move PDE tables to planning
3. Full testing

### Week 3: Data Profiling & Scoping
1. Rename data profiling tables
2. Rename scoping tables
3. Full testing

### Week 4: High-Dependency Phases
1. Data owner tables (coordinate with universal)
2. Sample selection tables
3. Request info tables

### Week 5: Test Execution & Observation
1. Test execution tables (especially `samples`)
2. Observation management tables
3. Move observation tables from test report

### Week 6: Cleanup & Verification
1. Final cleanup
2. Performance testing
3. Documentation update

## Success Metrics
1. Zero downtime during migration
2. All tests pass after each phase
3. No performance degradation
4. Clean rollback possible at each step

## Next Immediate Action
1. Create the `rename_single_table.py` script
2. Test on `pde_mapping_approval_rules`
3. Validate the approach before proceeding