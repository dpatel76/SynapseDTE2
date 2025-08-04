# Temporal Workflow Phase Reconciliation

This document maps the existing workflow steps to Temporal activities for each phase.

## Phase 1: Planning

### Existing Steps (Pre-Temporal):
1. Start Planning Phase
2. Upload Documents (Regulatory Spec, CDE List, Historical Issues)
3. Import/Create Attributes
4. Review Planning Checklist
5. Complete Planning Phase

### Current Temporal Activities:
- `start_planning_phase_activity`
- `complete_planning_phase_activity`

### Required Temporal Activities:
1. `start_planning_phase_activity` ✓
2. `upload_planning_documents_activity` ✗ (MISSING)
3. `import_create_attributes_activity` ✗ (MISSING)
4. `review_planning_checklist_activity` ✗ (MISSING)
5. `complete_planning_phase_activity` ✓

---

## Phase 2: Scoping

### Existing Steps (Pre-Temporal):
1. Start Scoping Phase
2. Generate LLM Recommendations
3. Tester Review & Decisions
4. Report Owner Approval
5. Complete Scoping Phase

### Current Temporal Activities:
- `start_scoping_phase_activity`
- `execute_scoping_activities` (auto-approves - WRONG)
- `complete_scoping_phase_activity`

### Required Temporal Activities:
1. `start_scoping_phase_activity` ✓
2. `generate_llm_recommendations_activity` ✗ (NEEDS REFACTOR)
3. `tester_review_attributes_activity` ✗ (MISSING)
4. `report_owner_approval_activity` ✗ (MISSING)
5. `complete_scoping_phase_activity` ✓

---

## Phase 3: Sample Selection

### Existing Steps (Pre-Temporal):
1. Start Sample Selection Phase
2. Define Selection Criteria
3. Generate/Upload Sample Sets
4. Review & Approve Samples
5. Complete Sample Selection Phase

### Current Temporal Activities:
- Unknown (need to check)

### Required Temporal Activities:
1. `start_sample_selection_phase_activity`
2. `define_selection_criteria_activity`
3. `generate_sample_sets_activity`
4. `review_approve_samples_activity`
5. `complete_sample_selection_phase_activity`

---

## Phase 4: Data Provider Identification

### Existing Steps (Pre-Temporal):
1. Start Data Provider ID Phase
2. Auto-Assign Data Providers (CDO Logic)
3. Manual Assignment Review
4. Send Notifications
5. Complete Data Provider ID Phase

### Current Temporal Activities:
- Unknown (need to check)

### Required Temporal Activities:
1. `start_data_provider_phase_activity`
2. `auto_assign_data_providers_activity`
3. `review_data_provider_assignments_activity`
4. `send_data_provider_notifications_activity`
5. `complete_data_provider_phase_activity`

---

## Phase 5: Request for Information

### Existing Steps (Pre-Temporal):
1. Start Request Info Phase
2. Generate Test Cases
3. Create Information Requests
4. Send RFI Emails
5. Track Responses
6. Complete Request Info Phase

### Current Temporal Activities:
- Unknown (need to check)

### Required Temporal Activities:
1. `start_request_info_phase_activity`
2. `generate_test_cases_activity`
3. `create_information_requests_activity`
4. `send_rfi_emails_activity`
5. `track_rfi_responses_activity`
6. `complete_request_info_phase_activity`

---

## Phase 6: Test Execution

### Existing Steps (Pre-Temporal):
1. Start Test Execution Phase
2. Create Test Execution Records
3. Execute Tests (Document & Database)
4. Record Test Results
5. Generate Test Summary
6. Complete Test Execution Phase

### Current Temporal Activities:
- Unknown (need to check)

### Required Temporal Activities:
1. `start_test_execution_phase_activity`
2. `create_test_execution_records_activity`
3. `execute_tests_activity`
4. `record_test_results_activity`
5. `generate_test_summary_activity`
6. `complete_test_execution_phase_activity`

---

## Phase 7: Observation Management

### Existing Steps (Pre-Temporal):
1. Start Observation Phase
2. Create Observations
3. Auto-Group Similar Observations
4. Review & Approve Observations
5. Generate Impact Assessment
6. Complete Observation Phase

### Current Temporal Activities:
- Unknown (need to check)

### Required Temporal Activities:
1. `start_observation_phase_activity`
2. `create_observations_activity`
3. `group_observations_activity`
4. `review_approve_observations_activity`
5. `generate_impact_assessment_activity`
6. `complete_observation_phase_activity`

---

## Phase 8: Preparing Test Report

### Existing Steps (Pre-Temporal):
1. Start Test Report Phase
2. Generate Report Sections
3. Generate Executive Summary (LLM)
4. Review & Edit Report
5. Finalize Report
6. Complete Test Report Phase

### Current Temporal Activities:
- Unknown (need to check)

### Required Temporal Activities:
1. `start_test_report_phase_activity`
2. `generate_report_sections_activity`
3. `generate_executive_summary_activity`
4. `review_edit_report_activity`
5. `finalize_report_activity`
6. `complete_test_report_phase_activity`

---

## Implementation Strategy

### 1. Remove Auto-Approvals
- No automatic approvals in any phase
- Each approval step must be explicit
- Maintain audit trail for all approvals

### 2. Add Human-in-the-Loop Activities
- Add wait conditions for human reviews
- Implement approval tracking
- Support rejection and rework flows

### 3. Preserve Existing Business Logic
- All activities should call existing services
- No duplication of business logic
- Maintain backward compatibility

### 4. Add Proper State Management
- Track sub-step completion
- Support resume from any step
- Maintain step-level metrics