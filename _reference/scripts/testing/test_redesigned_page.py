#!/usr/bin/env python3
"""Test the redesigned report testing page."""
import asyncio
from playwright.async_api import async_playwright

async def test_page():
    """Test redesigned page."""
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
        
        # Navigate to report page
        print("\nNavigating to /cycles/9/reports/156...")
        await page.goto("http://localhost:3001/cycles/9/reports/156")
        await page.wait_for_timeout(5000)
        
        # Take screenshot
        await page.screenshot(path="redesigned_report_page.png", full_page=True)
        
        # Check for phase cards
        phase_cards = await page.locator('.MuiCard-root').count()
        metrics_cards = await page.locator('.MuiPaper-root').count()
        
        print(f"\nPage elements:")
        print(f"  Phase cards: {phase_cards}")
        print(f"  Metric cards: {metrics_cards}")
        
        # Try clicking on a phase card
        print("\nTrying to click on Planning phase card...")
        planning_card = await page.locator('text=/Planning.*Analysis/').first
        if planning_card:
            await planning_card.click()
            await page.wait_for_timeout(2000)
            print(f"  Navigated to: {page.url}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_page())