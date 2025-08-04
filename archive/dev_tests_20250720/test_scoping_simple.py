import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def test_scoping_page():
    print("Starting simplified Playwright test for scoping page...")
    
    async with async_playwright() as p:
        # Launch browser in headless mode first
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console message logging
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text
        }))
        
        # Enable request/response logging for API calls
        api_calls = []
        
        async def handle_response(response):
            if '/api/' in response.url and 'attributes' in response.url:
                try:
                    body = await response.text()
                    api_calls.append({
                        "url": response.url,
                        "status": response.status,
                        "body": body[:1000]  # First 1000 chars
                    })
                except:
                    api_calls.append({
                        "url": response.url,
                        "status": response.status,
                        "body": "Could not read body"
                    })
        
        page.on("response", handle_response)
        
        try:
            # Step 1: Navigate to login page
            print("\n1. Navigating to login page...")
            response = await page.goto("http://localhost:3000/login", wait_until="networkidle")
            print(f"   Status: {response.status if response else 'No response'}")
            
            # Wait a bit and check what's on the page
            await page.wait_for_timeout(2000)
            
            # Try multiple selectors for email field
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email" i]',
                'input[id*="email" i]',
                '#email'
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        print(f"   Found email field with selector: {selector}")
                        await page.fill(selector, 'tester@example.com')
                        email_filled = True
                        break
                except:
                    continue
            
            if not email_filled:
                print("   ❌ Could not find email field!")
                # Take screenshot to see what's on the page
                await page.screenshot(path="login_page_debug.png")
                print("   Screenshot saved as login_page_debug.png")
                return
            
            # Try multiple selectors for password field
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password" i]',
                'input[id*="password" i]',
                '#password'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        print(f"   Found password field with selector: {selector}")
                        await page.fill(selector, 'password123')
                        password_filled = True
                        break
                except:
                    continue
            
            if not password_filled:
                print("   ❌ Could not find password field!")
                return
            
            # Try multiple selectors for submit button
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'input[type="submit"]',
                'button.login-button'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        print(f"   Found submit button with selector: {selector}")
                        await page.click(selector)
                        submitted = True
                        break
                except:
                    continue
            
            if not submitted:
                print("   ❌ Could not find submit button!")
                return
            
            # Wait for navigation
            print("   Waiting for login to complete...")
            await page.wait_for_timeout(3000)
            
            # Step 2: Navigate directly to scoping page
            print("\n2. Navigating to scoping page...")
            await page.goto("http://localhost:3000/cycles/54/reports/156/scoping", wait_until="networkidle")
            await page.wait_for_timeout(5000)  # Give time for API calls
            
            # Step 3: Take screenshot
            print("\n3. Taking screenshot...")
            screenshot_path = f"scoping_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"   Screenshot saved to: {screenshot_path}")
            
            # Step 4: Check console errors
            print("\n4. Console messages:")
            errors = [msg for msg in console_messages if msg["type"] == "error"]
            if errors:
                for error in errors:
                    print(f"   ❌ ERROR: {error['text']}")
            else:
                print("   ✅ No console errors")
            
            # Step 5: Check API calls
            print("\n5. API calls to attributes endpoint:")
            if api_calls:
                for call in api_calls:
                    print(f"   URL: {call['url']}")
                    print(f"   Status: {call['status']}")
                    print(f"   Response preview: {call['body'][:200]}...")
                    
                    # Try to parse as JSON
                    try:
                        data = json.loads(call['body'])
                        if isinstance(data, list):
                            print(f"   Number of items: {len(data)}")
                        elif isinstance(data, dict):
                            print(f"   Response keys: {list(data.keys())}")
                    except:
                        print("   Could not parse as JSON")
            else:
                print("   No API calls to attributes endpoint captured")
            
            # Step 6: Check page content
            print("\n6. Page content check:")
            
            # Check for any visible text about "no attributes"
            page_text = await page.locator('body').inner_text()
            if "no attributes" in page_text.lower():
                print("   ⚠️  Page shows 'no attributes' message")
            
            # Count table rows or grid items
            row_selectors = [
                'table tbody tr',
                '.ag-row',
                '[role="row"]',
                '.attribute-row',
                '[data-testid*="attribute"]'
            ]
            
            total_rows = 0
            for selector in row_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"   Found {count} rows with selector: {selector}")
                    total_rows += count
            
            if total_rows == 0:
                print("   ❌ No data rows found on page")
            else:
                print(f"   ✅ Total data rows found: {total_rows}")
            
            # Get current URL
            print(f"\n7. Current URL: {page.url}")
            
            # Check localStorage for token
            token = await page.evaluate("localStorage.getItem('token') || sessionStorage.getItem('token') || 'No token found'")
            print(f"\n8. Auth token present: {'Yes' if token != 'No token found' else 'No'}")
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
            
            # Take error screenshot
            try:
                await page.screenshot(path="error_screenshot.png")
                print("Error screenshot saved as error_screenshot.png")
            except:
                pass
            
        finally:
            await browser.close()
            print("\nTest complete.")

if __name__ == "__main__":
    asyncio.run(test_scoping_page())