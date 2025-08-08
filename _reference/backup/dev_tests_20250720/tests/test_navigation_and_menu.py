#!/usr/bin/env python3
"""
Test navigation and user menu functionality
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

class NavigationTester:
    def __init__(self):
        self.results = []
        self.base_url = "http://localhost:3000"
        
    async def test_navigation_and_menu(self):
        """Test navigation links and user menu"""
        print("🧪 Testing Navigation and User Menu")
        print("=" * 60)
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Login
                await page.goto(f"{self.base_url}/login")
                await page.wait_for_load_state("networkidle")
                
                await page.fill('input[name="email"]', "admin@example.com")
                await page.fill('input[name="password"]', "NewPassword123!")
                await page.click('button[type="submit"]')
                
                # Wait for dashboard
                await page.wait_for_function(
                    f"url => window.location.href !== '{self.base_url}/login'",
                    timeout=10000
                )
                print("✅ Login successful")
                
                # Test navigation items
                print("\n📌 Testing Navigation Links:")
                
                # Check if navigation exists (MUI Drawer)
                nav_exists = await page.query_selector('.MuiDrawer-root')
                if nav_exists:
                    print("✅ Navigation menu found")
                    self.results.append({"test": "navigation_exists", "success": True})
                else:
                    print("❌ Navigation menu not found")
                    self.results.append({"test": "navigation_exists", "success": False})
                
                # Test common navigation links
                nav_links = [
                    {"text": "Dashboard", "expected_url": "/dashboard"},
                    {"text": "Test Cycles", "expected_url": "/cycles"},
                    {"text": "Reports", "expected_url": "/reports"},
                    {"text": "Users", "expected_url": "/users"}
                ]
                
                for link in nav_links:
                    try:
                        # Try to find link by text in the drawer/navigation
                        link_element = await page.query_selector(f'text="{link["text"]}"')
                        if link_element:
                            await link_element.click()
                            await page.wait_for_load_state("networkidle", timeout=5000)
                            current_url = page.url
                            if link["expected_url"] in current_url:
                                print(f"✅ {link['text']} navigation works")
                                self.results.append({"test": f"nav_{link['text']}", "success": True})
                            else:
                                print(f"❌ {link['text']} navigation failed - wrong URL")
                                self.results.append({"test": f"nav_{link['text']}", "success": False})
                        else:
                            print(f"⚠️  {link['text']} link not found in navigation")
                            self.results.append({"test": f"nav_{link['text']}", "success": False, "error": "Link not found"})
                    except Exception as e:
                        print(f"❌ {link['text']} navigation error: {e}")
                        self.results.append({"test": f"nav_{link['text']}", "success": False, "error": str(e)})
                
                # Test user menu
                print("\n📌 Testing User Menu:")
                
                # Look for user menu button (usually an avatar or user icon)
                user_menu_selectors = [
                    'button[aria-label*="user"]',
                    'button[aria-label*="account"]',
                    'button[aria-label*="menu"]',
                    '#user-menu-button',
                    'button:has-text("Admin")',
                    '[data-testid="user-menu"]',
                    'button svg[data-testid="PersonIcon"]',
                    'button:has(svg)'
                ]
                
                user_menu_found = False
                for selector in user_menu_selectors:
                    user_menu = await page.query_selector(selector)
                    if user_menu:
                        try:
                            await user_menu.click()
                            await asyncio.sleep(0.5)  # Wait for menu to open
                            
                            # Check if logout option exists
                            logout_option = await page.query_selector('text=Logout')
                            if logout_option:
                                print("✅ User menu opens and logout option found")
                                user_menu_found = True
                                self.results.append({"test": "user_menu", "success": True})
                                
                                # Test logout
                                await logout_option.click()
                                await page.wait_for_url(f"{self.base_url}/login", timeout=5000)
                                print("✅ Logout functionality works")
                                self.results.append({"test": "logout", "success": True})
                                break
                        except:
                            # Try next selector
                            continue
                
                if not user_menu_found:
                    print("❌ User menu not found or not functional")
                    self.results.append({"test": "user_menu", "success": False})
                    self.results.append({"test": "logout", "success": False, "error": "User menu not found"})
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
                self.results.append({"test": "general", "success": False, "error": str(e)})
            
            finally:
                # Close browser
                await browser.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Summary:")
        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r.get("success", False))
        
        print(f"  Total tests: {total_tests}")
        print(f"  ✅ Successful: {successful}")
        print(f"  ❌ Failed: {total_tests - successful}")
        
        if successful == total_tests:
            print("\n✅ All navigation and menu tests passed!")
        else:
            print("\n❌ Some tests failed - review results above")
        
        # Save results
        with open("test_results/navigation_test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": total_tests,
                    "successful": successful,
                    "failed": total_tests - successful
                },
                "results": self.results
            }, f, indent=2)
        
        print("\n💾 Results saved to: test_results/navigation_test_results.json")

async def main():
    tester = NavigationTester()
    await tester.test_navigation_and_menu()

if __name__ == "__main__":
    asyncio.run(main())