-- SQL to add missing audit columns
BEGIN;

-- Table: document_extractions (Model: DocumentExtraction)
ALTER TABLE document_extractions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN document_extractions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_document_extractions_created_by ON document_extractions(created_by_id);
ALTER TABLE document_extractions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN document_extractions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_document_extractions_updated_by ON document_extractions(updated_by_id);

-- Table: test_execution_phases (Model: TestExecutionPhase)
ALTER TABLE test_execution_phases ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_execution_phases.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_test_execution_phases_created_by ON test_execution_phases(created_by_id);
ALTER TABLE test_execution_phases ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_execution_phases.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_test_execution_phases_updated_by ON test_execution_phases(updated_by_id);

-- Table: request_info_phases (Model: RequestInfoPhase)
ALTER TABLE request_info_phases ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN request_info_phases.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_request_info_phases_created_by ON request_info_phases(created_by_id);
ALTER TABLE request_info_phases ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN request_info_phases.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_request_info_phases_updated_by ON request_info_phases(updated_by_id);

-- Table: sample_sets (Model: SampleSet)
ALTER TABLE sample_sets ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sample_sets.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_sample_sets_created_by ON sample_sets(created_by_id);
ALTER TABLE sample_sets ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sample_sets.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_sample_sets_updated_by ON sample_sets(updated_by_id);

-- Table: metrics_execution (Model: ExecutionMetrics)
ALTER TABLE metrics_execution ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN metrics_execution.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_metrics_execution_created_by ON metrics_execution(created_by_id);
ALTER TABLE metrics_execution ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN metrics_execution.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_metrics_execution_updated_by ON metrics_execution(updated_by_id);

-- Table: data_queries (Model: DataQuery)
ALTER TABLE data_queries ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN data_queries.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_data_queries_created_by ON data_queries(created_by_id);
ALTER TABLE data_queries ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN data_queries.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_data_queries_updated_by ON data_queries(updated_by_id);

-- Table: observation_resolutions (Model: ObservationResolution)
ALTER TABLE cycle_report_observation_mgmt_resolutions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_resolutions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_observation_resolutions_created_by ON observation_resolutions(created_by_id);
ALTER TABLE cycle_report_observation_mgmt_resolutions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_resolutions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_observation_resolutions_updated_by ON observation_resolutions(updated_by_id);

-- Table: bulk_test_executions (Model: BulkTestExecution)
ALTER TABLE bulk_test_executions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN bulk_test_executions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_bulk_test_executions_created_by ON bulk_test_executions(created_by_id);
ALTER TABLE bulk_test_executions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN bulk_test_executions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_bulk_test_executions_updated_by ON bulk_test_executions(updated_by_id);

-- Table: data_profiling_phases (Model: DataProfilingPhase)
ALTER TABLE data_profiling_phases ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN data_profiling_phases.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_data_profiling_phases_created_by ON data_profiling_phases(created_by_id);
ALTER TABLE data_profiling_phases ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN data_profiling_phases.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_data_profiling_phases_updated_by ON data_profiling_phases(updated_by_id);

-- Table: sample_records (Model: SampleRecord)
ALTER TABLE sample_records ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sample_records.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_sample_records_created_by ON sample_records(created_by_id);
ALTER TABLE sample_records ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sample_records.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_sample_records_updated_by ON sample_records(updated_by_id);

-- Table: llm_sample_generations (Model: LLMSampleGeneration)
ALTER TABLE llm_sample_generations ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN llm_sample_generations.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_llm_sample_generations_created_by ON llm_sample_generations(created_by_id);
ALTER TABLE llm_sample_generations ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN llm_sample_generations.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_llm_sample_generations_updated_by ON llm_sample_generations(updated_by_id);

-- Table: universal_assignments (Model: UniversalAssignment)
ALTER TABLE universal_assignments ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN universal_assignments.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_universal_assignments_created_by ON universal_assignments(created_by_id);
ALTER TABLE universal_assignments ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN universal_assignments.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_universal_assignments_updated_by ON universal_assignments(updated_by_id);

-- Table: workflow_activity_dependencies (Model: WorkflowActivityDependency)
ALTER TABLE workflow_activity_dependencies ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_activity_dependencies.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_workflow_activity_dependencies_created_by ON workflow_activity_dependencies(created_by_id);
ALTER TABLE workflow_activity_dependencies ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_activity_dependencies.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_workflow_activity_dependencies_updated_by ON workflow_activity_dependencies(updated_by_id);

-- Table: workflow_alerts (Model: WorkflowAlert)
ALTER TABLE workflow_alerts ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_alerts.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_workflow_alerts_created_by ON workflow_alerts(created_by_id);
ALTER TABLE workflow_alerts ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_alerts.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_workflow_alerts_updated_by ON workflow_alerts(updated_by_id);

-- Table: intelligent_samples (Model: IntelligentSample)
ALTER TABLE intelligent_samples ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN intelligent_samples.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_intelligent_samples_created_by ON intelligent_samples(created_by_id);
ALTER TABLE intelligent_samples ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN intelligent_samples.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_intelligent_samples_updated_by ON intelligent_samples(updated_by_id);

-- Table: workflow_metrics (Model: WorkflowMetrics)
ALTER TABLE workflow_metrics ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_metrics.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_workflow_metrics_created_by ON workflow_metrics(created_by_id);
ALTER TABLE workflow_metrics ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_metrics.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_workflow_metrics_updated_by ON workflow_metrics(updated_by_id);

-- Table: observation_groups (Model: ObservationGroup)
ALTER TABLE observation_groups ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_groups.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_observation_groups_created_by ON observation_groups(created_by_id);
ALTER TABLE observation_groups ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_groups.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_observation_groups_updated_by ON observation_groups(updated_by_id);

-- Table: intelligent_sampling_jobs (Model: IntelligentSamplingJob)
ALTER TABLE intelligent_sampling_jobs ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN intelligent_sampling_jobs.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_intelligent_sampling_jobs_created_by ON intelligent_sampling_jobs(created_by_id);
ALTER TABLE intelligent_sampling_jobs ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN intelligent_sampling_jobs.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_intelligent_sampling_jobs_updated_by ON intelligent_sampling_jobs(updated_by_id);

-- Table: profiling_jobs (Model: ProfilingJob)
ALTER TABLE profiling_jobs ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_jobs.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_profiling_jobs_created_by ON profiling_jobs(created_by_id);
ALTER TABLE profiling_jobs ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_jobs.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_profiling_jobs_updated_by ON profiling_jobs(updated_by_id);

-- Table: document_analyses (Model: DocumentAnalysis)
ALTER TABLE cycle_report_test_execution_document_analyses ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN document_analyses.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_document_analyses_created_by ON document_analyses(created_by_id);
ALTER TABLE cycle_report_test_execution_document_analyses ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN document_analyses.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_document_analyses_updated_by ON document_analyses(updated_by_id);

-- Table: user_roles (Model: UserRole)
ALTER TABLE user_roles ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN user_roles.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_user_roles_created_by ON user_roles(created_by_id);
ALTER TABLE user_roles ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN user_roles.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_user_roles_updated_by ON user_roles(updated_by_id);

-- Table: attribute_mappings (Model: AttributeMapping)
ALTER TABLE attribute_mappings ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN attribute_mappings.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_attribute_mappings_created_by ON attribute_mappings(created_by_id);
ALTER TABLE attribute_mappings ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN attribute_mappings.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_attribute_mappings_updated_by ON attribute_mappings(updated_by_id);

-- Table: sample_validation_results (Model: SampleValidationResult)
ALTER TABLE sample_validation_results ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sample_validation_results.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_sample_validation_results_created_by ON sample_validation_results(created_by_id);
ALTER TABLE sample_validation_results ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sample_validation_results.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_sample_validation_results_updated_by ON sample_validation_results(updated_by_id);

-- Table: report_owner_scoping_reviews (Model: ReportOwnerScopingReview)
ALTER TABLE cycle_report_scoping_report_owner_reviews ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN report_owner_scoping_reviews.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_report_owner_scoping_reviews_created_by ON report_owner_scoping_reviews(created_by_id);
ALTER TABLE cycle_report_scoping_report_owner_reviews ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN report_owner_scoping_reviews.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_report_owner_scoping_reviews_updated_by ON report_owner_scoping_reviews(updated_by_id);

-- Table: observation_records (Model: ObservationRecord)
ALTER TABLE cycle_report_observation_mgmt_observation_records ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_records.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_observation_records_created_by ON observation_records(created_by_id);
ALTER TABLE cycle_report_observation_mgmt_observation_records ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_records.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_observation_records_updated_by ON observation_records(updated_by_id);

-- Table: test_executions (Model: TestExecution)
ALTER TABLE cycle_report_test_execution_test_executions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_executions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_test_executions_created_by ON test_executions(created_by_id);
ALTER TABLE cycle_report_test_execution_test_executions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_executions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_test_executions_updated_by ON test_executions(updated_by_id);

-- Table: workflow_steps (Model: WorkflowStep)
ALTER TABLE workflow_steps ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_steps.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_workflow_steps_created_by ON workflow_steps(created_by_id);
ALTER TABLE workflow_steps ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_steps.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_workflow_steps_updated_by ON workflow_steps(updated_by_id);

-- Table: cycle_report_attributes_planning (Model: CycleReportAttributesPlanning)
ALTER TABLE cycle_report_planning_attributes ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN cycle_report_attributes_planning.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_cycle_report_attributes_planning_created_by ON cycle_report_attributes_planning(created_by_id);
ALTER TABLE cycle_report_planning_attributes ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN cycle_report_attributes_planning.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_cycle_report_attributes_planning_updated_by ON cycle_report_attributes_planning(updated_by_id);

-- Table: workflow_activities (Model: WorkflowActivity)
ALTER TABLE workflow_activities ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_activities.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_workflow_activities_created_by ON workflow_activities(created_by_id);
ALTER TABLE workflow_activities ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_activities.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_workflow_activities_updated_by ON workflow_activities(updated_by_id);

-- Table: observations (Model: Observation)
ALTER TABLE observations ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observations.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_observations_created_by ON observations(created_by_id);
ALTER TABLE observations ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observations.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_observations_updated_by ON observations(updated_by_id);

-- Table: profiling_rules (Model: ProfilingRule)
ALTER TABLE cycle_report_data_profiling_rules ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_rules.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_profiling_rules_created_by ON profiling_rules(created_by_id);
ALTER TABLE cycle_report_data_profiling_rules ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_rules.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_profiling_rules_updated_by ON profiling_rules(updated_by_id);

-- Table: sampling_rules (Model: SamplingRule)
ALTER TABLE sampling_rules ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sampling_rules.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_sampling_rules_created_by ON sampling_rules(created_by_id);
ALTER TABLE sampling_rules ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sampling_rules.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_sampling_rules_updated_by ON sampling_rules(updated_by_id);

-- Table: observation_management_phases (Model: ObservationManagementPhase)
ALTER TABLE observation_management_phases ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_management_phases.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_observation_management_phases_created_by ON observation_management_phases(created_by_id);
ALTER TABLE observation_management_phases ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_management_phases.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_observation_management_phases_updated_by ON observation_management_phases(updated_by_id);

-- Table: documents (Model: Document)
ALTER TABLE documents ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN documents.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_documents_created_by ON documents(created_by_id);
ALTER TABLE documents ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN documents.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_documents_updated_by ON documents(updated_by_id);

-- Table: user_permissions (Model: UserPermission)
ALTER TABLE user_permissions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN user_permissions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_user_permissions_created_by ON user_permissions(created_by_id);
ALTER TABLE user_permissions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN user_permissions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_user_permissions_updated_by ON user_permissions(updated_by_id);

-- Table: cycle_reports (Model: CycleReport)
ALTER TABLE cycle_reports ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN cycle_reports.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_cycle_reports_created_by ON cycle_reports(created_by_id);
ALTER TABLE cycle_reports ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN cycle_reports.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_cycle_reports_updated_by ON cycle_reports(updated_by_id);

-- Table: document_revisions (Model: DocumentRevision)
ALTER TABLE document_revisions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN document_revisions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_document_revisions_created_by ON document_revisions(created_by_id);
ALTER TABLE document_revisions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN document_revisions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_document_revisions_updated_by ON document_revisions(updated_by_id);

-- Table: test_result_reviews (Model: TestResultReview)
ALTER TABLE test_result_reviews ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_result_reviews.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_test_result_reviews_created_by ON test_result_reviews(created_by_id);
ALTER TABLE test_result_reviews ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_result_reviews.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_test_result_reviews_updated_by ON test_result_reviews(updated_by_id);

-- Table: sla_escalation_rules (Model: SLAEscalationRule)
ALTER TABLE sla_escalation_rules ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sla_escalation_rules.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_sla_escalation_rules_created_by ON sla_escalation_rules(created_by_id);
ALTER TABLE sla_escalation_rules ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sla_escalation_rules.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_sla_escalation_rules_updated_by ON sla_escalation_rules(updated_by_id);

-- Table: attribute_version_comparisons (Model: AttributeVersionComparison)
ALTER TABLE attribute_version_comparisons ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN attribute_version_comparisons.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_attribute_version_comparisons_created_by ON attribute_version_comparisons(created_by_id);
ALTER TABLE attribute_version_comparisons ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN attribute_version_comparisons.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_attribute_version_comparisons_updated_by ON attribute_version_comparisons(updated_by_id);

-- Table: attribute_profiling_scores (Model: AttributeProfilingScore)
ALTER TABLE cycle_report_data_profiling_attribute_scores ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN attribute_profiling_scores.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_attribute_profiling_scores_created_by ON attribute_profiling_scores(created_by_id);
ALTER TABLE cycle_report_data_profiling_attribute_scores ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN attribute_profiling_scores.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_attribute_profiling_scores_updated_by ON attribute_profiling_scores(updated_by_id);

-- Table: attribute_version_change_logs (Model: AttributeVersionChangeLog)
ALTER TABLE attribute_version_change_logs ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN attribute_version_change_logs.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_attribute_version_change_logs_created_by ON attribute_version_change_logs(created_by_id);
ALTER TABLE attribute_version_change_logs ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN attribute_version_change_logs.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_attribute_version_change_logs_updated_by ON attribute_version_change_logs(updated_by_id);

-- Table: historical_data_owner_assignments (Model: HistoricalDataOwnerAssignment)
ALTER TABLE historical_data_owner_assignments ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN historical_data_owner_assignments.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_historical_data_owner_assignments_created_by ON historical_data_owner_assignments(created_by_id);
ALTER TABLE historical_data_owner_assignments ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN historical_data_owner_assignments.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_historical_data_owner_assignments_updated_by ON historical_data_owner_assignments(updated_by_id);

-- Table: escalation_email_logs (Model: EscalationEmailLog)
ALTER TABLE escalation_email_logs ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN escalation_email_logs.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_escalation_email_logs_created_by ON escalation_email_logs(created_by_id);
ALTER TABLE escalation_email_logs ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN escalation_email_logs.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_escalation_email_logs_updated_by ON escalation_email_logs(updated_by_id);

-- Table: tester_scoping_decisions (Model: TesterScopingDecision)
ALTER TABLE cycle_report_scoping_tester_decisions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN tester_scoping_decisions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_tester_scoping_decisions_created_by ON tester_scoping_decisions(created_by_id);
ALTER TABLE cycle_report_scoping_tester_decisions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN tester_scoping_decisions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_tester_scoping_decisions_updated_by ON tester_scoping_decisions(updated_by_id);

-- Table: test_report_sections (Model: TestReportSection)
ALTER TABLE cycle_report_test_report_sections ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_report_sections.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_test_report_sections_created_by ON test_report_sections(created_by_id);
ALTER TABLE cycle_report_test_report_sections ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_report_sections.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_test_report_sections_updated_by ON test_report_sections(updated_by_id);

-- Table: document_access_logs (Model: DocumentAccessLog)
ALTER TABLE document_access_logs ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN document_access_logs.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_document_access_logs_created_by ON document_access_logs(created_by_id);
ALTER TABLE document_access_logs ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN document_access_logs.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_document_access_logs_updated_by ON document_access_logs(updated_by_id);

-- Table: workflow_phases (Model: WorkflowPhase)
ALTER TABLE workflow_phases ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_phases.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_workflow_phases_created_by ON workflow_phases(created_by_id);
ALTER TABLE workflow_phases ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_phases.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_workflow_phases_updated_by ON workflow_phases(updated_by_id);

-- Table: test_report_phases (Model: TestReportPhase)
ALTER TABLE test_report_phases ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_report_phases.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_test_report_phases_created_by ON test_report_phases(created_by_id);
ALTER TABLE test_report_phases ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_report_phases.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_test_report_phases_updated_by ON test_report_phases(updated_by_id);

-- Table: attribute_scoping_recommendations (Model: AttributeScopingRecommendation)
ALTER TABLE cycle_report_scoping_attribute_recommendations ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN attribute_scoping_recommendations.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_attribute_scoping_recommendations_created_by ON attribute_scoping_recommendations(created_by_id);
ALTER TABLE cycle_report_scoping_attribute_recommendations ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN attribute_scoping_recommendations.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_attribute_scoping_recommendations_updated_by ON attribute_scoping_recommendations(updated_by_id);

-- Table: sample_selection_phases (Model: SampleSelectionPhase)
ALTER TABLE sample_selection_phases ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sample_selection_phases.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_sample_selection_phases_created_by ON sample_selection_phases(created_by_id);
ALTER TABLE sample_selection_phases ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sample_selection_phases.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_sample_selection_phases_updated_by ON sample_selection_phases(updated_by_id);

-- Table: observation_approvals (Model: ObservationApproval)
ALTER TABLE cycle_report_observation_mgmt_approvals ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_approvals.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_observation_approvals_created_by ON observation_approvals(created_by_id);
ALTER TABLE cycle_report_observation_mgmt_approvals ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_approvals.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_observation_approvals_updated_by ON observation_approvals(updated_by_id);

-- Table: observation_clarifications (Model: ObservationClarification)
ALTER TABLE observation_clarifications ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_clarifications.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_observation_clarifications_created_by ON observation_clarifications(created_by_id);
ALTER TABLE observation_clarifications ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_clarifications.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_observation_clarifications_updated_by ON observation_clarifications(updated_by_id);

-- Table: samples (Model: Sample)
ALTER TABLE cycle_report_sample_selection_samples ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN samples.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_samples_created_by ON samples(created_by_id);
ALTER TABLE cycle_report_sample_selection_samples ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN samples.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_samples_updated_by ON samples(updated_by_id);

-- Table: role_permissions (Model: RolePermission)
ALTER TABLE role_permissions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN role_permissions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_role_permissions_created_by ON role_permissions(created_by_id);
ALTER TABLE role_permissions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN role_permissions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_role_permissions_updated_by ON role_permissions(updated_by_id);

-- Table: resource_permissions (Model: ResourcePermission)
ALTER TABLE resource_permissions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN resource_permissions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_resource_permissions_created_by ON resource_permissions(created_by_id);
ALTER TABLE resource_permissions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN resource_permissions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_resource_permissions_updated_by ON resource_permissions(updated_by_id);

-- Table: resources (Model: Resource)
ALTER TABLE resources ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN resources.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_resources_created_by ON resources(created_by_id);
ALTER TABLE resources ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN resources.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_resources_updated_by ON resources(updated_by_id);

-- Table: sample_validation_issues (Model: SampleValidationIssue)
ALTER TABLE sample_validation_issues ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sample_validation_issues.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_sample_validation_issues_created_by ON sample_validation_issues(created_by_id);
ALTER TABLE sample_validation_issues ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sample_validation_issues.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_sample_validation_issues_updated_by ON sample_validation_issues(updated_by_id);

-- Table: profiling_results (Model: ProfilingResult)
ALTER TABLE cycle_report_data_profiling_results ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_results.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_profiling_results_created_by ON profiling_results(created_by_id);
ALTER TABLE cycle_report_data_profiling_results ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_results.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_profiling_results_updated_by ON profiling_results(updated_by_id);

-- Table: test_comparisons (Model: TestComparison)
ALTER TABLE test_comparisons ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_comparisons.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_test_comparisons_created_by ON test_comparisons(created_by_id);
ALTER TABLE test_comparisons ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN test_comparisons.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_test_comparisons_updated_by ON test_comparisons(updated_by_id);

-- Table: metrics_phases (Model: PhaseMetrics)
ALTER TABLE metrics_phases ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN metrics_phases.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_metrics_phases_created_by ON metrics_phases(created_by_id);
ALTER TABLE metrics_phases ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN metrics_phases.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_metrics_phases_updated_by ON metrics_phases(updated_by_id);

-- Table: profiling_executions (Model: ProfilingExecution)
ALTER TABLE profiling_executions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_executions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_profiling_executions_created_by ON profiling_executions(created_by_id);
ALTER TABLE profiling_executions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_executions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_profiling_executions_updated_by ON profiling_executions(updated_by_id);

-- Table: scoping_submissions (Model: ScopingSubmission)
ALTER TABLE cycle_report_scoping_submissions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN scoping_submissions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_scoping_submissions_created_by ON scoping_submissions(created_by_id);
ALTER TABLE cycle_report_scoping_submissions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN scoping_submissions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_scoping_submissions_updated_by ON scoping_submissions(updated_by_id);

-- Table: workflow_transitions (Model: WorkflowTransition)
ALTER TABLE workflow_transitions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_transitions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_workflow_transitions_created_by ON workflow_transitions(created_by_id);
ALTER TABLE workflow_transitions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_transitions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_workflow_transitions_updated_by ON workflow_transitions(updated_by_id);

-- Table: sla_configurations (Model: SLAConfiguration)
ALTER TABLE sla_configurations ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sla_configurations.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_sla_configurations_created_by ON sla_configurations(created_by_id);
ALTER TABLE sla_configurations ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN sla_configurations.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_sla_configurations_updated_by ON sla_configurations(updated_by_id);

-- Table: data_profiling_files (Model: DataProfilingFile)
ALTER TABLE cycle_report_data_profiling_files ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN data_profiling_files.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_data_profiling_files_created_by ON data_profiling_files(created_by_id);
ALTER TABLE cycle_report_data_profiling_files ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN data_profiling_files.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_data_profiling_files_updated_by ON data_profiling_files(updated_by_id);

-- Table: profiling_anomaly_patterns (Model: ProfilingAnomalyPattern)
ALTER TABLE cycle_report_data_profiling_anomaly_patterns ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_anomaly_patterns.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_profiling_anomaly_patterns_created_by ON profiling_anomaly_patterns(created_by_id);
ALTER TABLE cycle_report_data_profiling_anomaly_patterns ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_anomaly_patterns.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_profiling_anomaly_patterns_updated_by ON profiling_anomaly_patterns(updated_by_id);

-- Table: secure_data_access_logs (Model: SecureDataAccess)
ALTER TABLE secure_data_access_logs ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN secure_data_access_logs.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_secure_data_access_logs_created_by ON secure_data_access_logs(created_by_id);
ALTER TABLE secure_data_access_logs ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN secure_data_access_logs.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_secure_data_access_logs_updated_by ON secure_data_access_logs(updated_by_id);

-- Table: workflow_activity_templates (Model: WorkflowActivityTemplate)
ALTER TABLE workflow_activity_templates ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_activity_templates.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_workflow_activity_templates_created_by ON workflow_activity_templates(created_by_id);
ALTER TABLE workflow_activity_templates ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_activity_templates.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_workflow_activity_templates_updated_by ON workflow_activity_templates(updated_by_id);

-- Table: database_tests (Model: DatabaseTest)
ALTER TABLE cycle_report_test_execution_database_tests ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN database_tests.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_database_tests_created_by ON database_tests(created_by_id);
ALTER TABLE cycle_report_test_execution_database_tests ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN database_tests.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_database_tests_updated_by ON database_tests(updated_by_id);

-- Table: workflow_executions (Model: WorkflowExecution)
ALTER TABLE workflow_executions ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_executions.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_workflow_executions_created_by ON workflow_executions(created_by_id);
ALTER TABLE workflow_executions ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN workflow_executions.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_workflow_executions_updated_by ON workflow_executions(updated_by_id);

-- Table: data_owner_sla_violations (Model: DataOwnerSLAViolation)
ALTER TABLE data_owner_sla_violations ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN data_owner_sla_violations.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_data_owner_sla_violations_created_by ON data_owner_sla_violations(created_by_id);
ALTER TABLE data_owner_sla_violations ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN data_owner_sla_violations.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_data_owner_sla_violations_updated_by ON data_owner_sla_violations(updated_by_id);

-- Table: observation_impact_assessments (Model: ObservationImpactAssessment)
ALTER TABLE cycle_report_observation_mgmt_impact_assessments ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_impact_assessments.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_observation_impact_assessments_created_by ON observation_impact_assessments(created_by_id);
ALTER TABLE cycle_report_observation_mgmt_impact_assessments ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN observation_impact_assessments.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_observation_impact_assessments_updated_by ON observation_impact_assessments(updated_by_id);

-- Table: profiling_rule_sets (Model: ProfilingRuleSet)
ALTER TABLE profiling_rule_sets ADD COLUMN created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_rule_sets.created_by_id IS 'ID of user who created this record';
CREATE INDEX idx_profiling_rule_sets_created_by ON profiling_rule_sets(created_by_id);
ALTER TABLE profiling_rule_sets ADD COLUMN updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;
COMMENT ON COLUMN profiling_rule_sets.updated_by_id IS 'ID of user who last updated this record';
CREATE INDEX idx_profiling_rule_sets_updated_by ON profiling_rule_sets(updated_by_id);

COMMIT;