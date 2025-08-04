#!/usr/bin/env python3
"""
Refresh Data Owner page to trigger API call
"""
import asyncio
from playwright.async_api import async_playwright

async def refresh_page():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to login page
            await page.goto('http://localhost:3000/login')
            await page.wait_for_load_state('networkidle')
            
            # Login as data owner
            await page.fill('input[name="email"]', 'data.provider@example.com')
            await page.fill('input[name="password"]', 'password123')
            await page.click('button[type="submit"]')
            
            # Wait for dashboard to load
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            print("Refreshing page to trigger API call...")
            await page.reload()
            await page.wait_for_load_state('networkidle')
            
            await asyncio.sleep(2)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(refresh_page())