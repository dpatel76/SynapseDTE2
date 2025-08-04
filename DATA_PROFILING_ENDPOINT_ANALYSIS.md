# Data Profiling Endpoints Analysis - Redundancy Report

## Overview
The data profiling functionality is spread across 4 main files with significant overlap and redundancy:

1. **data_profiling.py** (Main file - 2183 lines)
2. **data_profiling_rules.py** (749 lines)
3. **data_profiling_assignments.py** (753 lines)
4. **data_profiling_resubmit.py** (297 lines)

## POST Endpoints by Functionality

### 1. Phase Start/Initialization
- **data_profiling.py**
  - `POST /phases/{phase_id}/start` (line 437)
  - `POST /cycles/{cycle_id}/reports/{report_id}/start` (line 708) - Legacy endpoint

### 2. Rule Generation
- **data_profiling.py**
  - `POST /cycles/{cycle_id}/reports/{report_id}/generate-rules` (line 736)

### 3. Rule Execution
- **data_profiling.py**
  - `POST /versions/{version_id}/execute` (line 524)
- **data_profiling_assignments.py**
  - `POST /cycles/{cycle_id}/reports/{report_id}/start-profiling` (line 508)

### 4. Individual Rule Approval/Rejection
- **data_profiling.py**
  - `PUT /rules/{rule_id}/tester-decision` (line 768)
  - `PUT /rules/{rule_id}/report-owner-decision` (line 814)
- **data_profiling_rules.py**
  - `PUT /rules/{rule_id}/approve` (line 169)
  - `PUT /rules/{rule_id}/reject` (line 237)
  - `PUT /cycles/{cycle_id}/reports/{report_id}/rules/{rule_id}/report-owner-decision` (line 298)

### 5. Bulk Rule Operations
- **data_profiling_rules.py**
  - `POST /rules/bulk-approve` (line 605)
  - `POST /rules/bulk-reject` (line 680)

### 6. Version Management
- **data_profiling.py**
  - `POST /versions/{version_id}/submit` (line 1890)
  - `POST /versions/{version_id}/approve` (line 2043)
  - `POST /cycles/{cycle_id}/reports/{report_id}/check-and-approve-version` (line 1529)

### 7. Report Owner Review Workflow
- **data_profiling.py**
  - `POST /cycles/{cycle_id}/reports/{report_id}/send-to-report-owner` (line 1159)
  - `POST /cycles/{cycle_id}/reports/{report_id}/resubmit-after-feedback` (line 1339)
- **data_profiling_resubmit.py**
  - `POST /cycles/{cycle_id}/reports/{report_id}/resubmit-after-feedback` (line 32) - DUPLICATE
  - `POST /cycles/{cycle_id}/reports/{report_id}/finalize-version` (line 198)

### 8. Phase Completion
- **data_profiling.py**
  - `POST /cycles/{cycle_id}/reports/{report_id}/complete` (line 887)
  - `POST /cycles/{cycle_id}/reports/{report_id}/mark-execution-complete` (line 1311)

### 9. Workflow Status Updates
- **data_profiling.py**
  - `POST /cycles/{cycle_id}/reports/{report_id}/update-workflow-status` (line 1101)

### 10. Assignments
- **data_profiling_assignments.py**
  - `POST /cycles/{cycle_id}/reports/{report_id}/assign-report-owner` (line 34)
  - `POST /cycles/{cycle_id}/reports/{report_id}/complete-assignment/{assignment_id}` (line 109)

## Major Redundancies Identified

### 1. Rule Approval/Rejection (3 different implementations)
- **data_profiling.py**: Uses `tester-decision` and `report-owner-decision` endpoints
- **data_profiling_rules.py**: Uses generic `approve` and `reject` endpoints with role detection
- Both implement the same functionality with slight variations

### 2. Resubmit After Feedback (2 identical implementations)
- **data_profiling.py** line 1339
- **data_profiling_resubmit.py** line 32
- Exact same functionality, different files

### 3. Rule Retrieval (3 different implementations)
- **data_profiling.py**: `GET /rules` (line 232)
- **data_profiling_rules.py**: `GET /attributes/{attribute_id}/rules` (line 139)
- **data_profiling_assignments.py**: `GET /rules` (line 593)

### 4. Status Endpoints (Multiple overlapping)
- **data_profiling.py**: `GET /status` (line 61)
- **data_profiling_assignments.py**: `GET /status` (line 348) - redirects to workflow-status
- **data_profiling_assignments.py**: `GET /workflow-status` (line 194)

### 5. Execution Endpoints (2 different approaches)
- **data_profiling.py**: Version-based execution
- **data_profiling_assignments.py**: Direct profiling job start

## Recommendations for Consolidation

### 1. Merge Rule Management
- Keep only one set of rule approval/rejection endpoints
- Use role-based logic in a single implementation
- Remove duplicates from data_profiling_rules.py

### 2. Remove Duplicate Resubmission
- Keep only one resubmit-after-feedback endpoint
- Remove the duplicate from data_profiling_resubmit.py

### 3. Unify Status Endpoints
- Create one comprehensive status endpoint
- Remove redundant status implementations
- Use consistent response format

### 4. Consolidate Rule Retrieval
- Use one endpoint with optional filters
- Support filtering by attribute, version, status, etc.
- Remove duplicate implementations

### 5. Standardize Execution
- Choose either version-based or job-based execution
- Remove the redundant approach
- Ensure consistent execution tracking

### 6. File Organization
Suggested consolidation:
- **data_profiling.py**: Core functionality (phases, versions, execution)
- **data_profiling_rules.py**: Remove (merge unique features into main)
- **data_profiling_assignments.py**: Keep only assignment-specific endpoints
- **data_profiling_resubmit.py**: Remove (already duplicated in main)

## Impact Assessment
- **High redundancy**: ~40% of endpoints have duplicates or overlaps
- **Code maintenance burden**: 4 files to maintain for one feature
- **Confusion risk**: Different endpoints doing the same thing
- **Testing overhead**: Multiple implementations to test