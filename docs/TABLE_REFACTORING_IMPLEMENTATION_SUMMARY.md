# Table Refactoring Implementation Summary

## What We've Accomplished

### 1. Analysis Phase ✅
- Created `analyze_table_dependencies.py` that found:
  - 52 tables to rename
  - 10 tables to remove
  - 23,365 total references (includes many false positives)
  - 102 foreign key references
  - 872 relationship references

### 2. Scripts Created ✅

#### Core Scripts:
1. **`analyze_table_dependencies.py`**
   - Analyzes all table dependencies
   - Generates comprehensive JSON report
   - Identifies foreign keys, relationships, string references

2. **`rename_single_table.py`**
   - Renames one table at a time
   - Updates model __tablename__
   - Updates all ForeignKey references
   - Creates migration script
   - Generates change report

3. **`remove_deprecated_tables.py`**
   - Removes tables that should use universal frameworks
   - Comments out model definitions
   - Comments out foreign key references
   - Creates drop table migrations

4. **`table_refactoring_master.py`**
   - Master coordinator for entire process
   - Executes refactoring in phases
   - Creates backups
   - Runs tests after each phase
   - Generates logs

5. **`validate_before_refactoring.py`**
   - Pre-flight validation checks
   - Verifies all tables exist
   - Checks for naming conflicts
   - Tests API endpoints
   - Generates validation report

#### SQL Scripts:
1. **`create_new_tables.sql`**
   - Creates `cycle_report_request_info_document_versions`
   - Creates `cycle_report_observation_mgmt_preliminary_findings`
   - Creates `_table_refactoring_log` for tracking

### 3. Documentation Created ✅
- `TABLE_NAMING_STANDARDIZATION.md` - Initial plan
- `TABLE_NAMING_CHANGES.md` - Current vs Proposed mapping
- `TABLE_NAMING_REVIEW_RESPONSES.md` - Responses to feedback
- `TABLE_REFACTORING_PLAN.md` - First principles approach
- `TABLE_REFACTORING_PHASED_APPROACH.md` - Practical phased plan

## Next Steps

### Immediate Actions:
1. **Run Validation**
   ```bash
   python scripts/validate_before_refactoring.py
   ```

2. **Start Phase 1 - Remove Deprecated Tables**
   ```bash
   python scripts/table_refactoring_master.py --phases phase1_remove_deprecated
   ```

3. **Monitor and Test**
   - Check application still works
   - Run test suite
   - Monitor for errors

### Phase Execution Order:
1. **Phase 1**: Remove deprecated tables (lowest risk)
2. **Phase 2**: Create new required tables
3. **Phase 3**: Planning phase tables
4. **Phase 4**: Scoping phase tables
5. **Phase 5**: Data profiling phase tables
6. **Phase 6**: Data owner phase tables
7. **Phase 7**: Sample selection phase tables
8. **Phase 8**: Request info phase tables
9. **Phase 9**: Test execution phase tables
10. **Phase 10**: Observation management phase tables
11. **Phase 11**: Test report phase tables

## Key Decisions Made

1. **Use Universal Frameworks**
   - Remove all phase-specific status tables
   - Use universal SLA, escalation, assignments

2. **Naming Convention**
   - Pattern: `cycle_report_<phase>_<entity/action>`
   - Consistent across all phases

3. **New Tables Added**
   - Document versioning for re-uploads
   - Preliminary findings for observations

4. **Phased Approach**
   - Too risky to do all at once
   - Phase by phase minimizes risk
   - Each phase can be rolled back

## Risk Mitigation

1. **Backup Strategy**
   - Database backup before each phase
   - Git branch for code changes
   - Rollback scripts generated

2. **Testing Strategy**
   - Run tests after each phase
   - Validate API endpoints
   - Check foreign key integrity

3. **Monitoring**
   - Log all changes
   - Track files modified
   - Generate reports

## Commands to Execute

```bash
# 1. First, validate current state
python scripts/validate_before_refactoring.py

# 2. If validation passes, start with Phase 1
python scripts/table_refactoring_master.py --phases phase1_remove_deprecated

# 3. To rename a single table (for testing)
python scripts/rename_single_table.py \
  --old-name "pde_mapping_approval_rules" \
  --new-name "cycle_report_planning_pde_mapping_approval_rules"

# 4. To see what would happen (dry run)
python scripts/table_refactoring_master.py --dry-run

# 5. To remove a single deprecated table
python scripts/remove_deprecated_tables.py --table data_profiling_phases

# 6. To execute specific phases
python scripts/table_refactoring_master.py --phases phase3_planning phase4_scoping
```

## Important Notes

1. **High-Risk Tables**
   - `samples` - 3,562 dependencies
   - `data_owner_assignments` - 1,187 dependencies
   - Handle these carefully, possibly with compatibility views

2. **Coordination Required**
   - Work with universal assignments migration
   - Ensure no conflicts with other ongoing work

3. **Performance Considerations**
   - Large tables may take time to rename
   - Consider off-hours execution
   - Monitor database performance

## Success Criteria

- ✅ All tables follow naming convention
- ✅ No duplicate functionality
- ✅ All tests pass
- ✅ No performance degradation
- ✅ Clean rollback possible

## Estimated Timeline

- Week 1: Remove deprecated tables, create new tables
- Week 2-3: Rename planning and scoping tables
- Week 4-5: Rename data profiling and data owner tables
- Week 6-7: Rename sample selection and request info tables
- Week 8-9: Rename test execution and observation tables
- Week 10: Final validation and cleanup

This is a major undertaking but with the scripts and phased approach, it can be executed safely and systematically.