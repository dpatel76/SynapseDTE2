#!/usr/bin/env python3
"""Debug data provider ID and observation management pages."""
import asyncio
from playwright.async_api import async_playwright

async def debug_pages():
    """Debug problematic pages."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Collect console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text
        }))
        
        # Collect network errors
        network_errors = []
        def log_response(response):
            if response.status >= 400:
                network_errors.append({
                    'url': response.url,
                    'status': response.status,
                    'method': response.request.method
                })
        page.on("response", log_response)
        
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
        
        # Test data-provider-id page
        print("\n1. Testing data-provider-id page...")
        console_messages.clear()
        network_errors.clear()
        
        await page.goto("http://localhost:3001/cycles/9/reports/156/data-provider-id", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="data_provider_id_debug.png")
        
        # Get page content
        page_text = await page.text_content("body")
        print(f"Page loads: {'Error' not in page_text and 'Failed' not in page_text}")
        
        # Print errors
        errors = [msg for msg in console_messages if msg['type'] == 'error']
        if errors:
            print(f"Console errors ({len(errors)}):")
            for err in errors[:3]:
                print(f"  - {err['text'][:150]}")
        
        if network_errors:
            print(f"Network errors ({len(network_errors)}):")
            for err in network_errors[:3]:
                print(f"  - {err['status']} {err['url']}")
        
        # Test observation-management page
        print("\n2. Testing observation-management page...")
        console_messages.clear()
        network_errors.clear()
        
        await page.goto("http://localhost:3001/cycles/9/reports/156/observation-management", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="observation_management_debug.png")
        
        # Check page elements
        print(f"Has mock data toggle: {await page.locator('text=/Mock Data/').count() > 0}")
        print(f"Has phase status section: {await page.locator('text=/Phase Status/').count() > 0}")
        print(f"Has workflow section: {await page.locator('text=/Workflow/').count() > 0}")
        
        # Check for real data
        real_data_indicators = [
            "Create Observation", "Review Observations", "Approve Observations",
            "Total Observations", "Resolution Rate", "Status Summary"
        ]
        
        for indicator in real_data_indicators:
            count = await page.locator(f'text=/{indicator}/').count()
            if count > 0:
                print(f"✓ Found: {indicator}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_pages())