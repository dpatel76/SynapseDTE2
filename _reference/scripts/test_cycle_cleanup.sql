-- Test Cycle Cleanup SQL Script
-- This script provides SQL commands to safely delete test cycles and all related data
-- Execute these statements in order to maintain referential integrity

-- WARNING: This script will permanently delete data. Create backups before running.
-- Replace :cycle_id with the actual cycle ID you want to delete

-- =============================================================================
-- PART 1: DELETE DEPENDENT DATA (Most dependent to least dependent)
-- =============================================================================

-- Workflow activity history and dependencies
DELETE FROM workflow_activity_history WHERE activity_id IN (
    SELECT activity_id FROM workflow_activities WHERE cycle_id = :cycle_id
);

DELETE FROM workflow_activity_dependencies WHERE phase_name IN (
    SELECT phase_name FROM workflow_phases WHERE cycle_id = :cycle_id
);

-- Test execution audit and reviews
DELETE FROM cycle_report_test_execution_audit WHERE execution_id IN (
    SELECT id FROM cycle_report_test_execution_results WHERE cycle_id = :cycle_id
);

DELETE FROM cycle_report_test_execution_reviews WHERE execution_id IN (
    SELECT id FROM cycle_report_test_execution_results WHERE cycle_id = :cycle_id
);

-- Test execution results and data
DELETE FROM cycle_report_test_execution_results WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_test_execution_database_tests WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_test_execution_document_analyses WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_test_executions WHERE cycle_id = :cycle_id;

-- Test report data
DELETE FROM cycle_report_test_report_generation WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_test_report_sections WHERE cycle_id = :cycle_id;

-- Observation management
DELETE FROM cycle_report_observation_mgmt_approvals WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_observation_mgmt_impact_assessments WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_observation_mgmt_resolutions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_observation_mgmt_observation_records WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_observation_mgmt_audit_logs WHERE cycle_id = :cycle_id;

-- Request for information
DELETE FROM cycle_report_request_info_testcase_source_evidence WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_request_info_document_versions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_request_info_phases WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_request_info_audit_logs WHERE cycle_id = :cycle_id;

-- Sample selection
DELETE FROM cycle_report_sample_selection_samples WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_sample_selection_versions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_sample_selection_audit_logs WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_sample_records WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_sample_sets WHERE cycle_id = :cycle_id;

-- Data profiling
DELETE FROM cycle_report_data_profiling_rule_versions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_data_profiling_results WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_data_profiling_files WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_data_profiling_rules WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_data_profiling_attribute_scores WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_data_profiling_uploads WHERE cycle_id = :cycle_id;

-- Scoping phase
DELETE FROM cycle_report_scoping_tester_decisions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_scoping_report_owner_reviews WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_scoping_decision_versions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_scoping_submissions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_scoping_attribute_recommendation_versions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_scoping_attribute_recommendations WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_scoping_decisions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_scoping_versions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_scoping_audit_logs WHERE cycle_id = :cycle_id;

-- Planning phase
DELETE FROM cycle_report_planning_pde_mapping_review_history WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_planning_pde_mapping_reviews WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_planning_pde_mapping_approval_rules WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_planning_pde_mappings WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_planning_pde_classifications WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_planning_attribute_version_history WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_planning_attributes WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_planning_data_sources WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_planning_versions WHERE cycle_id = :cycle_id;

-- Data owner and assignment tables
DELETE FROM cycle_report_data_owner_lob_attribute_versions WHERE cycle_id = :cycle_id;
DELETE FROM cycle_report_data_owner_lob_attribute_assignments WHERE cycle_id = :cycle_id;
DELETE FROM historical_data_owner_assignments WHERE cycle_id = :cycle_id;
DELETE FROM data_owner_sla_violations WHERE cycle_id = :cycle_id;
DELETE FROM data_owner_phase_audit_logs WHERE cycle_id = :cycle_id;
DELETE FROM data_owner_assignments WHERE cycle_id = :cycle_id;
DELETE FROM attribute_lob_assignments WHERE cycle_id = :cycle_id;

-- Test cases and legacy data
DELETE FROM cycle_report_test_cases WHERE cycle_id = :cycle_id;
DELETE FROM test_executions WHERE cycle_id = :cycle_id;  -- Legacy table if exists
DELETE FROM observations WHERE cycle_id = :cycle_id;     -- Legacy table if exists

-- Documents
DELETE FROM cycle_report_documents WHERE cycle_id = :cycle_id;

-- Metrics and audit logs
DELETE FROM execution_metrics WHERE cycle_id = :cycle_id;
DELETE FROM phase_metrics WHERE cycle_id = :cycle_id;
DELETE FROM llm_audit_logs WHERE cycle_id = :cycle_id;

-- =============================================================================
-- PART 2: DELETE WORKFLOW STRUCTURE
-- =============================================================================

-- Workflow activities (will cascade to activity history due to model cascade settings)
DELETE FROM workflow_activities WHERE cycle_id = :cycle_id;

-- Workflow phases (will cascade to activities due to model cascade settings)
DELETE FROM workflow_phases WHERE cycle_id = :cycle_id;

-- =============================================================================
-- PART 3: DELETE CORE RELATIONSHIPS
-- =============================================================================

-- Cycle reports (junction table)
DELETE FROM cycle_reports WHERE cycle_id = :cycle_id;

-- =============================================================================
-- PART 4: DELETE MAIN TABLE
-- =============================================================================

-- Test cycles (main table)
DELETE FROM test_cycles WHERE cycle_id = :cycle_id;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify the cycle has been deleted
SELECT COUNT(*) as remaining_cycles FROM test_cycles WHERE cycle_id = :cycle_id;

-- Check for any orphaned records (should return 0 for all)
SELECT 
    'cycle_reports' as table_name,
    COUNT(*) as orphaned_count
FROM cycle_reports 
WHERE cycle_id = :cycle_id

UNION ALL

SELECT 
    'workflow_phases' as table_name,
    COUNT(*) as orphaned_count
FROM workflow_phases 
WHERE cycle_id = :cycle_id

UNION ALL

SELECT 
    'workflow_activities' as table_name,
    COUNT(*) as orphaned_count
FROM workflow_activities 
WHERE cycle_id = :cycle_id;

-- =============================================================================
-- CLEANUP ORPHANED RECORDS (Run this occasionally to clean up data integrity issues)
-- =============================================================================

-- Clean up orphaned cycle_reports
DELETE FROM cycle_reports 
WHERE cycle_id NOT IN (SELECT cycle_id FROM test_cycles);

-- Clean up orphaned workflow_phases
DELETE FROM workflow_phases 
WHERE cycle_id NOT IN (SELECT cycle_id FROM test_cycles);

-- Clean up orphaned workflow_activities
DELETE FROM workflow_activities 
WHERE cycle_id NOT IN (SELECT cycle_id FROM test_cycles);

-- Clean up orphaned cycle_report_* tables (run for each table as needed)
-- Example:
-- DELETE FROM cycle_report_planning_attributes 
-- WHERE cycle_id NOT IN (SELECT cycle_id FROM test_cycles);

-- =============================================================================
-- BULK CLEANUP (Delete ALL test cycles and related data)
-- =============================================================================

/*
-- WARNING: This will delete ALL test cycles and related data
-- Uncomment and run only if you want to delete everything

-- Delete all dependent data first
TRUNCATE TABLE workflow_activity_history CASCADE;
TRUNCATE TABLE workflow_activity_dependencies CASCADE;
TRUNCATE TABLE cycle_report_test_execution_audit CASCADE;
TRUNCATE TABLE cycle_report_test_execution_reviews CASCADE;
TRUNCATE TABLE cycle_report_test_execution_results CASCADE;
TRUNCATE TABLE cycle_report_test_execution_database_tests CASCADE;
TRUNCATE TABLE cycle_report_test_execution_document_analyses CASCADE;
TRUNCATE TABLE cycle_report_test_executions CASCADE;
TRUNCATE TABLE cycle_report_test_report_generation CASCADE;
TRUNCATE TABLE cycle_report_test_report_sections CASCADE;

-- Continue with all other cycle_report_* tables...
TRUNCATE TABLE cycle_report_planning_attributes CASCADE;
TRUNCATE TABLE cycle_report_planning_data_sources CASCADE;
TRUNCATE TABLE cycle_report_planning_versions CASCADE;
TRUNCATE TABLE cycle_report_scoping_decisions CASCADE;
TRUNCATE TABLE cycle_report_scoping_versions CASCADE;
TRUNCATE TABLE cycle_report_data_profiling_rules CASCADE;
TRUNCATE TABLE cycle_report_data_profiling_results CASCADE;
TRUNCATE TABLE cycle_report_sample_selection_versions CASCADE;

-- Delete assignment and metrics data
TRUNCATE TABLE attribute_lob_assignments CASCADE;
TRUNCATE TABLE data_owner_assignments CASCADE;
TRUNCATE TABLE execution_metrics CASCADE;
TRUNCATE TABLE phase_metrics CASCADE;
TRUNCATE TABLE llm_audit_logs CASCADE;

-- Delete workflow structure
TRUNCATE TABLE workflow_activities CASCADE;
TRUNCATE TABLE workflow_phases CASCADE;

-- Delete core relationships
TRUNCATE TABLE cycle_reports CASCADE;

-- Delete main table
TRUNCATE TABLE test_cycles CASCADE;

-- Reset sequences if needed
SELECT setval('test_cycles_cycle_id_seq', 1, false);
*/