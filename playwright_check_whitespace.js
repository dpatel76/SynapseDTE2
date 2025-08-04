const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  try {
    console.log('Navigating to login page...');
    await page.goto('http://localhost:3000/login');
    
    // Wait for login form
    await page.waitForSelector('input[name="email"]', { timeout: 10000 });
    
    console.log('Logging in...');
    await page.fill('input[name="email"]', 'tester@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Wait for navigation to complete
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    console.log('Logged in successfully');
    
    // Navigate to My Assignments
    console.log('Navigating to My Assignments...');
    await page.goto('http://localhost:3000/my-assignments');
    await page.waitForLoadState('networkidle');
    
    // Take screenshot
    await page.screenshot({ path: 'my-assignments-whitespace.png', fullPage: false });
    console.log('Screenshot saved as my-assignments-whitespace.png');
    
    // Get the main content area dimensions
    const mainContent = await page.$('main');
    if (mainContent) {
      const box = await mainContent.boundingBox();
      console.log('Main content area:', box);
    }
    
    // Get the Box wrapper dimensions
    const boxWrapper = await page.$('main > div');
    if (boxWrapper) {
      const box = await boxWrapper.boundingBox();
      console.log('Box wrapper:', box);
      
      // Get computed styles
      const styles = await boxWrapper.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          padding: computed.padding,
          paddingLeft: computed.paddingLeft,
          paddingRight: computed.paddingRight,
          margin: computed.margin,
          marginLeft: computed.marginLeft,
          marginRight: computed.marginRight
        };
      });
      console.log('Box wrapper styles:', styles);
    }
    
    // Check for any container elements
    const containers = await page.$$('.MuiContainer-root');
    console.log('Found', containers.length, 'Container elements');
    
    // Wait a bit to see the page
    await page.waitForTimeout(5000);
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
})();