#\!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def final_check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # Login
        await page.goto("http://localhost:3000/login")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="test_results/final_login_theme.png")
        
        await page.fill('input[name="email"]', "admin@example.com")
        await page.fill('input[name="password"]', r"NewPassword123\!")
        await page.click('button[type="submit"]')
        
        # Wait for dashboard
        await asyncio.sleep(5)
        
        # Screenshot dashboard
        await page.screenshot(path="test_results/final_dashboard_theme.png", full_page=True)
        
        await browser.close()
        print("Final theme screenshots saved\!")

asyncio.run(final_check())
