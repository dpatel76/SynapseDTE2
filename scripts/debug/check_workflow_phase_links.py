#!/usr/bin/env python3
"""Check workflow phase links and errors."""
import asyncio
from playwright.async_api import async_playwright

async def check_links():
    """Check the workflow phase links."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Collect console messages
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        # Login as tester
        print("Logging in as tester...")
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
        
        # Go to cycles report page
        print("\nNavigating to /cycles/9/reports/156...")
        await page.goto("http://localhost:3001/cycles/9/reports/156")
        await page.wait_for_timeout(3000)
        
        # Look for the Planning link and check its href
        print("\nChecking workflow phase links...")
        planning_link = await page.locator('a:has-text("Planning")').first
        if planning_link:
            planning_href = await planning_link.get_attribute('href')
            print(f"Planning link href: {planning_href}")
            
            # Click it to see where it goes
            await planning_link.click()
            await page.wait_for_timeout(2000)
            print(f"After clicking Planning, URL is: {page.url}")
            
            # Go back
            await page.go_back()
            await page.wait_for_timeout(2000)
        
        # Look for all phase links
        print("\nLooking for all phase links...")
        phase_links = await page.locator('a').all()
        for link in phase_links:
            text = await link.text_content()
            if text and any(phase in text for phase in ['Planning', 'Scoping', 'Sample', 'Data', 'Request', 'Test', 'Observation']):
                href = await link.get_attribute('href')
                print(f"  {text}: {href}")
        
        # Now test the data-owner page directly
        print("\n\nTesting /cycles/9/reports/156/data-owner directly...")
        console_errors.clear()
        
        await page.goto("http://localhost:3001/cycles/9/reports/156/data-owner")
        await page.wait_for_timeout(3000)
        
        # Take screenshot
        await page.screenshot(path="data_owner_errors.png")
        
        # Check console errors
        if console_errors:
            print(f"\nConsole errors on data-owner page ({len(console_errors)}):")
            for err in console_errors[:5]:
                print(f"  - {err[:200]}")
        
        # Check page content
        has_error_boundary = await page.locator('text=/Failed to load component|Error/').count()
        print(f"\nError boundary triggered: {has_error_boundary > 0}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_links())