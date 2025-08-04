import { useState, useEffect, useCallback } from 'react';
import { temporalApi } from '../api/temporal';
import { versioningApi } from '../api/versioning';
import { 
  PhaseVersions, 
  PhaseStatuses, 
  PendingApproval, 
  VersionInfo,
  VersionHistory,
  VersionComparison
} from '../types/versioning';

interface UseWorkflowVersioningReturn {
  phaseVersions: PhaseVersions;
  phaseStatuses: PhaseStatuses;
  pendingApprovals: PendingApproval[];
  loading: boolean;
  error: string | null;
  refreshVersions: () => Promise<void>;
  submitApproval: (
    phase: string, 
    versionId: string, 
    approved: boolean, 
    notes?: string
  ) => Promise<void>;
  submitSampleReview: (
    versionId: string,
    decisions: any[],
    needsRevision: boolean,
    additionalSamples?: any[]
  ) => Promise<void>;
  getVersionHistory: (phase: string) => Promise<VersionHistory[]>;
  compareVersions: (
    phase: string, 
    versionId1: string, 
    versionId2: string
  ) => Promise<VersionComparison>;
  getVersionDetails: (phase: string, versionId: string) => Promise<VersionInfo>;
}

export const useWorkflowVersioning = (workflowId: string): UseWorkflowVersioningReturn => {
  const [phaseVersions, setPhaseVersions] = useState<PhaseVersions>({});
  const [phaseStatuses, setPhaseStatuses] = useState<PhaseStatuses>({});
  const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkflowState = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Query workflow for current state
      const [versionsResponse, statusesResponse, approvalsResponse] = await Promise.all([
        temporalApi.queryWorkflow(workflowId, 'get_phase_versions'),
        temporalApi.queryWorkflow(workflowId, 'get_phase_statuses'),
        temporalApi.queryWorkflow(workflowId, 'get_pending_approvals')
      ]);
      
      const versions = versionsResponse.data;
      const statuses = statusesResponse.data;
      const approvals = approvalsResponse.data;

      // Fetch detailed version info for each phase
      const detailedVersions: PhaseVersions = {};
      for (const [phase, versionId] of Object.entries(versions)) {
        if (versionId) {
          try {
            const versionInfo = await versioningApi.getVersion(phase, versionId as string);
            detailedVersions[phase] = versionInfo.data;
          } catch (err) {
            console.error(`Failed to fetch version for ${phase}:`, err);
          }
        }
      }

      setPhaseVersions(detailedVersions);
      setPhaseStatuses(statuses);
      setPendingApprovals(approvals);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch workflow state');
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  useEffect(() => {
    fetchWorkflowState();
    
    // Set up polling for updates
    const interval = setInterval(fetchWorkflowState, 30000); // Poll every 30 seconds
    
    return () => clearInterval(interval);
  }, [fetchWorkflowState]);

  const submitApproval = useCallback(async (
    phase: string,
    versionId: string,
    approved: boolean,
    notes?: string
  ) => {
    try {
      // Send approval signal to workflow
      await temporalApi.sendSignal(workflowId, 'submit_version_approval', {
        phase_name: phase,
        version_id: versionId,
        user_id: getCurrentUserId(), // Implement this based on your auth
        approved,
        notes
      });

      // Refresh state after approval
      await fetchWorkflowState();
    } catch (err) {
      throw new Error(`Failed to submit approval: ${err}`);
    }
  }, [workflowId, fetchWorkflowState]);

  const submitSampleReview = useCallback(async (
    versionId: string,
    decisions: any[],
    needsRevision: boolean,
    additionalSamples?: any[]
  ) => {
    try {
      await temporalApi.sendSignal(workflowId, 'submit_sample_review', {
        user_id: getCurrentUserId(),
        approved: !needsRevision && decisions.every(d => d.status !== 'rejected'),
        needs_revision: needsRevision,
        decisions,
        additional_samples: additionalSamples
      });

      await fetchWorkflowState();
    } catch (err) {
      throw new Error(`Failed to submit sample review: ${err}`);
    }
  }, [workflowId, fetchWorkflowState]);

  const getVersionHistory = useCallback(async (phase: string): Promise<VersionHistory[]> => {
    try {
      const cycleId = extractCycleId(workflowId); // Implement based on your workflow ID format
      const reportId = extractReportId(workflowId);
      
      const response = await versioningApi.getPhaseHistory(cycleId, reportId, phase);
      return response.data;
    } catch (err) {
      throw new Error(`Failed to fetch version history: ${err}`);
    }
  }, [workflowId]);

  const compareVersions = useCallback(async (
    phase: string,
    versionId1: string,
    versionId2: string
  ): Promise<VersionComparison> => {
    try {
      const response = await versioningApi.compareVersions(workflowId, phase, versionId1, versionId2);
      return response.data;
    } catch (err) {
      throw new Error(`Failed to compare versions: ${err}`);
    }
  }, [workflowId]);

  const getVersionDetails = useCallback(async (
    phase: string,
    versionId: string
  ): Promise<VersionInfo> => {
    try {
      const response = await versioningApi.getVersion(phase, versionId);
      return response.data;
    } catch (err) {
      throw new Error(`Failed to fetch version details: ${err}`);
    }
  }, []);

  return {
    phaseVersions,
    phaseStatuses,
    pendingApprovals,
    loading,
    error,
    refreshVersions: fetchWorkflowState,
    submitApproval,
    submitSampleReview,
    getVersionHistory,
    compareVersions,
    getVersionDetails
  };
};

// Helper functions (implement based on your auth and workflow ID format)
function getCurrentUserId(): number {
  // Get from your auth context/store
  return 1; // Placeholder
}

function extractCycleId(workflowId: string): number {
  // Extract from workflow ID format
  const match = workflowId.match(/cycle-(\d+)/);
  return match ? parseInt(match[1]) : 0;
}

function extractReportId(workflowId: string): number {
  // Extract from workflow ID format
  const match = workflowId.match(/report-(\d+)/);
  return match ? parseInt(match[1]) : 0;
}