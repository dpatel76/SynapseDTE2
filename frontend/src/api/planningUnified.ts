import apiClient from './client';

// Types for Unified Planning Phase API
export interface PlanningVersion {
  version_id: string;
  phase_id: number;
  workflow_activity_id?: number;
  version_number: number;
  version_status: 'draft' | 'pending_approval' | 'approved' | 'rejected' | 'superseded';
  parent_version_id?: string;
  
  // Temporal Workflow Context
  workflow_execution_id?: string;
  workflow_run_id?: string;
  
  // Planning Summary Statistics
  total_attributes: number;
  approved_attributes: number;
  pk_attributes: number;
  cde_attributes: number;
  mandatory_attributes: number;
  total_data_sources: number;
  approved_data_sources: number;
  total_pde_mappings: number;
  approved_pde_mappings: number;
  
  // LLM Generation Summary
  llm_generation_summary?: any;
  
  // Tester-Only Approval Workflow
  submitted_by_id?: number;
  submitted_at?: string;
  approved_by_id?: number;
  approved_at?: string;
  rejection_reason?: string;
  
  // Audit Fields
  created_at: string;
  created_by_id: number;
  updated_at: string;
  updated_by_id: number;
}

export interface PlanningDataSource {
  data_source_id: string;
  version_id: string;
  phase_id: number;
  
  // Data Source Definition
  source_name: string;
  source_type: 'database' | 'file' | 'api' | 'sftp' | 's3' | 'other';
  description?: string;
  
  // Connection Configuration
  connection_config: any;
  auth_config?: any;
  
  // Data Source Metadata
  refresh_schedule?: string;
  validation_rules?: any;
  estimated_record_count?: number;
  data_freshness_hours?: number;
  
  // Tester Decision
  tester_decision?: 'approve' | 'reject' | 'request_changes';
  tester_decided_by?: number;
  tester_decided_at?: string;
  tester_notes?: string;
  
  // Status
  status: 'pending' | 'approved' | 'rejected';
  
  // Audit Fields
  created_at: string;
  created_by_id: number;
  updated_at: string;
  updated_by_id: number;
}

export interface PlanningAttribute {
  attribute_id: string;
  version_id: string;
  phase_id: number;
  
  // Attribute Definition
  attribute_name: string;
  data_type: 'string' | 'integer' | 'decimal' | 'boolean' | 'date' | 'datetime' | 'text';
  description?: string;
  business_definition?: string;
  
  // Attribute Characteristics
  is_mandatory: boolean;
  is_cde: boolean;
  is_primary_key: boolean;
  max_length?: number;
  
  // Information Security Classification
  information_security_classification: 'public' | 'internal' | 'confidential' | 'restricted';
  
  // LLM Assistance Metadata
  llm_metadata?: any;
  
  // Tester Decision
  tester_decision?: 'approve' | 'reject' | 'request_changes';
  tester_decided_by?: number;
  tester_decided_at?: string;
  tester_notes?: string;
  
  // Status
  status: 'pending' | 'approved' | 'rejected';
  
  // PDE Mappings
  pde_mappings?: PlanningPDEMapping[];
  
  // Audit Fields
  created_at: string;
  created_by_id: number;
  updated_at: string;
  updated_by_id: number;
}

export interface PlanningPDEMapping {
  pde_mapping_id: string;
  version_id: string;
  attribute_id: string;
  data_source_id: string;
  phase_id: number;
  
  // PDE Definition
  pde_name: string;
  pde_code: string;
  mapping_type: 'direct' | 'calculated' | 'lookup' | 'conditional';
  
  // Data Source Mapping
  source_table: string;
  source_column: string;
  source_field: string;
  column_data_type?: string;
  transformation_rule?: string;
  condition_rule?: string;
  is_primary: boolean;
  
  // PDE Classification
  classification?: any;
  
  // LLM Assistance
  llm_metadata?: any;
  
  // Tester Decision
  tester_decision?: 'approve' | 'reject' | 'request_changes';
  tester_decided_by?: number;
  tester_decided_at?: string;
  tester_notes?: string;
  auto_approved: boolean;
  
  // Status
  status: 'pending' | 'approved' | 'rejected';
  
  // Relationships
  attribute?: PlanningAttribute;
  data_source?: PlanningDataSource;
  
  // Audit Fields
  created_at: string;
  created_by_id: number;
  updated_at: string;
  updated_by_id: number;
}

// Request/Response Types
export interface PlanningVersionCreateRequest {
  phase_id: number;
  workflow_activity_id?: number;
  parent_version_id?: string;
}

export interface PlanningDataSourceCreateRequest {
  source_name: string;
  source_type: 'database' | 'file' | 'api' | 'sftp' | 's3' | 'other';
  description?: string;
  connection_config: any;
  auth_config?: any;
  refresh_schedule?: string;
  validation_rules?: any;
  estimated_record_count?: number;
  data_freshness_hours?: number;
}

export interface PlanningAttributeCreateRequest {
  attribute_name: string;
  data_type: 'string' | 'integer' | 'decimal' | 'boolean' | 'date' | 'datetime' | 'text';
  description?: string;
  business_definition?: string;
  is_mandatory?: boolean;
  is_cde?: boolean;
  is_primary_key?: boolean;
  max_length?: number;
  information_security_classification?: 'public' | 'internal' | 'confidential' | 'restricted';
  llm_metadata?: any;
}

export interface PlanningPDEMappingCreateRequest {
  data_source_id: string;
  pde_name: string;
  pde_code: string;
  mapping_type?: 'direct' | 'calculated' | 'lookup' | 'conditional';
  source_table: string;
  source_column: string;
  source_field: string;
  column_data_type?: string;
  transformation_rule?: string;
  condition_rule?: string;
  is_primary?: boolean;
  classification?: any;
  llm_metadata?: any;
}

export interface TesterDecisionRequest {
  decision: 'approve' | 'reject' | 'request_changes';
  notes?: string;
}

export interface BulkTesterDecisionRequest {
  item_ids: string[];
  item_type: 'data_source' | 'attribute' | 'pde_mapping';
  decision: 'approve' | 'reject' | 'request_changes';
  notes?: string;
}

export interface PlanningDashboard {
  version: PlanningVersion;
  data_sources: {
    data_sources: PlanningDataSource[];
    total: number;
  };
  attributes: {
    attributes: PlanningAttribute[];
    total: number;
  };
  pde_mappings: {
    pde_mappings: PlanningPDEMapping[];
    total: number;
  };
  completion_percentage: number;
  pending_decisions: number;
  can_submit: boolean;
  submission_requirements: string[];
}

export interface PlanningVersionListResponse {
  versions: PlanningVersion[];
  total: number;
  current_page: number;
  total_pages: number;
}

// Helper function to convert legacy phase identifiers to version system
function getPhaseVersionId(cycleId: number, reportId: number): Promise<string> {
  // For now, we'll use a simple mapping. In production, this would query the backend
  // to find the current planning version for this cycle/report combination
  return Promise.resolve(`${cycleId}-${reportId}-planning-v1`);
}

// Helper function to check if unified planning is available for this cycle/report
async function hasUnifiedPlanning(cycleId: number, reportId: number): Promise<boolean> {
  try {
    // Try to get versions for this phase to see if unified planning is available
    const response = await apiClient.get(`/planning-unified/phases/${cycleId * 1000 + reportId}/versions`);
    return response.data.versions.length > 0;
  } catch (error) {
    // If endpoint fails, unified planning is not available
    return false;
  }
}

export const planningUnifiedApi = {
  // Version Management
  createVersion: async (phaseId: number, versionData: PlanningVersionCreateRequest): Promise<PlanningVersion> => {
    const response = await apiClient.post(`/planning-unified/versions`, {
      ...versionData,
      phase_id: phaseId
    });
    return response.data;
  },

  getVersion: async (versionId: string): Promise<PlanningVersion> => {
    const response = await apiClient.get(`/planning-unified/versions/${versionId}`);
    return response.data;
  },

  getVersionsByPhase: async (phaseId: number, page: number = 1, limit: number = 20): Promise<PlanningVersionListResponse> => {
    const response = await apiClient.get(`/planning-unified/phases/${phaseId}/versions?page=${page}&limit=${limit}`);
    return response.data;
  },

  updateVersion: async (versionId: string, updateData: Partial<PlanningVersion>): Promise<PlanningVersion> => {
    const response = await apiClient.put(`/planning-unified/versions/${versionId}`, updateData);
    return response.data;
  },

  submitVersion: async (versionId: string, submissionData: any = {}): Promise<PlanningVersion> => {
    const response = await apiClient.post(`/planning-unified/versions/${versionId}/submit`, submissionData);
    return response.data;
  },

  approveVersion: async (versionId: string, action: 'approve' | 'reject', notes?: string): Promise<PlanningVersion> => {
    const response = await apiClient.post(`/planning-unified/versions/${versionId}/approve`, {
      action,
      notes
    });
    return response.data;
  },

  // Data Source Management
  createDataSource: async (versionId: string, dataSourceData: PlanningDataSourceCreateRequest): Promise<PlanningDataSource> => {
    const response = await apiClient.post(`/planning-unified/versions/${versionId}/data-sources`, dataSourceData);
    return response.data;
  },

  getDataSourcesByVersion: async (versionId: string): Promise<PlanningDataSource[]> => {
    const response = await apiClient.get(`/planning-unified/versions/${versionId}/data-sources`);
    return response.data.data_sources;
  },

  updateDataSourceDecision: async (dataSourceId: string, decision: TesterDecisionRequest): Promise<any> => {
    const response = await apiClient.put(`/planning-unified/data-sources/${dataSourceId}/decision`, decision);
    return response.data;
  },

  // Attribute Management
  createAttribute: async (versionId: string, attributeData: PlanningAttributeCreateRequest): Promise<PlanningAttribute> => {
    const response = await apiClient.post(`/planning-unified/versions/${versionId}/attributes`, attributeData);
    return response.data;
  },

  getAttributesByVersion: async (versionId: string): Promise<PlanningAttribute[]> => {
    const response = await apiClient.get(`/planning-unified/versions/${versionId}/attributes`);
    return response.data.attributes;
  },

  updateAttributeDecision: async (attributeId: string, decision: TesterDecisionRequest): Promise<any> => {
    const response = await apiClient.put(`/planning-unified/attributes/${attributeId}/decision`, decision);
    return response.data;
  },

  // PDE Mapping Management
  createPDEMapping: async (attributeId: string, pdeMappingData: PlanningPDEMappingCreateRequest): Promise<PlanningPDEMapping> => {
    const response = await apiClient.post(`/planning-unified/attributes/${attributeId}/pde-mappings`, pdeMappingData);
    return response.data;
  },

  getPDEMappingsByVersion: async (versionId: string): Promise<PlanningPDEMapping[]> => {
    const response = await apiClient.get(`/planning-unified/versions/${versionId}/pde-mappings`);
    return response.data.pde_mappings;
  },

  getPDEMappingsByAttribute: async (attributeId: string): Promise<PlanningPDEMapping[]> => {
    const response = await apiClient.get(`/planning-unified/attributes/${attributeId}/pde-mappings`);
    return response.data.pde_mappings;
  },

  updatePDEMappingDecision: async (pdeMappingId: string, decision: TesterDecisionRequest): Promise<any> => {
    const response = await apiClient.put(`/planning-unified/pde-mappings/${pdeMappingId}/decision`, decision);
    return response.data;
  },

  // Bulk Operations
  bulkTesterDecision: async (bulkData: BulkTesterDecisionRequest): Promise<any> => {
    const response = await apiClient.post(`/planning-unified/bulk-decision`, bulkData);
    return response.data;
  },

  // Dashboard
  getVersionDashboard: async (versionId: string): Promise<PlanningDashboard> => {
    const response = await apiClient.get(`/planning-unified/versions/${versionId}/dashboard`);
    return response.data;
  },

  // Migration helpers - these help convert between legacy and unified systems
  
  // Create or get unified version for legacy cycle/report
  getOrCreateVersionForLegacyCycleReport: async (cycleId: number, reportId: number): Promise<PlanningVersion> => {
    try {
      // First check if unified planning is available
      const hasUnified = await hasUnifiedPlanning(cycleId, reportId);
      if (!hasUnified) {
        // Create a new version for this cycle/report
        const phaseId = cycleId * 1000 + reportId; // Simple phase ID mapping
        return await planningUnifiedApi.createVersion(phaseId, {
          phase_id: phaseId
        });
      }

      // Get existing versions
      const phaseId = cycleId * 1000 + reportId;
      const versionsResponse = await planningUnifiedApi.getVersionsByPhase(phaseId);
      
      if (versionsResponse.versions.length > 0) {
        // Return the most recent version
        return versionsResponse.versions[0];
      } else {
        // Create new version
        return await planningUnifiedApi.createVersion(phaseId, {
          phase_id: phaseId
        });
      }
    } catch (error) {
      console.error('Error getting/creating unified version:', error);
      throw error;
    }
  },

  // Legacy compatibility layer - convert legacy ReportAttribute to PlanningAttribute
  convertLegacyAttribute: (legacyAttr: any): PlanningAttributeCreateRequest => {
    return {
      attribute_name: legacyAttr.attribute_name || legacyAttr.name || '',
      data_type: legacyAttr.data_type?.toLowerCase() || 'string',
      description: legacyAttr.description || '',
      business_definition: legacyAttr.business_definition,
      is_mandatory: legacyAttr.mandatory_flag === 'Mandatory',
      is_cde: legacyAttr.cde_flag || false,
      is_primary_key: legacyAttr.is_primary_key || false,
      max_length: legacyAttr.max_length,
      information_security_classification: 
        legacyAttr.information_security_classification?.toLowerCase() || 'internal'
    };
  },

  // Check system availability
  checkUnifiedPlanningAvailability: async (cycleId: number, reportId: number): Promise<boolean> => {
    return await hasUnifiedPlanning(cycleId, reportId);
  }
};

// Export both legacy and unified APIs for gradual migration
export default planningUnifiedApi;