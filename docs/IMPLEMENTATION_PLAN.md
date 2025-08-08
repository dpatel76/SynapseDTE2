# Implementation Plan for Code Cleanup and Migration

## Phase 1: Immediate Actions (Week 1)

### 1.1 Backup Unused Code (Day 1)
**Objective**: Safely rename all identified unused files and obsolete database tables

#### Files to Backup (46 total):

**Frontend Components (14 files):**
- `WorkflowProgressEnhanced.tsx` (original version is used)
- `TesterDashboard.tsx` (replaced by enhanced)
- `TesterDashboardRedesigned.tsx` (enhanced is used)
- `TestExecutiveDashboard.tsx` (replaced by redesigned)
- `TestExecutiveDashboardEnhanced.tsx` (replaced by redesigned)
- `CycleDetailPageFixed.tsx` (original is used)
- `ReportTestingPage.tsx` (replaced by redesigned)
- `ObservationManagementPage.tsx` (replaced by enhanced)
- `MyAssignmentsPage.tsx` (replaced by universal)
- `DynamicActivityCards.tsx` (replaced by enhanced)
- `theme.ts` (replaced by theme-enhanced.ts)
- Previous unused components from corrected analysis

**Backend Services (18 files):**
- `llm_service_v2.py` (v1 is used)
- `benchmarking_service_refactored.py` (original is used)
- `activity_state_manager_v2.py` (check usage)
- `metrics_service_v2.py` (clean version is used)
- `test_report_service_simple_backup.py` (backup file)
- Previous unused services from corrected analysis

**Backend API Endpoints (14 files):**
- `metrics.py` (replaced by metrics_clean.py)
- `metrics_simple.py` (replaced by metrics_clean.py)
- `metrics_v2.py` (replaced by metrics_clean.py)
- `sample_selection_old.py` (old version)
- `lobs_clean.py` (non-clean version is used)
- `sample_selection_clean.py` (non-clean version is used)
- `cycles_clean_fixed.py` (cycles_clean.py is used)
- `test_execution_refactored.py` (clean version is used)
- `testing_execution_clean.py` (not in router)
- `testing_execution_refactored.py` (not in router)
- `workflow_clean.py` (not in router)
- Previous unused endpoints

#### Database Tables to Backup (1 confirmed):
- `observation_records` → `observation_records_backup`

### 1.2 Data Migration (Days 2-3)
**Objective**: Migrate data from obsolete tables to new structures

1. **Observation Records Migration**:
   ```sql
   -- Create migration script to move data from observation_records to observations
   -- Map old complex structure to new simplified structure with observation_groups
   ```

2. **Verify Migration**:
   - Count records in both tables
   - Validate data integrity
   - Test application functionality

### 1.3 Update Import References (Day 4)
**Objective**: Clean up imports to use correct versions

1. **Frontend Updates**:
   - Remove imports of unused components from index files
   - Update any lingering references to old versions

2. **Backend Updates**:
   - Update service imports
   - Clean up API endpoint imports

### 1.4 Testing & Verification (Day 5)
**Objective**: Ensure application still functions correctly

1. Run all automated tests
2. Manual testing of critical workflows
3. Verify all 7 phases work correctly
4. Check dashboard functionality

## Phase 2: Future Migrations (Weeks 2-4)

### 2.1 Complete Universal Assignment Migration
**Objective**: Migrate from phase-specific to universal assignment system

#### Week 2: Planning & Design
1. **Audit Current Usage**:
   - Document all uses of `cdo_notifications`
   - Document all uses of `data_owner_notifications`
   - Map to universal assignment types

2. **Create Migration Strategy**:
   - Design data migration scripts
   - Plan API endpoint updates
   - Design frontend changes

#### Week 3: Implementation
1. **Backend Migration**:
   ```python
   # Migrate CDO notifications to universal assignments
   # Type: 'LOB Assignment'
   
   # Migrate data owner notifications to universal assignments  
   # Type: 'Information Request'
   ```

2. **API Updates**:
   - Update endpoints to use universal assignment service
   - Maintain backward compatibility temporarily

3. **Frontend Updates**:
   - Update notification components
   - Use universal assignment APIs

#### Week 4: Testing & Rollout
1. Run parallel systems for verification
2. Complete data migration
3. Deprecate old notification tables
4. Update documentation

### 2.2 Consolidate Workflow Systems
**Objective**: Complete transition to unified workflow system

1. **Fix Circular Imports**:
   - Resolve issues with workflow_management.py
   - Resolve issues with workflow_versioning.py
   - Resolve issues with workflow_compensation.py

2. **Enable Workflow Endpoints**:
   - Uncomment disabled routers in api.py
   - Test workflow functionality

3. **Remove Legacy Workflow Code**:
   - Identify obsolete workflow implementations
   - Migrate to new workflow activity system

## Phase 3: Code Hygiene (Ongoing)

### 3.1 Remove Version Suffixes (Month 2)
**Objective**: Clean up naming once old versions are removed

1. **Rename Enhanced Components**:
   ```bash
   # After verifying old versions are gone
   mv DynamicActivityCardsEnhanced.tsx DynamicActivityCards.tsx
   mv ObservationManagementEnhanced.tsx ObservationManagement.tsx
   mv theme-enhanced.ts theme.ts
   ```

2. **Update Clean API Endpoints**:
   ```bash
   # Remove _clean suffix from actively used endpoints
   mv auth_clean.py auth.py
   mv users_clean.py users.py
   # etc...
   ```

3. **Update All Import References**:
   - Use find/replace across codebase
   - Update import statements
   - Test thoroughly

### 3.2 Documentation Updates (Month 2)
**Objective**: Keep documentation in sync with changes

1. **Update API Documentation**:
   - Remove references to deprecated endpoints
   - Document new universal systems

2. **Update Development Guides**:
   - Update CLAUDE.md with new patterns
   - Document universal assignment usage
   - Document workflow activity system

3. **Migration Guides**:
   - Create guide for universal assignments
   - Document data migration procedures

### 3.3 Establish Coding Standards (Month 3)
**Objective**: Prevent future accumulation of unused code

1. **Version Control Practices**:
   - Don't create "Enhanced" versions alongside originals
   - Use feature branches for major refactors
   - Clean up old versions immediately after migration

2. **Code Review Guidelines**:
   - Check for unused imports
   - Verify removal of old versions
   - Ensure consistent naming

3. **Automated Checks**:
   ```yaml
   # Add to CI/CD pipeline
   - name: Check for unused code
     run: |
       # Script to detect unused imports
       # Script to find orphaned files
       # Script to check for evolution patterns
   ```

## Implementation Timeline

### Month 1:
- Week 1: Immediate Actions (backup, migrate, test)
- Weeks 2-4: Universal Assignment Migration

### Month 2:
- Week 1-2: Workflow System Consolidation
- Week 3-4: Remove Version Suffixes

### Month 3:
- Documentation Updates
- Establish Coding Standards
- Set up Automated Checks

## Risk Mitigation

### Backup Strategy:
- All changes are reversible via restore scripts
- Keep backups for 90 days minimum
- Document all changes in git commits

### Testing Strategy:
- Automated test suite must pass
- Manual testing of all 7 phases
- User acceptance testing for critical workflows

### Rollback Plan:
- Restore scripts ready for immediate use
- Database backups before migrations
- Feature flags for gradual rollout

## Success Metrics

1. **Code Reduction**:
   - Target: Remove 50+ unused files
   - Reduce codebase by ~10%

2. **System Simplification**:
   - Consolidate to universal systems
   - Reduce duplicate implementations

3. **Developer Experience**:
   - Faster navigation
   - Clearer code structure
   - Reduced confusion

4. **Performance**:
   - Smaller bundle sizes
   - Faster build times
   - Improved load times

## Next Steps

1. Review and approve this plan
2. Schedule implementation phases
3. Assign team members to tasks
4. Set up tracking for progress
5. Create communication plan for changes