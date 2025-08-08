#!/usr/bin/env python3
"""Debug data owner dashboard."""
import asyncio
from playwright.async_api import async_playwright

async def debug_data_owner_dashboard():
    """Debug data owner dashboard."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Collect console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text
        }))
        
        # Login as data owner with actual data
        print("Logging in as data owner with assignments...")
        await page.goto("http://localhost:3001/login")
        await page.fill('input[name="email"]', "data.provider@example.com")
        await page.fill('input[name="password"]', "password123")
        
        # Force click
        await page.evaluate("""
            const overlay = document.querySelector('#webpack-dev-server-client-overlay');
            if (overlay) overlay.remove();
            const button = document.querySelector('button[type="submit"]');
            if (button) button.click();
        """)
        
        await page.wait_for_timeout(3000)
        
        # Go to data owner dashboard
        print("Navigating to data owner dashboard...")
        await page.goto("http://localhost:3001/data-owner-dashboard", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # Take screenshot
        await page.screenshot(path="data_owner_dashboard_debug.png")
        
        # Get page content
        page_text = await page.text_content("body")
        print("\nPage content preview:")
        print(page_text[:500])
        
        # Print console errors
        errors = [msg for msg in console_messages if msg['type'] == 'error']
        if errors:
            print(f"\nConsole errors ({len(errors)}):")
            for err in errors[:5]:
                print(f"  - {err['text'][:200]}")
        
        # Check what's visible
        print("\nChecking page elements:")
        print(f"  Has 'Data Owner Dashboard' title: {await page.locator('text=/Data Owner Dashboard/').count() > 0}")
        print(f"  Has loading indicator: {await page.locator('text=/Loading/').count() > 0}")
        print(f"  Has error message: {await page.locator('text=/Error|Failed/').count() > 0}")
        print(f"  Has cards: {await page.locator('.MuiCard-root').count()}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_data_owner_dashboard())