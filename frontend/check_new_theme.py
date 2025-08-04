#\!/usr/bin/env python3
"""Check the new theme application"""

import asyncio
from playwright.async_api import async_playwright

async def check_new_theme():
    """Check if new theme is applied"""
    print("🎨 Checking New Deloitte Theme Application")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # Login
            print("1. Logging in...")
            await page.goto("http://localhost:3000/login")
            await page.wait_for_load_state("networkidle")
            
            # Take screenshot of login page
            await page.screenshot(path="test_results/login_with_new_theme.png")
            print("📸 Login page screenshot saved")
            
            await page.fill('input[name="email"]', "admin@example.com")
            await page.fill('input[name="password"]', "NewPassword123\!")
            await page.click('button[type="submit"]')
            
            # Wait for dashboard
            await page.wait_for_function(
                "url => \!window.location.href.includes('/login')",
                timeout=10000
            )
            print("✅ Login successful")
            
            # Take screenshot after login
            await page.screenshot(path="test_results/dashboard_with_new_theme.png", full_page=True)
            print("📸 Dashboard screenshot saved")
            
            # Keep browser open for inspection
            print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            await browser.close()
    
    print("\nCheck complete. Screenshots saved in test_results/")

if __name__ == "__main__":
    asyncio.run(check_new_theme())
