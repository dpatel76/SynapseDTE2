import apiClient from './client';

export interface DataProfilingStatus {
  cycle_id: number;
  report_id: number;
  phase_status: string;
  files_uploaded: number;
  rules_generated: number;
  rules_approved: number;
  profiling_completed: boolean;
  can_upload_files: boolean;
  can_generate_rules: boolean;
  can_execute_profiling: boolean;
  can_complete: boolean;
  data_requested_at?: string;
  data_received_at?: string;
  rules_generated_at?: string;
  profiling_executed_at?: string;
  // Enhanced metrics fields
  total_attributes?: number;
  attributes_with_rules?: number;
  total_profiling_rules?: number;
  attributes_with_anomalies?: number;
  cdes_with_anomalies?: number;
  days_elapsed?: number;
  completion_percentage?: number;
  can_start_phase?: boolean;
  can_complete_phase?: boolean;
  started_at?: string;
  completed_at?: string;
}

export interface DataFile {
  file_id: number;
  file_name: string;
  file_format: string;
  file_size: number;
  row_count?: number;
  column_count?: number;
  is_validated: boolean;
  validation_errors?: string[];
  uploaded_by: number;
  uploaded_at: string;
}

export interface ProfilingRule {
  rule_id: number;
  attribute_id: number;
  rule_name: string;
  rule_type: string;
  rule_description?: string;
  rule_logic?: string;
  expected_result?: string;
  severity?: string;
  status: 'pending' | 'approved' | 'rejected' | 'needs_revision' | 'draft' | 'under_review' | 'resubmitted';
  version_number: number;
  is_current_version: boolean;
  business_key: string;
  approved_by?: number;
  approved_at?: string;
  approval_notes?: string;
  rejected_by?: number;
  rejected_at?: string;
  rejection_reason?: string;
  rejection_notes?: string;
  revision_notes?: string;
  llm_rationale?: string;
  regulatory_reference?: string;
  is_executable: boolean;
  can_approve: boolean;
  can_reject: boolean;
  can_revise: boolean;
  created_by?: number;
  created_at?: string;
  updated_by?: number;
  updated_at?: string;
}

export interface AttributeRulesSummary {
  attribute_id: number;
  attribute_name: string;
  attribute_type: string;
  mandatory: boolean;
  total_rules: number;
  approved_count: number;
  rejected_count: number;
  pending_count: number;
  needs_revision_count: number;
  last_updated?: string;
  can_approve: boolean;
  can_edit: boolean;
  line_item_number?: string;
  is_cde: boolean;
  is_primary_key: boolean;
  has_issues: boolean;
}

export interface ProfilingResult {
  result_id: number;
  rule_id: number;
  attribute_id: number;
  execution_status: string;
  passed_count: number;
  failed_count: number;
  total_count: number;
  pass_rate: number;
  severity: string;
  has_anomaly: boolean;
  anomaly_description?: string;
  executed_at: string;
}

export interface QualityScore {
  attribute_id: number;
  attribute_name: string;
  overall_quality_score: number;
  completeness_score: number;
  validity_score: number;
  accuracy_score: number;
  consistency_score: number;
  uniqueness_score: number;
  has_anomalies: boolean;
  anomaly_count: number;
  testing_recommendation?: string;
  risk_assessment?: string;
}

// Database Profiling Interfaces
export interface ProfilingConfiguration {
  id?: number;
  name: string;
  description?: string;
  source_type: 'file_upload' | 'database_direct' | 'api' | 'streaming';
  profiling_mode: 'full_scan' | 'sample_based' | 'incremental' | 'streaming';
  data_source_id?: number | null;
  file_upload_id?: number | null;
  use_timeframe: boolean;
  timeframe_start?: string | null;
  timeframe_end?: string | null;
  timeframe_column?: string;
  sample_size?: number | null;
  sample_percentage?: number;
  sample_method: string;
  partition_column?: string;
  partition_count?: number;
  max_memory_mb?: number;
  custom_query?: string;
  table_name?: string;
  schema_name?: string;
  where_clause?: string;
  exclude_columns?: string[];
  include_columns?: string[];
  profile_relationships?: boolean;
  profile_distributions?: boolean;
  profile_patterns?: boolean;
  detect_anomalies?: boolean;
  is_scheduled?: boolean;
  schedule_cron?: string;
}

export interface ProfilingJob {
  id: number;
  configuration_id: number;
  job_id: string;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  total_records?: number;
  records_processed?: number;
  records_failed?: number;
  processing_rate?: number;
  memory_peak_mb?: number;
  cpu_peak_percent?: number;
  anomalies_detected?: number;
  data_quality_score?: number;
  error_message?: string;
  retry_count?: number;
  created_at: string;
  updated_at: string;
}

export interface FileValidationResult {
  file_id: number;
  file_name: string;
  is_valid: boolean;
  errors: string[];
  missing_attributes: string[];
}

class DataProfilingAPI {
  async startPhase(cycleId: number, reportId: number) {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/start`
    );
    return response.data;
  }

  async getStatus(cycleId: number, reportId: number): Promise<DataProfilingStatus> {
    const response = await apiClient.get(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/status`
    );
    return response.data;
  }

  async requestData(cycleId: number, reportId: number, message?: string) {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/request-data`,
      { message }
    );
    return response.data;
  }

  // REMOVED: Role-specific assignment methods - use universal assignments instead
  // Use the universal assignment API through useUniversalAssignments hook

  async uploadFile(cycleId: number, reportId: number, file: File, delimiter?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (delimiter) {
      formData.append('delimiter', delimiter);
    }

    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/upload-file`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async getFiles(cycleId: number, reportId: number): Promise<DataFile[]> {
    const response = await apiClient.get(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/files`
    );
    return response.data;
  }

  async deleteFile(cycleId: number, reportId: number, fileId: number) {
    const response = await apiClient.delete(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/files/${fileId}`
    );
    return response.data;
  }

  async validateFiles(cycleId: number, reportId: number) {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/validate-files`
    );
    return response.data;
  }

  async generateRules(cycleId: number, reportId: number, preferredProvider = 'claude') {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/generate-rules?preferred_provider=${preferredProvider}`
    );
    return response.data;
  }

  async getRules(cycleId: number, reportId: number, status?: string, versionId?: string, testerDecision?: string, reportOwnerDecision?: string): Promise<ProfilingRule[]> {
    const params: any = {};
    if (status) params.status = status;
    if (versionId) params.version_id = versionId;
    if (testerDecision) params.tester_decision = testerDecision;
    if (reportOwnerDecision) params.report_owner_decision = reportOwnerDecision;
    
    const response = await apiClient.get(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/rules`,
      { params }
    );
    return response.data;
  }
  
  async getVersions(cycleId: number, reportId: number): Promise<any[]> {
    const response = await apiClient.get(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/versions`
    );
    return response.data;
  }

  async approveRuleOld(cycleId: number, reportId: number, ruleId: number, approvalNotes?: string) {
    const response = await apiClient.put(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/rules/${ruleId}/approve`,
      { approval_notes: approvalNotes }
    );
    return response.data;
  }

  // Enhanced endpoints for individual rule management
  async getAttributeRulesSummary(cycleId: number, reportId: number): Promise<AttributeRulesSummary[]> {
    const response = await apiClient.get(
      `/data-profiling/attributes/${cycleId}/${reportId}/rules-summary`
    );
    return response.data;
  }

  async getAttributeRules(attributeId: number, cycleId: number, reportId: number, includeHistory = false): Promise<ProfilingRule[]> {
    const response = await apiClient.get(
      `/data-profiling/attributes/${attributeId}/rules`,
      { params: { cycle_id: cycleId, report_id: reportId, include_history: includeHistory } }
    );
    return response.data;
  }

  async approveRule(ruleId: number, notes?: string) {
    const response = await apiClient.put(
      `/data-profiling/rules/${ruleId}/approve`,
      { notes }
    );
    return response.data;
  }

  async rejectRule(ruleId: number, reason: string, notes?: string, allowRevision = true) {
    const response = await apiClient.put(
      `/data-profiling/rules/${ruleId}/reject`,
      { 
        reason,
        notes,
        allow_revision: allowRevision
      }
    );
    return response.data;
  }

  async resetRuleToPending(ruleId: number) {
    const response = await apiClient.put(
      `/data-profiling/rules/${ruleId}/reset-pending`
    );
    return response.data;
  }

  async deleteRule(ruleId: number) {
    const response = await apiClient.delete(
      `/data-profiling/rules/${ruleId}`
    );
    return response.data;
  }

  // Deprecated methods - keeping for backward compatibility
  async approveIndividualRule(ruleId: number, notes?: string) {
    return this.approveRule(ruleId, notes);
  }

  async rejectIndividualRule(ruleId: number, reason: string, notes?: string, allowRevision = true) {
    return this.rejectRule(ruleId, reason, notes, allowRevision);
  }


  async getRuleHistory(ruleId: number): Promise<ProfilingRule[]> {
    const response = await apiClient.get(
      `/data-profiling/rules/${ruleId}/history`
    );
    return response.data;
  }

  async bulkApproveRules(ruleIds: string[], notes?: string) {
    const response = await apiClient.post(
      `/data-profiling/rules/bulk-approve`,
      { rule_ids: ruleIds, notes }
    );
    return response.data;
  }

  async bulkRejectRules(ruleIds: string[], reason: string, notes?: string, allowRevision = true) {
    const response = await apiClient.post(
      `/data-profiling/rules/bulk-reject`,
      { 
        rule_ids: ruleIds,
        reason,
        notes,
        allow_revision: allowRevision
      }
    );
    return response.data;
  }

  async executeProfiling(cycleId: number, reportId: number, versionId?: string) {
    // If versionId is provided, use the version-specific endpoint
    if (versionId) {
      const response = await apiClient.post(
        `/data-profiling/versions/${versionId}/execute`
      );
      return response.data;
    }
    
    // Otherwise use the cycle/report endpoint (which will use the latest version)
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/execute-profiling`
    );
    return response.data;
  }

  async markExecutionComplete(cycleId: number, reportId: number) {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/mark-execution-complete`
    );
    return response.data;
  }

  async checkJobStatus(jobId: string) {
    const response = await apiClient.get(
      `/data-profiling/jobs/${jobId}/status`
    );
    return response.data;
  }

  async getResults(cycleId: number, reportId: number, attributeId?: number): Promise<ProfilingResult[]> {
    const params = attributeId ? { attribute_id: attributeId } : {};
    const response = await apiClient.get(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/results`,
      { params }
    );
    // Handle both array and object with results property
    if (Array.isArray(response.data)) {
      return response.data;
    } else if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    } else {
      console.error('Unexpected results format:', response.data);
      return [];
    }
  }

  async getFailedRecords(
    resultId: number, 
    limit = 100, 
    offset = 0
  ): Promise<{
    result_id: number;
    rule_name: string;
    rule_type: string;
    attribute_tested: string;
    primary_key_attributes: string[];
    total_failed: number;
    records_returned: number;
    limit: number;
    offset: number;
    error?: string;
    failed_records: Array<{
      row_number: number;
      record_id?: string | number;
      primary_key_values: Record<string, any>;
      tested_attribute: {
        name: string;
        column: string;
        value: any;
      };
      failure_reason: string;
    }>;
  }> {
    const response = await apiClient.get(
      `/data-profiling/results/${resultId}/failed-records`,
      { params: { limit, offset } }
    );
    return response.data;
  }

  async getQualityScores(cycleId: number, reportId: number): Promise<QualityScore[]> {
    const response = await apiClient.get(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/quality-scores`
    );
    return response.data;
  }

  async completePhase(cycleId: number, reportId: number) {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/complete`
    );
    return response.data;
  }

  async sendToReportOwner(cycleId: number, reportId: number) {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/send-to-report-owner`
    );
    return response.data;
  }

  async updateReportOwnerDecision(
    cycleId: number, 
    reportId: number, 
    ruleId: number, 
    decision: 'APPROVED' | 'REJECTED',
    reason?: string,
    notes?: string
  ) {
    const response = await apiClient.put(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/rules/${ruleId}/report-owner-decision`,
      { decision, reason, notes }
    );
    return response.data;
  }


  // Get rules assigned to report owner for approval
  async getAssignedRulesForApproval(cycleId: number, reportId: number) {
    try {
      const response = await apiClient.get(`/data-profiling/cycles/${cycleId}/reports/${reportId}/assigned-rules`);
      return response.data;
    } catch (error) {
      console.error('Failed to get assigned rules for approval:', error);
      throw error;
    }
  }

  // Report owner specific approval (separate from tester approval)
  async reportOwnerApproveRule(cycleId: number, reportId: number, ruleId: number, notes?: string) {
    try {
      const response = await apiClient.put(
        `/data-profiling/cycles/${cycleId}/reports/${reportId}/rules/${ruleId}/report-owner-approve`,
        { notes: notes || '' }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to approve rule as report owner:', error);
      throw error;
    }
  }

  // Report owner specific rejection (separate from tester rejection)
  async reportOwnerRejectRule(cycleId: number, reportId: number, ruleId: number, reason: string, notes?: string) {
    try {
      const response = await apiClient.put(
        `/data-profiling/cycles/${cycleId}/reports/${reportId}/rules/${ruleId}/report-owner-reject`,
        { reason, notes: notes || '' }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to reject rule as report owner:', error);
      throw error;
    }
  }


  // Revise a rule that was rejected by report owner
  async reviseRuleForReportOwner(cycleId: number, reportId: number, ruleId: number, revisionData: {
    rule_name?: string;
    rule_description?: string;
    rule_logic?: string;
    rule_code?: string;
    revision_notes: string;
  }) {
    try {
      // Use the existing approve endpoint with revision flag
      const response = await apiClient.put(
        `/data-profiling/cycles/${cycleId}/reports/${reportId}/rules/${ruleId}/approve`,
        {
          ...revisionData,
          is_revision: true,
          approval_notes: revisionData.revision_notes
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to revise rule:', error);
      throw error;
    }
  }

  // Get version history for a specific rule
  async getRuleVersionHistory(cycleId: number, reportId: number, ruleId: number) {
    try {
      const response = await apiClient.get(
        `/data-profiling/cycles/${cycleId}/reports/${reportId}/rules/${ruleId}/versions`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get rule version history:', error);
      throw error;
    }
  }

  // Get rules from prior versions that can be added
  async getPriorVersionRules(cycleId: number, reportId: number, attributeId?: number) {
    try {
      const params = attributeId ? { attribute_id: attributeId } : {};
      const response = await apiClient.get(
        `/data-profiling/cycles/${cycleId}/reports/${reportId}/rules/prior-versions`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get prior version rules:', error);
      throw error;
    }
  }

  // Add a rule from a prior version
  async addRuleFromPriorVersion(cycleId: number, reportId: number, priorRuleId: number) {
    try {
      const response = await apiClient.post(
        `/data-profiling/cycles/${cycleId}/reports/${reportId}/rules/add-from-prior-version`,
        { prior_rule_id: priorRuleId }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to add rule from prior version:', error);
      throw error;
    }
  }

  // Get rules with option to include all versions
  async getRulesWithVersions(cycleId: number, reportId: number, includeVersions: boolean = false) {
    try {
      const response = await apiClient.get(
        `/data-profiling/cycles/${cycleId}/reports/${reportId}/rules`,
        { params: { include_versions: includeVersions } }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get rules with versions:', error);
      throw error;
    }
  }

  // Database Profiling Methods
  async createConfiguration(
    cycleId: number,
    reportId: number,
    config: ProfilingConfiguration
  ): Promise<ProfilingConfiguration> {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/profiling-configurations`,
      config
    );
    return response.data;
  }

  async getConfigurations(
    cycleId: number,
    reportId: number
  ): Promise<ProfilingConfiguration[]> {
    const response = await apiClient.get(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/profiling-configurations`
    );
    return response.data;
  }

  async startProfilingJob(
    cycleId: number,
    reportId: number,
    configId: number,
    runAsync: boolean = true
  ): Promise<ProfilingJob> {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/profiling-configurations/${configId}/start`,
      { run_async: runAsync }
    );
    return response.data;
  }

  async getJobs(
    cycleId: number,
    reportId: number,
    status?: string
  ): Promise<ProfilingJob[]> {
    const params = status ? { status } : {};
    const response = await apiClient.get(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/profiling-jobs`,
      { params }
    );
    return response.data;
  }

  async getJobProgress(
    cycleId: number,
    reportId: number,
    jobId: number
  ): Promise<{ progress_percentage: number; status: string; records_processed: number }> {
    const response = await apiClient.get(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/profiling-jobs/${jobId}/progress`
    );
    return response.data;
  }

  // Resubmit after report owner feedback
  async resubmitAfterFeedback(cycleId: number, reportId: number) {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/resubmit-after-feedback`
    );
    return response.data;
  }

  // Check and auto-approve version if all decisions match
  async checkAndApproveVersion(cycleId: number, reportId: number) {
    const response = await apiClient.post(
      `/data-profiling/cycles/${cycleId}/reports/${reportId}/check-and-approve-version`
    );
    return response.data;
  }

  // Manual version approval/rejection by report owner
  async approveVersion(versionId: string, approved: boolean, approvalNotes?: string) {
    const response = await apiClient.post(
      `/data-profiling/versions/${versionId}/approve`,
      {
        approved,
        approval_notes: approvalNotes
      }
    );
    return response.data;
  }
}

export const dataProfilingApi = new DataProfilingAPI();