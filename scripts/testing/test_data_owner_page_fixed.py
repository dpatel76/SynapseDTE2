#!/usr/bin/env python3
"""Test data owner page after permissions fix."""
import asyncio
from playwright.async_api import async_playwright

async def test_page():
    """Test data owner page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Login
        print("Logging in...")
        await page.goto("http://localhost:3001/login")
        await page.fill('input[name="email"]', "tester@example.com")
        await page.fill('input[name="password"]', "password123")
        
        await page.evaluate("""
            const overlay = document.querySelector('#webpack-dev-server-client-overlay');
            if (overlay) overlay.remove();
            const button = document.querySelector('button[type="submit"]');
            if (button) button.click();
        """)
        
        await page.wait_for_timeout(3000)
        
        # Navigate to data owner page  
        print("\nNavigating to data owner page...")
        await page.goto("http://localhost:3001/cycles/9/reports/156/data-owner")
        await page.wait_for_timeout(5000)
        
        # Take screenshot
        await page.screenshot(path="data_owner_page_fixed.png")
        
        # Check for content
        has_cards = await page.locator('.MuiCard-root').count()
        has_tables = await page.locator('table').count()
        has_errors = await page.locator('text=/Error|Failed/').count()
        
        print(f"\nPage status:")
        print(f"  Cards: {has_cards}")
        print(f"  Tables: {has_tables}")
        print(f"  Errors: {has_errors}")
        
        if has_cards > 1 or has_tables > 0:
            print("✅ Page loaded successfully!")
        else:
            print("❌ Page still not loading properly")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_page())