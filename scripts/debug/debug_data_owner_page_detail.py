#!/usr/bin/env python3
"""Debug data owner page in detail."""
import asyncio
from playwright.async_api import async_playwright

async def debug_page():
    """Debug data owner page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        
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
        
        # Check page state
        print("\nChecking page elements:")
        
        # Check for loading spinner
        loading = await page.locator('.MuiCircularProgress-root').count()
        print(f"Loading spinners: {loading}")
        
        # Check for any visible text
        visible_text = await page.locator('body').inner_text()
        print(f"Visible text length: {len(visible_text)}")
        print(f"First 200 chars: {visible_text[:200]}")
        
        # Check for cards
        cards = await page.locator('.MuiCard-root').count()
        print(f"Cards found: {cards}")
        
        # Check for error boundaries
        errors = await page.locator('text=/Error|Failed/').count()
        print(f"Error messages: {errors}")
        
        # Try to find mock data toggle
        mock_toggle = await page.locator('text=/Mock Data/').count()
        print(f"Mock data toggle: {mock_toggle}")
        
        # Check if mock data is enabled
        is_mock_enabled = await page.evaluate("""
            localStorage.getItem('enableMockData') === 'true'
        """)
        print(f"Mock data enabled: {is_mock_enabled}")
        
        # Try disabling mock data
        if is_mock_enabled:
            print("\nDisabling mock data...")
            await page.evaluate("localStorage.removeItem('enableMockData')")
            await page.reload()
            await page.wait_for_timeout(3000)
            
            visible_text_after = await page.locator('body').inner_text()
            print(f"Text after reload: {len(visible_text_after)} chars")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page())