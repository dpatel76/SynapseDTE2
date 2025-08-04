import { test, expect, Page } from '@playwright/test';
import { loginAsAdmin, testUsers } from './test-utils';

test.describe('Debug Authentication & API Flow', () => {
  test('trace login and API call sequence', async ({ page }) => {
    // Track all network requests
    const apiCalls: Array<{url: string, method: string, status: number, duration: number, response?: any}> = [];
    let loginStartTime = 0;
    let dashboardLoadTime = 0;
    
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        console.log(`🚀 API Request: ${request.method()} ${request.url()}`);
      }
    });
    
    page.on('response', async response => {
      if (response.url().includes('/api/')) {
        const duration = Date.now() - loginStartTime;
        const call: {url: string, method: string, status: number, duration: number, response?: any} = {
          url: response.url(),
          method: response.request().method(),
          status: response.status(),
          duration: duration
        };
        
        try {
          if (response.headers()['content-type']?.includes('application/json')) {
            call.response = await response.json();
          }
        } catch (e) {
          // Ignore JSON parse errors
        }
        
        apiCalls.push(call);
        console.log(`📡 API Response: ${call.method} ${call.url} - ${call.status} (${duration}ms)`);
        
        if (call.status >= 400) {
          console.log(`❌ API Error: ${JSON.stringify(call.response || {}, null, 2)}`);
        }
      }
    });
    
    console.log('🔐 Starting login flow...');
    loginStartTime = Date.now();
    
    // Go to login page
    await page.goto('/login');
    console.log('📄 Login page loaded');
    
    // Fill credentials with correct test user
    await page.fill('input[name="username"]', testUsers.admin.email);
    await page.fill('input[name="password"]', testUsers.admin.password);
    console.log(`✏️ Credentials filled (${testUsers.admin.email})`);
    
    // Submit login form and wait for navigation
    await page.click('button[type="submit"]');
    console.log('🚀 Login form submitted');
    
    // Wait for successful navigation to dashboard
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
    dashboardLoadTime = Date.now();
    console.log(`✅ Dashboard navigation completed in ${dashboardLoadTime - loginStartTime}ms`);
    
    // Check localStorage for token
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const user = await page.evaluate(() => localStorage.getItem('user'));
    
    console.log('🔑 Auth token present:', !!token);
    console.log('👤 User data present:', !!user);
    
    if (token) {
      console.log('🔑 Token prefix:', token.substring(0, 20) + '...');
    }
    
    if (user) {
      try {
        const userData = JSON.parse(user);
        console.log('👤 User role:', userData.role);
        console.log('👤 User LOB ID:', userData.lob_id);
      } catch (e) {
        console.log('❌ Failed to parse user data');
      }
    }
    
    // Wait a bit for dashboard API calls to complete
    console.log('⏳ Waiting for dashboard API calls...');
    await page.waitForTimeout(5000);
    
    // Check current page content
    const pageContent = await page.textContent('body');
    const hasLoadingText = pageContent?.includes('Loading dashboard');
    const hasFailedText = pageContent?.includes('Failed to load dashboard data');
    const hasWelcomeText = pageContent?.includes('Welcome to SynapseDT');
    
    console.log('📊 Dashboard state:');
    console.log('  - Loading text present:', hasLoadingText);
    console.log('  - Failed text present:', hasFailedText);
    console.log('  - Welcome text present:', hasWelcomeText);
    
    // Test specific API calls manually
    console.log('🧪 Testing API calls with current auth state...');
    
    const testCalls = [
      { name: 'Cycles', endpoint: '/cycles/' },
      { name: 'Reports', endpoint: '/reports/' },
      { name: 'Current User', endpoint: '/auth/me' }
    ];
    
    for (const testCall of testCalls) {
      try {
        const response = await page.evaluate(async (endpoint) => {
          const token = localStorage.getItem('access_token');
          const response = await fetch(`http://localhost:8001/api/v1${endpoint}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });
          
          return {
            status: response.status,
            statusText: response.statusText,
            data: response.ok ? await response.json() : await response.text()
          };
        }, testCall.endpoint);
        
        console.log(`🧪 ${testCall.name} (${testCall.endpoint}):`, response.status, response.statusText);
        if (response.status >= 400) {
          console.log(`   Error data:`, response.data);
        } else {
          console.log(`   Success - Data length:`, JSON.stringify(response.data).length);
        }
        
      } catch (error) {
        console.log(`🧪 ${testCall.name} (${testCall.endpoint}): ERROR -`, error);
      }
    }
    
    // Final summary
    console.log('\n📊 SUMMARY:');
    console.log(`Total API calls: ${apiCalls.length}`);
    console.log('API calls breakdown:');
    
    const callsByStatus = apiCalls.reduce((acc, call) => {
      const status = Math.floor(call.status / 100) * 100;
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {} as Record<number, number>);
    
    Object.entries(callsByStatus).forEach(([status, count]) => {
      console.log(`  ${status}xx: ${count} calls`);
    });
    
    const failedCalls = apiCalls.filter(call => call.status >= 400);
    if (failedCalls.length > 0) {
      console.log('\n❌ Failed API calls:');
      failedCalls.forEach(call => {
        console.log(`  ${call.method} ${call.url} - ${call.status}`);
      });
    }
    
    // The test should pass regardless of API issues since we fixed the dashboard to be resilient
    expect(page.url()).toContain('/dashboard');
  });
}); 