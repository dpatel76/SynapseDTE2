import apiClient from './client';
import { User, UserRole, ApiResponse, PaginatedResponse } from '../types/api';

export interface CreateUserRequest {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  role: UserRole;
  lob_id?: number;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  role?: UserRole;
  lob_id?: number;
  is_active?: boolean;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ImpersonateResponse {
  access_token: string;
  token_type: string;
  impersonated_user: User;
}

export const usersApi = {
  // Get all users with pagination
  getAll: async (page: number = 1, per_page: number = 10): Promise<PaginatedResponse<User>> => {
    const response = await apiClient.get('/users/', {
      params: { page, per_page }
    });
    
    // Handle backend response structure {users: [...], total: X} -> {items: [...], total: X}
    const data = response.data;
    const mappedResponse: PaginatedResponse<User> = {
      items: (data.users || []).map((user: any) => ({
        ...user,
        username: user.email // Use email as username since backend doesn't provide username
      })),
      total: data.total || 0,
      page: page,
      per_page: per_page,
      pages: Math.ceil((data.total || 0) / per_page)
    };
    return mappedResponse;
  },

  // Get a specific user by ID
  getById: async (userId: number): Promise<User> => {
    const response = await apiClient.get(`/users/${userId}`);
    return {
      ...response.data,
      username: response.data.email // Use email as username
    };
  },

  // Create a new user
  create: async (userData: CreateUserRequest): Promise<User> => {
    const response = await apiClient.post('/users/', userData);
    return {
      ...response.data,
      username: response.data.email // Use email as username
    };
  },

  // Update an existing user
  update: async (userId: number, userData: UpdateUserRequest): Promise<User> => {
    const response = await apiClient.put(`/users/${userId}`, userData);
    return {
      ...response.data,
      username: response.data.email // Use email as username
    };
  },

  // Delete a user
  delete: async (userId: number): Promise<void> => {
    await apiClient.delete(`/users/${userId}`);
  },

  // Get current user profile
  getProfile: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me');
    return {
      ...response.data,
      username: response.data.email // Use email as username
    };
  },

  // Update current user profile
  updateProfile: async (userData: Partial<UpdateUserRequest>): Promise<User> => {
    // Since there's no /users/me endpoint, we need to get the current user ID first
    const currentUser = await apiClient.get('/auth/me');
    const response = await apiClient.put(`/users/${currentUser.data.user_id}`, userData);
    return {
      ...response.data,
      username: response.data.email // Use email as username
    };
  },

  // Change password for current user
  changePassword: async (passwordData: ChangePasswordRequest): Promise<ApiResponse<any>> => {
    const response = await apiClient.post('/auth/change-password', passwordData);
    return response.data;
  },

  // Reset user password (admin only)
  resetPassword: async (userId: number): Promise<ApiResponse<any>> => {
    const response = await apiClient.post(`/users/${userId}/reset-password`);
    return response.data;
  },

  // Get users by role
  getByRole: async (role: UserRole): Promise<User[]> => {
    const response = await apiClient.get(`/users/role/${role}`);
    return response.data.map((user: any) => ({
      ...user,
      username: user.email // Use email as username
    }));
  },

  // Activate/deactivate user
  toggleStatus: async (userId: number, isActive: boolean): Promise<User> => {
    const response = await apiClient.patch(`/users/${userId}/status`, { is_active: isActive });
    return {
      ...response.data,
      username: response.data.email // Use email as username
    };
  },

  // Impersonate a user (admin only)
  impersonate: async (userId: number): Promise<ImpersonateResponse> => {
    const response = await apiClient.post(`/users/${userId}/impersonate`);
    return response.data;
  },

  // Get all report owners (Report Owner and Report Owner Executive roles)
  getReportOwners: async (): Promise<User[]> => {
    const response = await apiClient.get('/users/report-owners');
    return response.data.map((user: any) => ({
      ...user,
      username: user.email // Use email as username
    }));
  }
}; 