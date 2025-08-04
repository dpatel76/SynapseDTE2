import client from './client';

export interface WorkflowInfo {
  workflowId: string;
  runId: string;
  status: 'Running' | 'Completed' | 'Failed' | 'Terminated' | 'Timed Out';
  startTime: string;
  closeTime?: string;
  historyLength: number;
  executionTime?: number;
}

export interface WorkflowActivity {
  activityId: string;
  activityType: string;
  status: 'Scheduled' | 'Started' | 'Completed' | 'Failed' | 'Timed Out';
  scheduledTime: string;
  startedTime?: string;
  closedTime?: string;
  attempt: number;
  maximumAttempts: number;
  input?: any;
  result?: any;
  failure?: any;
}

export const temporalApi = {
  // Get workflow info
  getWorkflowInfo: (workflowId: string) =>
    client.get<WorkflowInfo>(`/api/v1/temporal/workflow/${workflowId}`),

  // Get workflow activities
  getWorkflowActivities: (workflowId: string) =>
    client.get<WorkflowActivity[]>(`/api/v1/temporal/workflow/${workflowId}/activities`),

  // Send signal to workflow
  sendSignal: (workflowId: string, signalName: string, data: any) =>
    client.post(`/api/v1/temporal/workflow/${workflowId}/signal/${signalName}`, data),

  // Query workflow state
  queryWorkflow: (workflowId: string, queryType: string) =>
    client.get(`/api/v1/temporal/workflow/${workflowId}/query/${queryType}`),

  // Terminate workflow
  terminateWorkflow: (workflowId: string, reason: string) =>
    client.post(`/api/v1/temporal/workflow/${workflowId}/terminate`, { reason }),

  // Get workflow handle
  getWorkflowHandle: (workflowId: string) =>
    client.get(`/api/v1/temporal/workflow/${workflowId}/handle`)
};