import apiClient from '../api/client';

export const requestInfoService = {
  // Get test case evidence details (same view as data owner)
  getTestCaseEvidenceDetails: (testCaseId: string) => {
    return apiClient.get(`/request-info/test-cases/${testCaseId}/evidence-details`);
  },

  // Other request info related methods can be added here
};