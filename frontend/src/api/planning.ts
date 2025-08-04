import apiClient from './client';
import { planningUnifiedApi, PlanningVersion, PlanningAttribute as UnifiedPlanningAttribute } from './planningUnified';

// Types for Planning Phase API
export interface DocumentUpload {
  document_id: string;
  document_name: string;
  document_type: 'Regulatory Specification' | 'CDE List' | 'Historical Issues';
  file_size: number;
  created_at: string;
  status: 'Uploaded' | 'Processing' | 'Processed';
}

export interface ReportAttribute {
  id: string; // UUID instead of attribute_id for new unified planning
  attribute_name: string;
  description?: string;
  data_type: 'string' | 'integer' | 'decimal' | 'date' | 'datetime' | 'boolean' | 'text'; // Updated to match unified planning enums
  mandatory_flag: 'mandatory' | 'conditional' | 'optional'; // Lowercase to match unified planning
  cde_flag: boolean;
  historical_issues_flag: boolean;
  llm_generated: boolean;
  llm_rationale?: string;
  is_scoped?: boolean;
  tester_notes?: string;
  
  // Data dictionary import fields
  line_item_number?: string;
  technical_line_item_name?: string;
  mdrm?: string;
  
  // Enhanced LLM-generated fields for better testing guidance
  validation_rules?: string;
  typical_source_documents?: string;
  keywords_to_look_for?: string;
  testing_approach?: string;
  
  // Risk assessment fields
  risk_score?: number;
  llm_risk_rationale?: string;
  
  // Approval workflow field  
  approval_status?: 'pending' | 'approved' | 'rejected';
  
  // Information Security Classification (updated to match unified planning)
  information_security_classification?: 'public' | 'internal' | 'confidential' | 'restricted';
  
  // Unified Planning Fields
  version_id: string; // Required for unified planning
  phase_id: number; // Required for unified planning
  is_primary_key: boolean;
  primary_key_order?: number;
  tester_decision?: 'approve' | 'reject' | 'request_changes';
  tester_decision_date?: string;
  tester_decision_notes?: string;
  
  // Audit fields from unified model
  created_at: string;
  created_by_id: number;
  updated_at: string;
  updated_by_id: number;
  cycle_id: number;
  report_id: number;
}

export interface PlanningPhaseStatus {
  cycle_id: number;
  report_id: number;
  status: 'Not Started' | 'In Progress' | 'Complete';
  
  // Date fields
  planned_start_date?: string;
  planned_end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  
  // Alternative names for compatibility
  started_at?: string;
  completed_at?: string;
  
  // Attribute metrics
  attributes_count: number;
  approved_count: number;
  cde_count: number;
  historical_issues_count: number;
  llm_generated_count: number;
  manual_added_count: number;
  can_complete: boolean;
  completion_requirements: string[];
}

export interface CreateAttributeRequest {
  attribute_name: string;
  description: string;
  data_type: string;
  mandatory_flag: string;
  cde_flag?: boolean;
  historical_issues_flag?: boolean;
  tester_notes?: string;
  
  // Enhanced LLM-generated fields for better testing guidance
  validation_rules?: string;
  typical_source_documents?: string;
  keywords_to_look_for?: string;
  testing_approach?: string;
}

export interface UpdateAttributeRequest {
  attribute_name?: string;
  description?: string;
  data_type?: string;
  mandatory_flag?: string;
  cde_flag?: boolean;
  historical_issues_flag?: boolean;
  tester_notes?: string;
  
  // Enhanced LLM-generated fields for better testing guidance
  validation_rules?: string;
  typical_source_documents?: string;
  keywords_to_look_for?: string;
  testing_approach?: string;
  
  // Risk assessment fields
  risk_score?: number;
  llm_risk_rationale?: string;
  
  // Primary key support fields
  is_primary_key?: boolean;
  primary_key_order?: number;
  
  // Approval status field
  approval_status?: 'pending' | 'approved' | 'rejected';
  
  // Information Security Classification
  information_security_classification?: 'HRCI' | 'Confidential' | 'Proprietary' | 'Public';
  
  // LLM classification rationale
  llm_classification_rationale?: string;
}

export interface LLMGenerationRequest {
  document_ids: string[];
  generation_type: 'full' | 'incremental';
  include_cde_matching: boolean;
  include_historical_matching: boolean;
  provider?: 'claude' | 'gemini' | 'auto' | 'hybrid';
  discovery_provider?: 'claude' | 'gemini';
  details_provider?: 'claude' | 'gemini';
  regulatory_context?: string;
  regulatory_report?: string;
  schedule?: string;
}

export interface FileUploadResponse {
  document_id: string;
  file_name: string;
  file_size: number;
  document_type: string;
  status: string;
  upload_date: string;
}

export interface PlanningPhaseStart {
  planned_start_date?: string;
  planned_end_date?: string;
}

export interface PlanningPhaseComplete {
  completion_notes?: string;
  attributes_confirmed: boolean;
  documents_verified: boolean;
}

// Job Status API
export interface JobStatus {
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
  metadata: any;
}

// Global flag to enable/disable unified planning for testing
let USE_UNIFIED_PLANNING = false;

// Helper to check if we should use unified planning for this cycle/report
async function shouldUseUnifiedPlanning(cycleId: number, reportId: number): Promise<boolean> {
  if (!USE_UNIFIED_PLANNING) return false;
  
  try {
    return await planningUnifiedApi.checkUnifiedPlanningAvailability(cycleId, reportId);
  } catch (error) {
    console.warn('Unified planning check failed, falling back to legacy:', error);
    return false;
  }
}

// Convert unified attributes to legacy format for backward compatibility
function convertUnifiedToLegacyAttribute(unifiedAttr: UnifiedPlanningAttribute): ReportAttribute {
  return {
    id: unifiedAttr.attribute_id,
    attribute_name: unifiedAttr.attribute_name,
    description: unifiedAttr.description || '',
    data_type: unifiedAttr.data_type.charAt(0).toUpperCase() + unifiedAttr.data_type.slice(1) as any,
    mandatory_flag: unifiedAttr.is_mandatory ? 'mandatory' : 'optional',
    cde_flag: unifiedAttr.is_cde,
    historical_issues_flag: false, // Not in unified model
    llm_generated: false, // Default
    llm_rationale: undefined,
    is_scoped: true, // Default
    tester_notes: unifiedAttr.tester_notes,
    
    // Data dictionary import fields - not in unified model
    line_item_number: undefined,
    technical_line_item_name: undefined,
    mdrm: undefined,
    
    // Enhanced LLM-generated fields
    validation_rules: undefined,
    typical_source_documents: undefined,
    keywords_to_look_for: undefined,
    testing_approach: undefined,
    
    // Risk assessment fields
    risk_score: undefined,
    llm_risk_rationale: undefined,
    
    // Primary key support fields
    is_primary_key: unifiedAttr.is_primary_key,
    primary_key_order: undefined,
    
    // Approval workflow field
    approval_status: unifiedAttr.tester_decision as any || 'pending',
    
    // Information Security Classification
    information_security_classification: unifiedAttr.information_security_classification 
      ? (unifiedAttr.information_security_classification.charAt(0).toUpperCase() + 
         unifiedAttr.information_security_classification.slice(1)) as any
      : 'public' as any,
    
    created_at: unifiedAttr.created_at,
    updated_at: unifiedAttr.updated_at,
    cycle_id: Math.floor(unifiedAttr.phase_id / 1000), // Reverse phase ID mapping
    report_id: unifiedAttr.phase_id % 1000,
    version_id: unifiedAttr.version_id,
    phase_id: unifiedAttr.phase_id,
    created_by_id: unifiedAttr.created_by_id,
    updated_by_id: unifiedAttr.updated_by_id
  };
}

export const planningApi = {
  // Start planning phase
  startPhase: async (cycleId: number, reportId: number, phaseData: PlanningPhaseStart): Promise<PlanningPhaseStatus> => {
    const response = await apiClient.post(`/planning/cycles/${cycleId}/reports/${reportId}/start`, phaseData);
    return response.data;
  },

  // Get planning phase status
  getStatus: async (cycleId: number, reportId: number): Promise<PlanningPhaseStatus> => {
    const response = await apiClient.get(`/planning/cycles/${cycleId}/reports/${reportId}/status`);
    return response.data;
  },

  // Upload document
  uploadDocument: async (
    cycleId: number, 
    reportId: number, 
    file: File, 
    documentType: string
  ): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const response = await apiClient.post(
      `/planning/cycles/${cycleId}/reports/${reportId}/documents/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // List documents
  listDocuments: async (cycleId: number, reportId: number): Promise<DocumentUpload[]> => {
    const response = await apiClient.get(`/planning/cycles/${cycleId}/reports/${reportId}/documents/`);
    return response.data;
  },

  // Create attribute
  createAttribute: async (
    cycleId: number, 
    reportId: number, 
    attributeData: CreateAttributeRequest
  ): Promise<ReportAttribute> => {
    const useUnified = await shouldUseUnifiedPlanning(cycleId, reportId);
    
    if (useUnified) {
      try {
        // Get or create unified version for this cycle/report
        const version = await planningUnifiedApi.getOrCreateVersionForLegacyCycleReport(cycleId, reportId);
        
        // Convert legacy attribute data to unified format
        const unifiedAttributeData = planningUnifiedApi.convertLegacyAttribute({
          ...attributeData,
          mandatory_flag: attributeData.mandatory_flag
        });
        
        // Create attribute in unified system
        const unifiedAttribute = await planningUnifiedApi.createAttribute(version.version_id, unifiedAttributeData);
        
        // Convert back to legacy format for UI compatibility
        return convertUnifiedToLegacyAttribute(unifiedAttribute);
      } catch (error) {
        console.warn('Unified planning failed, falling back to legacy:', error);
        // Fall through to legacy implementation
      }
    }
    
    // Legacy implementation
    const response = await apiClient.post(`/planning/cycles/${cycleId}/reports/${reportId}/attributes/`, attributeData);
    return response.data;
  },

  // List attributes
  listAttributes: async (cycleId: number, reportId: number): Promise<ReportAttribute[]> => {
    const useUnified = await shouldUseUnifiedPlanning(cycleId, reportId);
    
    if (useUnified) {
      try {
        // Get unified version for this cycle/report
        const version = await planningUnifiedApi.getOrCreateVersionForLegacyCycleReport(cycleId, reportId);
        
        // Get attributes from unified system
        const unifiedAttributes = await planningUnifiedApi.getAttributesByVersion(version.version_id);
        
        // Convert to legacy format for UI compatibility
        return unifiedAttributes.map(convertUnifiedToLegacyAttribute);
      } catch (error) {
        console.warn('Unified planning failed, falling back to legacy:', error);
        // Fall through to legacy implementation
      }
    }
    
    // Legacy implementation
    const response = await apiClient.get(`/planning/cycles/${cycleId}/reports/${reportId}/attributes/`);
    console.log('Raw API response:', response);
    console.log('Response data:', response.data);
    console.log('Response data type:', typeof response.data);
    
    // Handle both direct array response and wrapped response
    const attributesArray = Array.isArray(response.data) ? response.data : (response.data.attributes || []);
    console.log('Extracted attributes array:', attributesArray);
    console.log('Array length:', attributesArray.length);
    if (attributesArray.length > 0) {
      console.log('First attribute before mapping:', attributesArray[0]);
    }
    
    // Transform attribute_id to id for frontend compatibility
    const mappedAttributes = attributesArray.map((attr: any) => ({
      ...attr,
      id: String(attr.attribute_id || attr.id) // Convert to string as expected by ReportAttribute interface
    }));
    
    console.log('Mapped attributes:', mappedAttributes);
    if (mappedAttributes.length > 0) {
      console.log('First mapped attribute:', mappedAttributes[0]);
    }
    
    return mappedAttributes;
  },

  // Update attribute
  updateAttribute: async (
    cycleId: number, 
    reportId: number, 
    attributeId: string, 
    attributeData: UpdateAttributeRequest
  ): Promise<ReportAttribute> => {
    // Check if we're only updating classification
    if (Object.keys(attributeData).length === 1 && 'information_security_classification' in attributeData) {
      // Use the new classification endpoint
      const response = await apiClient.put(
        `/planning/cycles/${cycleId}/reports/${reportId}/attributes/${attributeId}/classification`,
        attributeData
      );
      // Return the attribute (we'll need to fetch it again to get updated data)
      const attributes = await planningApi.listAttributes(cycleId, reportId);
      return attributes.find((a: ReportAttribute) => a.id === attributeId) || attributes[0];
    }
    
    // Use standard attribute update endpoint for other updates
    const response = await apiClient.put(
      `/planning/cycles/${cycleId}/reports/${reportId}/attributes/${attributeId}`, 
      attributeData
    );
    return response.data;
  },

  // Delete attribute
  deleteAttribute: async (cycleId: number, reportId: number, attributeId: string): Promise<void> => {
    await apiClient.delete(`/planning/cycles/${cycleId}/reports/${reportId}/attributes/${attributeId}`);
  },

  // Bulk update attributes
  bulkUpdateAttributes: async (
    cycleId: number, 
    reportId: number, 
    attributeIds: string[], 
    updateData: Record<string, any>
  ): Promise<{ updated: number; message: string }> => {
    const response = await apiClient.post(
      `/planning/cycles/${cycleId}/reports/${reportId}/attributes/bulk-update`,
      {
        attribute_ids: attributeIds,
        update_data: updateData
      }
    );
    return response.data;
  },

  // Generate attributes using LLM
  generateAttributesLLM: async (
    cycleId: number, 
    reportId: number, 
    generationRequest: LLMGenerationRequest
  ): Promise<any> => {
    try {
      // Get the document text from uploaded documents to create regulatory context (optional)
      const documents = await planningApi.listDocuments(cycleId, reportId);
      
      // Find regulatory specification document (optional)
      const regSpec = documents.find(doc => doc.document_type === 'Regulatory Specification');
      
      // Create regulatory context from document information if available
      let regulatoryContext = generationRequest.regulatory_context;
      
      if (!regulatoryContext) {
        if (regSpec) {
          regulatoryContext = `Generate comprehensive test attributes for regulatory compliance report.
Document: ${regSpec.document_name}
Document Type: ${regSpec.document_type}
File Size: ${regSpec.file_size} bytes

Please generate ALL attributes required for financial regulatory compliance testing. Include attributes for:
- Entity identification (borrower info, account details)
- Financial data (amounts, balances, ratios)  
- Date fields (origination, maturity, reporting dates)
- Status and classification fields
- Risk and compliance indicators
- Data quality and validation flags

Generate a comprehensive list that covers the entire regulatory schedule/report.`;
        } else {
          regulatoryContext = `Generate comprehensive test attributes for regulatory compliance testing.

Please generate ALL attributes required for financial regulatory compliance testing. Include attributes for:
- Entity identification (borrower info, account details)  
- Financial data (amounts, balances, ratios)
- Date fields (origination, maturity, reporting dates)
- Status and classification fields
- Risk and compliance indicators
- Data quality and validation flags

Generate a comprehensive list based on the specified regulatory report and schedule.`;
        }
      }

      // Call the LLM endpoint with provider selection and extended timeout
      const llmRequest: any = {
        regulatory_context: regulatoryContext,
        report_type: 'Compliance Report'
      };

      // Add provider preference if specified
      if (generationRequest.provider && generationRequest.provider !== 'auto') {
        llmRequest.preferred_provider = generationRequest.provider;
      }
      
      // Add specific provider preferences for 2-phase approach
      if (generationRequest.discovery_provider) {
        llmRequest.discovery_provider = generationRequest.discovery_provider;
      }
      
      if (generationRequest.details_provider) {
        llmRequest.details_provider = generationRequest.details_provider;
      }
      
      // Add regulatory report and schedule if specified
      if (generationRequest.regulatory_report) {
        llmRequest.regulatory_report = generationRequest.regulatory_report;
      }
      
      if (generationRequest.schedule) {
        llmRequest.schedule = generationRequest.schedule;
      }

      // Use the new planning endpoint for LLM generation with CDE/historical matching
      const response = await apiClient.post(`/planning/cycles/${cycleId}/reports/${reportId}/generate-attributes-llm`, {
        ...generationRequest,
        ...llmRequest
      }, {
        timeout: 180000 // 3 minutes
      });
      
      // The new endpoint handles saving attributes on the backend
      // Just return the response which includes saved attributes
      return response.data;
    } catch (error: any) {
      // Handle timeout errors specifically
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        // Even if timeout occurred, check if attributes were generated by refreshing the list
        const checkError = new Error('LLM generation timed out on the frontend, but it may have completed on the server. Please refresh the page to check if attributes were generated.');
        (checkError as any).isTimeoutError = true;
        throw checkError;
      }
      
      // Handle authentication errors specifically for LLM endpoint
      if (error.response?.status === 401 || error.response?.status === 403) {
        // Throw a custom error that won't trigger logout
        const authError = new Error('Authentication failed for LLM service. Please refresh the page and try again.');
        (authError as any).isAuthError = true;
        (authError as any).skipLogout = true;
        throw authError;
      }
      
      // Handle other HTTP errors
      if (error.response?.status === 500) {
        throw new Error('LLM service is temporarily unavailable. Please try again later.');
      }
      
      // Re-throw the original error for other cases
      throw error;
    }
  },

  // Complete planning phase
  completePhase: async (cycleId: number, reportId: number, completion: PlanningPhaseComplete): Promise<PlanningPhaseStatus> => {
    const response = await apiClient.post(`/planning/cycles/${cycleId}/reports/${reportId}/complete`, completion);
    return response.data;
  },

  // Set planning phase to In Progress
  setInProgress: async (cycleId: number, reportId: number): Promise<PlanningPhaseStatus> => {
    const response = await apiClient.post(`/planning/cycles/${cycleId}/reports/${reportId}/set-in-progress`);
    return response.data;
  },

  // Get document by ID
  getDocument: async (cycleId: number, reportId: number, documentId: string): Promise<DocumentUpload> => {
    const response = await apiClient.get(`/planning/cycles/${cycleId}/reports/${reportId}/documents/${documentId}`);
    return response.data;
  },

  // Delete document
  deleteDocument: async (cycleId: number, reportId: number, documentId: string): Promise<void> => {
    await apiClient.delete(`/planning/cycles/${cycleId}/reports/${reportId}/documents/${documentId}`);
  },

  // Get attributes by status/version
  getAttributesByStatus: async (
    cycleId: number, 
    reportId: number, 
    versionFilter: string = 'latest',
    statusFilter?: string
  ): Promise<{ attributes: ReportAttribute[], total: number, filter_applied: any }> => {
    const params = new URLSearchParams();
    params.append('version_filter', versionFilter);
    if (statusFilter) {
      params.append('status_filter', statusFilter);
    }
    const response = await apiClient.get(`/planning/cycles/${cycleId}/reports/${reportId}/attributes/by-status?${params.toString()}`);
    return response.data;
  },

  // Get job status
  getJobStatus: async (jobId: string): Promise<JobStatus> => {
    const response = await apiClient.get(`/background_jobs/${jobId}/status`);
    return response.data;
  }
}; 