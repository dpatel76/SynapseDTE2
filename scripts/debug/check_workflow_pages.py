#!/usr/bin/env python3
"""Check specific workflow pages for mock data and errors."""
import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def check_workflow_pages():
    """Check specific workflow pages for functionality and mock data."""
    pages_to_check = [
        "/cycles/9/reports/156/sample-selection",
        "/cycles/9/reports/156/data-provider-id", 
        "/cycles/9/reports/156/request-info",
        "/cycles/9/reports/156/test-execution",
        "/cycles/9/reports/156/observation-management"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Collect console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text,
            'location': msg.location
        }))
        
        # Collect network errors
        network_errors = []
        def log_response(response):
            if response.status >= 400:
                network_errors.append({
                    'url': response.url,
                    'status': response.status,
                    'method': response.request.method
                })
        page.on("response", log_response)
        
        results = []
        
        # Login as tester first
        print("Logging in as tester...")
        await page.goto("http://localhost:3001/login")
        await page.wait_for_load_state("networkidle")
        
        # Remove webpack overlay if present
        await page.evaluate("""
            const overlay = document.querySelector('#webpack-dev-server-client-overlay');
            if (overlay) overlay.remove();
        """)
        
        # Fill login form
        await page.fill('input[name="email"]', "tester@synapse.com")
        await page.fill('input[name="password"]', "TestUser123!")
        
        # Force click with JavaScript if normal click fails
        try:
            await page.click('button[type="submit"]', timeout=2000)
        except:
            await page.evaluate("""
                const button = document.querySelector('button[type="submit"]');
                if (button) button.click();
            """)
        
        # Wait for navigation - could be dashboard or tester-dashboard
        try:
            await page.wait_for_url("**/dashboard", timeout=5000)
        except:
            await page.wait_for_url("**/tester-dashboard", timeout=5000)
        print("Login successful!")
        
        # Check each page
        for page_url in pages_to_check:
            console_messages.clear()
            network_errors.clear()
            
            print(f"\nChecking {page_url}...")
            full_url = f"http://localhost:3001{page_url}"
            
            try:
                await page.goto(full_url)
                await page.wait_for_load_state("networkidle", timeout=10000)
                
                # Take screenshot
                screenshot_name = page_url.replace("/", "_") + ".png"
                await page.screenshot(path=f"workflow_check{screenshot_name}")
                
                # Check for visible content
                content_check = {
                    'has_loading': await page.locator('text="Loading"').count() > 0,
                    'has_error': await page.locator('text="Error"').count() > 0,
                    'has_no_data': await page.locator('text="No data"').count() > 0,
                    'has_table': await page.locator('table').count() > 0,
                    'has_cards': await page.locator('.MuiCard-root').count() > 0,
                }
                
                # Get page title or header
                page_title = await page.text_content('h4, h5, h6')
                
                # Check for specific mock data indicators
                mock_data_indicators = {
                    'sample-selection': await page.locator('text=/Sample Set|Sample Type|Selection Method/').count() > 0,
                    'data-provider-id': await page.locator('text=/Data Provider|Assignment|Escalation/').count() > 0,
                    'request-info': await page.locator('text=/Test Case|Submission|Evidence/').count() > 0,
                    'test-execution': await page.locator('text=/Test Execution|Test Results|Pass.*Fail/').count() > 0,
                    'observation-management': await page.locator('text=/Observation|Issue|Finding/').count() > 0,
                }
                
                # Get the console errors
                console_errors = [msg for msg in console_messages if msg['type'] == 'error']
                
                result = {
                    'url': page_url,
                    'page_title': page_title,
                    'content_check': content_check,
                    'has_mock_data': any(mock_data_indicators.values()),
                    'mock_data_details': mock_data_indicators,
                    'console_errors': len(console_errors),
                    'console_error_samples': console_errors[:3],
                    'network_errors': len(network_errors),
                    'network_error_samples': network_errors[:3],
                    'screenshot': screenshot_name
                }
                
                results.append(result)
                
                # Print immediate feedback
                print(f"  Title: {page_title}")
                print(f"  Content: {content_check}")
                print(f"  Mock data present: {result['has_mock_data']}")
                print(f"  Console errors: {len(console_errors)}")
                print(f"  Network errors: {len(network_errors)}")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
                results.append({
                    'url': page_url,
                    'error': str(e)
                })
        
        await browser.close()
        
        # Save results
        with open('workflow_pages_check.json', 'w') as f:
            json.dump({
                'check_date': datetime.now().isoformat(),
                'results': results
            }, f, indent=2)
        
        print("\n\nResults saved to workflow_pages_check.json")
        
        # Summary
        print("\n=== SUMMARY ===")
        for result in results:
            if 'error' in result:
                print(f"❌ {result['url']} - ERROR: {result['error']}")
            else:
                status = "✅" if result['has_mock_data'] and result['console_errors'] == 0 else "❌"
                print(f"{status} {result['url']}")
                print(f"   - Mock data: {result['has_mock_data']}")
                print(f"   - Console errors: {result['console_errors']}")
                print(f"   - Network errors: {result['network_errors']}")

if __name__ == "__main__":
    asyncio.run(check_workflow_pages())