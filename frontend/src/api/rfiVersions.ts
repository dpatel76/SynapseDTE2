/**
 * RFI Versions API Client
 * 
 * This module provides API methods for interacting with the RFI versioning system,
 * following the same pattern as sample selection and scoping.
 */

import apiClient from './client';
import { 
  RFIVersion, 
  RFIVersionListItem,
  RFIEvidence,
  RFIVersionCreate,
  RFIEvidenceUpdate,
  BulkEvidenceDecision,
  SendToReportOwnerRequest,
  ResubmitRequest,
  DataOwnerSubmissionSummary,
  QueryValidationRequest,
  QueryValidationResponse
} from '../types/rfiVersions';

const BASE_URL = '/rfi';

export const rfiVersionsApi = {
  /**
   * Get all versions for a cycle/report
   */
  async getVersions(cycleId: number, reportId: number): Promise<RFIVersionListItem[]> {
    const response = await apiClient.get(`${BASE_URL}/cycles/${cycleId}/reports/${reportId}/versions`);
    return response.data;
  },

  /**
   * Get a specific version with all evidence
   */
  async getVersion(versionId: string): Promise<RFIVersion> {
    const response = await apiClient.get(`${BASE_URL}/versions/${versionId}`);
    return response.data;
  },

  /**
   * Create a new version
   */
  async createVersion(
    cycleId: number, 
    reportId: number, 
    data: RFIVersionCreate
  ): Promise<RFIVersion> {
    const response = await apiClient.post(
      `${BASE_URL}/cycles/${cycleId}/reports/${reportId}/versions`,
      data
    );
    return response.data;
  },

  /**
   * Submit version for approval
   */
  async submitForApproval(versionId: string): Promise<void> {
    await apiClient.put(`${BASE_URL}/versions/${versionId}/submit-for-approval`);
  },

  /**
   * Get evidence for a version with optional filters
   */
  async getVersionEvidence(
    versionId: string,
    filters?: {
      testCaseId?: number;
      dataOwnerId?: number;
      evidenceStatus?: string;
      testerDecision?: string;
      reportOwnerDecision?: string;
    }
  ): Promise<RFIEvidence[]> {
    const params = new URLSearchParams();
    if (filters?.testCaseId) params.append('test_case_id', filters.testCaseId.toString());
    if (filters?.dataOwnerId) params.append('data_owner_id', filters.dataOwnerId.toString());
    if (filters?.evidenceStatus) params.append('evidence_status', filters.evidenceStatus);
    if (filters?.testerDecision) params.append('tester_decision', filters.testerDecision);
    if (filters?.reportOwnerDecision) params.append('report_owner_decision', filters.reportOwnerDecision);
    
    const response = await apiClient.get(
      `${BASE_URL}/versions/${versionId}/evidence${params.toString() ? '?' + params.toString() : ''}`
    );
    return response.data;
  },

  /**
   * Submit evidence for a test case
   */
  async submitEvidence(
    testCaseId: number,
    formData: FormData
  ): Promise<RFIEvidence> {
    const response = await apiClient.post(
      `${BASE_URL}/test-cases/${testCaseId}/submit-evidence`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Update tester decision on evidence
   */
  async updateTesterDecision(
    evidenceId: string,
    decision: RFIEvidenceUpdate
  ): Promise<void> {
    await apiClient.put(`${BASE_URL}/evidence/${evidenceId}/tester-decision`, decision);
  },

  /**
   * Update report owner decision on evidence
   */
  async updateReportOwnerDecision(
    evidenceId: string,
    decision: RFIEvidenceUpdate
  ): Promise<void> {
    await apiClient.put(`${BASE_URL}/evidence/${evidenceId}/report-owner-decision`, decision);
  },

  /**
   * Apply bulk tester decision
   */
  async bulkTesterDecision(
    versionId: string,
    data: BulkEvidenceDecision
  ): Promise<void> {
    await apiClient.post(`${BASE_URL}/versions/${versionId}/bulk-tester-decision`, data);
  },

  /**
   * Send evidence to report owner for review
   */
  async sendToReportOwner(
    versionId: string,
    data: SendToReportOwnerRequest = {}
  ): Promise<{ message: string; assignment_id: string; evidence_count: number }> {
    const response = await apiClient.post(
      `${BASE_URL}/versions/${versionId}/send-to-report-owner`,
      data
    );
    return response.data;
  },

  /**
   * Create new version for resubmission after report owner feedback
   */
  async resubmitAfterFeedback(
    versionId: string,
    data: ResubmitRequest = { carry_forward_approved: true, reset_rejected: true }
  ): Promise<RFIVersion> {
    const response = await apiClient.post(
      `${BASE_URL}/versions/${versionId}/resubmit-after-feedback`,
      data
    );
    return response.data;
  },

  /**
   * Get submission status by data owner
   */
  async getSubmissionStatus(
    cycleId: number,
    reportId: number,
    versionId?: string
  ): Promise<DataOwnerSubmissionSummary[]> {
    const params = new URLSearchParams();
    if (versionId) params.append('version_id', versionId);
    
    const response = await apiClient.get(
      `${BASE_URL}/cycles/${cycleId}/reports/${reportId}/submission-status${params.toString() ? '?' + params.toString() : ''}`
    );
    return response.data;
  },

  /**
   * Validate query before submission
   */
  async validateQuery(data: QueryValidationRequest): Promise<QueryValidationResponse> {
    const response = await apiClient.post(`${BASE_URL}/query-validation`, data);
    return response.data;
  },
};