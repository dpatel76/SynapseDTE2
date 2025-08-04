import { test, expect, Page } from '@playwright/test';

test.describe('Authentication', () => {
  test.describe.configure({ mode: 'serial' });

  test('should display login page', async ({ page }) => {
    await page.goto('/login');
    
    // Check page title
    await expect(page).toHaveTitle(/SynapseDT/);
    
    // Check for login form elements
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Check for SynapseDT branding
    await expect(page.locator('text=SynapseDT')).toBeVisible();
    await expect(page.locator('text=Data Testing Platform')).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    await page.goto('/login');
    
    // The button should be disabled when fields are empty
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
    
    // Fill only username, button should still be disabled
    await page.fill('input[name="username"]', 'test@example.com');
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
    
    // Clear username and fill only password, button should still be disabled
    await page.fill('input[name="username"]', '');
    await page.fill('input[name="password"]', 'password123');
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
    
    // Fill both fields, button should be enabled
    await page.fill('input[name="username"]', 'test@example.com');
    await expect(page.locator('button[type="submit"]')).toBeEnabled();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Fill invalid credentials
    await page.fill('input[name="username"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    
    // Wait for the request to complete and error to appear
    await page.waitForLoadState('networkidle');
    
    // Should see error message
    await expect(page.locator('.MuiAlert-root')).toBeVisible();
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Fill valid credentials
    await page.fill('input[name="username"]', 'admin@synapsedt.com');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    // Try to access dashboard without being logged in
    await page.goto('/dashboard');
    
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin@synapsedt.com');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard to load
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Click user menu
    await page.click('[data-testid="user-menu-button"]');
    
    // Click logout
    await page.click('text=Logout');
    
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });
}); 