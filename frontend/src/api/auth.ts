import apiClient from './client';
import { LoginRequest, LoginResponse, User } from '../types/api';

export const authApi = {
  // Login
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    console.log('Login request:', credentials);
    const response = await apiClient.post('/auth/login', credentials);
    console.log('Login response:', response.data);
    
    // Validate response structure
    if (!response.data.access_token || !response.data.user) {
      console.error('Invalid login response:', response.data);
      throw new Error('Invalid login response from server');
    }
    
    return {
      access_token: response.data.access_token,
      token_type: response.data.token_type || 'bearer',
      user: response.data.user
    };
  },

  // Logout
  logout: async (): Promise<void> => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('impersonation_token');
  },

  // Get current user
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  // Check if user is authenticated
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('token');
  },

  // Check if user is impersonating
  isImpersonating: (): boolean => {
    return !!localStorage.getItem('impersonation_token');
  },

  // Get stored user data
  getStoredUser: (): User | null => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
    return null;
  },

  // Get stored token
  getStoredToken: (): string | null => {
    return localStorage.getItem('impersonation_token') || localStorage.getItem('token');
  },
}; 