import apiClient from './client';
import { AxiosResponse } from 'axios';

export interface MetricsData {
  aggregate_metrics: {
    total_reports: number;
    reports_completed: number;
    reports_in_progress: number;
    overall_progress: number;
    sla_compliance_rate: number;
    average_completion_time: number;
    error_rate: number;
    [key: string]: any;
  };
  phase_metrics: {
    phase_name: string;
    total_items: number;
    completed_items: number;
    in_progress_items: number;
    average_duration: number;
    sla_compliance: number;
    [key: string]: any;
  }[];
  trends: {
    metric_name: string;
    values: {
      date: string;
      value: number;
    }[];
  }[];
  role_specific_data?: any;
}

export interface VersionHistory {
  id: string;
  entity_type: string;
  entity_id: string;
  version_number: number;
  change_type: string;
  change_reason: string;
  changed_by: string;
  changed_at: string;
  change_details: any;
}

export interface ActivityState {
  activity_name: string;
  state: 'Not Started' | 'In Progress' | 'Completed' | 'Revision Requested';
  last_updated: string;
  updated_by?: string;
  can_start?: boolean;
  can_complete?: boolean;
}

export interface BatchProgress {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress_percentage: number;
  current_step: string;
  total_steps: number;
  completed_steps: number;
  message: string;
  result?: any;
  error?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  metadata?: any;
}

// Metrics endpoints
export const metricsApi = {
  // Get dashboard metrics for a specific user
  getDashboardMetrics: async (
    userId?: string,
    cycleId?: string,
    timePeriod: string = 'current_cycle'
  ): Promise<AxiosResponse<MetricsData>> => {
    const params = new URLSearchParams();
    if (cycleId) params.append('cycle_id', cycleId);
    params.append('time_period', timePeriod);
    
    // If userId is provided, get user-specific metrics, otherwise get current user's metrics
    const endpoint = userId ? `/metrics/dashboard/${userId}` : '/metrics/dashboard/current-user';
    return apiClient.get(`${endpoint}?${params.toString()}`);
  },

  // Get role-specific metrics
  getTesterMetrics: async (
    userId: string,
    cycleId: string,
    reportId?: string
  ): Promise<AxiosResponse<any>> => {
    // Handle "all" cycle_id by not sending it
    const params = new URLSearchParams();
    if (cycleId && cycleId !== 'all') {
      params.append('cycle_id', cycleId);
    }
    if (reportId) params.append('report_id', reportId);
    
    return apiClient.get(`/metrics/tester/${userId}?${params.toString()}`);
  },

  getTestExecutiveMetrics: async (
    cycleId: string,
    lob?: string
  ): Promise<AxiosResponse<any>> => {
    const params = new URLSearchParams({ cycle_id: cycleId });
    if (lob) params.append('lob', lob);
    
    return apiClient.get(`/metrics/test-executive?${params.toString()}`);
  },

  getReportOwnerMetrics: async (
    userId: string,
    cycleId: string,
    reportId?: string
  ): Promise<AxiosResponse<any>> => {
    const params = new URLSearchParams({ cycle_id: cycleId });
    if (reportId) params.append('report_id', reportId);
    
    return apiClient.get(`/metrics/report-owner/${userId}?${params.toString()}`);
  },

  getDataProviderMetrics: async (
    userId: string,
    cycleId: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.get(`/metrics/data-provider/${userId}?cycle_id=${cycleId}`);
  },

  getDataExecutiveMetrics: async (
    cycleId: string,
    lob?: string
  ): Promise<AxiosResponse<any>> => {
    const params = new URLSearchParams({ cycle_id: cycleId });
    if (lob) params.append('lob', lob);
    
    return apiClient.get(`/metrics/data-executive?${params.toString()}`);
  },

  // Phase metrics
  getPhaseMetrics: async (
    cycleId: string,
    reportId: string,
    phaseName: string
  ): Promise<AxiosResponse<any>> => {
    // Don't make the request if cycleId or reportId are empty
    if (!cycleId || !reportId) {
      return Promise.resolve({ 
        data: {
          total_attributes: 0,
          non_pk_scoped: 0,
          samples_approved: 0,
          lobs_count: 0,
          completion_time: 0,
          submission_date: null
        } 
      } as AxiosResponse<any>);
    }
    return apiClient.get(`/metrics/phases/${phaseName}?cycle_id=${cycleId}&report_id=${reportId}`);
  },

  // Testing summary
  getTestingSummary: async (
    cycleId: string,
    reportId: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.get(`/metrics/testing-summary?cycle_id=${cycleId}&report_id=${reportId}`);
  }
};

// Version history endpoints
export const versionApi = {
  getVersionHistory: async (
    entityType: string,
    entityId: string
  ): Promise<AxiosResponse<VersionHistory[]>> => {
    return apiClient.get(`/versions/history/${entityType}/${entityId}`);
  },

  compareVersions: async (
    entityType: string,
    version1Id: string,
    version2Id: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.get(`/versions/compare?entity_type=${entityType}&version1_id=${version1Id}&version2_id=${version2Id}`);
  },

  revertToVersion: async (
    entityType: string,
    entityId: string,
    versionNumber: number
  ): Promise<AxiosResponse<any>> => {
    return apiClient.post(`/versions/revert`, {
      entity_type: entityType,
      entity_id: entityId,
      target_version_number: versionNumber,
      reason: 'Reverting to previous version'
    });
  },

  createVersion: async (data: {
    entity_type: string;
    entity_id: string;
    reason: string;
    notes?: string;
    auto_approve?: boolean;
  }): Promise<AxiosResponse<any>> => {
    return apiClient.post('/versions/create', data);
  },

  approveVersion: async (
    entityType: string,
    versionId: string,
    notes?: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.post(`/versions/approve/${entityType}/${versionId}`, { notes });
  },

  rejectVersion: async (
    entityType: string,
    versionId: string,
    reason: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.post(`/versions/reject/${entityType}/${versionId}`, { reason });
  },

  getLatestVersion: async (
    entityType: string,
    entityId: string,
    approvedOnly: boolean = false
  ): Promise<AxiosResponse<any>> => {
    return apiClient.get(`/versions/latest/${entityType}/${entityId}?approved_only=${approvedOnly}`);
  }
};

// Activity state endpoints
export const activityApi = {
  getActivityStates: async (
    cycleId: string,
    reportId: string,
    phaseName: string
  ): Promise<AxiosResponse<ActivityState[]>> => {
    return apiClient.get(`/activities/${cycleId}/${reportId}/${phaseName}`);
  },

  updateActivityState: async (
    activityName: string,
    newState: string,
    cycleId: string,
    reportId: string,
    phaseName: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.post('/activities/transition', {
      cycle_id: cycleId,
      report_id: reportId,
      phase_name: phaseName,
      activity_name: activityName,
      target_state: newState
    });
  },

  startPhase: async (
    cycleId: string,
    reportId: string,
    phaseName: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.post(`/activities/${cycleId}/${reportId}/${phaseName}/start`);
  },

  completePhase: async (
    cycleId: string,
    reportId: string,
    phaseName: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.post(`/activities/${cycleId}/${reportId}/${phaseName}/complete`);
  },

  submitForReview: async (
    cycleId: string,
    reportId: string,
    phaseName: string,
    submissionId?: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.post(`/activities/${cycleId}/${reportId}/${phaseName}/submit`, {
      submission_id: submissionId
    });
  },

  approveSubmission: async (
    cycleId: string,
    reportId: string,
    phaseName: string,
    notes?: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.post(`/activities/${cycleId}/${reportId}/${phaseName}/approve`, {
      notes
    });
  },

  rejectSubmission: async (
    cycleId: string,
    reportId: string,
    phaseName: string,
    reason: string
  ): Promise<AxiosResponse<any>> => {
    return apiClient.post(`/activities/${cycleId}/${reportId}/${phaseName}/reject`, {
      reason
    });
  }
};

// Batch processing endpoints
export const batchApi = {
  getBatchProgress: async (jobId: string): Promise<AxiosResponse<BatchProgress>> => {
    return apiClient.get(`/jobs/${jobId}/status`);
  },

  cancelBatch: async (jobId: string): Promise<AxiosResponse<any>> => {
    return apiClient.post(`/batch/cancel/${jobId}`);
  }
};