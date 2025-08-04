import client from './client';
import { 
  PhaseVersions, 
  PhaseStatuses, 
  VersionInfo, 
  VersionHistory,
  SampleDecision,
  SampleDecisionStatus,
  SampleSelectionVersion,
  VersionComparison
} from '../types/versioning';

export const versioningApi = {
  // Get current versions for all phases
  getPhaseVersions: (workflowId: string) =>
    client.get<PhaseVersions>(`/api/v1/versions/workflow/${workflowId}/phases`),

  // Get phase statuses
  getPhaseStatuses: (workflowId: string) =>
    client.get<PhaseStatuses>(`/api/v1/versions/workflow/${workflowId}/status`),

  // Get version history for a phase
  getVersionHistory: (workflowId: string, phase: string) =>
    client.get<VersionHistory[]>(`/api/v1/versions/workflow/${workflowId}/phase/${phase}/history`),

  // Create new version
  createVersion: (workflowId: string, phase: string, data: any) =>
    client.post<VersionInfo>(`/api/v1/versions/workflow/${workflowId}/phase/${phase}`, data),

  // Approve version
  approveVersion: (workflowId: string, phase: string, versionId: string, notes?: string) =>
    client.post(`/api/v1/versions/workflow/${workflowId}/phase/${phase}/version/${versionId}/approve`, { notes }),

  // Reject version
  rejectVersion: (workflowId: string, phase: string, versionId: string, reason: string) =>
    client.post(`/api/v1/versions/workflow/${workflowId}/phase/${phase}/version/${versionId}/reject`, { reason }),

  // Compare versions
  compareVersions: (workflowId: string, phase: string, v1: string, v2: string) =>
    client.get<VersionComparison>(`/api/v1/versions/workflow/${workflowId}/phase/${phase}/compare?v1=${v1}&v2=${v2}`),

  // Sample selection specific
  getSampleSelectionVersion: (versionId: string) =>
    client.get<SampleSelectionVersion>(`/api/v1/versions/sample-selection/${versionId}`),

  // Get sample decisions
  getSampleDecisions: (versionId: string) =>
    client.get<SampleDecision[]>(`/api/v1/versions/sample-selection/${versionId}/decisions`),

  // Submit sample decisions
  submitSampleDecisions: (workflowId: string, versionId: string, decisions: Map<string, SampleDecisionStatus>) =>
    client.post(`/api/v1/versions/sample-selection/${versionId}/decisions`, {
      decisions: Array.from(decisions.entries()).map(([sampleId, status]) => ({
        sample_id: sampleId,
        decision_status: status
      }))
    }),

  // Finalize sample selection
  finalizeSampleSelection: (workflowId: string, versionId: string) =>
    client.post(`/api/v1/versions/sample-selection/${versionId}/finalize`),

  // Get specific version
  getVersion: (phase: string, versionId: string) =>
    client.get<VersionInfo>(`/api/v1/versions/phase/${phase}/version/${versionId}`),

  // Get phase history
  getPhaseHistory: (cycleId: number, reportId: number, phase: string) =>
    client.get<VersionHistory[]>(`/api/v1/versions/cycle/${cycleId}/report/${reportId}/phase/${phase}/history`)
};