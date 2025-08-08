# Phase 3: Code Hygiene and Cleanup Plan

## Overview
This phase focuses on cleaning up the codebase after the major refactoring and migration work.

## 3.1 Remove Version Suffixes (After Stability Confirmed)

### Backend Services
- [ ] `llm_service_v2.py` → `llm_service.py` (after removing old version)
- [ ] `metrics_service_v2.py` → `metrics_service.py` (after removing old version)
- [ ] `activity_state_manager_v2.py` → `activity_state_manager.py`

### API Endpoints
- [ ] `metrics_v2.py` → `metrics.py` (after confirming unified_metrics is working)
- [ ] `cycles_clean_fixed.py` → `cycles.py`
- [ ] `*_clean.py` endpoints → Remove "_clean" suffix after verification

### Frontend Components
- [ ] `DynamicActivityCardsEnhanced.tsx` → `DynamicActivityCards.tsx`
- [ ] `ObservationManagementEnhanced.tsx` → `ObservationManagementPage.tsx`
- [ ] `DataProfilingEnhanced.tsx` → `DataProfilingPage.tsx`
- [ ] Remove all "Redesigned", "Enhanced", "Fixed" suffixes

## 3.2 Documentation Updates

### Update CLAUDE.md
- [ ] Document the universal assignment system
- [ ] Update role names (Data Owner, Data Executive)
- [ ] Document new unified status system
- [ ] Add migration rollback procedures

### Create Architecture Docs
- [ ] Document the 7-phase workflow with new activity system
- [ ] Create universal assignment flow diagram
- [ ] Document notification migration strategy

## 3.3 Code Organization

### Consolidate Duplicate Functionality
- [ ] Merge multiple metrics endpoints into unified_metrics
- [ ] Consolidate dashboard services
- [ ] Remove redundant API endpoints

### Remove Dead Code
- [ ] Remove commented-out code blocks
- [ ] Remove unused imports
- [ ] Clean up test files for removed components

## 3.4 Establish Coding Standards

### Frontend Standards
- [ ] Consistent use of DynamicActivityCards across all phases
- [ ] Remove custom activity rendering from all pages
- [ ] Standardize error handling patterns
- [ ] Consistent TypeScript types usage

### Backend Standards
- [ ] Consistent async/await patterns
- [ ] Standardized error responses
- [ ] Consistent logging patterns
- [ ] Proper type hints throughout

## 3.5 Performance Optimizations

### Database
- [ ] Add missing indexes for universal_assignments
- [ ] Optimize queries in unified_status_service
- [ ] Clean up orphaned records from migrations

### Frontend
- [ ] Implement proper memoization for activity cards
- [ ] Optimize re-renders in phase pages
- [ ] Lazy load heavy components

## 3.6 Testing Updates

### Update Tests
- [ ] Update tests for new role names
- [ ] Add tests for universal assignment system
- [ ] Update workflow tests for new activity system
- [ ] Add integration tests for notification migration

### Remove Obsolete Tests
- [ ] Remove tests for backed-up components
- [ ] Update mocked data to match new schemas

## 3.7 Final Cleanup Tasks

### Environment
- [ ] Update .env.example with new variables
- [ ] Clean up temporary migration scripts
- [ ] Archive backup logs older than 30 days

### Dependencies
- [ ] Review and update requirements.txt
- [ ] Update package.json dependencies
- [ ] Remove unused packages

## Execution Timeline

### Week 1: Stabilization
- Monitor application for issues
- Collect user feedback
- Fix any critical bugs

### Week 2: Version Suffix Removal
- Remove version suffixes from stable components
- Update all imports
- Test thoroughly

### Week 3: Documentation & Standards
- Update all documentation
- Establish and document coding standards
- Create architecture diagrams

### Week 4: Final Cleanup
- Remove dead code
- Optimize performance
- Update tests

## Rollback Procedures

All changes should be reversible:
1. Keep backup copies before removing version suffixes
2. Document all file renames in a tracking log
3. Create git tags before major cleanup operations
4. Maintain rollback scripts for database changes

## Success Criteria

- [ ] No version suffixes in production code
- [ ] All tests passing
- [ ] Documentation up to date
- [ ] No unused imports or dead code
- [ ] Consistent coding patterns throughout
- [ ] Performance metrics improved or maintained