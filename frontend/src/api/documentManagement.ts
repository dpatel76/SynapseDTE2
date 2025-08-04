import { apiClient } from './client';

// Document Management API Types
export interface Document {
  id: number;
  cycle_id: number;
  report_id: number;
  phase_id: number;
  test_case_id?: string;
  document_type: string;
  document_category: string;
  original_filename: string;
  file_size: number;
  file_format: string;
  mime_type: string;
  document_title: string;
  document_description?: string;
  document_version: string;
  is_latest_version: boolean;
  access_level: string;
  upload_status: string;
  processing_status: string;
  validation_status: string;
  content_preview?: string;
  quality_score?: number;
  download_count: number;
  view_count: number;
  required_for_completion: boolean;
  approval_required: boolean;
  workflow_stage?: string;
  uploaded_by: number;
  uploaded_at?: string;
  created_at?: string;
  updated_at?: string;
  is_archived: boolean;
}

export interface DocumentUploadRequest {
  cycle_id: number;
  report_id: number;
  phase_id: number;
  test_case_id?: string;
  document_type: string;
  document_title: string;
  document_description?: string;
  document_category?: string;
  access_level?: string;
  required_for_completion?: boolean;
  approval_required?: boolean;
  workflow_stage?: string;
}

export interface DocumentListResponse {
  documents: Document[];
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
  };
}

export interface DocumentSearchRequest {
  search_query: string;
  cycle_id?: number;
  report_id?: number;
  phase_id?: number;
  document_type?: string;
  page?: number;
  page_size?: number;
}

export interface DocumentSearchResponse {
  search_results: {
    document: Document;
    relevance_score: number;
  }[];
  search_query: string;
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
  };
}

export interface DocumentMetrics {
  total_documents: number;
  total_size_bytes: number;
  total_size_mb: number;
  by_document_type: Record<string, { count: number; size_bytes: number }>;
  by_upload_status: Record<string, number>;
  by_file_format: Record<string, { count: number; size_bytes: number }>;
}

export interface DocumentVersions {
  versions: Document[];
  total_versions: number;
  latest_version?: Document;
}

// Document Management API Service
export class DocumentManagementAPI {
  
  // List documents with filtering
  static async listDocuments(params: {
    cycle_id?: number;
    report_id?: number;
    phase_id?: number;
    test_case_id?: string;
    document_type?: string;
    include_archived?: boolean;
    latest_only?: boolean;
    page?: number;
    page_size?: number;
  } = {}): Promise<DocumentListResponse> {
    const response = await apiClient.get('/document-management/documents/', {
      params: {
        cycle_id: params.cycle_id,
        report_id: params.report_id,
        phase_id: params.phase_id,
        test_case_id: params.test_case_id,
        document_type: params.document_type,
        include_archived: params.include_archived ?? false,
        latest_only: params.latest_only ?? true,
        page: params.page ?? 1,
        page_size: params.page_size ?? 50
      }
    });
    return response.data;
  }

  // Get document details
  static async getDocument(documentId: number): Promise<Document> {
    const response = await apiClient.get(`/document-management/documents/${documentId}`);
    return response.data;
  }

  // Upload document
  static async uploadDocument(
    file: File,
    metadata: DocumentUploadRequest
  ): Promise<{ success: boolean; document_id?: number; document?: Document; error?: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('cycle_id', metadata.cycle_id.toString());
    formData.append('report_id', metadata.report_id.toString());
    formData.append('phase_id', metadata.phase_id.toString());
    formData.append('document_type', metadata.document_type);
    formData.append('document_title', metadata.document_title);
    
    if (metadata.document_description) {
      formData.append('document_description', metadata.document_description);
    }
    if (metadata.document_category) {
      formData.append('document_category', metadata.document_category);
    }
    if (metadata.access_level) {
      formData.append('access_level', metadata.access_level);
    }
    if (metadata.required_for_completion !== undefined) {
      formData.append('required_for_completion', metadata.required_for_completion.toString());
    }
    if (metadata.approval_required !== undefined) {
      formData.append('approval_required', metadata.approval_required.toString());
    }
    if (metadata.workflow_stage) {
      formData.append('workflow_stage', metadata.workflow_stage);
    }
    if (metadata.test_case_id) {
      formData.append('test_case_id', metadata.test_case_id);
    }

    const response = await apiClient.post('/document-management/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  }

  // Download document
  static async downloadDocument(documentId: number, trackDownload: boolean = true): Promise<Blob> {
    const response = await apiClient.get(`/document-management/documents/${documentId}/download`, {
      params: { track_download: trackDownload },
      responseType: 'blob'
    });
    return response.data;
  }

  // Update document metadata
  static async updateDocument(
    documentId: number,
    updates: Partial<DocumentUploadRequest>
  ): Promise<{ success: boolean; document?: Document; error?: string }> {
    const response = await apiClient.put(`/document-management/documents/${documentId}`, updates);
    return response.data;
  }

  // Delete document
  static async deleteDocument(
    documentId: number,
    permanent: boolean = false
  ): Promise<{ success: boolean; message?: string; error?: string }> {
    const response = await apiClient.delete(`/document-management/documents/${documentId}`, {
      params: { permanent }
    });
    return response.data;
  }

  // Search documents
  static async searchDocuments(searchRequest: DocumentSearchRequest): Promise<DocumentSearchResponse> {
    const response = await apiClient.post('/document-management/documents/search', searchRequest);
    return response.data;
  }

  // Get document statistics
  static async getDocumentStatistics(params: {
    cycle_id?: number;
    report_id?: number;
    phase_id?: number;
  } = {}): Promise<DocumentMetrics> {
    const response = await apiClient.get('/document-management/documents/statistics/summary', {
      params
    });
    return response.data;
  }

  // Version management
  static async createDocumentVersion(
    documentId: number,
    file: File,
    metadata: {
      document_title: string;
      document_description?: string;
      version_notes?: string;
    }
  ): Promise<{ success: boolean; document_id?: number; document?: Document; version?: string; error?: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_title', metadata.document_title);
    
    if (metadata.document_description) {
      formData.append('document_description', metadata.document_description);
    }
    if (metadata.version_notes) {
      formData.append('version_notes', metadata.version_notes);
    }

    const response = await apiClient.post(`/document-management/documents/${documentId}/versions`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  }

  static async getDocumentVersions(documentId: number): Promise<DocumentVersions> {
    const response = await apiClient.get(`/document-management/documents/${documentId}/versions`);
    return response.data;
  }

  static async restoreDocumentVersion(
    versionId: number
  ): Promise<{ success: boolean; message?: string; document?: Document; error?: string }> {
    const response = await apiClient.post(`/document-management/documents/versions/${versionId}/restore`);
    return response.data;
  }

  static async compareDocumentVersions(
    version1Id: number,
    version2Id: number
  ): Promise<{
    version1: Document;
    version2: Document;
    differences: Record<string, { version1: any; version2: any }>;
    has_differences: boolean;
  }> {
    const response = await apiClient.post('/document-management/documents/versions/compare', {
      version1_id: version1Id,
      version2_id: version2Id
    });
    return response.data;
  }

  // Bulk operations
  static async bulkDeleteDocuments(
    documentIds: number[],
    permanent: boolean = false
  ): Promise<{
    success_count: number;
    failure_count: number;
    total_count: number;
    successes: number[];
    failures: Array<{ document_id: number; error: string }>;
  }> {
    const response = await apiClient.post('/document-management/documents/bulk/delete', {
      document_ids: documentIds,
      permanent
    });
    return response.data;
  }

  // Utility methods
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  static getFileIcon(fileFormat: string): string {
    const iconMap: Record<string, string> = {
      'pdf': '📄',
      'docx': '📝',
      'word': '📝',
      'xlsx': '📊',
      'excel': '📊',
      'xls': '📊',
      'csv': '📊',
      'pipe': '📊',
      'jpg': '🖼️',
      'jpeg': '🖼️',
      'png': '🖼️',
    };
    return iconMap[fileFormat.toLowerCase()] || '📎';
  }

  static getStatusColor(status: string): string {
    const colorMap: Record<string, string> = {
      'uploaded': 'success',
      'processing': 'warning',
      'processed': 'success',
      'failed': 'error',
      'quarantined': 'error',
      'valid': 'success',
      'invalid': 'error',
      'warning': 'warning',
    };
    return colorMap[status] || 'default';
  }
}

export default DocumentManagementAPI;