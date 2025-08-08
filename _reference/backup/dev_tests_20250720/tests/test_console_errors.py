#!/usr/bin/env python3
"""
Test for console errors and warnings on all pages
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

# Test users for each role
TEST_USERS = {
    "admin": {"email": "admin@example.com", "password": "NewPassword123!"},
}

class ConsoleErrorTester:
    def __init__(self):
        self.results = []
        self.base_url = "http://localhost:3000"
        
    async def test_login(self, page, role, credentials):
        """Test login for a specific role"""
        try:
            await page.goto(f"{self.base_url}/login")
            await page.wait_for_load_state("networkidle")
            
            # Fill login form
            await page.fill('input[name="email"]', credentials["email"])
            await page.fill('input[name="password"]', credentials["password"])
            
            # Click login button
            await page.click('button[type="submit"]')
            
            # Wait for navigation to any dashboard
            await page.wait_for_function(
                f"url => window.location.href !== '{self.base_url}/login'",
                timeout=10000
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    async def test_pages_for_errors(self):
        """Test common pages for console errors"""
        print("🧪 Testing for Console Errors")
        print("=" * 60)
        
        pages_to_test = [
            "/dashboard",
            "/cycles",
            "/reports",
            "/users",
            "/admin/rbac",
            "/phases/planning",
            "/phases/testing-execution"
        ]
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Collect console messages
            console_messages = []
            
            def handle_console(msg):
                if msg.type in ["error", "warning"]:
                    console_messages.append({
                        "type": msg.type,
                        "text": msg.text,
                        "location": msg.location if hasattr(msg, 'location') else None,
                        "url": page.url
                    })
            
            page.on("console", handle_console)
            
            # Login first
            if await self.test_login(page, "admin", TEST_USERS["admin"]):
                print("✅ Login successful\n")
                
                # Test each page
                for path in pages_to_test:
                    full_url = f"{self.base_url}{path}"
                    console_messages.clear()  # Clear previous messages
                    
                    try:
                        response = await page.goto(full_url)
                        await page.wait_for_load_state("networkidle", timeout=10000)
                        
                        # Wait a bit for any async errors
                        await asyncio.sleep(1)
                        
                        errors = [m for m in console_messages if m["type"] == "error"]
                        warnings = [m for m in console_messages if m["type"] == "warning"]
                        
                        if len(errors) == 0 and len(warnings) == 0:
                            print(f"✅ {path} - No console errors or warnings")
                        else:
                            print(f"❌ {path} - {len(errors)} errors, {len(warnings)} warnings")
                            for error in errors:
                                print(f"   ERROR: {error['text']}")
                            for warning in warnings:
                                print(f"   WARNING: {warning['text']}")
                        
                        self.results.append({
                            "path": path,
                            "errors": errors,
                            "warnings": warnings,
                            "success": len(errors) == 0
                        })
                        
                    except Exception as e:
                        print(f"❌ {path} - Failed to load: {e}")
                        self.results.append({
                            "path": path,
                            "error": str(e),
                            "success": False
                        })
            
            # Close browser
            await browser.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Summary:")
        total_pages = len(self.results)
        pages_with_errors = sum(1 for r in self.results if not r.get("success", False))
        total_errors = sum(len(r.get("errors", [])) for r in self.results)
        total_warnings = sum(len(r.get("warnings", [])) for r in self.results)
        
        print(f"  Pages tested: {total_pages}")
        print(f"  Pages with errors: {pages_with_errors}")
        print(f"  Total console errors: {total_errors}")
        print(f"  Total console warnings: {total_warnings}")
        
        if total_errors == 0:
            print("\n✅ No console errors found!")
        else:
            print("\n❌ Console errors need to be fixed")
        
        # Save results
        with open("test_results/console_error_test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "pages_tested": total_pages,
                    "pages_with_errors": pages_with_errors,
                    "total_errors": total_errors,
                    "total_warnings": total_warnings
                },
                "results": self.results
            }, f, indent=2)
        
        print("\n💾 Results saved to: test_results/console_error_test_results.json")

async def main():
    tester = ConsoleErrorTester()
    await tester.test_pages_for_errors()

if __name__ == "__main__":
    asyncio.run(main())