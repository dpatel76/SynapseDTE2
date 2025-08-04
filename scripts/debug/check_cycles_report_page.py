#!/usr/bin/env python3
"""Check cycles report page for data provider ID link."""
import asyncio
from playwright.async_api import async_playwright

async def check_cycles_report_page():
    """Check the cycles report page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
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
        print("Navigating to cycles/9/reports/156...")
        await page.goto("http://localhost:3001/cycles/9/reports/156", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # Take screenshot
        await page.screenshot(path="cycles_report_page.png")
        
        # Look for data provider links
        print("\nSearching for data provider links...")
        
        # Check for any links containing "data-provider"
        data_provider_links = await page.locator('a[href*="data-provider"]').all()
        if data_provider_links:
            print(f"Found {len(data_provider_links)} data-provider links:")
            for link in data_provider_links:
                href = await link.get_attribute('href')
                text = await link.text_content()
                print(f"  - Text: '{text}', Href: {href}")
        
        # Check for any links containing "data-owner"
        data_owner_links = await page.locator('a[href*="data-owner"]').all()
        if data_owner_links:
            print(f"\nFound {len(data_owner_links)} data-owner links:")
            for link in data_owner_links:
                href = await link.get_attribute('href')
                text = await link.text_content()
                print(f"  - Text: '{text}', Href: {href}")
        
        # Check for phase navigation buttons/links
        print("\nChecking phase navigation...")
        phase_elements = await page.locator('text=/Data Provider|Data Owner|Identification/i').all()
        if phase_elements:
            print(f"Found {len(phase_elements)} phase elements mentioning data provider/owner:")
            for elem in phase_elements:
                text = await elem.text_content()
                print(f"  - {text}")
        
        # Check stepper or workflow elements
        print("\nChecking workflow/stepper elements...")
        stepper_items = await page.locator('.MuiStep-root, .MuiStepper-root').all()
        if stepper_items:
            print(f"Found {len(stepper_items)} stepper items")
        
        # Get all clickable elements that might lead to data provider
        print("\nChecking all clickable phase elements...")
        phase_buttons = await page.locator('button, [role="button"]').all()
        for button in phase_buttons:
            text = await button.text_content()
            if text and ('data' in text.lower() and 'provider' in text.lower()):
                print(f"  - Found button: '{text}'")
                # Try to get onclick or href
                onclick = await button.get_attribute('onclick')
                if onclick:
                    print(f"    onclick: {onclick}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_cycles_report_page())