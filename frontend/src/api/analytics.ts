import apiClient from './client';

export interface PerformanceMetric {
  label: string;
  value: string;
  trend: 'up' | 'down';
  trend_value: string;
}

export interface ActivityItem {
  action: string;
  detail: string;
  time: string;
  type: 'success' | 'info' | 'warning' | 'error';
  user?: string;
}

export interface TrendDataPoint {
  date: string;
  value: number;
  label: string;
}

export interface AnalyticsOverview {
  total_cycles: number;
  active_cycles: number;
  completed_cycles: number;
  completion_rate: number;
  total_reports: number;
  active_reports: number;
  open_issues: number;
  critical_issues: number;
}

export interface AnalyticsResponse {
  overview: AnalyticsOverview;
  performance_metrics: PerformanceMetric[];
  recent_activities: ActivityItem[];
  trend_data: TrendDataPoint[];
}

export interface PhaseMetric {
  phase_name: string;
  total: number;
  completed: number;
  in_progress: number;
  not_started: number;
  completion_rate: number;
  avg_duration_hours: number;
}

export const analyticsApi = {
  getAnalytics: async (days: number = 30): Promise<AnalyticsResponse> => {
    const response = await apiClient.get<AnalyticsResponse>(`/analytics/?days=${days}`);
    return response.data;
  },

  getTrends: async (metricType: string, days: number = 30): Promise<TrendDataPoint[]> => {
    const response = await apiClient.get<TrendDataPoint[]>(`/analytics/trends/${metricType}?days=${days}`);
    return response.data;
  },

  getPhaseMetrics: async (cycleId?: number): Promise<PhaseMetric[]> => {
    const params = cycleId ? `?cycle_id=${cycleId}` : '';
    const response = await apiClient.get<PhaseMetric[]>(`/analytics/phase-metrics${params}`);
    return response.data;
  },
};