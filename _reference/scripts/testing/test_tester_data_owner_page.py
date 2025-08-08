#!/usr/bin/env python3
"""Test Tester's data owner page"""

from playwright.sync_api import sync_playwright
import time

def test_tester_data_owner_page():
    """Test tester's view of data owner page"""
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
            
            # Wait for navigation - testers go to tester-dashboard
            page.wait_for_url("**/tester-dashboard", timeout=10000)
            print("3. Successfully logged in to tester dashboard")
            
            # Navigate to cycles
            print("4. Navigating to cycles...")
            page.click("text=Test Cycles")
            page.wait_for_load_state("networkidle")
            
            # Click on a cycle
            print("5. Clicking on Test Cycle - Q2.2 2025...")
            page.click("text=Test Cycle - Q2.2 2025")
            page.wait_for_load_state("networkidle")
            
            # Click on a report
            print("6. Clicking on a report...")
            # Look for "Loan Summary Report" or similar
            report_link = page.locator("a").filter(has_text="Loan Summary Report").first
            if report_link.count() > 0:
                report_link.click()
            else:
                # Try alternative
                page.locator("tr").filter(has_text="report").locator("a").first.click()
            
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Navigate to data owner phase
            print("7. Navigating to Data Owner ID phase...")
            if page.locator("text=Data Owner ID").count() > 0:
                page.click("text=Data Owner ID")
            elif page.locator("text=Data Provider ID").count() > 0:
                page.click("text=Data Provider ID")
            else:
                print("❌ Data Owner/Provider ID phase link not found")
                
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Check for content
            print("8. Checking page content...")
            
            # Check if error message is shown
            if page.locator("text=failed to load phase status").count() > 0:
                print("❌ Error: Failed to load phase status")
                page.screenshot(path="tester_data_owner_error.png")
            else:
                print("✅ Page loaded successfully")
                
                # Check for content
                if page.locator("text=Data Provider Identification").count() > 0:
                    print("✅ Data Provider Identification title found")
                    
                if page.locator("text=Assignment Matrix").count() > 0:
                    print("✅ Assignment Matrix section found")
                    
                if page.locator("text=Primary Key Attributes").count() > 0:
                    print("✅ Primary Key Attributes section found")
                    
                if page.locator("text=Non-Primary Key Attributes").count() > 0:
                    print("✅ Non-Primary Key Attributes section found")
                    
                page.screenshot(path="tester_data_owner_success.png")
                print("✅ Screenshot saved as tester_data_owner_success.png")
            
            print("\n✅ Test completed!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="tester_error_screenshot.png")
            print("Error screenshot saved as tester_error_screenshot.png")
            raise
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    print("Testing Tester's Data Owner Page...")
    test_tester_data_owner_page()