#!/usr/bin/env python3
"""Test if the pages are fixed after database migration."""
import asyncio
from playwright.async_api import async_playwright
import requests

async def test_fixed_pages():
    """Test if pages are working after fixes."""
    
    # First test the API endpoints directly
    print("Testing API endpoints directly...")
    
    # Login first
    login_data = {"username": "tester@example.com", "password": "password123"}
    login_resp = requests.post("http://localhost:8001/api/v1/auth/login", data=login_data)
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        
        # Test endpoints
        endpoints = [
            "/api/v1/sample-selection/9/reports/156/sample-sets",
            "/api/v1/request-info/cycles/9/reports/156/request-info-phase",
            "/api/v1/test-execution/9/reports/156/submitted-test-cases",
        ]
        
        for endpoint in endpoints:
            resp = requests.get(f"http://localhost:8001{endpoint}", headers=headers)
            print(f"\n{endpoint}:")
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  ✅ Success - Data returned")
            else:
                print(f"  ❌ Error: {resp.text[:200]}")
    
    # Now test the frontend
    print("\n\nTesting frontend pages...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Login
        await page.goto("http://localhost:3001/login")
        await page.fill('input[name="email"]', "tester@example.com")
        await page.fill('input[name="password"]', "password123")
        
        # Force click
        await page.evaluate("""
            const overlay = document.querySelector('#webpack-dev-server-client-overlay');
            if (overlay) overlay.remove();
            const button = document.querySelector('button[type="submit"]');
            if (button) button.click();
        """)
        
        await page.wait_for_timeout(3000)
        
        # Test pages
        test_pages = [
            ("/cycles/9/reports/156/sample-selection", "Sample Selection"),
            ("/cycles/9/reports/156/request-info", "Request for Information"),
            ("/cycles/9/reports/156/test-execution", "Test Execution"),
        ]
        
        for url, expected_title in test_pages:
            print(f"\nTesting {url}...")
            
            # Collect errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            
            await page.goto(f"http://localhost:3001{url}", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            # Check for data
            has_title = await page.locator(f'text=/{expected_title}/').count() > 0
            has_table = await page.locator('table').count() > 0
            has_cards = await page.locator('.MuiCard-root').count() > 2
            has_error = await page.locator('text=/Failed|Error/i').count() > 0
            
            if has_title and (has_table or has_cards) and not has_error:
                print(f"  ✅ Page loaded successfully")
            else:
                print(f"  ❌ Page has issues:")
                print(f"     Title found: {has_title}")
                print(f"     Has table: {has_table}")
                print(f"     Has cards: {has_cards}")
                print(f"     Has errors: {has_error}")
                if console_errors:
                    print(f"     Console errors: {len(console_errors)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_fixed_pages())