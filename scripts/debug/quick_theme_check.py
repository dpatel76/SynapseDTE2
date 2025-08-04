#\!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def quick_check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("http://localhost:3000/login")
        await page.wait_for_load_state("networkidle")
        
        # Screenshot login
        await page.screenshot(path="test_results/login_new_theme.png")
        
        # Login and get dashboard
        await page.fill('input[name="email"]', "admin@example.com")
        await page.fill('input[name="password"]', "NewPassword123\!")
        await page.click('button[type="submit"]')
        await asyncio.sleep(3)
        
        # Screenshot dashboard
        await page.screenshot(path="test_results/dashboard_new_theme.png")
        
        await browser.close()
        print("Screenshots saved\!")

asyncio.run(quick_check())
