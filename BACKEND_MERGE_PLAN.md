# Backend File Merge Plan

Based on the analysis, all 6 conflicting backend endpoints have both `_clean` and regular versions in use:

## Current Usage Pattern
- `api.py` imports the `_clean` versions with aliases (e.g., `planning_clean as planning`)
- The regular versions are imported by tests and other scripts
- Both versions are actively used in the codebase

## Merge Strategy

### 1. Planning Endpoints
**Files:** `planning_clean.py` (used by API) vs `planning.py` (used by tests)
**Action:** 
- Keep `planning_clean.py` as the main implementation
- Copy any unique endpoints from `planning.py` to `planning_clean.py`
- Rename `planning_clean.py` → `planning.py`
- Delete the old `planning.py`

### 2. Scoping Endpoints
**Files:** `scoping_clean.py` (used by API) vs `scoping.py` (used by tests)
**Action:**
- Keep `scoping_clean.py` as the main implementation
- Merge unique endpoints from `scoping.py`
- Rename `scoping_clean.py` → `scoping.py`
- Delete the old `scoping.py`

### 3. Data Owner Endpoints
**Files:** `data_owner_clean.py` (used by API) vs `data_owner.py` (used by tests)
**Action:**
- Keep `data_owner_clean.py` as the main implementation
- Merge unique endpoints from `data_owner.py`
- Rename `data_owner_clean.py` → `data_owner.py`
- Delete the old `data_owner.py`

### 4. Request Info Endpoints
**Files:** `request_info_clean.py` (used by API) vs `request_info.py` (used by tests)
**Action:**
- Keep `request_info_clean.py` as the main implementation
- Merge unique endpoints from `request_info.py`
- Rename `request_info_clean.py` → `request_info.py`
- Delete the old `request_info.py`

### 5. Test Execution Endpoints
**Files:** `test_execution_clean.py` (used by API) vs `test_execution.py` (used by tests)
**Action:**
- Keep `test_execution_clean.py` as the main implementation
- Merge unique endpoints from `test_execution.py`
- Rename `test_execution_clean.py` → `test_execution.py`
- Delete the old `test_execution.py`

### 6. Observation Management Endpoints
**Files:** `observation_management_clean.py` (used by API) vs `observation_management.py` (used by tests)
**Action:**
- Keep `observation_management_clean.py` as the main implementation
- Merge unique endpoints from `observation_management.py`
- Rename `observation_management_clean.py` → `observation_management.py`
- Delete the old `observation_management.py`

## Implementation Steps

1. **Backup all files** before merging
2. **Compare endpoints** in each file pair to identify unique endpoints
3. **Merge unique endpoints** from regular version into clean version
4. **Update imports** in api.py to remove aliases
5. **Rename clean files** to regular names
6. **Delete old regular files**
7. **Test all endpoints** to ensure nothing is broken

## Risk Mitigation

- Create full backup before starting
- Test each endpoint after merging
- Keep detailed log of changes
- Have rollback script ready