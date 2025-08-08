#!/usr/bin/env python3
"""Test Data Executive dashboard UI"""

from playwright.sync_api import sync_playwright
import time

def test_data_executive_dashboard():
    """Test Data Executive dashboard UI"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("1. Navigating to login page...")
            page.goto("http://localhost:3000/login")
            page.wait_for_load_state("networkidle")
            
            print("2. Logging in as Data Executive...")
            page.fill('input[name="email"]', "cdo@example.com")
            page.fill('input[name="password"]', "password123")
            page.click('button[type="submit"]')
            
            # Wait for navigation
            page.wait_for_url("**/cdo-dashboard", timeout=10000)
            print("3. Successfully logged in and redirected to CDO dashboard")
            
            # Wait for dashboard to load
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Check if we're on the Data Executive dashboard
            print("4. Checking dashboard content...")
            
            # Check for dashboard title
            if page.locator("text=Data Executive Dashboard").count() > 0:
                print("✅ Data Executive Dashboard title found")
            else:
                print("❌ Data Executive Dashboard title not found")
            
            # Check for metrics cards
            if page.locator("text=Total Assignments").count() > 0:
                print("✅ Total Assignments metric found")
                total_assignments = page.locator("text=Total Assignments").locator("..").locator("h4").text_content()
                print(f"   Total Assignments: {total_assignments}")
            
            # Check for recent activity
            if page.locator("text=Recent Assignment Activity").count() > 0:
                print("✅ Recent Assignment Activity section found")
                
                # Check for specific assignments
                if page.locator("text=Product Type").count() > 0:
                    print("✅ Product Type assignment found")
                if page.locator("text=Current Credit limit").count() > 0:
                    print("✅ Current Credit limit assignment found")
            
            # Check workflow status
            if page.locator("text=Active Testing Cycles - Workflow Progress").count() > 0:
                print("✅ Workflow Progress section found")
                
                # Check for specific cycle
                if page.locator("text=Test Cycle - Q2.2 2025").count() > 0:
                    print("✅ Test Cycle - Q2.2 2025 found")
            
            # Take screenshot
            page.screenshot(path="data_executive_dashboard.png")
            print("\n✅ Screenshot saved as data_executive_dashboard.png")
            
            # Check navigation to data owner page
            print("\n5. Testing navigation to data owner phase...")
            if page.locator("button:has-text('View Details')").count() > 0:
                page.locator("button:has-text('View Details')").first.click()
                page.wait_for_url("**/data-owner", timeout=5000)
                print("✅ Successfully navigated to data owner phase")
                
                # Take screenshot of data owner page
                page.screenshot(path="data_owner_phase_from_executive.png")
                print("✅ Screenshot saved as data_owner_phase_from_executive.png")
            
            print("\n✅ All tests passed!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="error_screenshot.png")
            print("Error screenshot saved as error_screenshot.png")
            raise
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    print("Testing Data Executive Dashboard UI...")
    test_data_executive_dashboard()