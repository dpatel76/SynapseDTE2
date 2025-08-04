import apiClient from './client';
import { TestCycle, CycleStatus, ApiResponse, PaginatedResponse } from '../types/api';

export interface CreateTestCycleRequest {
  cycle_name: string;
  description?: string;
  start_date: string;
  end_date?: string;
  report_ids?: number[];
}

export interface UpdateTestCycleRequest {
  cycle_name?: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  status?: CycleStatus | string;
}

export const cyclesApi = {
  // Get all test cycles with pagination
  getAll: async (page: number = 1, per_page: number = 10): Promise<PaginatedResponse<TestCycle>> => {
    const skip = (page - 1) * per_page;
    console.log('cyclesApi.getAll - Request params:', { page, per_page, skip, limit: per_page });
    
    const response = await apiClient.get('/cycles/', {
      params: { skip, limit: per_page }
    });
    
    console.log('cyclesApi.getAll - Raw response:', response.data);
    console.log('cyclesApi.getAll - Cycles count:', response.data.cycles?.length);
    console.log('cyclesApi.getAll - Total:', response.data.total);
    
    // Transform backend response to match frontend expectations
    const result = {
      items: response.data.cycles,
      total: response.data.total,
      page: page,
      per_page: per_page,
      pages: Math.ceil(response.data.total / per_page)
    };
    
    console.log('cyclesApi.getAll - Transformed result:', result);
    return result;
  },

  // Get a specific test cycle by ID
  getById: async (cycleId: number): Promise<TestCycle> => {
    const response = await apiClient.get(`/cycles/${cycleId}`);
    return response.data;
  },

  // Create a new test cycle
  create: async (cycleData: CreateTestCycleRequest): Promise<TestCycle> => {
    const response = await apiClient.post('/cycles/', cycleData);
    return response.data;
  },

  // Update an existing test cycle
  update: async (cycleId: number, cycleData: UpdateTestCycleRequest): Promise<TestCycle> => {
    const response = await apiClient.put(`/cycles/${cycleId}`, cycleData);
    return response.data;
  },

  // Delete a test cycle
  delete: async (cycleId: number): Promise<void> => {
    await apiClient.delete(`/cycles/${cycleId}`);
  },

  // Get reports assigned to a cycle
  getReports: async (cycleId: number): Promise<any[]> => {
    const response = await apiClient.get(`/cycles/${cycleId}/reports`);
    return response.data;
  },

  // Assign reports to a cycle
  assignReports: async (cycleId: number, reportIds: number[]): Promise<ApiResponse<any>> => {
    const response = await apiClient.post(`/cycles/${cycleId}/reports`, {
      report_ids: reportIds
    });
    return response.data;
  },

  // Remove reports from a cycle
  removeReports: async (cycleId: number, reportIds: number[]): Promise<ApiResponse<any>> => {
    const response = await apiClient.delete(`/cycles/${cycleId}/reports`, {
      data: { report_ids: reportIds }
    });
    return response.data;
  },

  // Get cycle statistics
  getStats: async (): Promise<any> => {
    const response = await apiClient.get('/cycles/stats');
    return response.data;
  }
}; 