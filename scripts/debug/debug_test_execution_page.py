#!/usr/bin/env python3
"""Debug test execution page errors."""
import asyncio
from playwright.async_api import async_playwright

async def debug_test_execution():
    """Debug test execution page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Collect console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text
        }))
        
        # Login
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
        
        # Go to test execution page
        print("Navigating to test execution page...")
        await page.goto("http://localhost:3001/cycles/9/reports/156/test-execution", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # Take screenshot
        await page.screenshot(path="test_execution_debug.png")
        
        # Get page content
        page_text = await page.text_content("body")
        print("\nPage content preview:")
        print(page_text[:500])
        
        # Print console errors
        errors = [msg for msg in console_messages if msg['type'] == 'error']
        if errors:
            print(f"\nConsole errors ({len(errors)}):")
            for err in errors:
                print(f"  - {err['text']}")
        
        # Check what's visible
        print("\nChecking page elements:")
        print(f"  Has 'Test Execution' title: {await page.locator('text=/Test Execution/').count() > 0}")
        print(f"  Has loading indicator: {await page.locator('text=/Loading/').count() > 0}")
        print(f"  Has error message: {await page.locator('text=/Error|Failed/').count() > 0}")
        print(f"  Has table: {await page.locator('table').count() > 0}")
        print(f"  Has 'No test cases' message: {await page.locator('text=/No test cases/').count() > 0}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_test_execution())