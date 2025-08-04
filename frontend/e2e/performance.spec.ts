import { test, expect } from '@playwright/test';
import { 
  loginAsAdmin, 
  loginAsTester, 
  testUsers, 
  waitForPageLoad, 
  navigateAndWait,
  checkForErrors,
  retry,
  waitForApiRequest
} from './test-utils';

test.describe('Performance Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Set up performance monitoring
    await page.addInitScript(() => {
      window.performance.mark('test-start');
    });
  });

  test('Dashboard loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    
    await loginAsAdmin(page);
    
    // Wait for dashboard to fully load
    await waitForPageLoad(page);
    
    const loadTime = Date.now() - startTime;
    console.log(`Dashboard load time: ${loadTime}ms`);
    
    // Dashboard should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
    
    // Check for performance metrics
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
      };
    });
    
    console.log('Performance metrics:', performanceMetrics);
    
    // Verify key elements are visible
    await expect(page.locator('h4')).toBeVisible();
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
  });

  test('Large data table renders efficiently', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Navigate to a page with large data tables
    await navigateAndWait(page, '/reports');
    
    // Wait for table to load
    await waitForApiRequest(page, '/api/v1/reports', 10000);
    
    const startTime = Date.now();
    
    // Trigger table rendering with large dataset
    await retry(async () => {
      await page.selectOption('[data-testid="page-size-select"]', '100');
    });
    
    // Wait for table to re-render
    await waitForPageLoad(page);
    
    const renderTime = Date.now() - startTime;
    console.log(`Large table render time: ${renderTime}ms`);
    
    // Table should render within 3 seconds
    expect(renderTime).toBeLessThan(3000);
    
    // Verify table is functional
    await expect(page.locator('[data-testid="data-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="table-row"]').first()).toBeVisible();
    
    // Check for errors
    const error = await checkForErrors(page);
    expect(error).toBeNull();
  });

  test('Form submission performance', async ({ page }) => {
    await loginAsTester(page);
    
    await navigateAndWait(page, '/phases/planning?reportId=1');
    
    const startTime = Date.now();
    
    // Fill out a complex form
    await retry(async () => {
      await page.click('[data-testid="add-attribute-button"]');
      await page.fill('[data-testid="attr-name-input"]', 'performance_test_attribute');
      await page.fill('[data-testid="attr-description-input"]', 'This is a test attribute for performance testing');
      await page.selectOption('[data-testid="attr-type-select"]', 'String');
      await page.selectOption('[data-testid="attr-flag-select"]', 'Mandatory');
      await page.click('[data-testid="save-attribute-button"]');
    });
    
    // Wait for form submission to complete
    await waitForApiRequest(page, '/api/v1/attributes', 5000);
    await waitForPageLoad(page);
    
    const submissionTime = Date.now() - startTime;
    console.log(`Form submission time: ${submissionTime}ms`);
    
    // Form submission should complete within 2 seconds
    expect(submissionTime).toBeLessThan(2000);
    
    // Verify submission was successful
    await expect(page.locator('[data-testid="attribute-performance_test_attribute"]')).toBeVisible();
    
    // Check for errors
    const error = await checkForErrors(page);
    expect(error).toBeNull();
  });

  test('Navigation performance between pages', async ({ page }) => {
    await loginAsAdmin(page);
    
    const navigationTimes: number[] = [];
    const pages = [
      '/dashboard',
      '/cycles',
      '/reports',
      '/users',
      '/phases/planning',
      '/phases/scoping'
    ];
    
    for (const targetPage of pages) {
      const startTime = Date.now();
      
      await navigateAndWait(page, targetPage);
      
      const navigationTime = Date.now() - startTime;
      navigationTimes.push(navigationTime);
      
      console.log(`Navigation to ${targetPage}: ${navigationTime}ms`);
      
      // Each navigation should complete within 3 seconds
      expect(navigationTime).toBeLessThan(3000);
      
      // Verify page loaded correctly
      await expect(page.locator('main')).toBeVisible();
      
      // Check for errors
      const error = await checkForErrors(page);
      expect(error).toBeNull();
    }
    
    const averageNavigationTime = navigationTimes.reduce((a, b) => a + b, 0) / navigationTimes.length;
    console.log(`Average navigation time: ${averageNavigationTime}ms`);
    
    // Average navigation time should be reasonable
    expect(averageNavigationTime).toBeLessThan(2000);
  });

  test('API response times', async ({ page }) => {
    await loginAsAdmin(page);
    
    const apiEndpoints = [
      '/api/v1/reports',
      '/api/v1/cycles',
      '/api/v1/users',
      '/api/v1/lobs'
    ];
    
    for (const endpoint of apiEndpoints) {
      const startTime = Date.now();
      
      // Make API request and wait for response
      const response = await page.request.get(`http://localhost:8001${endpoint}`);
      
      const responseTime = Date.now() - startTime;
      console.log(`API ${endpoint} response time: ${responseTime}ms`);
      
      // API should respond within 1 second
      expect(responseTime).toBeLessThan(1000);
      
      // Verify response is successful
      expect(response.status()).toBeLessThan(400);
    }
  });

  test('Memory usage during extended session', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Get initial memory usage
    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory ? {
        usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        totalJSHeapSize: (performance as any).memory.totalJSHeapSize
      } : null;
    });
    
    if (!initialMemory) {
      console.log('Memory API not available, skipping memory test');
      return;
    }
    
    console.log('Initial memory usage:', initialMemory);
    
    // Perform various operations to simulate extended session
    const operations = [
      () => navigateAndWait(page, '/dashboard'),
      () => navigateAndWait(page, '/reports'),
      () => navigateAndWait(page, '/cycles'),
      () => navigateAndWait(page, '/users'),
      () => page.reload(),
      () => navigateAndWait(page, '/phases/planning?reportId=1'),
      () => navigateAndWait(page, '/phases/scoping?reportId=1')
    ];
    
    for (const operation of operations) {
      await operation();
      await waitForPageLoad(page);
      
      // Small delay between operations
      await page.waitForTimeout(500);
    }
    
    // Get final memory usage
    const finalMemory = await page.evaluate(() => {
      return {
        usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        totalJSHeapSize: (performance as any).memory.totalJSHeapSize
      };
    });
    
    console.log('Final memory usage:', finalMemory);
    
    const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
    const memoryIncreasePercent = (memoryIncrease / initialMemory.usedJSHeapSize) * 100;
    
    console.log(`Memory increase: ${memoryIncrease} bytes (${memoryIncreasePercent.toFixed(2)}%)`);
    
    // Memory increase should be reasonable (less than 50% increase)
    expect(memoryIncreasePercent).toBeLessThan(50);
  });

  test('Concurrent user simulation', async ({ browser }) => {
    const contexts = await Promise.all([
      browser.newContext(),
      browser.newContext(),
      browser.newContext()
    ]);
    
    const pages = await Promise.all(contexts.map(context => context.newPage()));
    
    const startTime = Date.now();
    
    // Simulate concurrent users
    await Promise.all([
      (async () => {
        await loginAsAdmin(pages[0]);
        await navigateAndWait(pages[0], '/dashboard');
        await navigateAndWait(pages[0], '/reports');
      })(),
      (async () => {
        await loginAsTester(pages[1]);
        await navigateAndWait(pages[1], '/dashboard');
        await navigateAndWait(pages[1], '/phases/planning?reportId=1');
      })(),
      (async () => {
        await loginAsAdmin(pages[2]);
        await navigateAndWait(pages[2], '/cycles');
        await navigateAndWait(pages[2], '/users');
      })()
    ]);
    
    const concurrentTime = Date.now() - startTime;
    console.log(`Concurrent operations completed in: ${concurrentTime}ms`);
    
    // Concurrent operations should complete within reasonable time
    expect(concurrentTime).toBeLessThan(10000);
    
    // Verify all pages are functional
    for (const page of pages) {
      await expect(page.locator('main')).toBeVisible();
      const error = await checkForErrors(page);
      expect(error).toBeNull();
    }
    
    // Clean up
    await Promise.all(contexts.map(context => context.close()));
  });

  test('Large file upload performance', async ({ page }) => {
    await loginAsTester(page);
    
    await navigateAndWait(page, '/phases/planning?reportId=1');
    
    const startTime = Date.now();
    
    // Simulate large file upload
    await retry(async () => {
      await page.click('[data-testid="upload-regulatory-spec-button"]');
      const fileInput = page.locator('[data-testid="regulatory-spec-input"]');
      
      // Create a mock large file (this would be a real file in actual testing)
      await fileInput.setInputFiles({
        name: 'large-regulatory-spec.pdf',
        mimeType: 'application/pdf',
        buffer: new Uint8Array(1024 * 1024) // 1MB mock file
      });
      
      await page.click('[data-testid="upload-file-button"]');
    });
    
    // Wait for upload to complete
    await waitForApiRequest(page, '/api/v1/documents/upload', 15000);
    await waitForPageLoad(page);
    
    const uploadTime = Date.now() - startTime;
    console.log(`Large file upload time: ${uploadTime}ms`);
    
    // Upload should complete within 10 seconds
    expect(uploadTime).toBeLessThan(10000);
    
    // Verify upload was successful
    await expect(page.locator('[data-testid="upload-success"]')).toBeVisible();
    
    // Check for errors
    const error = await checkForErrors(page);
    expect(error).toBeNull();
  });
}); 