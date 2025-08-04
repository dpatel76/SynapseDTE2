import apiClient from './client';

export interface TestCase {
  test_case_id: string;
  attribute_name: string;
  sample_identifier: string;
  primary_key_attributes: Record<string, any>;
  submission_deadline: string;
  special_instructions: string;
  status: string;
}

export interface DataSource {
  id: number;
  name: string;
  description: string;
  data_source_type: string;
}

export interface Evidence {
  id: number;
  evidence_type: 'document' | 'data_source';
  version_number: number;
  is_current: boolean;
  validation_status: string;
  validation_notes: string;
  submitted_at: string;
  submission_notes: string;
  // Document fields
  document_name?: string;
  document_size?: number;
  mime_type?: string;
  // Data source fields
  data_source_id?: number;
  query_text?: string;
  query_parameters?: Record<string, any>;
  query_result_sample?: Record<string, any>;
}

export interface ValidationResult {
  rule: string;
  result: 'passed' | 'failed' | 'warning';
  message: string;
  validated_at: string;
}

export interface TesterDecision {
  decision: 'approved' | 'rejected' | 'requires_revision';
  decision_notes: string;
  decision_date: string;
  decided_by_name: string;
  requires_resubmission: boolean;
  resubmission_deadline?: string;
  follow_up_instructions?: string;
}

export interface EvidencePortalData {
  test_case: TestCase;
  current_evidence?: Evidence;
  validation_results: ValidationResult[];
  tester_decisions: TesterDecision[];
  available_data_sources: DataSource[];
  can_submit_evidence: boolean;
  can_resubmit: boolean;
}

export interface EvidenceSubmissionData {
  data_source_id: number;
  query_text: string;
  query_parameters?: Record<string, any>;
  submission_notes?: string;
}

export interface TesterDecisionData {
  decision: 'approved' | 'rejected' | 'requires_revision';
  decision_notes: string;
  requires_resubmission: boolean;
  resubmission_deadline?: string;
  follow_up_instructions?: string;
}

export interface EvidenceForReview {
  evidence_id: number;
  test_case_id: string;
  sample_id: string;
  attribute_name: string;
  evidence_type: 'document' | 'data_source';
  submitted_by: string;
  submitted_at: string;
  validation_status: string;
  validation_notes: string;
  submission_notes: string;
  // Document fields
  document_name?: string;
  document_size?: number;
  mime_type?: string;
  // Data source fields
  data_source_id?: number;
  query_text?: string;
  query_result_sample?: Record<string, any>;
  // Validation results
  validation_results: ValidationResult[];
}

export class RequestInfoAPI {
  /**
   * Get evidence portal data for a test case (Data Owner)
   */
  static async getEvidencePortalData(testCaseId: string): Promise<EvidencePortalData> {
    const response = await apiClient.get(`/request-info/data-owner/test-cases/${testCaseId}/evidence-portal`);
    return response.data;
  }

  /**
   * Submit document evidence for a test case
   */
  static async submitDocumentEvidence(testCaseId: string, formData: FormData): Promise<any> {
    const response = await apiClient.post(
      `/request-info/test-cases/${testCaseId}/evidence/document`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * Submit data source evidence for a test case
   */
  static async submitDataSourceEvidence(testCaseId: string, data: EvidenceSubmissionData): Promise<any> {
    const response = await apiClient.post(
      `/request-info/test-cases/${testCaseId}/evidence/data-source`,
      data
    );
    return response.data;
  }

  /**
   * Get evidence for a test case
   */
  static async getTestCaseEvidence(testCaseId: string): Promise<any> {
    const response = await apiClient.get(`/request-info/test-cases/${testCaseId}/evidence`);
    return response.data;
  }

  /**
   * Get evidence pending review for a phase (Tester)
   */
  static async getEvidencePendingReview(phaseId: number): Promise<EvidenceForReview[]> {
    const response = await apiClient.get(`/request-info/phases/${phaseId}/evidence/pending-review`);
    return response.data;
  }

  /**
   * Submit tester decision on evidence
   */
  static async submitTesterDecision(evidenceId: number, decision: TesterDecisionData): Promise<any> {
    const response = await apiClient.post(
      `/request-info/evidence/${evidenceId}/review`,
      decision
    );
    return response.data;
  }

  /**
   * Get evidence validation details
   */
  static async getEvidenceValidation(evidenceId: number): Promise<any> {
    const response = await apiClient.get(`/request-info/evidence/${evidenceId}/validation`);
    return response.data;
  }

  /**
   * Revalidate evidence
   */
  static async revalidateEvidence(evidenceId: number): Promise<any> {
    const response = await apiClient.post(`/request-info/evidence/${evidenceId}/revalidate`);
    return response.data;
  }

  /**
   * Get evidence collection progress for a phase
   */
  static async getEvidenceProgress(phaseId: number): Promise<any> {
    const response = await apiClient.get(`/request-info/phases/${phaseId}/evidence/progress`);
    return response.data;
  }

  // Legacy endpoints for backward compatibility
  
  /**
   * Get test cases for data owner
   */
  static async getDataOwnerTestCases(status?: string): Promise<any> {
    const params = status ? { status } : {};
    const response = await apiClient.get('/request-info/data-owner/test-cases', { params });
    return response.data;
  }

  /**
   * Get test case details
   */
  static async getTestCase(testCaseId: string): Promise<any> {
    const response = await apiClient.get(`/request-info/test-cases/${testCaseId}`);
    return response.data;
  }

  /**
   * Submit document for test case (legacy)
   */
  static async submitDocument(testCaseId: string, formData: FormData): Promise<any> {
    const response = await apiClient.post(
      `/request-info/test-cases/${testCaseId}/submit`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * Get test case submissions
   */
  static async getTestCaseSubmissions(testCaseId: string, includeAllRevisions = false): Promise<any> {
    const response = await apiClient.get(
      `/request-info/test-cases/${testCaseId}/submissions`,
      {
        params: { include_all_revisions: includeAllRevisions },
      }
    );
    return response.data;
  }

  /**
   * Get test cases for a cycle/report
   */
  static async getCycleReportTestCases(
    cycleId: number,
    reportId: number,
    filters?: { data_owner_id?: number; status?: string }
  ): Promise<any> {
    const params = filters || {};
    const response = await apiClient.get(
      `/request-info/cycles/${cycleId}/reports/${reportId}/test-cases`,
      { params }
    );
    return response.data;
  }

  /**
   * Get request info phase status
   */
  static async getPhaseStatus(cycleId: number, reportId: number): Promise<any> {
    const response = await apiClient.get(`/request-info/${cycleId}/reports/${reportId}/status`);
    return response.data;
  }

  /**
   * Start request info phase
   */
  static async startPhase(cycleId: number, reportId: number, data: any): Promise<any> {
    const response = await apiClient.post(`/request-info/${cycleId}/reports/${reportId}/start`, data);
    return response.data;
  }

  /**
   * Complete request info phase
   */
  static async completePhase(cycleId: number, reportId: number, data: any): Promise<any> {
    const response = await apiClient.post(`/request-info/${cycleId}/reports/${reportId}/complete`, data);
    return response.data;
  }

  /**
   * Get phase progress
   */
  static async getPhaseProgress(cycleId: number, reportId: number): Promise<any> {
    const response = await apiClient.get(`/request-info/${cycleId}/reports/${reportId}/progress`);
    return response.data;
  }

  /**
   * Get data owner assignments
   */
  static async getDataOwnerAssignments(cycleId: number, reportId: number): Promise<any> {
    const response = await apiClient.get(`/request-info/${cycleId}/reports/${reportId}/assignments`);
    return response.data;
  }

  /**
   * Create test case
   */
  static async createTestCase(cycleId: number, reportId: number, data: any): Promise<any> {
    const response = await apiClient.post(`/request-info/${cycleId}/reports/${reportId}/test-cases`, data);
    return response.data;
  }

  /**
   * Bulk create test cases
   */
  static async bulkCreateTestCases(cycleId: number, reportId: number, data: any): Promise<any> {
    const response = await apiClient.post(`/request-info/${cycleId}/reports/${reportId}/test-cases/bulk`, data);
    return response.data;
  }

  /**
   * Resend test case
   */
  static async resendTestCase(testCaseId: string, data: any): Promise<any> {
    const response = await apiClient.post(`/request-info/test-cases/${testCaseId}/resend`, data);
    return response.data;
  }

  /**
   * Reupload document
   */
  static async reuploadDocument(submissionId: string, formData: FormData): Promise<any> {
    const response = await apiClient.post(
      `/request-info/submissions/${submissionId}/reupload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * List test cases with filters
   */
  static async listTestCases(
    cycleId: number,
    reportId: number,
    filters?: { status?: string; data_owner_id?: number }
  ): Promise<any> {
    const params = filters || {};
    const response = await apiClient.get(
      `/request-info/${cycleId}/reports/${reportId}/test-cases`,
      { params }
    );
    return response.data;
  }
}

export default RequestInfoAPI;