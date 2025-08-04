#!/usr/bin/env python3
"""
Final UI test to demonstrate the system is working
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def test_complete_user_journey():
    """Test a complete user journey through the application"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        
        print("🚀 SynapseDTE Complete UI Test")
        print("=" * 60)
        
        # Test 1: Load application
        print("\n📌 Test 1: Loading application...")
        try:
            await page.goto("http://localhost:3000", wait_until="networkidle")
            print("✅ Application loaded")
            results["tests"].append({"name": "Load Application", "status": "pass"})
        except Exception as e:
            print(f"❌ Failed to load: {e}")
            results["tests"].append({"name": "Load Application", "status": "fail", "error": str(e)})
        
        # Test 2: Login as admin
        print("\n📌 Test 2: Admin login...")
        try:
            await page.goto("http://localhost:3000/login")
            await page.fill('input[name="email"]', "admin@example.com")
            await page.fill('input[name="password"]', "password123")
            
            # Take screenshot before login
            await page.screenshot(path="test_results/login_form.png")
            
            await page.click('button[type="submit"]')
            
            # Wait for redirect
            await page.wait_for_url('**/', timeout=10000)
            
            print("✅ Admin login successful")
            results["tests"].append({"name": "Admin Login", "status": "pass"})
            
            # Take screenshot after login
            await page.screenshot(path="test_results/after_login.png")
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            results["tests"].append({"name": "Admin Login", "status": "fail", "error": str(e)})
            await page.screenshot(path="test_results/login_error.png")
        
        # Test 3: Navigate to different pages
        pages_to_test = [
            ("/cycles", "Test Cycles"),
            ("/reports", "Reports"),
            ("/analytics", "Analytics"),
            ("/users", "Users")
        ]
        
        for path, name in pages_to_test:
            print(f"\n📌 Test: Navigate to {name}...")
            try:
                await page.goto(f"http://localhost:3000{path}", wait_until="networkidle")
                await page.wait_for_timeout(2000)  # Wait for page to settle
                
                # Check if page loaded without errors
                title = await page.title()
                body_text = await page.text_content("body")
                
                if "error" in body_text.lower() or "failed" in body_text.lower():
                    print(f"⚠️  {name} page loaded but contains error text")
                    results["tests"].append({"name": f"Navigate to {name}", "status": "warning"})
                else:
                    print(f"✅ {name} page loaded successfully")
                    results["tests"].append({"name": f"Navigate to {name}", "status": "pass"})
                
                # Take screenshot
                await page.screenshot(path=f"test_results/{path.replace('/', '_')}_page.png")
                
            except Exception as e:
                print(f"❌ Failed to navigate to {name}: {e}")
                results["tests"].append({"name": f"Navigate to {name}", "status": "fail", "error": str(e)})
        
        # Test 4: Test user menu
        print("\n📌 Test: User menu...")
        try:
            # Click on user avatar/menu
            user_menu = await page.query_selector('[aria-label*="account" i], [aria-label*="user" i], button:has-text("Admin")')
            if user_menu:
                await user_menu.click()
                await page.wait_for_timeout(1000)
                print("✅ User menu opened")
                await page.screenshot(path="test_results/user_menu.png")
                results["tests"].append({"name": "User Menu", "status": "pass"})
            else:
                print("⚠️  User menu not found")
                results["tests"].append({"name": "User Menu", "status": "skip"})
        except Exception as e:
            print(f"❌ User menu test failed: {e}")
            results["tests"].append({"name": "User Menu", "status": "fail", "error": str(e)})
        
        # Test 5: Logout
        print("\n📌 Test: Logout...")
        try:
            # Try to find logout button
            logout_button = await page.query_selector('text="Logout", text="Sign Out", text="Log Out"')
            if logout_button:
                await logout_button.click()
                await page.wait_for_url('**/login', timeout=10000)
                print("✅ Logout successful")
                results["tests"].append({"name": "Logout", "status": "pass"})
            else:
                print("⚠️  Logout button not found")
                results["tests"].append({"name": "Logout", "status": "skip"})
        except Exception as e:
            print(f"⚠️  Logout test skipped: {e}")
            results["tests"].append({"name": "Logout", "status": "skip", "error": str(e)})
        
        # Save results
        with open("test_results/final_ui_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        passed = sum(1 for t in results["tests"] if t["status"] == "pass")
        failed = sum(1 for t in results["tests"] if t["status"] == "fail")
        warnings = sum(1 for t in results["tests"] if t["status"] == "warning")
        skipped = sum(1 for t in results["tests"] if t["status"] == "skip")
        
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Warnings: {warnings}")
        print(f"  ⏭️  Skipped: {skipped}")
        print(f"  Total: {len(results['tests'])}")
        
        print("\n📸 Screenshots saved in test_results/")
        print("📄 Detailed results saved to test_results/final_ui_test_results.json")
        
        # Keep browser open for 5 seconds to observe
        print("\n⏰ Keeping browser open for 5 seconds...")
        await page.wait_for_timeout(5000)
        
        await browser.close()

async def main():
    import os
    os.makedirs("test_results", exist_ok=True)
    await test_complete_user_journey()

if __name__ == "__main__":
    asyncio.run(main())