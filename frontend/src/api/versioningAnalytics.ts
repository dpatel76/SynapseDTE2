import client from './client';

export interface PhaseMetrics {
  [phase: string]: {
    version_count: number;
    average_approval_time_hours: number;
    rejection_rate: number;
    current_version?: number;
    last_updated?: string;
    status: 'not_started' | 'in_progress' | 'complete';
    sample_statistics?: {
      total: number;
      approved: number;
      rejected: number;
      carried_forward: number;
      approval_rate: number;
    };
  };
}

export interface WorkflowMetrics {
  total_operations: number;
  successful_operations: number;
  failed_operations: number;
  overall_success_rate: number;
  phase_operations: {
    phase: string;
    total: number;
    successful: number;
    failed: number;
    average_duration_ms: number;
  }[];
}

export interface BottleneckInfo {
  phase: string;
  issue: string;
  duration_hours: number;
  severity: 'low' | 'medium' | 'high';
}

export interface TrendData {
  date: string;
  version_count: number;
  approval_time: number;
}

export const versioningAnalyticsApi = {
  // Get phase metrics
  getPhaseMetrics: (cycleId: number, reportId?: number) =>
    client.get<PhaseMetrics>(`/api/v1/analytics/versioning/phases?cycleId=${cycleId}${reportId ? `&reportId=${reportId}` : ''}`),

  // Get workflow metrics
  getWorkflowMetrics: (cycleId: number, reportId?: number) =>
    client.get<WorkflowMetrics>(`/api/v1/analytics/versioning/workflow?cycleId=${cycleId}${reportId ? `&reportId=${reportId}` : ''}`),

  // Get bottlenecks
  getBottlenecks: (cycleId: number, reportId?: number) =>
    client.get<BottleneckInfo[]>(`/api/v1/analytics/versioning/bottlenecks?cycleId=${cycleId}${reportId ? `&reportId=${reportId}` : ''}`),

  // Get trend data
  getTrendData: (cycleId: number, phase: string, period: '7d' | '30d' | '90d') =>
    client.get<TrendData[]>(`/api/v1/analytics/versioning/trends?cycleId=${cycleId}&phase=${phase}&period=${period}`),

  // Get version trends
  getVersionTrends: (phase: string, days: number) =>
    client.get<TrendData[]>(`/api/v1/analytics/versioning/version-trends?phase=${phase}&days=${days}`)
};