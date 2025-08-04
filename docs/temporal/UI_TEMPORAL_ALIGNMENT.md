# UI and Temporal Workflow Alignment

## Current UI vs Temporal Activities Mapping

### Phase 1: Planning
**Current UI Steps:**
1. Start Planning Phase
2. Upload Documents
3. Import/Create Attributes
4. Review Planning Checklist
5. Complete Planning Phase

**Temporal Activities (Reconciled):**
1. ✅ `start_planning_phase_activity` 
2. ✅ `upload_planning_documents_activity`
3. ✅ `import_create_attributes_activity`
4. ✅ `review_planning_checklist_activity`
5. ✅ `complete_planning_phase_activity`

**Status:** ✅ ALIGNED

---

### Phase 2: Scoping
**Current UI Steps:**
1. Start Scoping Phase
2. Generate LLM Recommendations
3. Tester Review & Decisions
4. Report Owner Approval
5. Complete Scoping Phase

**Temporal Activities (Reconciled):**
1. ✅ `start_scoping_phase_activity`
2. ✅ `generate_llm_recommendations_activity`
3. ✅ `tester_review_attributes_activity`
4. ✅ `report_owner_approval_activity`
5. ✅ `complete_scoping_phase_activity`

**Status:** ✅ ALIGNED

---

### Phase 3: Sample Selection
**UI Steps:** Need to check
**Temporal Activities (Reconciled):**
1. `start_sample_selection_phase_activity`
2. `define_selection_criteria_activity`
3. `generate_sample_sets_activity`
4. `review_approve_samples_activity`
5. `complete_sample_selection_phase_activity`

---

### Phase 4: Data Provider ID
**UI Steps:** Need to check
**Temporal Activities (Reconciled):**
1. `start_data_provider_phase_activity`
2. `auto_assign_data_providers_activity`
3. `review_data_provider_assignments_activity`
4. `send_data_provider_notifications_activity`
5. `complete_data_provider_phase_activity`

---

### Phase 5: Request Info
**UI Steps:** Need to check
**Temporal Activities (Reconciled):**
1. `start_request_info_phase_activity`
2. `generate_test_cases_activity`
3. `create_information_requests_activity`
4. `send_rfi_emails_activity`
5. `track_rfi_responses_activity`
6. `complete_request_info_phase_activity`

---

### Phase 6: Test Execution
**UI Steps:** Need to check
**Temporal Activities (Reconciled):**
1. `start_test_execution_phase_activity`
2. `create_test_execution_records_activity`
3. `execute_document_tests_activity`
4. `execute_database_tests_activity`
5. `record_test_results_activity`
6. `generate_test_summary_activity`
7. `complete_test_execution_phase_activity`

---

### Phase 7: Observations
**UI Steps:** Need to check
**Temporal Activities (Reconciled):**
1. `start_observation_phase_activity`
2. `create_observations_activity`
3. `auto_group_observations_activity`
4. `review_approve_observations_activity`
5. `generate_impact_assessment_activity`
6. `complete_observation_phase_activity`

---

### Phase 8: Test Report
**UI Steps:** Need to check
**Temporal Activities (Reconciled):**
1. `start_test_report_phase_activity`
2. `generate_report_sections_activity`
3. `generate_executive_summary_activity`
4. `review_edit_report_activity`
5. `finalize_report_activity`
6. `complete_test_report_phase_activity`

---

## Progress Calculation Rules

### Phase Progress
```
Phase Progress = (Completed Steps - 2) / (Total Steps - 2) * 100
```
- Exclude `start_phase` and `complete_phase` from calculation
- Only count the actual work activities

### Workflow Progress
```
Workflow Progress = (Total Completed Steps - 16) / (Total Steps - 16) * 100
```
- Total of 8 phases × 2 (start/complete) = 16 activities to exclude
- Count all completed work activities across all phases

### Example Calculations

#### Scoping Phase (5 total activities)
- Work activities: 3 (Generate LLM, Tester Review, Report Owner Approval)
- If 2 work activities complete: 2/3 = 66.7% phase progress

#### Full Workflow (47 total activities)
- Work activities: 47 - 16 = 31
- If 15 work activities complete: 15/31 = 48.4% workflow progress