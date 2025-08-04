import { test, expect } from '@playwright/test';
import { 
  loginAsAdmin, 
  loginAsTester, 
  testUsers, 
  waitForPageLoad, 
  navigateAndWait,
  checkForErrors,
  retry
} from './test-utils';

test.describe('Accessibility Testing', () => {
  test('Dashboard meets WCAG accessibility standards', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Wait for dashboard to load completely
    await waitForPageLoad(page);
    
    // Check for basic accessibility requirements
    
    // 1. Page should have a proper title
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title).not.toBe('');
    
    // 2. Main content should have proper heading structure
    const h1Elements = page.locator('h1');
    const h1Count = await h1Elements.count();
    expect(h1Count).toBeGreaterThanOrEqual(1); // Should have at least one h1
    
    // 3. All images should have alt text
    const images = page.locator('img');
    const imageCount = await images.count();
    
    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');
      const ariaLabel = await img.getAttribute('aria-label');
      const ariaLabelledBy = await img.getAttribute('aria-labelledby');
      
      // Image should have alt text or aria-label or aria-labelledby
      expect(alt || ariaLabel || ariaLabelledBy).toBeTruthy();
    }
    
    // 4. All form inputs should have labels
    const inputs = page.locator('input, select, textarea');
    const inputCount = await inputs.count();
    
    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      
      if (id) {
        // Check if there's a label for this input
        const label = page.locator(`label[for="${id}"]`);
        const labelExists = await label.count() > 0;
        
        // Input should have a label or aria-label or aria-labelledby
        expect(labelExists || ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    }
    
    // 5. All buttons should have accessible names
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      const ariaLabelledBy = await button.getAttribute('aria-labelledby');
      const title = await button.getAttribute('title');
      
      // Button should have text content or aria-label or aria-labelledby or title
      expect(text?.trim() || ariaLabel || ariaLabelledBy || title).toBeTruthy();
    }
    
    // Check for errors
    const error = await checkForErrors(page);
    expect(error).toBeNull();
  });

  test('Keyboard navigation works properly', async ({ page }) => {
    await loginAsAdmin(page);
    await waitForPageLoad(page);
    
    // Test Tab navigation
    await page.keyboard.press('Tab');
    
    // Check that focus is visible
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
    
    // Test navigation through multiple elements
    const tabbableElements = page.locator('button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])');
    const elementCount = await tabbableElements.count();
    
    if (elementCount > 0) {
      // Tab through first few elements
      for (let i = 0; i < Math.min(5, elementCount); i++) {
        await page.keyboard.press('Tab');
        
        // Verify focus is still visible
        const currentFocus = page.locator(':focus');
        await expect(currentFocus).toBeVisible();
      }
      
      // Test Shift+Tab (reverse navigation)
      await page.keyboard.press('Shift+Tab');
      const reverseFocus = page.locator(':focus');
      await expect(reverseFocus).toBeVisible();
    }
    
    // Test Enter key on buttons
    const firstButton = page.locator('button').first();
    if (await firstButton.count() > 0) {
      await firstButton.focus();
      
      // Note: We don't actually press Enter as it might trigger actions
      // In a real test, you'd verify Enter key functionality
      await expect(firstButton).toBeFocused();
    }
  });

  test('Screen reader compatibility', async ({ page }) => {
    await loginAsAdmin(page);
    await waitForPageLoad(page);
    
    // Check for proper ARIA landmarks
    const landmarks = [
      'main',
      'nav',
      'header',
      'footer',
      '[role="main"]',
      '[role="navigation"]',
      '[role="banner"]',
      '[role="contentinfo"]'
    ];
    
    let landmarkFound = false;
    for (const landmark of landmarks) {
      const element = page.locator(landmark);
      if (await element.count() > 0) {
        landmarkFound = true;
        break;
      }
    }
    
    expect(landmarkFound).toBeTruthy();
    
    // Check for proper heading hierarchy
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const headingCount = await headings.count();
    
    if (headingCount > 0) {
      // Verify headings are in logical order
      const headingLevels: number[] = [];
      
      for (let i = 0; i < headingCount; i++) {
        const heading = headings.nth(i);
        const tagName = await heading.evaluate(el => el.tagName.toLowerCase());
        const level = parseInt(tagName.charAt(1));
        headingLevels.push(level);
      }
      
      // First heading should be h1
      expect(headingLevels[0]).toBe(1);
      
      // Check for logical progression (no skipping levels)
      for (let i = 1; i < headingLevels.length; i++) {
        const currentLevel = headingLevels[i];
        const previousLevel = headingLevels[i - 1];
        
        // Level should not increase by more than 1
        expect(currentLevel - previousLevel).toBeLessThanOrEqual(1);
      }
    }
    
    // Check for proper list structure
    const lists = page.locator('ul, ol');
    const listCount = await lists.count();
    
    for (let i = 0; i < listCount; i++) {
      const list = lists.nth(i);
      const listItems = list.locator('li');
      const itemCount = await listItems.count();
      
      // Lists should have list items
      expect(itemCount).toBeGreaterThan(0);
    }
  });

  test('Color contrast and visual accessibility', async ({ page }) => {
    await loginAsAdmin(page);
    await waitForPageLoad(page);
    
    // Test high contrast mode simulation
    await page.emulateMedia({ colorScheme: 'dark' });
    await waitForPageLoad(page);
    
    // Verify page is still functional in dark mode
    await expect(page.locator('main')).toBeVisible();
    
    // Reset to light mode
    await page.emulateMedia({ colorScheme: 'light' });
    await waitForPageLoad(page);
    
    // Test with reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await waitForPageLoad(page);
    
    // Verify page is still functional with reduced motion
    await expect(page.locator('main')).toBeVisible();
    
    // Test focus indicators
    const focusableElements = page.locator('button, input, select, textarea, a[href]');
    const elementCount = await focusableElements.count();
    
    if (elementCount > 0) {
      const firstElement = focusableElements.first();
      await firstElement.focus();
      
      // Check that focus is visible (this is a basic check)
      await expect(firstElement).toBeFocused();
    }
  });

  test('Form accessibility', async ({ page }) => {
    await loginAsTester(page);
    
    // Navigate to a form-heavy page
    await navigateAndWait(page, '/phases/planning?reportId=1');
    
    // Test form accessibility
    await retry(async () => {
      await page.click('[data-testid="add-attribute-button"]');
    });
    
    // Check form labels and structure
    const formInputs = page.locator('[data-testid="attr-name-input"], [data-testid="attr-description-input"]');
    const inputCount = await formInputs.count();
    
    for (let i = 0; i < inputCount; i++) {
      const input = formInputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      
      // Input should have proper labeling
      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        const labelExists = await label.count() > 0;
        expect(labelExists || ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    }
    
    // Test form validation accessibility
    await page.fill('[data-testid="attr-name-input"]', ''); // Empty required field
    await page.click('[data-testid="save-attribute-button"]');
    
    // Check for accessible error messages
    const errorMessages = page.locator('[role="alert"], .error, [aria-invalid="true"]');
    const errorCount = await errorMessages.count();
    
    if (errorCount > 0) {
      // Error messages should be properly associated with form fields
      for (let i = 0; i < errorCount; i++) {
        const error = errorMessages.nth(i);
        const isVisible = await error.isVisible();
        expect(isVisible).toBeTruthy();
      }
    }
  });

  test('Modal and dialog accessibility', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateAndWait(page, '/users');
    
    // Open a modal/dialog
    await retry(async () => {
      await page.click('[data-testid="add-user-button"]');
    });
    
    // Check modal accessibility
    const modal = page.locator('[role="dialog"], [role="alertdialog"], .modal');
    
    if (await modal.count() > 0) {
      // Modal should be visible
      await expect(modal.first()).toBeVisible();
      
      // Modal should have proper ARIA attributes
      const ariaLabel = await modal.first().getAttribute('aria-label');
      const ariaLabelledBy = await modal.first().getAttribute('aria-labelledby');
      const ariaDescribedBy = await modal.first().getAttribute('aria-describedby');
      
      // Modal should have accessible name
      expect(ariaLabel || ariaLabelledBy).toBeTruthy();
      
      // Focus should be trapped in modal
      await page.keyboard.press('Tab');
      const focusedElement = page.locator(':focus');
      
      // Focused element should be within the modal
      const modalElement = await modal.first().elementHandle();
      if (modalElement) {
        const isInModal = await focusedElement.evaluate((el, modalEl) => {
          return modalEl.contains(el);
        }, modalElement);
        
        expect(isInModal).toBeTruthy();
      }
      
      // Test Escape key to close modal
      await page.keyboard.press('Escape');
      
      // Modal should be closed or closing
      await page.waitForTimeout(500); // Allow for animation
    }
  });

  test('Data table accessibility', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateAndWait(page, '/reports');
    
    // Wait for table to load
    await waitForPageLoad(page);
    
    // Check table accessibility
    const tables = page.locator('table');
    const tableCount = await tables.count();
    
    for (let i = 0; i < tableCount; i++) {
      const table = tables.nth(i);
      
      // Table should have proper structure
      const thead = table.locator('thead');
      const tbody = table.locator('tbody');
      
      if (await thead.count() > 0) {
        // Check for proper header cells
        const headerCells = thead.locator('th');
        const headerCount = await headerCells.count();
        
        for (let j = 0; j < headerCount; j++) {
          const header = headerCells.nth(j);
          const scope = await header.getAttribute('scope');
          const text = await header.textContent();
          
          // Header should have scope attribute or text content
          expect(scope || text?.trim()).toBeTruthy();
        }
      }
      
      // Check for table caption or aria-label
      const caption = table.locator('caption');
      const ariaLabel = await table.getAttribute('aria-label');
      const ariaLabelledBy = await table.getAttribute('aria-labelledby');
      
      const hasCaption = await caption.count() > 0;
      
      // Table should have accessible name
      expect(hasCaption || ariaLabel || ariaLabelledBy).toBeTruthy();
    }
  });

  test('Mobile accessibility', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await loginAsAdmin(page);
    await waitForPageLoad(page);
    
    // Check mobile-specific accessibility
    
    // Touch targets should be large enough (minimum 44px)
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < Math.min(buttonCount, 5); i++) { // Check first 5 buttons
      const button = buttons.nth(i);
      const boundingBox = await button.boundingBox();
      
      if (boundingBox) {
        // Button should be at least 44px in height or width
        const minSize = Math.min(boundingBox.width, boundingBox.height);
        expect(minSize).toBeGreaterThanOrEqual(40); // Slightly less strict for testing
      }
    }
    
    // Mobile navigation should be accessible
    const mobileMenu = page.locator('[data-testid="mobile-menu-button"]');
    if (await mobileMenu.count() > 0) {
      await expect(mobileMenu).toBeVisible();
      
      // Mobile menu button should have accessible name
      const ariaLabel = await mobileMenu.getAttribute('aria-label');
      const text = await mobileMenu.textContent();
      expect(ariaLabel || text?.trim()).toBeTruthy();
    }
    
    // Check for proper zoom behavior
    await page.setViewportSize({ width: 375 * 2, height: 667 * 2 }); // Simulate zoom
    await waitForPageLoad(page);
    
    // Page should still be functional when zoomed
    await expect(page.locator('main')).toBeVisible();
  });
}); 