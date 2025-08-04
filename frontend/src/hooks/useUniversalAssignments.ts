import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import apiClient from '../api/client';
import { getPhaseAssignmentTypes, requiresAcknowledgement } from '../config/universalAssignmentTypes';

export interface UniversalAssignment {
  assignment_id: string;  // UUID string, not number
  assignment_type: string;
  title: string;
  description?: string;
  task_instructions?: string;
  from_role: string;
  to_role: string;
  from_user_id: number;
  to_user_id?: number;
  from_user_name?: string;
  to_user_name?: string;
  status: string;
  priority: string;
  assigned_at: string;
  due_date?: string;
  acknowledged_at?: string;
  started_at?: string;
  completed_at?: string;
  completion_notes?: string;
  completion_data?: any;
  requires_approval: boolean;
  approval_role?: string;
  approved_by_user_id?: number;
  approved_at?: string;
  approval_notes?: string;
  is_overdue: boolean;
  days_until_due: number;
  is_active: boolean;
  is_completed: boolean;
  context_type: string;
  context_data?: any;
  action_url?: string;
}

export interface UseUniversalAssignmentsOptions {
  phase: string;
  cycleId: number;
  reportId: number;
  autoNavigate?: boolean;
  assignmentType?: string;
}

export interface UseUniversalAssignmentsReturn {
  hasAssignment: boolean;
  assignment: UniversalAssignment | undefined;
  assignments: UniversalAssignment[];
  isLoading: boolean;
  canDirectAccess: boolean;
  acknowledgeMutation: any;
  startMutation: any;
  completeMutation: any;
  refreshAssignments: () => void;
  acknowledgeAssignment: (assignmentId: string) => void;
  startAssignment: (assignmentId: string) => void;
  completeAssignment: (assignmentId: string, notes?: string) => void;
}

export const useUniversalAssignments = (options: UseUniversalAssignmentsOptions): UseUniversalAssignmentsReturn => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useNotifications();
  
  // Check for assignments related to this phase
  const { data: assignments = [], isLoading, refetch } = useQuery({
    queryKey: ['universal-assignments', options.phase, options.cycleId, options.reportId, user?.user_id],
    queryFn: async () => {
      try {
        // Use context-based endpoint for better filtering
        const params: any = {
          cycle_id: options.cycleId,
          report_id: options.reportId,
          phase_name: options.phase,
          status_filter: 'Assigned,Acknowledged,In Progress'
        };

        // Add assignment type filter if specified
        if (options.assignmentType) {
          params.assignment_type_filter = options.assignmentType;
        }

        const response = await apiClient.get('/universal-assignments/context/Report', { params });
        return response.data || [];
      } catch (error) {
        console.error('Error fetching universal assignments:', error);
        return [];
      }
    },
    enabled: !!user?.user_id && !!options.cycleId && !!options.reportId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
  
  // Extract current assignment if any
  const activeAssignments = assignments.filter((a: UniversalAssignment) => 
    a.to_user_id === user?.user_id &&
    a.status !== 'completed' && 
    a.status !== 'approved' &&
    a.status !== 'rejected'
  );

  const currentAssignment = activeAssignments[0];
  
  // Acknowledge assignment mutation
  const acknowledgeMutation = useMutation({
    mutationFn: async (assignmentId: string) => {
      const response = await apiClient.post(`/universal-assignments/assignments/${assignmentId}/acknowledge`);
      return response.data;
    },
    onSuccess: () => {
      showToast('success', 'Assignment acknowledged');
      queryClient.invalidateQueries({ queryKey: ['universal-assignments'] });
    },
    onError: (error: any) => {
      showToast('error', `Failed to acknowledge: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Start assignment mutation
  const startMutation = useMutation({
    mutationFn: async (assignmentId: string) => {
      const response = await apiClient.post(`/universal-assignments/assignments/${assignmentId}/start`);
      return response.data;
    },
    onSuccess: () => {
      showToast('success', 'Assignment started');
      queryClient.invalidateQueries({ queryKey: ['universal-assignments'] });
    },
    onError: (error: any) => {
      showToast('error', `Failed to start: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Complete assignment mutation
  const completeMutation = useMutation({
    mutationFn: async ({ assignmentId, notes }: { assignmentId: string; notes?: string }) => {
      const response = await apiClient.post(`/universal-assignments/assignments/${assignmentId}/complete`, { notes });
      return response.data;
    },
    onSuccess: () => {
      showToast('success', 'Assignment completed');
      queryClient.invalidateQueries({ queryKey: ['universal-assignments'] });
    },
    onError: (error: any) => {
      showToast('error', `Failed to complete: ${error.response?.data?.detail || error.message}`);
    },
  });
  
  // Determine if user can access the page directly (without assignment)
  const canDirectAccess = !currentAssignment || 
    user?.role === 'Admin' || 
    user?.role === 'Test Executive' ||
    (currentAssignment && ['In Progress', 'Acknowledged'].includes(currentAssignment.status));
  
  // Helper functions
  const acknowledgeAssignment = (assignmentId: string) => {
    acknowledgeMutation.mutate(assignmentId);
  };

  const startAssignment = (assignmentId: string) => {
    startMutation.mutate(assignmentId);
  };

  const completeAssignment = (assignmentId: string, notes?: string) => {
    completeMutation.mutate({ assignmentId, notes });
  };
  
  return {
    hasAssignment: !!currentAssignment,
    assignment: currentAssignment,
    assignments: activeAssignments,
    isLoading,
    canDirectAccess,
    acknowledgeMutation,
    startMutation,
    completeMutation,
    refreshAssignments: refetch,
    acknowledgeAssignment,
    startAssignment,
    completeAssignment
  };
};