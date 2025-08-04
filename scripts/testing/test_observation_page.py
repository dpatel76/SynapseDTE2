#!/usr/bin/env python3
"""Test Observation Management page"""

from playwright.sync_api import sync_playwright
import time

def test_observation_page():
    """Test observation management page with real data"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("1. Navigating to login page...")
            page.goto("http://localhost:3000/login")
            page.wait_for_load_state("networkidle")
            
            print("2. Logging in as Tester...")
            page.fill('input[name="email"]', "tester@example.com")
            page.fill('input[name="password"]', "password123")
            page.click('button[type="submit"]')
            
            # Wait for navigation
            page.wait_for_url("**/tester-dashboard", timeout=10000)
            print("3. Successfully logged in")
            
            # Navigate to cycles
            print("4. Navigating to cycles...")
            page.click("text=Test Cycles")
            page.wait_for_load_state("networkidle")
            
            # Click on a cycle
            print("5. Clicking on Test Cycle - Q2.2 2025...")
            page.click("text=Test Cycle - Q2.2 2025")
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            
            # Click on a report
            print("6. Clicking on a report...")
            # Try to find and click on a report
            report_rows = page.locator("tr").filter(has_text="Loan Summary Report")
            if report_rows.count() > 0:
                report_rows.first.locator("a").click()
            else:
                # Try alternative - click first report link
                page.locator("tbody tr").first.locator("a").click()
            
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Navigate to observation management phase
            print("7. Navigating to Observation Management phase...")
            page.click("text=Observation Management")
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # Check for content
            print("8. Checking page content...")
            
            # Check if the page is showing real data or mock data
            if page.locator("text=Observation Management Phase").count() > 0:
                print("✅ Observation Management Phase title found")
            
            # Check for phase status
            if page.locator("text=Phase Status").count() > 0:
                print("✅ Phase Status section found")
                
                # Check if showing loading spinner
                if page.locator(".MuiCircularProgress-root").count() > 0:
                    print("⏳ Page is loading data...")
                    page.wait_for_selector(".MuiCircularProgress-root", state="hidden", timeout=10000)
                    print("✅ Data loaded")
            
            # Check for observations
            if page.locator("text=Total Observations").count() > 0:
                print("✅ Total Observations metric found")
                # Get the value
                total_obs = page.locator("text=Total Observations").locator("..").locator("h4").text_content()
                print(f"   Total Observations: {total_obs}")
            
            # Check if mock data text is present
            if page.locator("text=Total Assets Calculation Logic").count() > 0:
                print("⚠️  WARNING: Page is still showing mock data")
                print("   Found mock observation: 'Total Assets Calculation Logic'")
            else:
                print("✅ No mock data found - page is using real data")
            
            # Check for observation cards or table
            if page.locator("text=Observation Status Summary").count() > 0:
                print("✅ Observation Status Summary found")
            
            # Take screenshot
            page.screenshot(path="observation_management_page.png")
            print("\n✅ Screenshot saved as observation_management_page.png")
            
            print("\n✅ Test completed!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="observation_error_screenshot.png")
            print("Error screenshot saved as observation_error_screenshot.png")
            raise
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    print("Testing Observation Management Page...")
    test_observation_page()