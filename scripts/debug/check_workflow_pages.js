const { chromium } = require('../frontend/node_modules/playwright');

async function checkWorkflowPages() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Console Error:', msg.text());
    }
  });

  // Monitor network failures
  page.on('requestfailed', request => {
    console.log('Request failed:', request.url(), request.failure().errorText);
  });

  const pages = [
    'http://localhost:3000/cycles/9/reports/156/sample-selection',
    'http://localhost:3000/cycles/9/reports/156/data-provider-id',
    'http://localhost:3000/cycles/9/reports/156/request-info',
    'http://localhost:3000/cycles/9/reports/156/test-execution',
    'http://localhost:3000/cycles/9/reports/156/observation-management'
  ];

  // First, login as tester
  console.log('Logging in as tester...');
  await page.goto('http://localhost:3000/login');
  
  // Wait for login form to be ready
  await page.waitForSelector('input[name="username"]', { timeout: 10000 }).catch(() => {
    console.log('Username field not found, trying ID selector...');
  });
  
  // Try different selectors for username
  const usernameInput = await page.$('input[name="username"]') || 
                       await page.$('input#username') || 
                       await page.$('input[type="text"]');
  
  if (usernameInput) {
    await usernameInput.fill('tester_user');
  } else {
    console.log('Could not find username input');
    await page.screenshot({ path: 'screenshots/login-page.png' });
    throw new Error('Login form not found');
  }
  
  // Try different selectors for password
  const passwordInput = await page.$('input[name="password"]') || 
                       await page.$('input#password') || 
                       await page.$('input[type="password"]');
  
  if (passwordInput) {
    await passwordInput.fill('password123');
  }
  
  // Try different selectors for submit button
  const submitButton = await page.$('button[type="submit"]') || 
                      await page.$('button:has-text("Login")') ||
                      await page.$('button:has-text("Sign in")');
  
  if (submitButton) {
    await submitButton.click();
  }
  
  // Wait for navigation after login
  await page.waitForURL('**/dashboard/**', { timeout: 10000 }).catch(() => {
    console.log('Login might have failed or redirected to a different page');
  });

  console.log('Checking workflow pages...\n');

  for (const url of pages) {
    console.log(`\nChecking: ${url}`);
    console.log('=' .repeat(80));
    
    try {
      // Navigate and wait for network idle
      const response = await page.goto(url, { waitUntil: 'networkidle' });
      
      // Check response status
      console.log(`Response status: ${response.status()}`);
      
      // Check for error messages
      const errorElement = await page.$('[class*="error"], [class*="Error"]');
      if (errorElement) {
        const errorText = await errorElement.textContent();
        console.log(`Error found on page: ${errorText}`);
      }
      
      // Check for loading states
      const loadingElement = await page.$('[class*="loading"], [class*="Loading"], [class*="progress"], [class*="Progress"]');
      if (loadingElement) {
        console.log('Page is still loading or showing loading indicator');
      }
      
      // Check for empty states
      const emptyStates = await page.$$('[class*="empty"], [class*="Empty"], text=/no data/i, text=/no records/i');
      if (emptyStates.length > 0) {
        console.log('Page shows empty state or no data');
      }
      
      // Get page title and any main content
      const title = await page.title();
      console.log(`Page title: ${title}`);
      
      // Check for specific content based on page type
      const pageName = url.split('/').pop();
      switch(pageName) {
        case 'sample-selection':
          const sampleCount = await page.$$('[data-testid*="sample"], [class*="sample"]').then(els => els.length);
          console.log(`Sample elements found: ${sampleCount}`);
          break;
        case 'data-provider-id':
          const providerCount = await page.$$('[data-testid*="provider"], [class*="provider"]').then(els => els.length);
          console.log(`Provider elements found: ${providerCount}`);
          break;
        case 'request-info':
          const infoCount = await page.$$('[data-testid*="info"], [class*="info"], form').then(els => els.length);
          console.log(`Info/form elements found: ${infoCount}`);
          break;
        case 'test-execution':
          const testCount = await page.$$('[data-testid*="test"], [class*="test"], table').then(els => els.length);
          console.log(`Test elements found: ${testCount}`);
          break;
        case 'observation-management':
          const obsCount = await page.$$('[data-testid*="observation"], [class*="observation"]').then(els => els.length);
          console.log(`Observation elements found: ${obsCount}`);
          break;
      }
      
      // Take a screenshot for debugging
      await page.screenshot({ path: `screenshots/${pageName}.png`, fullPage: true });
      console.log(`Screenshot saved: screenshots/${pageName}.png`);
      
    } catch (error) {
      console.log(`Error checking page: ${error.message}`);
    }
  }

  await browser.close();
}

checkWorkflowPages().catch(console.error);