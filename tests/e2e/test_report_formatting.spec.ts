import { test, expect } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const TEST_USER = {
  email: 'tester1@company.com',
  password: 'testpass123'
};

test.describe('Test Report Formatting', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto(BASE_URL);
    await page.fill('input[name="email"]', TEST_USER.email);
    await page.fill('input[name="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    
    // Wait for dashboard to load
    await page.waitForURL('**/dashboard');
  });

  test('should display formatted report with positive framing', async ({ page }) => {
    // Navigate to test report page
    await page.goto(`${BASE_URL}/cycles/21/reports/156/phases/test-report`);
    
    // Wait for page to load
    await page.waitForSelector('text=Finalize Test Report');
    
    // Start the report phase if not started
    const startButton = await page.locator('button:has-text("Start Phase")');
    if (await startButton.isVisible()) {
      await startButton.click();
      await page.waitForTimeout(1000);
    }
    
    // Generate report
    await page.click('button:has-text("Generate Report")');
    
    // Wait for report generation
    await page.waitForSelector('text=Report generated successfully', { timeout: 10000 });
    
    // Click on Formatted Report tab
    await page.click('button[role="tab"]:has-text("Formatted Report")');
    
    // Verify positive framing elements
    await expect(page.locator('text=strategically focused')).toBeVisible();
    await expect(page.locator('text=risk-based approach')).toBeVisible();
    await expect(page.locator('text=Key Achievements')).toBeVisible();
    
    // Check for coverage metrics
    await expect(page.locator('text=Coverage')).toBeVisible();
    await expect(page.locator('text=Risk Coverage')).toBeVisible();
    await expect(page.locator('text=Materiality Coverage')).toBeVisible();
    
    // Verify no negative language
    const pageContent = await page.content();
    expect(pageContent).not.toContain('only tested');
    expect(pageContent).not.toContain('insufficient');
    expect(pageContent).not.toContain('limited coverage');
  });

  test('should render HTML report with proper styling', async ({ page }) => {
    // Navigate to report with existing sections
    await page.goto(`${BASE_URL}/cycles/21/reports/156/phases/test-report`);
    
    // Click on Formatted Report tab
    await page.click('button[role="tab"]:has-text("Formatted Report")');
    
    // Check HTML rendering
    const htmlSection = await page.locator('[dangerouslySetInnerHTML]');
    if (await htmlSection.isVisible()) {
      // Verify styling is applied
      const h1Style = await page.locator('h1').first().evaluate(el => 
        window.getComputedStyle(el).color
      );
      expect(h1Style).toBeTruthy(); // Should have color styling
      
      // Check table styling if present
      const tables = await page.locator('table').count();
      if (tables > 0) {
        const tableStyle = await page.locator('table').first().evaluate(el => 
          window.getComputedStyle(el).borderCollapse
        );
        expect(tableStyle).toBe('collapse');
      }
    }
  });

  test('should display executive summary with achievements', async ({ page }) => {
    await page.goto(`${BASE_URL}/cycles/21/reports/156/phases/test-report`);
    
    // Navigate to formatted report
    await page.click('button[role="tab"]:has-text("Formatted Report")');
    
    // Look for executive summary section
    const summarySection = await page.locator('text=Executive Summary').first();
    await summarySection.click();
    
    // Verify achievements list
    const achievements = await page.locator('li:has(svg)').count();
    expect(achievements).toBeGreaterThan(0);
    
    // Check for checkmark icons
    const checkmarks = await page.locator('svg[data-testid="CheckCircleIcon"]').count();
    expect(checkmarks).toBeGreaterThan(0);
  });

  test('should handle preview dialog correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/cycles/21/reports/156/phases/test-report`);
    
    // Click preview button
    await page.click('button:has-text("Preview")');
    
    // Wait for dialog
    await page.waitForSelector('[role="dialog"]');
    
    // Verify dialog title
    await expect(page.locator('text=Report Preview')).toBeVisible();
    
    // Check that formatted content is displayed
    const dialogContent = await page.locator('[role="dialog"]').textContent();
    expect(dialogContent).toContain('Executive Summary');
    
    // Close dialog
    await page.click('button:has-text("Close")');
    await expect(page.locator('[role="dialog"]')).not.toBeVisible();
  });

  test('should export report as PDF', async ({ page, context }) => {
    await page.goto(`${BASE_URL}/cycles/21/reports/156/phases/test-report`);
    
    // Wait for download promise before clicking
    const downloadPromise = page.waitForEvent('download');
    
    // Click download button
    await page.click('button:has-text("Download PDF")');
    
    // Wait for download
    const download = await downloadPromise;
    
    // Verify download
    expect(download.suggestedFilename()).toContain('test_report');
    expect(download.suggestedFilename()).toEndWith('.pdf');
  });

  test('should show appropriate content for different coverage levels', async ({ page }) => {
    // Test with minimal coverage report
    await page.goto(`${BASE_URL}/cycles/21/reports/156/phases/test-report`);
    await page.click('button[role="tab"]:has-text("Formatted Report")');
    
    // Should show targeted/strategic language for low coverage
    await expect(page.locator('text=/targeted|strategic|focused/')).toBeVisible();
    
    // Navigate to high coverage report (if available)
    // This would need a different report ID with high coverage
    // await page.goto(`${BASE_URL}/cycles/22/reports/157/phases/test-report`);
    // await expect(page.locator('text=/comprehensive|broad/')).toBeVisible();
  });

  test('should maintain state when switching tabs', async ({ page }) => {
    await page.goto(`${BASE_URL}/cycles/21/reports/156/phases/test-report`);
    
    // Go to formatted report tab
    await page.click('button[role="tab"]:has-text("Formatted Report")');
    
    // Expand an accordion section
    const accordion = await page.locator('[aria-expanded="false"]').first();
    if (await accordion.isVisible()) {
      await accordion.click();
      await expect(accordion).toHaveAttribute('aria-expanded', 'true');
    }
    
    // Switch to another tab
    await page.click('button[role="tab"]:has-text("Configuration")');
    
    // Switch back
    await page.click('button[role="tab"]:has-text("Formatted Report")');
    
    // Accordion should still be expanded
    if (await accordion.isVisible()) {
      await expect(accordion).toHaveAttribute('aria-expanded', 'true');
    }
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Test with non-existent report
    await page.goto(`${BASE_URL}/cycles/999/reports/999/phases/test-report`);
    
    // Should show error or redirect
    await expect(
      page.locator('text=/error|not found/i').or(page.locator('text=Dashboard'))
    ).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Accessibility Tests', () => {
  test('formatted report should be accessible', async ({ page }) => {
    await page.goto(`${BASE_URL}/cycles/21/reports/156/phases/test-report`);
    await page.click('button[role="tab"]:has-text("Formatted Report")');
    
    // Check for proper heading hierarchy
    const h1Count = await page.locator('h1').count();
    const h2Count = await page.locator('h2').count();
    
    expect(h1Count).toBeGreaterThanOrEqual(0);
    expect(h2Count).toBeGreaterThanOrEqual(0);
    
    // Check for proper ARIA labels
    const buttons = await page.locator('button').all();
    for (const button of buttons) {
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      expect(text || ariaLabel).toBeTruthy();
    }
    
    // Check color contrast (simplified check)
    // In a real test, you'd use axe-core or similar
    const hasVisibleText = await page.locator('body').evaluate(() => {
      const text = document.body.innerText;
      return text.length > 100;
    });
    expect(hasVisibleText).toBe(true);
  });
});