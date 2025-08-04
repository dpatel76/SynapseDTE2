import apiClient from './client';

// Types for Data Owner LOB Assignment API

// Base types
export interface DataOwnerLOBAttributeVersion {
  version_id: string;
  phase_id: number;
  workflow_activity_id?: number;
  version_number: number;
  version_status: 'draft' | 'active' | 'superseded';
  parent_version_id?: string;
  workflow_execution_id?: string;
  workflow_run_id?: string;
  total_lob_attributes: number;
  assigned_lob_attributes: number;
  unassigned_lob_attributes: number;
  data_executive_id: number;
  assignment_batch_date: string;
  assignment_notes?: string;
  created_at: string;
  created_by_id: number;
  updated_at: string;
  updated_by_id: number;
}

export interface DataOwnerLOBAttributeAssignment {
  assignment_id: string;
  version_id: string;
  phase_id: number;
  sample_id: number;
  attribute_id: number;
  lob_id: number;
  data_owner_id?: number;
  data_executive_id: number;
  assigned_by_data_executive_at: string;
  assignment_rationale?: string;
  previous_data_owner_id?: number;
  change_reason?: string;
  assignment_status: 'assigned' | 'unassigned' | 'changed' | 'confirmed';
  data_owner_acknowledged: boolean;
  data_owner_acknowledged_at?: string;
  data_owner_response_notes?: string;
  created_at: string;
  created_by_id: number;
  updated_at: string;
  updated_by_id: number;
}

// Enhanced response types with related data
export interface AssignmentWithDetails extends DataOwnerLOBAttributeAssignment {
  lob_name?: string;
  attribute_name?: string;
  data_owner_name?: string;
  data_executive_name?: string;
  sample_description?: string;
}

export interface VersionWithAssignments extends DataOwnerLOBAttributeVersion {
  assignments: AssignmentWithDetails[];
}

// Request types
export interface CreateVersionRequest {
  phase_id: number;
  assignment_notes?: string;
  workflow_activity_id?: number;
  workflow_execution_id?: string;
  workflow_run_id?: string;
}

export interface AssignmentRequest {
  phase_id: number;
  sample_id: number;
  attribute_id: number;
  lob_id: number;
  data_owner_id?: number;
  assignment_rationale?: string;
}

export interface BulkAssignmentRequest {
  assignments: AssignmentRequest[];
}

export interface BulkAssignmentResponse {
  version_id: string;
  created_assignments: number;
  updated_assignments: number;
  errors: number;
  error_details: Array<{
    assignment_data: any;
    error: string;
  }>;
}

export interface AcknowledgeAssignmentRequest {
  response_notes?: string;
}

export interface UnassignmentRequest {
  unassignment_reason?: string;
}

// Dashboard and analytics types
export interface AssignmentSummary {
  total_assignments: number;
  assigned_count: number;
  unassigned_count: number;
  acknowledged_count: number;
  pending_acknowledgment_count: number;
}

export interface LOBBreakdown {
  lob_id: number;
  lob_name: string;
  total_attributes: number;
  assigned_attributes: number;
  acknowledged_attributes: number;
}

export interface DataOwnerWorkload {
  data_owner_id: number;
  data_owner_name: string;
  total_assignments: number;
  acknowledged_assignments: number;
}

export interface PhaseAssignmentDashboard {
  phase_id: number;
  current_version?: {
    version_id: string;
    version_number: number;
    status: string;
    created_at: string;
    data_executive_id: number;
  };
  assignment_summary: AssignmentSummary;
  lob_breakdown: LOBBreakdown[];
  data_owner_workload: DataOwnerWorkload[];
}

export interface DataOwnerWorkloadDetail {
  data_owner_id: number;
  phase_id: number;
  version_id?: string;
  total_assignments: number;
  acknowledged_assignments: number;
  pending_assignments: number;
  assignments: AssignmentWithDetails[];
}

export interface AssignmentChange {
  version_number: number;
  version_date: string;
  data_executive_id: number;
  assignment_id: string;
  lob_id: number;
  lob_name?: string;
  attribute_id: number;
  attribute_name?: string;
  sample_id: number;
  data_owner_id?: number;
  data_owner_name?: string;
  previous_data_owner_id?: number;
  previous_data_owner_name?: string;
  change_reason?: string;
  assignment_status: string;
  assignment_rationale?: string;
}

export interface AssignmentHistoryResponse {
  phase_id: number;
  changes: AssignmentChange[];
}

// Filter types
export interface AssignmentFilters {
  lob_id?: number;
  data_owner_id?: number;
  assignment_status?: 'assigned' | 'unassigned' | 'changed' | 'confirmed';
  acknowledged?: boolean;
}

// API Client
export const dataOwnerLobAssignmentApi = {
  // Version Management
  async createVersion(request: CreateVersionRequest): Promise<DataOwnerLOBAttributeVersion> {
    const response = await apiClient.post('/data-owner-lob-assignments/versions', request);
    return response.data;
  },

  async getVersionWithAssignments(versionId: string): Promise<VersionWithAssignments> {
    const response = await apiClient.get(`/data-owner-lob-assignments/versions/${versionId}`);
    return response.data;
  },

  async getCurrentVersion(phaseId: number): Promise<DataOwnerLOBAttributeVersion | null> {
    const response = await apiClient.get(`/data-owner-lob-assignments/phases/${phaseId}/current-version`);
    return response.data;
  },

  async getVersionHistory(phaseId: number): Promise<DataOwnerLOBAttributeVersion[]> {
    const response = await apiClient.get(`/data-owner-lob-assignments/phases/${phaseId}/version-history`);
    return response.data;
  },

  // Assignment Management
  async createAssignment(versionId: string, request: AssignmentRequest): Promise<AssignmentWithDetails> {
    const response = await apiClient.post(`/data-owner-lob-assignments/versions/${versionId}/assignments`, request);
    return response.data;
  },

  async bulkAssignDataOwners(versionId: string, request: BulkAssignmentRequest): Promise<BulkAssignmentResponse> {
    const response = await apiClient.post(`/data-owner-lob-assignments/versions/${versionId}/bulk-assignments`, request);
    return response.data;
  },

  async unassignDataOwner(assignmentId: string, request: UnassignmentRequest): Promise<AssignmentWithDetails> {
    const response = await apiClient.delete(`/data-owner-lob-assignments/assignments/${assignmentId}`, { data: request });
    return response.data;
  },

  // Data Owner Acknowledgment
  async acknowledgeAssignment(assignmentId: string, request: AcknowledgeAssignmentRequest): Promise<AssignmentWithDetails> {
    const response = await apiClient.post(`/data-owner-lob-assignments/assignments/${assignmentId}/acknowledge`, request);
    return response.data;
  },

  // Query and Dashboard
  async getLobAttributeAssignments(
    phaseId: number,
    filters?: AssignmentFilters & { version_id?: string }
  ): Promise<AssignmentWithDetails[]> {
    const params = new URLSearchParams();
    if (filters?.version_id) params.append('version_id', filters.version_id);
    if (filters?.lob_id !== undefined) params.append('lob_id', filters.lob_id.toString());
    if (filters?.data_owner_id !== undefined) params.append('data_owner_id', filters.data_owner_id.toString());
    if (filters?.assignment_status) params.append('assignment_status', filters.assignment_status);

    const response = await apiClient.get(`/data-owner-lob-assignments/phases/${phaseId}/assignments?${params}`);
    return response.data;
  },

  async getPhaseAssignmentDashboard(phaseId: number): Promise<PhaseAssignmentDashboard> {
    const response = await apiClient.get(`/data-owner-lob-assignments/phases/${phaseId}/dashboard`);
    return response.data;
  },

  async getDataOwnerWorkload(phaseId: number, dataOwnerId: number): Promise<DataOwnerWorkloadDetail> {
    const response = await apiClient.get(`/data-owner-lob-assignments/phases/${phaseId}/data-owners/${dataOwnerId}/workload`);
    return response.data;
  },

  async getMyAssignments(phaseId: number): Promise<DataOwnerWorkloadDetail> {
    const response = await apiClient.get(`/data-owner-lob-assignments/data-owners/my-assignments/${phaseId}`);
    return response.data;
  },

  async getAssignmentHistory(
    phaseId: number,
    filters?: { lob_id?: number; attribute_id?: number; sample_id?: number }
  ): Promise<AssignmentHistoryResponse> {
    const params = new URLSearchParams();
    if (filters?.lob_id !== undefined) params.append('lob_id', filters.lob_id.toString());
    if (filters?.attribute_id !== undefined) params.append('attribute_id', filters.attribute_id.toString());
    if (filters?.sample_id !== undefined) params.append('sample_id', filters.sample_id.toString());

    const response = await apiClient.get(`/data-owner-lob-assignments/phases/${phaseId}/history?${params}`);
    return response.data;
  },

  // Utility
  async getAssignmentById(assignmentId: string): Promise<AssignmentWithDetails> {
    const response = await apiClient.get(`/data-owner-lob-assignments/assignments/${assignmentId}`);
    return response.data;
  },

  // Health Check
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await apiClient.get('/data-owner-lob-assignments/health');
    return response.data;
  }
};

export default dataOwnerLobAssignmentApi;