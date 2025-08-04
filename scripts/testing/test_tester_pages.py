#!/usr/bin/env python3
"""Test pages for tester role with working credentials."""
import asyncio
from playwright.async_api import async_playwright

async def test_tester_pages():
    """Test pages as tester@example.com."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Login
        print("Logging in as tester@example.com...")
        await page.goto("http://localhost:3001/login")
        
        # Remove webpack overlay
        await page.evaluate("""
            const overlay = document.querySelector('#webpack-dev-server-client-overlay');
            if (overlay) overlay.remove();
        """)
        
        await page.fill('input[name="email"]', "tester@example.com")
        await page.fill('input[name="password"]', "password123")
        await page.click('button[type="submit"]')
        
        # Wait for dashboard
        await page.wait_for_url("**/dashboard", timeout=10000)
        print("Login successful!")
        
        # Test pages mentioned by user
        test_pages = [
            "/cycles/9/reports/156/sample-selection",
            "/cycles/9/reports/156/request-info", 
            "/cycles/9/reports/156/test-execution",
            "/data-owner-dashboard"
        ]
        
        for url in test_pages:
            print(f"\nTesting {url}...")
            try:
                await page.goto(f"http://localhost:3001{url}", wait_until="networkidle")
                await page.wait_for_timeout(2000)
                
                # Take screenshot
                screenshot = f"test_{url.replace('/', '_')}.png"
                await page.screenshot(path=screenshot)
                
                # Check for data
                table_count = await page.locator('table').count()
                row_count = await page.locator('tbody tr').count()
                error_count = await page.locator('text=/Failed to load|Error/i').count()
                
                print(f"  Tables: {table_count}, Rows: {row_count}, Errors: {error_count}")
                print(f"  Screenshot: {screenshot}")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_tester_pages())