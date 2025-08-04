import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import { useNotification } from '../contexts/NotificationContext';

interface WorkflowStatus {
  current_phase: string;
  awaiting_action: string | null;
  phase_results: Record<string, any>;
}

interface UseTemporalWorkflowOptions {
  workflowId?: string;
  cycleId: number;
  reportId: number;
  enabled?: boolean;
}

export function useTemporalWorkflow({
  workflowId,
  cycleId,
  reportId,
  enabled = true
}: UseTemporalWorkflowOptions) {
  const queryClient = useQueryClient();
  const { showSuccess, showError, showInfo } = useNotification();
  const [isPolling, setIsPolling] = useState(false);

  // Query workflow status
  const { data: workflowStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['workflow-status', workflowId],
    queryFn: async () => {
      if (!workflowId) return null;
      const response = await apiClient.get(`/temporal/workflow/${workflowId}/status`);
      return response.data;
    },
    enabled: enabled && !!workflowId,
    refetchInterval: isPolling ? 5000 : false // Poll every 5 seconds when enabled
  });

  // Query awaiting action
  const { data: awaitingAction } = useQuery({
    queryKey: ['workflow-awaiting-action', workflowId],
    queryFn: async () => {
      if (!workflowId) return null;
      const response = await apiClient.get(`/temporal/workflow/${workflowId}/awaiting-action`);
      return response.data;
    },
    enabled: enabled && !!workflowId,
    refetchInterval: isPolling ? 5000 : false
  });

  // Send signal mutation
  const sendSignalMutation = useMutation({
    mutationFn: async ({ signalName, data }: { signalName: string; data: any }) => {
      if (!workflowId) throw new Error('No workflow ID');
      const response = await apiClient.post(
        `/temporal/workflow/${workflowId}/signal/${signalName}`,
        { signal_name: signalName, data }
      );
      return response.data;
    },
    onSuccess: (data, variables) => {
      showSuccess('Action submitted successfully');
      // Refetch status after signal
      queryClient.invalidateQueries({ queryKey: ['workflow-status', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['workflow-awaiting-action', workflowId] });
    },
    onError: (error: any) => {
      showError(
        error.response?.data?.detail || 'Failed to submit action'
      );
    }
  });

  // Helper functions for specific signals
  const submitPlanningDocuments = useCallback(
    async (documents: any[]) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_planning_documents',
        data: { documents }
      });
    },
    [sendSignalMutation]
  );

  const submitPlanningAttributes = useCallback(
    async (attributes: any) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_planning_attributes',
        data: attributes
      });
    },
    [sendSignalMutation]
  );

  const submitTesterReview = useCallback(
    async (attributeDecisions: any[]) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_tester_review',
        data: { attribute_decisions: attributeDecisions }
      });
    },
    [sendSignalMutation]
  );

  const submitReportOwnerApproval = useCallback(
    async (approvalDecision: string, attributeDecisions?: any[]) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_report_owner_approval',
        data: {
          approval_decision: approvalDecision,
          attribute_decisions: attributeDecisions
        }
      });
    },
    [sendSignalMutation]
  );

  const submitSelectionCriteria = useCallback(
    async (criteria: any) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_selection_criteria',
        data: criteria
      });
    },
    [sendSignalMutation]
  );

  const submitSampleApproval = useCallback(
    async (setApprovals: any[]) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_sample_approval',
        data: { set_approvals: setApprovals }
      });
    },
    [sendSignalMutation]
  );

  const submitDataProviderReview = useCallback(
    async (assignmentUpdates: any[]) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_dp_assignment_review',
        data: { assignment_updates: assignmentUpdates }
      });
    },
    [sendSignalMutation]
  );

  const submitRFIResponses = useCallback(
    async (checkResponses: boolean, sendReminders: boolean = false) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_rfi_responses',
        data: {
          check_responses: checkResponses,
          send_reminders: sendReminders
        }
      });
    },
    [sendSignalMutation]
  );

  const submitDocumentTests = useCallback(
    async (testResults: any[]) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_document_tests',
        data: { document_test_results: testResults }
      });
    },
    [sendSignalMutation]
  );

  const submitDatabaseTests = useCallback(
    async (testResults: any[]) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_database_tests',
        data: { database_test_results: testResults }
      });
    },
    [sendSignalMutation]
  );

  const submitObservations = useCallback(
    async (observations: any[], autoGenerate: boolean = false) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_observations',
        data: {
          observations,
          auto_generate_from_failures: autoGenerate
        }
      });
    },
    [sendSignalMutation]
  );

  const submitObservationReview = useCallback(
    async (reviews: any[], groupReviews?: any[]) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_observation_review',
        data: {
          reviews,
          group_reviews: groupReviews
        }
      });
    },
    [sendSignalMutation]
  );

  const submitReportReview = useCallback(
    async (sectionEdits: any[], approveReport: boolean = false) => {
      return sendSignalMutation.mutateAsync({
        signalName: 'submit_report_review',
        data: {
          section_edits: sectionEdits,
          approve_report: approveReport
        }
      });
    },
    [sendSignalMutation]
  );

  // Start/stop polling
  const startPolling = useCallback(() => {
    setIsPolling(true);
  }, []);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
  }, []);

  return {
    // Workflow state
    workflowId,
    workflowStatus: workflowStatus?.status as WorkflowStatus | undefined,
    awaitingAction: awaitingAction?.awaiting_action,
    canPerformAction: awaitingAction?.can_perform_action,
    
    // Loading states
    isLoading: statusLoading,
    isSendingSignal: sendSignalMutation.isPending,
    
    // Polling control
    isPolling,
    startPolling,
    stopPolling,
    
    // Generic signal sender
    sendSignal: sendSignalMutation.mutateAsync,
    
    // Phase-specific signal senders
    submitPlanningDocuments,
    submitPlanningAttributes,
    submitTesterReview,
    submitReportOwnerApproval,
    submitSelectionCriteria,
    submitSampleApproval,
    submitDataProviderReview,
    submitRFIResponses,
    submitDocumentTests,
    submitDatabaseTests,
    submitObservations,
    submitObservationReview,
    submitReportReview
  };
}