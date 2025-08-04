#!/usr/bin/env python3
"""
Check the new theme application
"""

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
            await page.fill('input[name="password"]', "NewPassword123!")
            await page.click('button[type="submit"]')
            
            # Wait for dashboard
            await page.wait_for_function(
                "url => !window.location.href.includes('/login')",
                timeout=10000
            )
            print("✅ Login successful")
            
            # Take screenshot after login
            await page.screenshot(path="test_results/dashboard_with_new_theme.png", full_page=True)
            print("📸 Dashboard screenshot saved")
            
            # Check theme colors
            print("\n2. Checking theme colors:")
            
            # Get AppBar background color
            appbar_color = await page.evaluate('''() => {
                const appBar = document.querySelector('.MuiAppBar-root');
                if (appBar) {
                    const styles = window.getComputedStyle(appBar);
                    return styles.backgroundColor;
                }
                return null;
            }''')
            print(f"   - AppBar color: {appbar_color}")
            
            # Check if it's using the new teal color
            if appbar_color and ('14, 124, 123' in appbar_color or '0e7c7b' in appbar_color.lower()):
                print("   ✅ Using new Deloitte teal branding!")
            else:
                print("   ❌ Not using new teal theme")
            
            # Check button colors
            button_color = await page.evaluate('''() => {
                const button = document.querySelector('.MuiButton-containedPrimary');
                if (button) {
                    const styles = window.getComputedStyle(button);
                    return styles.backgroundColor;
                }
                return null;
            }''')
            print(f"   - Primary button color: {button_color}")
            
            # Navigate to different pages to see theme
            print("\n3. Testing theme on different pages:")
            
            # Test Cycles page
            cycles_link = await page.query_selector('text="Test Cycles"')
            if cycles_link:
                await cycles_link.click()
                await page.wait_for_load_state("networkidle")
                await page.screenshot(path="test_results/cycles_with_new_theme.png")
                print("✅ Test Cycles page screenshot saved")
            
            # Keep browser open for inspection
            print("\n⏸️  Browser will stay open for 15 seconds for inspection...")
            await asyncio.sleep(15)
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            await browser.close()
    
    print("\n" + "=" * 60)
    print("Check complete. Screenshots saved in test_results/")
    print("\n📸 Screenshots to review:")
    print("  - test_results/login_with_new_theme.png")
    print("  - test_results/dashboard_with_new_theme.png")
    print("  - test_results/cycles_with_new_theme.png")

if __name__ == "__main__":
    asyncio.run(check_new_theme())