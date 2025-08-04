import apiClient from './client';
import { Report, ApiResponse, PaginatedResponse, AssignedReport } from '../types/api';

export interface CreateReportRequest {
  report_name: string;
  lob_id: number;
  report_owner_id: number;
  description?: string;
  frequency: string;
  regulation?: string;
}

export interface UpdateReportRequest {
  report_name?: string;
  lob_id?: number;
  description?: string;
  frequency?: string;
  is_active?: boolean;
}

export interface TesterStats {
  total_assigned: number;
  in_progress: number;
  completed: number;
  pending_actions: number;
  overdue_items: number;
}

export const reportsApi = {
  // Get all reports with pagination
  getAll: async (page: number = 1, per_page: number = 10): Promise<PaginatedResponse<Report>> => {
    const skip = (page - 1) * per_page;
    const response = await apiClient.get('/reports/', {
      params: { skip, limit: per_page }
    });
    
    // Transform backend response to match frontend expectations
    return {
      items: response.data.reports,
      total: response.data.total,
      page: page,
      per_page: per_page,
      pages: Math.ceil(response.data.total / per_page)
    };
  },

  // Get a specific report by ID
  getById: async (reportId: number): Promise<Report> => {
    const response = await apiClient.get(`/reports/${reportId}`);
    return response.data;
  },

  // Create a new report
  create: async (reportData: CreateReportRequest): Promise<Report> => {
    const response = await apiClient.post('/reports/', reportData);
    return response.data;
  },

  // Update an existing report
  update: async (reportId: number, reportData: UpdateReportRequest): Promise<Report> => {
    const response = await apiClient.put(`/reports/${reportId}`, reportData);
    return response.data;
  },

  // Delete a report
  delete: async (reportId: number): Promise<void> => {
    await apiClient.delete(`/reports/${reportId}`);
  },

  // Get report attributes
  getAttributes: async (reportId: number): Promise<any[]> => {
    const response = await apiClient.get(`/reports/${reportId}/attributes`);
    return response.data;
  },

  // Add attribute to report
  addAttribute: async (reportId: number, attributeData: any): Promise<any> => {
    const response = await apiClient.post(`/reports/${reportId}/attributes`, attributeData);
    return response.data;
  },

  // Update report attribute
  updateAttribute: async (reportId: number, attributeId: number, attributeData: any): Promise<any> => {
    const response = await apiClient.put(`/reports/${reportId}/attributes/${attributeId}`, attributeData);
    return response.data;
  },

  // Delete report attribute
  deleteAttribute: async (reportId: number, attributeId: number): Promise<void> => {
    await apiClient.delete(`/reports/${reportId}/attributes/${attributeId}`);
  },

  // Get reports by LOB
  getByLOB: async (lobId: number): Promise<Report[]> => {
    const response = await apiClient.get(`/reports/lob/${lobId}`);
    return response.data;
  },

  // Get tester statistics
  getTesterStats: async (testerId: number): Promise<TesterStats> => {
    const response = await apiClient.get(`/cycle-reports/tester-stats/${testerId}`);
    return response.data;
  },

  // Get reports by tester ID
  getByTester: async (testerId: number): Promise<AssignedReport[]> => {
    const response = await apiClient.get(`/cycle-reports/by-tester/${testerId}`);
    return response.data;
  }
}; 