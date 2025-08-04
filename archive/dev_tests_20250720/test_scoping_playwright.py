import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def test_scoping_page():
    print("Starting Playwright test for scoping page...")
    
    async with async_playwright() as p:
        # Launch browser with devtools open to capture console and network
        browser = await p.chromium.launch(
            headless=False,  # Set to False to see the browser
            devtools=True
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console message logging
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }))
        
        # Enable request/response logging
        network_logs = []
        
        def log_request(request):
            if 'api' in request.url:
                network_logs.append({
                    "type": "request",
                    "url": request.url,
                    "method": request.method,
                    "headers": request.headers,
                    "timestamp": datetime.now().isoformat()
                })
        
        def log_response(response):
            if 'api' in response.url:
                network_logs.append({
                    "type": "response",
                    "url": response.url,
                    "status": response.status,
                    "headers": response.headers,
                    "timestamp": datetime.now().isoformat()
                })
        
        page.on("request", log_request)
        page.on("response", log_response)
        
        try:
            # Step 1: Navigate to login page
            print("\n1. Navigating to login page...")
            await page.goto("http://localhost:3000/login")
            await page.wait_for_load_state("networkidle")
            
            # Step 2: Login
            print("2. Logging in...")
            await page.fill('input[type="email"]', 'tester@example.com')
            await page.fill('input[type="password"]', 'password123')
            await page.click('button[type="submit"]')
            
            # Wait for navigation after login
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)  # Give time for any redirects
            
            # Step 3: Navigate to scoping page
            print("3. Navigating to scoping page...")
            await page.goto("http://localhost:3000/cycles/54/reports/156/scoping")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)  # Give time for API calls
            
            # Step 4: Take screenshot
            print("4. Taking screenshot...")
            screenshot_path = f"/Users/dineshpatel/code/projects/SynapseDTE/scoping_page_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"   Screenshot saved to: {screenshot_path}")
            
            # Step 5: Get page content
            print("\n5. Checking page content...")
            page_title = await page.title()
            print(f"   Page title: {page_title}")
            
            # Check for specific elements
            has_loading = await page.locator('.loading').count() > 0
            has_error = await page.locator('.error').count() > 0
            has_attributes = await page.locator('[data-testid="attribute-row"], .attribute-row, tr').count() > 0
            
            print(f"   Has loading indicator: {has_loading}")
            print(f"   Has error message: {has_error}")
            print(f"   Has attribute rows: {has_attributes}")
            
            # Get any visible text content
            body_text = await page.locator('body').inner_text()
            if "no attributes" in body_text.lower() or "no data" in body_text.lower():
                print("   ⚠️  Page contains 'no attributes' or 'no data' message")
            
            # Step 6: Analyze console messages
            print("\n6. Console messages:")
            error_count = 0
            for msg in console_messages:
                if msg["type"] == "error":
                    error_count += 1
                    print(f"   ❌ ERROR: {msg['text']}")
                    if msg["location"]:
                        print(f"      Location: {msg['location']}")
                elif msg["type"] == "warning":
                    print(f"   ⚠️  WARNING: {msg['text']}")
            
            if error_count == 0:
                print("   ✅ No console errors found")
            
            # Step 7: Analyze network logs
            print("\n7. API calls:")
            api_calls = [log for log in network_logs if log["type"] == "request" and "/api/" in log["url"]]
            for call in api_calls:
                print(f"   {call['method']} {call['url']}")
                
                # Find corresponding response
                response = next((r for r in network_logs if r["type"] == "response" and r["url"] == call["url"]), None)
                if response:
                    print(f"     Response Status: {response['status']}")
                    
                    # Try to get response body for attributes endpoint
                    if "attributes" in call["url"] and response["status"] == 200:
                        try:
                            response_obj = await page.evaluate(f"""
                                fetch('{call['url']}', {{
                                    headers: {{
                                        'Authorization': localStorage.getItem('token') || sessionStorage.getItem('token') || ''
                                    }}
                                }}).then(r => r.json())
                            """)
                            print(f"     Response body: {json.dumps(response_obj, indent=2)[:500]}...")  # First 500 chars
                            if isinstance(response_obj, list):
                                print(f"     Number of attributes returned: {len(response_obj)}")
                        except Exception as e:
                            print(f"     Could not fetch response body: {e}")
            
            # Step 8: Check for specific UI elements
            print("\n8. Checking UI elements...")
            
            # Check for table or grid
            table_element = await page.locator('table, .ag-root, .data-grid').count()
            print(f"   Table/Grid elements found: {table_element}")
            
            # Check for any data rows
            data_rows = await page.locator('tbody tr, .ag-row, [role="row"]').count()
            print(f"   Data rows found: {data_rows}")
            
            # Get current URL
            current_url = page.url
            print(f"\n9. Current URL: {current_url}")
            
            # Additional debugging - get all text content
            print("\n10. Page text content (first 1000 chars):")
            print(body_text[:1000])
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Keep browser open for manual inspection
            print("\n\nTest complete. Browser will remain open for manual inspection.")
            print("Press Ctrl+C to close the browser and exit.")
            try:
                await asyncio.sleep(300)  # Keep open for 5 minutes
            except KeyboardInterrupt:
                print("\nClosing browser...")
            
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_scoping_page())