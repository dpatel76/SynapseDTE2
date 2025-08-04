#!/usr/bin/env python3
"""
Test all UI pages for each user role
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

# Test users for each role
TEST_USERS = {
    "admin": {"email": "admin@example.com", "password": "NewPassword123!"},
    "tester": {"email": "tester@example.com", "password": "password123"},
    "test_manager": {"email": "test.manager@example.com", "password": "password123"},
    "report_owner": {"email": "report.owner@example.com", "password": "password123"},
    "report_owner_executive": {"email": "report.owner.executive@example.com", "password": "password123"},
    "data_owner": {"email": "data.provider@example.com", "password": "password123"},
    "cdo": {"email": "cdo@example.com", "password": "password123"}
}

# Pages to test for each role
PAGES_BY_ROLE = {
    "admin": [
        "/dashboard",
        "/cycles",
        "/reports",
        "/users",
        "/admin/rbac",
        "/admin/sla-configurations"
    ],
    "tester": [
        "/tester-dashboard",
        "/cycles",
        "/phases/planning",
        "/phases/scoping",
        "/phases/sample-selection",
        "/phases/request-info",
        "/phases/testing-execution",
        "/phases/observation-management"
    ],
    "test_manager": [
        "/test-manager-dashboard",
        "/cycles",
        "/reports",
        "/phases/planning",
        "/phases/observation-management"
    ],
    "report_owner": [
        "/report-owner-dashboard",
        "/cycles",
        "/reports",
        "/phases/planning",
        "/phases/observation-management"
    ],
    "report_owner_executive": [
        "/report-owner-dashboard",
        "/reports",
        "/phases/observation-management"
    ],
    "data_owner": [
        "/data-owner-dashboard",
        "/phases/data-owner",
        "/phases/request-info"
    ],
    "cdo": [
        "/cdo-dashboard",
        "/phases/cdo-assignment"
    ]
}

class UIPageTester:
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
            dashboard_urls = [
                f"{self.base_url}/dashboard",
                f"{self.base_url}/tester-dashboard",
                f"{self.base_url}/test-manager-dashboard",
                f"{self.base_url}/report-owner-dashboard",
                f"{self.base_url}/data-owner-dashboard",
                f"{self.base_url}/cdo-dashboard",
                f"{self.base_url}/"  # Root redirect
            ]
            
            # Wait for any of the dashboard URLs
            await page.wait_for_function(
                f"url => {json.dumps(dashboard_urls)}.some(d => window.location.href.startsWith(d))",
                timeout=10000
            )
            
            print(f"✅ Login successful for {role}")
            return True
            
        except Exception as e:
            print(f"❌ Login failed for {role}: {e}")
            return False
    
    async def test_page(self, page, role, path):
        """Test a specific page"""
        full_url = f"{self.base_url}{path}"
        
        try:
            # Navigate to page
            response = await page.goto(full_url)
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Check response status
            status = response.status if response else 0
            
            # Check for error messages
            error_elements = await page.query_selector_all('.MuiAlert-root.MuiAlert-standardError')
            has_errors = len(error_elements) > 0
            
            # Check console errors
            console_errors = []
            
            # Take screenshot
            screenshot_path = f"test_results/screenshots/{role}_{path.replace('/', '_')}.png"
            await page.screenshot(path=screenshot_path)
            
            result = {
                "role": role,
                "path": path,
                "status": status,
                "success": status == 200 and not has_errors,
                "has_errors": has_errors,
                "screenshot": screenshot_path
            }
            
            if result["success"]:
                print(f"  ✅ {path}")
            else:
                print(f"  ❌ {path} - Status: {status}, Errors: {has_errors}")
            
            self.results.append(result)
            return result
            
        except Exception as e:
            print(f"  ❌ {path} - Error: {e}")
            self.results.append({
                "role": role,
                "path": path,
                "status": 0,
                "success": False,
                "error": str(e)
            })
            return None
    
    async def test_role(self, browser, role, credentials):
        """Test all pages for a specific role"""
        print(f"\n🧪 Testing {role.upper()} role")
        print("=" * 40)
        
        # Create new context for this role
        context = await browser.new_context()
        page = await context.new_page()
        
        # Listen for console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        
        # Login
        if await self.test_login(page, role, credentials):
            # Test each page
            pages = PAGES_BY_ROLE.get(role, [])
            for path in pages:
                await self.test_page(page, role, path)
                await asyncio.sleep(0.5)  # Brief pause between pages
        
        # Close context
        await context.close()
    
    async def run_all_tests(self):
        """Run all UI tests for all roles"""
        print("🧪 Testing All UI Pages for Each Role")
        print("=" * 60)
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            
            # Create screenshots directory
            import os
            os.makedirs("test_results/screenshots", exist_ok=True)
            
            # Test each role
            for role, credentials in TEST_USERS.items():
                await self.test_role(browser, role, credentials)
            
            # Close browser
            await browser.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        total = len(self.results)
        success = sum(1 for r in self.results if r.get("success", False))
        failed = total - success
        
        print(f"  Total Pages Tested: {total}")
        print(f"  ✅ Success: {success}")
        print(f"  ❌ Failed: {failed}")
        print(f"  Success Rate: {(success/total*100):.1f}%" if total > 0 else "N/A")
        
        # List failed pages by role
        if failed > 0:
            print("\n❌ Failed Pages:")
            for role in TEST_USERS.keys():
                role_failures = [r for r in self.results if r.get("role") == role and not r.get("success", False)]
                if role_failures:
                    print(f"\n  {role.upper()}:")
                    for r in role_failures:
                        print(f"    - {r['path']} (Status: {r.get('status', 'Error')})")
        
        # Save results
        with open("test_results/ui_page_test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "success": success,
                    "failed": failed,
                    "success_rate": f"{(success/total*100):.1f}%" if total > 0 else "N/A"
                },
                "results": self.results
            }, f, indent=2)
        
        print("\n💾 Detailed results saved to: test_results/ui_page_test_results.json")
        print("📸 Screenshots saved to: test_results/screenshots/")

async def main():
    tester = UIPageTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())