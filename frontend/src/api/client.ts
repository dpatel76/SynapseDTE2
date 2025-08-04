import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { handleMockResponse, isMockDataEnabled } from './mockInterceptor';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    // Use impersonation token if available, otherwise use regular token
    const impersonationToken = localStorage.getItem('impersonation_token');
    const regularToken = localStorage.getItem('token');
    
    const token = impersonationToken || regularToken;
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    // Don't log 404 errors for certain endpoints as they're expected when no data exists
    const isFeedbackEndpoint = error.config?.url?.includes('/feedback');
    const isJobStatusEndpoint = error.config?.url?.includes('/job-status');
    const is404Error = error.response?.status === 404;
    
    // Don't log 403 errors for LOBs endpoint as it's expected for Tester role
    const isLobsEndpoint = error.config?.url?.includes('/lobs/');
    const is403Error = error.response?.status === 403;
    
    if (!((isFeedbackEndpoint || isJobStatusEndpoint) && is404Error) && !(isLobsEndpoint && is403Error)) {
      console.error('API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers
      });
    }

    if (error.response?.status === 401) {
      // Don't redirect if this is a login attempt failure
      if (error.config?.url?.includes('/auth/login')) {
        return Promise.reject(error);
      }
      
      // Don't redirect if this is an LLM endpoint - let the calling code handle it
      if (error.config?.url?.includes('/llm/')) {
        console.log('LLM authentication error - not triggering logout');
        return Promise.reject(error);
      }
      
      // Clear tokens and redirect to login for other 401 errors
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('impersonation_token');
      window.location.href = '/login';
    }

    if (error.response?.status === 403) {
      // Don't redirect for LLM endpoints - let the calling code handle it
      if (error.config?.url?.includes('/llm/')) {
        console.log('LLM permission error - not triggering logout');
        return Promise.reject(error);
      }
    }

    // Handle CORS errors
    if (error.message === 'Network Error') {
      console.error('CORS or Network Error:', error);
      return Promise.reject(new Error('Unable to connect to the server. Please check your network connection.'));
    }

    // Handle 500 errors
    if (error.response?.status === 500) {
      console.error('Server Error:', error.response?.data);
      return Promise.reject(new Error('Server error occurred. Please try again later.'));
    }

    // Try to handle with mock data before rejecting
    const mockResponse = handleMockResponse(error);
    if (mockResponse) {
      console.log(`🎭 Using mock data for ${error.config?.url}`);
      return mockResponse;
    }
    
    return Promise.reject(error);
  }
);

// Export helper to check if mock data is enabled
export { isMockDataEnabled };

// Export both default and named exports to maintain compatibility
export { apiClient };
export default apiClient; 