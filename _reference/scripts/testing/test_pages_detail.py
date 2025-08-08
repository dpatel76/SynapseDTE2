#!/usr/bin/env python3
"""
Test specific pages with detailed debugging
"""

import asyncio
import httpx
from playwright.async_api import async_playwright
import json

BASE_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"

async def test_pages():
    # Login as tester
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "tester@example.com", "password": "password123"}
        )
        login_data = response.json()
        token = login_data["access_token"]
        print(f"✅ Logged in as tester")
    
    # Test with browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Add auth token to all requests
        await context.add_init_script(f"""
            window.localStorage.setItem('access_token', '{token}');
            window.localStorage.setItem('user', JSON.stringify({json.dumps(login_data['user'])}));
        """)
        
        page = await context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"[Console {msg.type}] {msg.text}"))
        
        # Monitor API calls
        page.on("request", lambda request: print(f"[API Request] {request.method} {request.url}") if 'api' in request.url else None)
        page.on("response", lambda response: print(f"[API Response] {response.status} {response.url}") if 'api' in response.url else None)
        
        # Test observation management page
        print("\n📍 Testing Observation Management Page...")
        await page.goto(f"{FRONTEND_URL}/cycles/9/reports/156/observation-management")
        await page.wait_for_timeout(3000)
        
        # Check for mock data indicator
        mock_elements = await page.query_selector_all('text=/mock/i')
        if mock_elements:
            print(f"⚠️  Found {len(mock_elements)} elements with 'mock' text")
        
        # Take screenshot
        await page.screenshot(path="observation_page_test.png")
        print("📸 Screenshot saved: observation_page_test.png")
        
        # Test test-execution page
        print("\n📍 Testing Test Execution Page...")
        await page.goto(f"{FRONTEND_URL}/cycles/9/reports/156/test-execution")
        await page.wait_for_timeout(3000)
        
        # Check for error messages
        error_elements = await page.query_selector_all('[class*="error"], [class*="Error"]')
        if error_elements:
            print(f"⚠️  Found {len(error_elements)} error elements")
            for elem in error_elements:
                text = await elem.text_content()
                if text:
                    print(f"   Error: {text}")
        
        await page.screenshot(path="test_execution_page_test.png")
        print("📸 Screenshot saved: test_execution_page_test.png")
        
        # Test request-info page  
        print("\n📍 Testing Request Info Page...")
        await page.goto(f"{FRONTEND_URL}/cycles/9/reports/156/request-info")
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path="request_info_page_test.png")
        print("📸 Screenshot saved: request_info_page_test.png")
        
        # Test data-owner page
        print("\n📍 Testing Data Owner Page...")
        await page.goto(f"{FRONTEND_URL}/cycles/9/reports/156/data-owner")
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path="data_owner_page_test.png")
        print("📸 Screenshot saved: data_owner_page_test.png")
        
        print("\n✅ Test complete. Browser will stay open for inspection.")
        await asyncio.sleep(300)  # Keep open for 5 minutes
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_pages())