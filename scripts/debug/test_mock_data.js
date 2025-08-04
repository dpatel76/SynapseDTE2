const { chromium } = require('../frontend/node_modules/playwright');

async function testMockData() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('Opening frontend...');
  await page.goto('http://localhost:3000/login');
  
  // Enable mock data via localStorage
  await page.evaluate(() => {
    localStorage.setItem('enableMockData', 'true');
  });
  
  console.log('Mock data enabled via localStorage');
  
  // Login
  console.log('Logging in...');
  await page.fill('input[type="text"]', 'tester@example.com');
  await page.fill('input[type="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  await page.waitForTimeout(2000);
  
  // Navigate to sample selection page
  console.log('Navigating to sample selection page...');
  await page.goto('http://localhost:3000/cycles/9/reports/156/sample-selection');
  await page.waitForTimeout(3000);
  
  // Check if mock data is displayed
  const pageContent = await page.content();
  if (pageContent.includes('In Progress') || pageContent.includes('sample')) {
    console.log('✅ Sample selection page is showing content (likely mock data)');
  } else {
    console.log('❌ Sample selection page is not showing expected content');
  }
  
  // Take screenshot
  await page.screenshot({ path: 'screenshots/sample-selection-mock.png', fullPage: true });
  console.log('Screenshot saved to screenshots/sample-selection-mock.png');
  
  // Test other pages
  const pages = [
    'data-provider-id',
    'request-info',
    'test-execution',
    'observation-management'
  ];
  
  for (const pageName of pages) {
    console.log(`\nNavigating to ${pageName} page...`);
    await page.goto(`http://localhost:3000/cycles/9/reports/156/${pageName}`);
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `screenshots/${pageName}-mock.png`, fullPage: true });
    console.log(`Screenshot saved to screenshots/${pageName}-mock.png`);
  }
  
  console.log('\nDone! Check the screenshots directory for results.');
  
  // Keep browser open for manual inspection
  console.log('Browser will stay open for manual inspection. Close it when done.');
}

testMockData().catch(console.error);