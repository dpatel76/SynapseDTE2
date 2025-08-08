#!/usr/bin/env python3
"""
Manual frontend test to check authentication and page loading
"""

import asyncio
from playwright.async_api import async_playwright
import httpx

BASE_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"

async def main():
    # First, login to get token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "tester@example.com", "password": "password123"}
        )
        login_data = response.json()
        token = login_data["access_token"]
        print(f"✅ Login successful, got token: {token[:20]}...")
    
    # Test frontend with authentication
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context()
        
        # Try setting token in localStorage before navigation
        page = await context.new_page()
        
        # Navigate to login page first
        await page.goto(f"{FRONTEND_URL}/login")
        await page.wait_for_timeout(1000)
        
        # Set token in localStorage
        await page.evaluate(f"""
            localStorage.setItem('access_token', '{token}');
            localStorage.setItem('user', JSON.stringify({login_data['user']}));
        """)
        
        print("✅ Set authentication in localStorage")
        
        # Now navigate to dashboard
        await page.goto(f"{FRONTEND_URL}/dashboard")
        await page.wait_for_timeout(3000)
        
        # Check current URL
        current_url = page.url
        print(f"Current URL: {current_url}")
        
        # Take screenshot
        await page.screenshot(path="test_manual_dashboard.png")
        print("✅ Screenshot saved to test_manual_dashboard.png")
        
        # Check for errors
        errors = await page.query_selector_all('[class*="error"], [class*="Error"]')
        if errors:
            print(f"⚠️  Found {len(errors)} error elements on page")
            for error in errors:
                text = await error.text_content()
                if text:
                    print(f"   Error: {text}")
        
        # Keep browser open for manual inspection
        print("\n🔍 Browser will stay open for manual inspection. Press Ctrl+C to close.")
        await asyncio.sleep(300)  # Keep open for 5 minutes
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())