# E2E Test Improvements Guide

## Summary of Applied Learnings from Auth Tests

Based on the successful resolution of authentication test issues, we've identified and implemented several key improvements that should be applied to all E2E tests.

## ✅ **Key Issues Resolved:**

### 1. **Authentication & Login Consistency**
- **Problem**: Tests used inconsistent selectors (`[data-testid="email-input"]` vs `input[name="username"]`)
- **Solution**: Standardized on `input[name="username"]` and `input[name="password"]` selectors
- **Pattern**: Always use the actual form field names that match the frontend implementation

### 2. **API Client Error Handling**
- **Problem**: Response interceptor was redirecting login failures before error messages could display
- **Solution**: Modified interceptor to skip redirects for `/auth/login` endpoint errors
- **Pattern**: Ensure error handling doesn't interfere with expected error display

### 3. **Dynamic Data Management**
- **Problem**: Tests used hardcoded IDs that didn't exist after database resets
- **Solution**: Created dynamic LOB ID fetching via `/test/get-lobs` endpoint
- **Pattern**: Always fetch current data IDs rather than hardcoding

### 4. **Global Setup/Teardown**
- **Problem**: User creation failed due to hardcoded LOB IDs
- **Solution**: Dynamic LOB ID fetching in global setup
- **Pattern**: Make setup scripts adaptive to changing database state

### 5. **Test Utilities & Code Reuse**
- **Problem**: Duplicate login functions and user definitions across test files
- **Solution**: Created shared `test-utils.ts` with common functions
- **Pattern**: Centralize common test functionality

## 📋 **Implementation Patterns:**

### **Login Pattern:**
```typescript
import { loginAsUser, loginAsAdmin, testUsers } from './test-utils';

// Instead of:
await page.fill('[data-testid="email-input"]', 'user@example.com');

// Use:
await loginAsUser(page, testUsers.tester);
// or
await loginAsAdmin(page);
```

### **Navigation Pattern:**
```typescript
import { navigateAndWait, waitForPageLoad } from './test-utils';

// Instead of:
await page.goto('/dashboard');

// Use:
await navigateAndWait(page, '/dashboard');
// or
await page.goto('/dashboard');
await waitForPageLoad(page);
```

### **Form Filling Pattern:**
```typescript
import { fillField, retry } from './test-utils';

// Instead of:
await page.fill('[data-testid="input"]', 'value');

// Use:
await fillField(page, '[data-testid="input"]', 'value');

// For critical operations:
await retry(async () => {
  await fillField(page, '[data-testid="input"]', 'value');
  await page.click('[data-testid="submit"]');
});
```

### **Error Handling Pattern:**
```typescript
import { checkForErrors, waitForApiRequest } from './test-utils';

// After form submissions:
await waitForPageLoad(page);
const error = await checkForErrors(page);
if (error) {
  console.warn(`Operation error: ${error}`);
}

// For API-dependent operations:
await waitForApiRequest(page, '/api/v1/reports');
```

### **Dynamic Data Pattern:**
```typescript
import { getLOBIds, createTestReport } from './test-utils';

// Instead of hardcoded IDs:
const reportId = '1';

// Use:
const lobIds = await getLOBIds();
const reportId = await createTestReport({
  report_name: 'Test Report',
  lob_id: lobIds.retailbanking
});
```

## 🔧 **Available Utility Functions:**

### **Authentication:**
- `loginAsUser(page, user)` - Login with specific user
- `loginAsAdmin(page)` - Login as admin
- `loginAsTester(page)` - Login as tester

### **Navigation:**
- `navigateAndWait(page, url)` - Navigate and wait for load
- `waitForPageLoad(page, timeout?)` - Wait for page to load completely
- `clickAndWait(page, selector)` - Click and wait for navigation

### **Form Handling:**
- `fillField(page, selector, value)` - Fill form field with error handling
- `elementExists(page, selector)` - Check if element exists

### **Error Handling:**
- `checkForErrors(page)` - Check for error alerts
- `retry(operation, maxAttempts?, delay?)` - Retry flaky operations
- `waitForApiRequest(page, urlPattern, timeout?)` - Wait for API calls

### **Data Management:**
- `getLOBIds()` - Get current LOB IDs from database
- `createTestReport(data)` - Create test report via API

## 🚨 **Common Issues to Avoid:**

### 1. **Hardcoded IDs**
```typescript
// ❌ Don't do this:
await page.goto('/phases/planning?reportId=1');

// ✅ Do this:
const reportId = await createTestReport(testData);
await page.goto(`/phases/planning?reportId=${reportId}`);
```

### 2. **Inconsistent Selectors**
```typescript
// ❌ Don't mix selectors:
await page.fill('[data-testid="email-input"]', email);
await page.fill('input[name="password"]', password);

// ✅ Use consistent selectors:
await page.fill('input[name="username"]', email);
await page.fill('input[name="password"]', password);
```

### 3. **Missing Wait Conditions**
```typescript
// ❌ Don't assume immediate availability:
await page.click('button[type="submit"]');
await expect(page.locator('.success')).toBeVisible();

// ✅ Wait for operations to complete:
await page.click('button[type="submit"]');
await waitForPageLoad(page);
await expect(page.locator('.success')).toBeVisible();
```

### 4. **No Error Handling**
```typescript
// ❌ Don't ignore potential errors:
await page.click('[data-testid="submit"]');

// ✅ Handle errors gracefully:
await retry(async () => {
  await page.click('[data-testid="submit"]');
});
const error = await checkForErrors(page);
if (error) {
  console.warn(`Submit error: ${error}`);
}
```

## 📊 **Test Status After Improvements:**

### ✅ **Fixed Tests:**
- **auth.spec.ts**: All 6 tests passing
- **dashboard.spec.ts**: Improved with better wait conditions and error handling
- **role-based-testing.spec.ts**: Updated to use shared utilities

### 🔄 **Tests Needing Updates:**
- **llm-integration.spec.ts**: Needs selector consistency fixes
- **complete-workflow.spec.ts**: Needs dynamic data management
- **performance.spec.ts**: Needs error handling improvements
- **accessibility.spec.ts**: Needs wait condition improvements

## 🎯 **Next Steps:**

1. **Update remaining test files** to use the new utility functions
2. **Fix selector inconsistencies** across all tests
3. **Implement dynamic data management** for all hardcoded IDs
4. **Add proper error handling** to all critical operations
5. **Test the complete test suite** to ensure all improvements work

## 📝 **Example Migration:**

### Before:
```typescript
test('should create report', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[data-testid="email-input"]', 'tester@example.com');
  await page.fill('[data-testid="password-input"]', 'Tester123!');
  await page.click('[data-testid="login-button"]');
  
  await page.goto('/reports');
  await page.click('[data-testid="create-report"]');
  await page.fill('[data-testid="report-name"]', 'Test Report');
  await page.selectOption('[data-testid="lob-select"]', '1');
  await page.click('[data-testid="save-button"]');
  
  await expect(page.locator('text=Test Report')).toBeVisible();
});
```

### After:
```typescript
import { loginAsTester, navigateAndWait, fillField, retry, getLOBIds, checkForErrors } from './test-utils';

test('should create report', async ({ page }) => {
  await loginAsTester(page);
  
  await navigateAndWait(page, '/reports');
  
  const lobIds = await getLOBIds();
  
  await retry(async () => {
    await page.click('[data-testid="create-report"]');
    await fillField(page, '[data-testid="report-name"]', 'Test Report');
    await page.selectOption('[data-testid="lob-select"]', lobIds.retailbanking.toString());
    await page.click('[data-testid="save-button"]');
  });
  
  await waitForPageLoad(page);
  const error = await checkForErrors(page);
  if (error) {
    console.warn(`Report creation error: ${error}`);
  }
  
  await expect(page.locator('text=Test Report')).toBeVisible();
});
```

This migration shows how the improvements make tests more robust, maintainable, and less prone to flaky failures. 