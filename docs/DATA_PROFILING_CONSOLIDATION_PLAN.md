# Data Profiling Endpoint Consolidation Plan

## Overview
Data profiling endpoints are currently spread across 4 files with significant redundancy. This plan outlines consolidation into a single, well-organized module.

## Current State Analysis

### File Structure Problems
1. **data_profiling.py** (1,871 lines) - Main file
2. **data_profiling_rules.py** (741 lines) - Rule-specific operations
3. **data_profiling_assignments.py** (564 lines) - Assignment operations  
4. **data_profiling_resubmit.py** (761 lines) - Duplicate resubmit functionality

Total: ~3,937 lines across 4 files

### Major Redundancies Identified

#### 1. Resubmit After Feedback
- **Exact duplicate** in `data_profiling.py` and `data_profiling_resubmit.py`
- Same functionality, same code, different files

#### 2. Rule Approval/Rejection
- `data_profiling_rules.py`: `/rules/{rule_id}/tester-decision` and `/rules/{rule_id}/report-owner-decision`
- `data_profiling.py`: Generic approve/reject in bulk operations
- Different patterns for same functionality

#### 3. Status Endpoints
- `/status` - Basic status
- `/comprehensive-status` - Detailed status
- Multiple endpoints returning overlapping information

#### 4. Execution Endpoints
- Version-based execution in main file
- Job-based execution across files
- Different approaches to same goal

## Consolidation Strategy

### Phase 1: File Consolidation

**Target**: Single `data_profiling.py` file with clear sections

```python
# data_profiling.py structure:
# 1. Core Status & Version Management (lines 1-500)
# 2. Rule Generation & Management (lines 501-1000)  
# 3. Execution & Jobs (lines 1001-1500)
# 4. Decisions & Approvals (lines 1501-2000)
# 5. Assignments (lines 2001-2500)
```

### Phase 2: Endpoint Consolidation

#### 1. Unify Decision Endpoints
**Current**: Multiple endpoints for decisions
**Target**: Single decision endpoint with role detection

```python
@router.post("/rules/{rule_id}/decision")
async def update_rule_decision(
    rule_id: str,
    decision_data: RuleDecisionRequest,
    current_user: User = Depends(get_current_user)
):
    # Automatically determine if tester or report owner based on user role
    if current_user.role in tester_roles:
        return await _update_tester_decision(...)
    elif current_user.role in report_owner_roles:
        return await _update_report_owner_decision(...)
```

#### 2. Merge Status Endpoints
**Current**: 3 different status endpoints
**Target**: 1 comprehensive status endpoint with query parameters

```python
@router.get("/cycles/{cycle_id}/reports/{report_id}/status")
async def get_profiling_status(
    cycle_id: int,
    report_id: int,
    detail_level: str = Query("basic", enum=["basic", "summary", "comprehensive"]),
    ...
):
    # Return appropriate level of detail based on parameter
```

#### 3. Single Execution Approach
**Keep**: Version-based execution (more complete)
**Remove**: Standalone job execution endpoints

### Phase 3: Remove Redundant Files

1. **Delete `data_profiling_resubmit.py`**: 
   - Completely redundant with main file
   - No unique functionality

2. **Merge `data_profiling_rules.py`**:
   - Move unique rule operations to main file
   - Remove duplicate decision endpoints

3. **Keep `data_profiling_assignments.py`**:
   - Has unique assignment functionality
   - Consider renaming to `data_profiling_universal_assignments.py` for clarity

## Migration Implementation

### Step 1: Create Consolidated Structure
```python
# New section markers in data_profiling.py
# ============= Core Endpoints =============
# Status, versions, phase management

# ============= Rule Management =============
# Generation, updates, retrievals

# ============= Execution =============
# Running rules, job management

# ============= Decisions & Approvals =============
# All approval flows

# ============= Assignments =============
# Universal assignment integration
```

### Step 2: Move Endpoints with Adapters
```python
# Temporary adapters for backward compatibility
@router.post("/rules/{rule_id}/tester-decision", deprecated=True)
async def legacy_tester_decision(...):
    """Deprecated: Use /rules/{rule_id}/decision instead"""
    return await update_rule_decision(...)
```

### Step 3: Update References
1. Search codebase for endpoint usage
2. Update service classes
3. Update frontend API calls
4. Update documentation

## Endpoints to Keep vs Remove

### Keep (Consolidated):
1. `/cycles/{cycle_id}/reports/{report_id}/status` - Unified status
2. `/cycles/{cycle_id}/reports/{report_id}/versions` - List versions
3. `/cycles/{cycle_id}/reports/{report_id}/generate-rules` - Generate rules
4. `/versions/{version_id}/execute` - Execute profiling
5. `/versions/{version_id}/submit` - Submit for approval
6. `/versions/{version_id}/approve` - Approve version
7. `/rules/{rule_id}/decision` - Update any decision
8. `/rules/bulk-operations` - All bulk operations
9. `/cycles/{cycle_id}/reports/{report_id}/resubmit-after-feedback` - Make changes

### Remove (Redundant):
1. All endpoints in `data_profiling_resubmit.py`
2. `/rules/{rule_id}/tester-decision` - Use unified decision
3. `/rules/{rule_id}/report-owner-decision` - Use unified decision  
4. `/comprehensive-status` - Use status with parameters
5. `/check-and-approve-version` - Redundant with standard flow
6. Duplicate bulk operations across files

## Benefits

1. **Code Reduction**: ~40% less code (from 3,937 to ~2,400 lines)
2. **Single Source of Truth**: All data profiling in one file
3. **Consistent Patterns**: Unified approach to decisions and approvals
4. **Easier Maintenance**: No need to check multiple files
5. **Better Organization**: Clear sections for different functionality

## Implementation Steps

### Week 1: Analysis and Preparation
- Map all endpoint usage in frontend
- Identify service dependencies
- Create detailed migration checklist

### Week 2: Create Consolidated File
- Set up new structure in main file
- Add section markers
- Implement adapter functions

### Week 3: Migrate Endpoints
- Move endpoints one section at a time
- Test each migration
- Update service references

### Week 4: Frontend Updates
- Update API calls to new endpoints
- Test all workflows
- Fix any issues

### Week 5: Cleanup
- Remove deprecated files
- Remove adapter functions
- Final testing

## Risk Mitigation

1. **Gradual Migration**: Move one section at a time
2. **Adapter Pattern**: Keep old endpoints working during transition
3. **Comprehensive Testing**: Test each workflow after changes
4. **Rollback Plan**: Keep backup of original files
5. **Frontend Coordination**: Work closely with frontend team

## Success Metrics

1. All workflows continue to function
2. No production incidents during migration
3. Code reduction of at least 30%
4. Improved API response times
5. Positive developer feedback on clarity