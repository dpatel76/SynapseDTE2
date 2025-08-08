#!/usr/bin/env python3
"""
Check if new UI features are visible
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def check_ui_features():
    """Check for new UI features"""
    print("🧪 Checking UI Features and Branding")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Launch browser with UI visible
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # Login
            print("1. Logging in...")
            await page.goto("http://localhost:3000/login")
            await page.wait_for_load_state("networkidle")
            
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
            await page.screenshot(path="test_results/actual_dashboard.png", full_page=True)
            print("📸 Dashboard screenshot saved")
            
            # Check for new features
            print("\n2. Checking for new UI features:")
            
            # Check for GlobalSearch
            global_search = await page.query_selector('[placeholder*="Search"]')
            if global_search:
                print("✅ Global Search component found")
                # Get computed styles
                search_box = await page.evaluate('''() => {
                    const el = document.querySelector('[placeholder*="Search"]');
                    if (el) {
                        const styles = window.getComputedStyle(el);
                        return {
                            exists: true,
                            placeholder: el.placeholder
                        };
                    }
                    return {exists: false};
                }''')
                print(f"   - Search placeholder: {search_box.get('placeholder', 'N/A')}")
            else:
                print("❌ Global Search not found")
            
            # Check for NotificationBell
            notification_bell = await page.query_selector('[data-testid*="notification"], [aria-label*="notification"], svg[data-testid="NotificationsIcon"]')
            if notification_bell:
                print("✅ Notification Bell found")
            else:
                print("❌ Notification Bell not found")
            
            # Check branding/theme
            print("\n3. Checking theme and branding:")
            
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
            if appbar_color and ('14, 124, 123' in appbar_color or '#0e7c7b' in appbar_color.lower()):
                print("   ✅ Using new Deloitte teal branding!")
            else:
                print("   ❌ Still using old blue theme")
            
            # Check for brand name
            brand_text = await page.evaluate('''() => {
                const brand = document.querySelector('h6');
                return brand ? brand.textContent : null;
            }''')
            print(f"   - Brand name: {brand_text}")
            
            # Check for enhanced UI elements
            print("\n4. Checking for enhanced UI elements:")
            
            # Check for cards with shadows
            cards = await page.query_selector_all('.MuiCard-root')
            print(f"   - Number of cards: {len(cards)}")
            
            # Check sidebar
            sidebar = await page.query_selector('.MuiDrawer-root')
            print(f"   - Sidebar exists: {'✅' if sidebar else '❌'}")
            
            # Navigate to test the navigation
            print("\n5. Testing navigation:")
            cycles_link = await page.query_selector('text="Test Cycles"')
            if cycles_link:
                await cycles_link.click()
                await page.wait_for_load_state("networkidle")
                await page.screenshot(path="test_results/cycles_page.png")
                print("✅ Navigation to Test Cycles works")
            
            # Keep browser open for manual inspection
            print("\n⏸️  Browser will stay open for 10 seconds for manual inspection...")
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await page.screenshot(path="test_results/error_state.png")
        
        finally:
            await browser.close()
    
    print("\n" + "=" * 60)
    print("Check complete. Screenshots saved in test_results/")

if __name__ == "__main__":
    asyncio.run(check_ui_features())