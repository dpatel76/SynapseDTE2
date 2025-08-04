import { test, expect } from '@playwright/test';

test('check my-assignments whitespace', async ({ page }) => {
  // Navigate to login
  await page.goto('http://localhost:3000/login');
  
  // Login
  await page.fill('input[name="email"]', 'tester@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  // Wait for dashboard
  await page.waitForURL('**/dashboard');
  
  // Navigate to My Assignments
  await page.goto('http://localhost:3000/my-assignments');
  await page.waitForLoadState('networkidle');
  
  // Take screenshot
  await page.screenshot({ path: 'my-assignments-whitespace.png', fullPage: false });
  
  // Debug: Get main content area info
  const mainContent = await page.locator('main').first();
  const mainBox = await mainContent.boundingBox();
  console.log('Main content box:', mainBox);
  
  // Get the direct child of main
  const contentWrapper = await page.locator('main > *').first();
  const wrapperBox = await contentWrapper.boundingBox();
  console.log('Content wrapper box:', wrapperBox);
  
  // Get computed styles
  const mainStyles = await mainContent.evaluate((el) => {
    const styles = window.getComputedStyle(el);
    return {
      padding: styles.padding,
      paddingLeft: styles.paddingLeft,
      margin: styles.margin,
      marginLeft: styles.marginLeft,
    };
  });
  console.log('Main styles:', mainStyles);
  
  const wrapperStyles = await contentWrapper.evaluate((el) => {
    const styles = window.getComputedStyle(el);
    return {
      padding: styles.padding,
      paddingLeft: styles.paddingLeft,
      margin: styles.margin,
      marginLeft: styles.marginLeft,
      maxWidth: styles.maxWidth,
    };
  });
  console.log('Wrapper styles:', wrapperStyles);
  
  // Check for MuiContainer
  const containers = await page.locator('.MuiContainer-root').count();
  console.log('Container count:', containers);
  
  // Keep browser open for inspection
  await page.waitForTimeout(10000);
});