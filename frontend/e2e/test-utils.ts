import { Page, expect } from '@playwright/test';

export interface TestUser {
  email: string;
  password: string;
  role: string;
  name: string;
}

// Test users that match the global setup
export const testUsers: Record<string, TestUser> = {
  admin: {
    email: 'admin@synapsedt.com',
    password: 'admin123',
    role: 'Test Manager',
    name: 'Admin User'
  },
  testManager: {
    email: 'test.manager@example.com',
    password: 'TestManager123!',
    role: 'Test Manager',
    name: 'Test Manager'
  },
  tester: {
    email: 'tester@example.com', 
    password: 'Tester123!',
    role: 'Tester',
    name: 'Jane Doe'
  },
  reportOwner: {
    email: 'report.owner@example.com',
    password: 'ReportOwner123!',
    role: 'Report Owner',
    name: 'Mike Johnson'
  },
  reportOwnerExecutive: {
    email: 'report.exec@example.com',
    password: 'ReportExec123!',
    role: 'Report Owner Executive', 
    name: 'Sarah Wilson'
  },
  cdo: {
    email: 'cdo@example.com',
    password: 'CDO123!',
    role: 'CDO',
    name: 'David Brown'
  },
  dataProvider: {
    email: 'data.provider@example.com',
    password: 'DataProvider123!',
    role: 'Data Provider',
    name: 'Lisa Chen'
  }
};

/**
 * Login as a specific user using consistent selectors
 */
export async function loginAsUser(page: Page, user: TestUser) {
  await page.goto('/login');
  
  // Use consistent selectors from auth tests
  await page.fill('input[name="username"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.click('button[type="submit"]');
  
  // Wait for navigation to complete
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveURL(/\/dashboard/);
}

/**
 * Login as admin user (shortcut for most common case)
 */
export async function loginAsAdmin(page: Page) {
  await loginAsUser(page, testUsers.admin);
}

/**
 * Login as tester user (common for workflow tests)
 */
export async function loginAsTester(page: Page) {
  await loginAsUser(page, testUsers.tester);
}

/**
 * Wait for page to load completely with error handling
 */
export async function waitForPageLoad(page: Page, timeout: number = 10000) {
  try {
    await page.waitForLoadState('networkidle', { timeout });
  } catch (error) {
    console.warn('Page load timeout, continuing with test');
  }
}

/**
 * Navigate to a page and wait for it to load
 */
export async function navigateAndWait(page: Page, url: string) {
  await page.goto(url);
  await waitForPageLoad(page);
}

/**
 * Click an element and wait for navigation
 */
export async function clickAndWait(page: Page, selector: string) {
  await page.click(selector);
  await waitForPageLoad(page);
}

/**
 * Fill form field with error handling
 */
export async function fillField(page: Page, selector: string, value: string) {
  try {
    await page.fill(selector, value);
  } catch (error) {
    console.warn(`Failed to fill field ${selector}: ${error}`);
    throw error;
  }
}

/**
 * Check if element exists without throwing error
 */
export async function elementExists(page: Page, selector: string): Promise<boolean> {
  try {
    await page.locator(selector).waitFor({ timeout: 2000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Wait for API request to complete
 */
export async function waitForApiRequest(page: Page, urlPattern: string, timeout: number = 10000) {
  try {
    await page.waitForResponse(response => 
      response.url().includes(urlPattern) && response.status() < 400,
      { timeout }
    );
  } catch (error) {
    console.warn(`API request timeout for ${urlPattern}`);
  }
}

/**
 * Handle potential error alerts
 */
export async function checkForErrors(page: Page) {
  const errorAlert = page.locator('.MuiAlert-root[severity="error"]');
  if (await errorAlert.isVisible()) {
    const errorText = await errorAlert.textContent();
    console.warn(`Error alert found: ${errorText}`);
    return errorText;
  }
  return null;
}

/**
 * Get dynamic LOB IDs from the API
 */
export async function getLOBIds(): Promise<Record<string, number>> {
  try {
    const response = await fetch('http://localhost:8001/api/v1/test/get-lobs');
    if (response.ok) {
      const lobs = await response.json();
      const lobMap: Record<string, number> = {};
      
      for (const lob of lobs) {
        const key = lob.lob_name.toLowerCase().replace(/\s+/g, '');
        lobMap[key] = lob.lob_id;
      }
      
      return lobMap;
    }
  } catch (error) {
    console.warn('Failed to fetch LOB IDs:', error);
  }
  
  // Return fallback IDs
  return {
    retailbanking: 1,
    commercialbanking: 2,
    investmentbanking: 3
  };
}

/**
 * Create test data via API
 */
export async function createTestReport(reportData: any): Promise<string | null> {
  try {
    const response = await fetch('http://localhost:8001/api/v1/test/create-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reportData)
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.report_id || '1';
    }
  } catch (error) {
    console.warn('Failed to create test report:', error);
  }
  
  return null;
}

/**
 * Retry function for flaky operations
 */
export async function retry<T>(
  operation: () => Promise<T>,
  maxAttempts: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      console.warn(`Attempt ${attempt} failed: ${error}`);
      
      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError!;
} 