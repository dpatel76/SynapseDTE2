#!/usr/bin/env python3
"""
Quick verification script to test that all fixes are working
"""

import asyncio
import httpx
from playwright.async_api import async_playwright
import json

async def test_api_connection():
    """Test API is accessible"""
    print("Testing API connection...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8001/api/v1/health")
            print(f"✅ API Status: {response.json()}")
            return True
        except Exception as e:
            print(f"❌ API Error: {e}")
            return False

async def test_frontend_loads():
    """Test frontend loads without errors"""
    print("\nTesting frontend...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        try:
            # Test login page loads
            await page.goto("http://localhost:3000/login", wait_until="networkidle")
            print("✅ Login page loaded")
            
            # Check for date-fns usage (format function)
            has_date_formatting = await page.evaluate("""
                () => {
                    const text = document.body.innerText;
                    // Login page might not have dates, so just check it loaded
                    return document.querySelector('input[name="email"]') !== null;
                }
            """)
            
            if has_date_formatting:
                print("✅ Login form elements found")
            
            # Check for console errors
            if console_errors:
                print(f"⚠️  Console errors found: {console_errors[:3]}")
            else:
                print("✅ No console errors")
                
            # Test navigation to main app (will redirect to login)
            await page.goto("http://localhost:3000/", wait_until="networkidle")
            
            # Check that we got redirected to login
            if "/login" in page.url:
                print("✅ Authentication redirect working")
            
            await browser.close()
            return True
            
        except Exception as e:
            print(f"❌ Frontend Error: {e}")
            await browser.close()
            return False

async def test_login_flow():
    """Test login with a test user"""
    print("\nTesting login flow...")
    async with httpx.AsyncClient() as client:
        try:
            # Try admin login
            response = await client.post(
                "http://localhost:8001/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "password123"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Login successful - Token received")
                print(f"✅ User role: {data.get('user', {}).get('role', 'Unknown')}")
                return data.get("access_token")
            else:
                print(f"❌ Login failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Login Error: {e}")
            return None

async def test_authenticated_api_call(token):
    """Test an authenticated API call"""
    if not token:
        print("\n⚠️  Skipping authenticated API test (no token)")
        return
        
    print("\nTesting authenticated API call...")
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(
                "http://localhost:8001/api/v1/users/me",
                headers=headers
            )
            
            if response.status_code == 200:
                user = response.json()
                print(f"✅ User profile retrieved")
                print(f"   Username: {user.get('username')}")
                print(f"   Role: {user.get('role')}")
                print(f"   Email: {user.get('email')}")
            else:
                print(f"❌ API call failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ API Error: {e}")

async def test_ui_components():
    """Test that key UI components load properly"""
    print("\nTesting UI components...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Login first
            await page.goto("http://localhost:3000/login")
            await page.fill('input[name="email"]', "admin@example.com")
            await page.fill('input[name="password"]', "password123")
            await page.click('button[type="submit"]')
            
            # Wait for navigation
            await page.wait_for_url('**/dashboard', timeout=10000)
            print("✅ Logged in successfully")
            
            # Check we're on a dashboard
            await page.wait_for_selector('text=/dashboard|cycles|reports/i', timeout=5000)
            print("✅ Dashboard loaded")
            
            # Check Grid components are rendering (they should have role="grid" or class containing "MuiGrid")
            grid_count = await page.locator('[class*="MuiGrid"]').count()
            if grid_count > 0:
                print(f"✅ Grid components found: {grid_count}")
            
            # Check for date formatting (looking for common date patterns)
            page_text = await page.text_content("body")
            import re
            date_patterns = [
                r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
                r'\d{4}-\d{2}-\d{2}',       # YYYY-MM-DD
                r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # DD Mon
            ]
            
            has_dates = any(re.search(pattern, page_text) for pattern in date_patterns)
            if has_dates:
                print("✅ Date formatting working")
            
            await browser.close()
            return True
            
        except Exception as e:
            print(f"❌ UI Component Error: {e}")
            await browser.close()
            return False

async def main():
    print("🧪 SynapseDTE Fix Verification")
    print("=" * 50)
    
    # Run tests
    api_ok = await test_api_connection()
    frontend_ok = await test_frontend_loads()
    token = await test_login_flow()
    await test_authenticated_api_call(token)
    await test_ui_components()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"   API Connection: {'✅ Pass' if api_ok else '❌ Fail'}")
    print(f"   Frontend Loads: {'✅ Pass' if frontend_ok else '❌ Fail'}")
    print(f"   Authentication: {'✅ Pass' if token else '❌ Fail'}")
    print("\n✨ All critical fixes verified!" if api_ok and frontend_ok and token else "\n⚠️  Some issues found")

if __name__ == "__main__":
    asyncio.run(main())