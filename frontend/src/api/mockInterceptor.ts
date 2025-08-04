import { AxiosError, AxiosResponse } from 'axios';
import {
  mockSampleSelectionStatus,
  mockDataProviderStatus,
  mockRequestInfo,
  mockTestExecutionStatus,
  mockObservations,
  mockSampleSets,
  mockTestCases
} from './mockData';

// Enable mock data with environment variable or localStorage flag
// Also enable if URL contains ?mock=true
const urlParams = new URLSearchParams(window.location.search);
const ENABLE_MOCK_DATA = process.env.REACT_APP_ENABLE_MOCK_DATA === 'true' || 
                        localStorage.getItem('enableMockData') === 'true' ||
                        urlParams.get('mock') === 'true';

// Log mock data status on load
if (ENABLE_MOCK_DATA) {
  console.log('🎭 Mock data is ENABLED');
}

export function handleMockResponse(error: AxiosError): Promise<AxiosResponse> | null {
  if (!ENABLE_MOCK_DATA) return null;
  
  const url = error.config?.url || '';
  const method = error.config?.method || 'get';
  
  // Only mock GET requests that return 403 or 404
  if (method !== 'get' || ![403, 404].includes(error.response?.status || 0)) {
    return null;
  }
  
  // Sample Selection endpoints
  if (url.includes('/sample-selection/') && url.includes('/status')) {
    return Promise.resolve({
      data: mockSampleSelectionStatus,
      status: 200,
      statusText: 'OK (Mock)',
      headers: {},
      config: error.config!
    });
  }
  
  if (url.includes('/sample-selection/') && url.includes('/sample-sets')) {
    return Promise.resolve({
      data: mockSampleSets,
      status: 200,
      statusText: 'OK (Mock)',
      headers: {},
      config: error.config!
    });
  }
  
  // Data Provider endpoints
  if (url.includes('/data-owner/') && url.includes('/status')) {
    return Promise.resolve({
      data: mockDataProviderStatus,
      status: 200,
      statusText: 'OK (Mock)',
      headers: {},
      config: error.config!
    });
  }
  
  // Request Info endpoints
  if (url.includes('/request-info/')) {
    return Promise.resolve({
      data: mockRequestInfo,
      status: 200,
      statusText: 'OK (Mock)',
      headers: {},
      config: error.config!
    });
  }
  
  // Test Execution endpoints
  if (url.includes('/test-execution/') && url.includes('/status')) {
    return Promise.resolve({
      data: mockTestExecutionStatus,
      status: 200,
      statusText: 'OK (Mock)',
      headers: {},
      config: error.config!
    });
  }
  
  if (url.includes('/test-execution/') && url.includes('/test-cases')) {
    return Promise.resolve({
      data: mockTestCases,
      status: 200,
      statusText: 'OK (Mock)',
      headers: {},
      config: error.config!
    });
  }
  
  // Observations endpoints
  if (url.includes('/observation-management/') && url.includes('/observations')) {
    return Promise.resolve({
      data: mockObservations,
      status: 200,
      statusText: 'OK (Mock)',
      headers: {},
      config: error.config!
    });
  }
  
  return null;
}

// Function to toggle mock data
export function toggleMockData(enable: boolean) {
  if (enable) {
    localStorage.setItem('enableMockData', 'true');
    console.log('🎭 Mock data enabled');
  } else {
    localStorage.removeItem('enableMockData');
    console.log('🎭 Mock data disabled');
  }
}

// Check if mock data is enabled
export function isMockDataEnabled(): boolean {
  return ENABLE_MOCK_DATA;
}