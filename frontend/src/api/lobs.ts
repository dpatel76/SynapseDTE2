import apiClient from './client';
import { LOB, ApiResponse, PaginatedResponse } from '../types/api';

export interface CreateLOBRequest {
  lob_name: string;
  description?: string;
}

export interface UpdateLOBRequest {
  lob_name?: string;
  description?: string;
  is_active?: boolean;
}

export const lobsApi = {
  // Get all LOBs with pagination
  getAll: async (page: number = 1, per_page: number = 10): Promise<PaginatedResponse<LOB>> => {
    const response = await apiClient.get('/lobs/', {
      params: { page, per_page }
    });
    return response.data;
  },

  // Get all LOBs without pagination (for dropdowns)
  getAllActive: async (): Promise<LOB[]> => {
    const response = await apiClient.get('/lobs/active');
    return response.data;
  },

  // Get a specific LOB by ID
  getById: async (lobId: number): Promise<LOB> => {
    const response = await apiClient.get(`/lobs/${lobId}`);
    return response.data;
  },

  // Create a new LOB
  create: async (lobData: CreateLOBRequest): Promise<LOB> => {
    const response = await apiClient.post('/lobs/', lobData);
    return response.data;
  },

  // Update an existing LOB
  update: async (lobId: number, lobData: UpdateLOBRequest): Promise<LOB> => {
    const response = await apiClient.put(`/lobs/${lobId}`, lobData);
    return response.data;
  },

  // Delete a LOB
  delete: async (lobId: number): Promise<void> => {
    await apiClient.delete(`/lobs/${lobId}`);
  }
}; 