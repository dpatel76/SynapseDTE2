#!/usr/bin/env python3
"""Test Data Executive assignment interface"""

from playwright.sync_api import sync_playwright
import time

def test_data_executive_assignment():
    """Test Data Executive can assign data providers"""
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
            print("3. Successfully logged in")
            
            # Wait for dashboard to load
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            print("4. Looking for assignment buttons...")
            # Click on View Details for an assignment
            view_details_buttons = page.locator("button:has-text('View Details')")
            if view_details_buttons.count() > 0:
                print(f"   Found {view_details_buttons.count()} assignment(s)")
                view_details_buttons.first.click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                
                # Check if we're on the assignment interface
                print("5. Checking assignment interface...")
                if page.locator("text=Pending Assignments").count() > 0:
                    print("✅ Assignment interface loaded")
                    
                    # Look for Product Type
                    if page.locator("text=Product Type").count() > 0:
                        print("✅ Product Type attribute found in pending assignments!")
                        
                        # Check if there are data providers to select
                        select_elements = page.locator("text=Select Data Owner")
                        if select_elements.count() > 0:
                            print(f"✅ Found {select_elements.count()} dropdown(s) for data owner selection")
                            
                            # Take screenshot
                            page.screenshot(path="data_executive_assignment_interface.png")
                            print("✅ Screenshot saved as data_executive_assignment_interface.png")
                            
                            # Try to click the first dropdown
                            select_elements.first.click()
                            time.sleep(1)
                            
                            # Check if dropdown opened and has options
                            menu_items = page.locator("li[role='option']")
                            if menu_items.count() > 0:
                                print(f"✅ Found {menu_items.count()} data providers available")
                                # Close dropdown
                                page.keyboard.press("Escape")
                            else:
                                print("❌ No data providers found in dropdown")
                        else:
                            print("❌ No data owner selection dropdowns found")
                    else:
                        print("❌ Product Type not found in pending assignments")
                        
                        # Debug: Check what attributes are shown
                        attribute_cells = page.locator("td").filter(has_text="Type")
                        if attribute_cells.count() > 0:
                            print(f"   Found attributes with 'Type' in name: {attribute_cells.count()}")
                else:
                    print("❌ Assignment interface not loaded properly")
                    page.screenshot(path="assignment_interface_error.png")
            else:
                print("❌ No assignment View Details buttons found")
                page.screenshot(path="cdo_dashboard_no_assignments.png")
            
            print("\n✅ Test completed!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="data_executive_test_error.png")
            print("Error screenshot saved")
            raise
        finally:
            # Keep browser open for manual inspection
            input("Press Enter to close browser...")
            context.close()
            browser.close()

if __name__ == "__main__":
    print("Testing Data Executive Assignment Interface...")
    print("=" * 60)
    test_data_executive_assignment()