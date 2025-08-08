#!/usr/bin/env python3
"""
Simple page testing script - test login and basic page loads
"""

import asyncio
from playwright.async_api import async_playwright
import json

TEST_USERS = {
    "Admin": {"email": "admin@example.com", "password": "password123"},
    "Test Executive": {"email": "test.manager@example.com", "password": "password123"},
    "Tester": {"email": "tester@example.com", "password": "password123"},
    "Data Owner": {"email": "data.provider@example.com", "password": "password123"},
    "Data Executive": {"email": "cdo@example.com", "password": "password123"},
    "Report Owner": {"email": "report.owner@example.com", "password": "password123"},
    "Report Owner Executive": {"email": "report_owner_executive@example.com", "password": "password123"}
}

# Critical pages to test
CRITICAL_PAGES = [
    ("/dashboard", "Dashboard"),
    ("/phases/planning", "Planning Phase"),
    ("/phases/scoping", "Scoping Phase"),
    ("/phases/data-provider-identification", "Data Provider ID"),
    ("/phases/sample-selection", "Sample Selection"),
    ("/phases/request-information", "Request Info"),
    ("/phases/test-execution", "Test Execution"),
    ("/phases/observation-management", "Observations")
]

async def test_login_and_pages():
    """Test login and basic page access"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        
        results = {}
        
        for role, creds in TEST_USERS.items():
            print(f"\n{'='*50}")
            print(f"Testing: {role}")
            print(f"Email: {creds['email']}")
            print(f"{'='*50}")
            
            context = await browser.new_context()
            page = await context.new_page()
            
            # Monitor console errors
            console_errors = []
            page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
            
            try:
                # Login
                print("1. Testing login...")
                await page.goto('http://localhost:3000/login')
                await page.fill('input[name="email"]', creds['email'])
                await page.fill('input[name="password"]', creds['password'])
                await page.click('button[type="submit"]')
                
                # Wait for navigation
                try:
                    await page.wait_for_url(lambda url: '/login' not in url, timeout=5000)
                    print("   ✅ Login successful")
                except:
                    print("   ❌ Login failed")
                    await context.close()
                    continue
                
                # Test pages
                page_results = []
                for path, name in CRITICAL_PAGES:
                    print(f"\n2. Testing {name} ({path})...")
                    
                    try:
                        await page.goto(f'http://localhost:3000{path}')
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        
                        # Check if redirected
                        current_url = page.url
                        if path not in current_url:
                            print(f"   ⚠️  Redirected to: {current_url}")
                        else:
                            print(f"   ✅ Page loaded")
                        
                        # Check for data
                        tables = await page.locator('table').count()
                        buttons = await page.locator('button').count()
                        print(f"   📊 Found {tables} tables, {buttons} buttons")
                        
                        if console_errors:
                            print(f"   ⚠️  {len(console_errors)} console errors")
                            for err in console_errors[-3:]:  # Show last 3
                                print(f"      - {err[:100]}...")
                        
                        page_results.append({
                            'page': name,
                            'success': True,
                            'errors': len(console_errors)
                        })
                        
                    except Exception as e:
                        print(f"   ❌ Error: {str(e)}")
                        page_results.append({
                            'page': name,
                            'success': False,
                            'error': str(e)
                        })
                    
                    console_errors.clear()
                
                results[role] = page_results
                
            except Exception as e:
                print(f"   ❌ Role test failed: {str(e)}")
                results[role] = {'error': str(e)}
            
            await context.close()
            
            # Pause between roles
            await asyncio.sleep(2)
        
        await browser.close()
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        for role, role_results in results.items():
            if isinstance(role_results, dict) and 'error' in role_results:
                print(f"\n{role}: ❌ Failed - {role_results['error']}")
            else:
                success_count = sum(1 for r in role_results if r['success'])
                print(f"\n{role}: {success_count}/{len(role_results)} pages loaded")
                
                failures = [r for r in role_results if not r['success']]
                if failures:
                    print("  Failed pages:")
                    for f in failures:
                        print(f"    - {f['page']}")

if __name__ == "__main__":
    asyncio.run(test_login_and_pages())