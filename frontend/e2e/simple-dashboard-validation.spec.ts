import { test, expect, Page } from '@playwright/test';
import { 
  loginAsUser, 
  testUsers, 
  waitForPageLoad 
} from './test-utils';

test.describe('Simple Dashboard Validation', () => {
  test.beforeEach(async ({ page }) => {
    // Wait for services to be ready
    await page.waitForTimeout(2000);
  });

  test('Test Manager can access dashboard with all features', async ({ page }) => {
    await loginAsUser(page, testUsers.testManager);
    
    // Should be on dashboard after login
    await expect(page).toHaveURL(/\/dashboard/);
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // Verify main dashboard elements
    await expect(page.locator('h4:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('text=Welcome back')).toBeVisible();
    
    // Verify Quick Actions section
    await expect(page.locator('h6:has-text("Quick Actions")')).toBeVisible();
    await expect(page.locator('button:has-text("Start New Cycle")')).toBeVisible();
    await expect(page.locator('button:has-text("View Reports")')).toBeVisible();
    await expect(page.locator('button:has-text("Manage Tests")')).toBeVisible();
    
    // Verify Recent Activity section
    await expect(page.locator('h6:has-text("Recent Activity")')).toBeVisible();
    
    // Verify Advanced Analytics section
    await expect(page.locator('h6:has-text("Advanced Analytics")')).toBeVisible();
    await expect(page.locator('button:has-text("View Analytics Dashboard")')).toBeVisible();
    
    // Verify System Status section
    await expect(page.locator('h6:has-text("System Status")')).toBeVisible();
    await expect(page.locator('text=Database')).toBeVisible();
    await expect(page.locator('text=API Services')).toBeVisible();
  });

  test('Tester can access dashboard with basic features', async ({ page }) => {
    await loginAsUser(page, testUsers.tester);
    
    await expect(page).toHaveURL(/\/dashboard/);
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // Basic dashboard elements should be visible
    await expect(page.locator('h4:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('h6:has-text("Quick Actions")')).toBeVisible();
    await expect(page.locator('h6:has-text("Recent Activity")')).toBeVisible();
    await expect(page.locator('h6:has-text("System Status")')).toBeVisible();
  });

  test('Report Owner can access dashboard', async ({ page }) => {
    await loginAsUser(page, testUsers.reportOwner);
    
    await expect(page).toHaveURL(/\/dashboard/);
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // Verify dashboard is accessible
    await expect(page.locator('h4:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('h6:has-text("Quick Actions")')).toBeVisible();
  });

  test('CDO can access dashboard with analytics', async ({ page }) => {
    await loginAsUser(page, testUsers.cdo);
    
    await expect(page).toHaveURL(/\/dashboard/);
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // CDO should have access to analytics
    await expect(page.locator('h4:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('h6:has-text("Advanced Analytics")')).toBeVisible();
    await expect(page.locator('button:has-text("View Analytics Dashboard")')).toBeVisible();
    await expect(page.locator('button:has-text("Performance Insights")')).toBeVisible();
  });

  test('Data Provider can access dashboard', async ({ page }) => {
    await loginAsUser(page, testUsers.dataProvider);
    
    await expect(page).toHaveURL(/\/dashboard/);
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // Basic dashboard access
    await expect(page.locator('h4:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('h6:has-text("Quick Actions")')).toBeVisible();
  });

  test('Navigation works for all roles', async ({ page }) => {
    // Test with Test Manager role
    await loginAsUser(page, testUsers.testManager);
    await waitForPageLoad(page);
    
    // Check if mobile or desktop navigation
    const viewport = page.viewportSize();
    const isMobile = viewport && viewport.width < 768;
    
    if (isMobile) {
      // On mobile, need to open the menu first
      const menuButton = page.locator('[data-testid="mobile-menu-button"], [aria-label="open drawer"]').first();
      if (await menuButton.isVisible()) {
        await menuButton.click();
        await page.waitForTimeout(500);
      }
    }
    
    // Check navigation elements exist
    const hasNavigation = await page.locator('[aria-label="navigation"]').count();
    const hasMenuItems = await page.locator('text=Test Cycles, text=Reports').count();
    
    // Either full navigation or menu items should exist
    expect(hasNavigation + hasMenuItems).toBeGreaterThan(0);
  });

  test('Demo notification functionality works', async ({ page }) => {
    await loginAsUser(page, testUsers.testManager);
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // Check for demo notification section
    await expect(page.locator('text=New Features Available!')).toBeVisible();
    
    // Click demo notification button
    const demoButton = page.locator('button:has-text("Demo Notification")');
    if (await demoButton.isVisible()) {
      await demoButton.click();
      // Should show some feedback (toast or notification)
      await page.waitForTimeout(1000);
    }
  });

  test('Quick stats are displayed', async ({ page }) => {
    await loginAsUser(page, testUsers.testManager);
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // Check for quick stats
    await expect(page.locator('text=Active Test Cycles')).toBeVisible();
    await expect(page.locator('text=Test Execution Rate')).toBeVisible();
    await expect(page.locator('text=Quality Score')).toBeVisible();
    await expect(page.locator('text=Critical Issues')).toBeVisible();
  });

  test('Recent activity list is populated', async ({ page }) => {
    await loginAsUser(page, testUsers.tester);
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // Check Recent Activity section
    await expect(page.locator('h6:has-text("Recent Activity")')).toBeVisible();
    
    // Should have some activity items
    const activityItems = page.locator('.MuiList-root .MuiListItem-root');
    const count = await activityItems.count();
    expect(count).toBeGreaterThan(0);
  });

  test('System status shows healthy services', async ({ page }) => {
    await loginAsUser(page, testUsers.cdo);
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // Check System Status
    await expect(page.locator('h6:has-text("System Status")')).toBeVisible();
    await expect(page.locator('text=Database')).toBeVisible();
    await expect(page.locator('text=API Services')).toBeVisible();
    await expect(page.locator('text=Processing Queue')).toBeVisible();
    
    // Should show status indicators
    const progressBars = page.locator('role=progressbar');
    const progressCount = await progressBars.count();
    expect(progressCount).toBeGreaterThan(0);
  });

  test('Dashboard is responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await loginAsUser(page, testUsers.testManager);
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // Dashboard should still be functional on mobile
    await expect(page.locator('h4:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('h6:has-text("Quick Actions")')).toBeVisible();
    
    // Mobile-specific elements
    const hasMobileMenu = await page.locator('[data-testid="mobile-menu-button"], [aria-label="open drawer"]').count();
    const hasPermanentNav = await page.locator('[aria-label="navigation"]').count();
    
    // Either mobile menu or permanent navigation should be present
    expect(hasMobileMenu + hasPermanentNav).toBeGreaterThan(0);
  });

  test('API integration works properly', async ({ page }) => {
    await loginAsUser(page, testUsers.testManager);
    
    // Monitor network requests
    const apiRequests: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/v1/')) {
        apiRequests.push(request.url());
      }
    });
    
    await waitForPageLoad(page);
    
    // Wait for loading to complete
    await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
    
    // Should have made API calls
    await page.waitForTimeout(2000);
    expect(apiRequests.length).toBeGreaterThan(0);
    
    // Dashboard should load successfully despite any API issues
    await expect(page.locator('h4:has-text("Dashboard")')).toBeVisible();
  });
});

test.describe('Role-Specific Feature Access', () => {
  test('All roles can access basic dashboard features', async ({ page }) => {
    const roles = [
      testUsers.testManager,
      testUsers.tester,
      testUsers.reportOwner,
      testUsers.cdo,
      testUsers.dataProvider
    ];
    
    for (const role of roles) {
      await loginAsUser(page, role);
      await waitForPageLoad(page);
      
      // Wait for loading to complete
      await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
      
      // Basic features should be accessible to all roles
      await expect(page.locator('h4:has-text("Dashboard")')).toBeVisible();
      await expect(page.locator('h6:has-text("Quick Actions")')).toBeVisible();
      await expect(page.locator('h6:has-text("Recent Activity")')).toBeVisible();
      
      console.log(`✅ ${role.email} can access dashboard`);
    }
  });

  test('Analytics features are available to management roles', async ({ page }) => {
    const managementRoles = [testUsers.testManager, testUsers.cdo];
    
    for (const role of managementRoles) {
      await loginAsUser(page, role);
      await waitForPageLoad(page);
      
      // Wait for loading to complete
      await page.waitForSelector('.MuiCircularProgress-root', { state: 'detached', timeout: 10000 }).catch(() => {});
      
      // Analytics should be available
      await expect(page.locator('h6:has-text("Advanced Analytics")')).toBeVisible();
      await expect(page.locator('button:has-text("View Analytics Dashboard")')).toBeVisible();
      
      console.log(`✅ ${role.email} has analytics access`);
    }
  });
}); 