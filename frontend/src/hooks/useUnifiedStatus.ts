/**
 * Unified Status Hook - Single source of truth for all phase and activity status
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import apiClient from '../api/client';

export type PhaseStatusType = 'not_started' | 'in_progress' | 'completed' | 'blocked';
export type ActivityStatusType = 'not_started' | 'pending' | 'active' | 'in_progress' | 'completed' | 'blocked' | 'skipped';

export interface ActivityStatus {
  activity_id: string;
  name: string;
  description: string;
  status: ActivityStatusType;
  can_start: boolean;
  can_complete: boolean;
  can_reset?: boolean;
  completion_percentage?: number;
  blocking_reason?: string;
  last_updated?: string;
  metadata?: Record<string, any>;
}

export interface PhaseStatus {
  phase_name: string;
  cycle_id: number;
  report_id: number;
  phase_status: PhaseStatusType;
  overall_completion_percentage: number;
  activities: ActivityStatus[];
  can_proceed_to_next: boolean;
  blocking_issues: string[];
  last_updated: string;
  metadata?: Record<string, any>;
}

export interface UnifiedStatusHookResult {
  data?: PhaseStatus;
  isLoading: boolean;
  error: any;
  refetch: () => void;
}

/**
 * Hook to get unified status for a specific phase
 */
export const usePhaseStatus = (
  phaseName: string,
  cycleId: number,
  reportId: number,
  options?: {
    enabled?: boolean;
    refetchInterval?: number;
  }
): UnifiedStatusHookResult => {
  const queryResult: UseQueryResult<PhaseStatus> = useQuery({
    queryKey: ['phaseStatus', phaseName, cycleId, reportId],
    queryFn: async () => {
      const response = await apiClient.get(
        `/status/cycles/${cycleId}/reports/${reportId}/phases/${encodeURIComponent(phaseName)}/status`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && Boolean(phaseName && cycleId && reportId),
    refetchInterval: options?.refetchInterval || 30000, // Default 30 seconds
    staleTime: 1000, // Consider data stale after 1 second
    gcTime: 300000, // Keep in cache for 5 minutes
  });

  return {
    data: queryResult.data,
    isLoading: queryResult.isLoading,
    error: queryResult.error,
    refetch: queryResult.refetch,
  };
};

/**
 * Hook to get unified status for all phases
 */
export const useAllPhasesStatus = (
  cycleId: number,
  reportId: number,
  options?: {
    enabled?: boolean;
    refetchInterval?: number;
  }
): UseQueryResult<Record<string, PhaseStatus>> => {
  return useQuery({
    queryKey: ['allPhasesStatus', cycleId, reportId],
    queryFn: async () => {
      const response = await apiClient.get(
        `/status/cycles/${cycleId}/reports/${reportId}/status/all`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && Boolean(cycleId && reportId),
    refetchInterval: options?.refetchInterval || 60000, // Default 1 minute for all phases
    staleTime: 30000, // Consider data stale after 30 seconds
    gcTime: 300000, // Keep in cache for 5 minutes
  });
};

/**
 * Hook to get status for a specific activity within a phase
 */
export const useActivityStatus = (
  phaseName: string,
  activityId: string,
  cycleId: number,
  reportId: number,
  options?: {
    enabled?: boolean;
    refetchInterval?: number;
  }
): UseQueryResult<ActivityStatus> => {
  return useQuery({
    queryKey: ['activityStatus', phaseName, activityId, cycleId, reportId],
    queryFn: async () => {
      const response = await apiClient.get(
        `/status/cycles/${cycleId}/reports/${reportId}/phases/${encodeURIComponent(phaseName)}/activities/${activityId}/status`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && Boolean(phaseName && activityId && cycleId && reportId),
    refetchInterval: options?.refetchInterval || 30000, // Default 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
    gcTime: 300000, // Keep in cache for 5 minutes
  });
};

/**
 * Helper function to get status color for UI display
 */
export const getStatusColor = (status: PhaseStatusType | ActivityStatusType): string => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'in_progress':
    case 'active':
      return 'info';
    case 'blocked':
      return 'error';
    case 'not_started':
    case 'pending':
      return 'default';
    case 'skipped':
      return 'warning';
    default:
      return 'default';
  }
};

/**
 * Helper function to get status icon for UI display
 */
export const getStatusIcon = (status: PhaseStatusType | ActivityStatusType): string => {
  switch (status) {
    case 'completed':
      return 'CheckCircle';
    case 'in_progress':
    case 'active':
      return 'PlayCircle';
    case 'blocked':
      return 'Error';
    case 'not_started':
    case 'pending':
      return 'RadioButtonUnchecked';
    case 'skipped':
      return 'SkipNext';
    default:
      return 'Help';
  }
};

/**
 * Helper function to format status text for display
 */
export const formatStatusText = (status: PhaseStatusType | ActivityStatusType): string => {
  switch (status) {
    case 'not_started':
      return 'Not Started';
    case 'in_progress':
      return 'In Progress';
    case 'completed':
      return 'Completed';
    case 'blocked':
      return 'Blocked';
    case 'pending':
      return 'Pending';
    case 'active':
      return 'Active';
    case 'skipped':
      return 'Skipped';
    default:
      return status;
  }
};