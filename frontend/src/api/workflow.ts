/**
 * Workflow Orchestrator API Client
 * Handles workflow initialization, status tracking, and phase transitions with date management
 */

import apiClient from './client';

export interface WorkflowPhase {
  phase_id: number;
  phase_name: string;
  
  // Legacy status (for backward compatibility)
  status: 'Not Started' | 'In Progress' | 'Complete' | 'Pending Approval';
  
  // Enhanced state and status tracking
  state: 'Not Started' | 'In Progress' | 'Complete';
  schedule_status: 'On Track' | 'At Risk' | 'Past Due';
  
  // Override capabilities
  state_override?: 'Not Started' | 'In Progress' | 'Complete' | null;
  status_override?: 'On Track' | 'At Risk' | 'Past Due' | null;
  override_reason?: string | null;
  override_by?: number | null;
  override_at?: string | null;
  
  // Date tracking
  planned_start_date?: string;
  planned_end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  
  // User tracking
  started_by?: number | null;
  completed_by?: number | null;
  notes?: string | null;
  
  // Computed fields
  effective_state: 'Not Started' | 'In Progress' | 'Complete';
  effective_status: 'On Track' | 'At Risk' | 'Past Due';
  has_overrides: boolean;
  days_until_due?: number | null;
  is_overdue: boolean;
  is_at_risk: boolean;
  progress_percentage?: number;
  
  // Legacy fields for compatibility
  can_start: boolean;
  dependencies: string[];
}

export interface WorkflowPhaseOverride {
  state_override?: 'Not Started' | 'In Progress' | 'Complete' | null;
  status_override?: 'On Track' | 'At Risk' | 'Past Due' | null;
  override_reason: string;
}

export interface WorkflowStatus {
  cycle_id: number;
  report_id: number;
  overall_state: 'Not Started' | 'In Progress' | 'Complete';
  overall_status: 'On Track' | 'At Risk' | 'Past Due';
  overall_progress: number;
  current_phase: string | null;
  completed_phases: number;
  total_phases: number;
  phases: WorkflowPhase[];
  phase_summary: {
    state_distribution: Record<string, number>;
    status_distribution: Record<string, number>;
    total_overrides: number;
    overdue_phases: number;
    at_risk_phases: number;
  };
}

export interface WorkflowInitializationResult {
  message: string;
  cycle_id: number;
  report_id: number;
  tester_id: number;
  phases_created: number;
  phase_names: string[];
}

export interface PhaseTransitionResult {
  completed_phase: string;
  completion_time: string;
  enabled_phases: string[];
  can_proceed: boolean;
}

export interface PhaseTransitionRequest {
  action: 'start' | 'complete' | 'update_dates';
  planned_start_date?: string;
  planned_end_date?: string;
  notes?: string;
}

export interface WorkflowPhaseUpdate {
  status?: string;
  planned_start_date?: string | null;
  planned_end_date?: string | null;
  actual_start_date?: string;
  actual_end_date?: string;
  notes?: string;
}

export interface DependencyCheck {
  cycle_id: number;
  report_id: number;
  phase_name: string;
  can_start: boolean;
  blocking_phases: string[];
  dependencies: string[];
}

export const workflowApi = {
  /**
   * Initialize all workflow phases for a report
   */
  async initializeWorkflow(cycleId: number, reportId: number): Promise<WorkflowInitializationResult> {
    const response = await apiClient.post(
      `/cycle-reports/${cycleId}/reports/${reportId}/initialize-workflow`
    );
    return response.data;
  },

  /**
   * Get comprehensive workflow status for a report
   */
  async getWorkflowStatus(cycleId: number, reportId: number): Promise<WorkflowStatus | null> {
    try {
      const response = await apiClient.get(
        `/cycle-reports/${cycleId}/reports/${reportId}/workflow-status`
      );
      return response.data;
    } catch (error: any) {
      // If 404, workflow doesn't exist yet
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  /**
   * Check if a specific phase can be started based on dependencies
   */
  async checkPhaseDependencies(cycleId: number, reportId: number, phaseName: string): Promise<DependencyCheck> {
    const response = await apiClient.get(
      `/cycle-reports/${cycleId}/reports/${reportId}/phase-dependencies/${phaseName}`
    );
    return response.data;
  },

  /**
   * Complete a phase and trigger automatic transitions
   */
  async completePhase(cycleId: number, reportId: number, phaseName: string, notes?: string): Promise<PhaseTransitionResult> {
    const response = await apiClient.post(
      `/cycle-reports/${cycleId}/reports/${reportId}/phases/${phaseName}/complete`,
      {
        completion_notes: notes
      }
    );
    return response.data;
  },

  /**
   * Start a specific phase (original method for backward compatibility)
   */
  async startPhase(cycleId: number, reportId: number, phaseName: string): Promise<void> {
    await apiClient.post(
      `/cycle-reports/${cycleId}/reports/${reportId}/phases/${phaseName}/start`,
      {
        action: 'start'
      }
    );
  },

  /**
   * Start a phase with date planning
   */
  async startPhaseWithDates(cycleId: number, reportId: number, phaseName: string, request: PhaseTransitionRequest): Promise<any> {
    const response = await apiClient.post(
      `/cycle-reports/${cycleId}/reports/${reportId}/phases/${phaseName}/start`,
      request
    );
    return response.data;
  },

  /**
   * Update planned dates for a phase
   */
  async updatePhaseDates(cycleId: number, reportId: number, phaseName: string, update: WorkflowPhaseUpdate): Promise<any> {
    const response = await apiClient.put(
      `/cycle-reports/${cycleId}/reports/${reportId}/phases/${phaseName}/dates`,
      update
    );
    return response.data;
  },

  /**
   * Get date-based status for a specific phase
   */
  async getPhaseDateStatus(cycleId: number, reportId: number, phaseName: string): Promise<any> {
    const response = await apiClient.get(
      `/cycle-reports/${cycleId}/reports/${reportId}/phases/${phaseName}/date-status`
    );
    return response.data;
  },

  /**
   * Override phase state or status
   */
  async overridePhaseStatus(cycleId: number, reportId: number, phaseName: string, override: WorkflowPhaseOverride): Promise<WorkflowPhase> {
    const response = await apiClient.post(
      `/cycle-reports/${cycleId}/reports/${reportId}/phases/${phaseName}/override`,
      override
    );
    return response.data;
  },

  /**
   * Clear phase overrides
   */
  async clearPhaseOverrides(cycleId: number, reportId: number, phaseName: string): Promise<WorkflowPhase> {
    const response = await apiClient.delete(
      `/cycle-reports/${cycleId}/reports/${reportId}/phases/${phaseName}/override`
    );
    return response.data;
  },

  /**
   * Update phase state (automatic status calculation)
   */
  async updatePhaseState(cycleId: number, reportId: number, phaseName: string, newState: 'Not Started' | 'In Progress' | 'Complete', notes?: string): Promise<WorkflowPhase> {
    const response = await apiClient.put(
      `/cycle-reports/${cycleId}/reports/${reportId}/phases/${phaseName}/state`,
      {
        state: newState,
        notes: notes
      }
    );
    return response.data;
  }
};

export default workflowApi; 