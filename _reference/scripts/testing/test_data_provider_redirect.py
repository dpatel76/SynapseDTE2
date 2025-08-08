#!/usr/bin/env python3
"""Test data provider ID redirect."""
import asyncio
from playwright.async_api import async_playwright

async def test_redirect():
    """Test if data-provider-id redirects to data-owner."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Login as tester
        print("Logging in...")
        await page.goto("http://localhost:3001/login")
        await page.fill('input[name="email"]', "tester@example.com")
        await page.fill('input[name="password"]', "password123")
        
        # Force click
        await page.evaluate("""
            const overlay = document.querySelector('#webpack-dev-server-client-overlay');
            if (overlay) overlay.remove();
            const button = document.querySelector('button[type="submit"]');
            if (button) button.click();
        """)
        
        await page.wait_for_timeout(3000)
        
        # Try the data-provider-id URL
        print("\nNavigating to data-provider-id URL...")
        await page.goto("http://localhost:3001/cycles/9/reports/156/data-provider-id")
        await page.wait_for_timeout(2000)
        
        # Check final URL
        final_url = page.url
        print(f"Final URL: {final_url}")
        
        if "data-owner" in final_url:
            print("✅ Redirect successful!")
        else:
            print("❌ Redirect failed")
        
        # Take screenshot
        await page.screenshot(path="data_provider_page_test.png")
        
        # Check if page loaded
        page_title = await page.text_content("h4, h5, h6")
        print(f"Page title: {page_title}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_redirect())