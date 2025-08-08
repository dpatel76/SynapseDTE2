#!/usr/bin/env python3
"""
Diagnose frontend issues by capturing console errors and network failures
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def diagnose_frontend():
    """Capture all frontend errors and issues"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Run with UI to see what's happening
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }))
        
        # Capture page errors
        page_errors = []
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        
        # Capture network failures
        failed_requests = []
        page.on("requestfailed", lambda req: failed_requests.append({
            "url": req.url,
            "failure": req.failure,
            "method": req.method
        }))
        
        # Capture responses
        responses = []
        page.on("response", lambda res: responses.append({
            "url": res.url,
            "status": res.status,
            "ok": res.ok
        }) if not res.ok else None)
        
        print("🔍 Diagnosing Frontend Issues")
        print("=" * 60)
        
        # Test 1: Load main page
        print("\n📌 Loading main page...")
        try:
            await page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
            print("✅ Page loaded")
            
            # Check if React app mounted
            root_content = await page.text_content("#root")
            if root_content and len(root_content.strip()) > 0:
                print("✅ React app mounted")
            else:
                print("❌ React app did not mount - #root is empty")
                
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
        
        # Test 2: Check for JavaScript errors
        print("\n📌 Console messages:")
        error_count = 0
        for msg in console_messages:
            if msg["type"] in ["error", "warning"]:
                print(f"  {msg['type'].upper()}: {msg['text']}")
                if msg.get("location"):
                    print(f"    at {msg['location'].get('url', 'unknown')}:{msg['location'].get('lineNumber', '?')}")
                error_count += 1
        
        if error_count == 0:
            print("  ✅ No console errors")
        else:
            print(f"  ❌ Found {error_count} console errors/warnings")
        
        # Test 3: Check for page errors
        print("\n📌 Page errors:")
        if page_errors:
            for err in page_errors:
                print(f"  ❌ {err}")
        else:
            print("  ✅ No page errors")
        
        # Test 4: Check failed network requests
        print("\n📌 Failed network requests:")
        if failed_requests:
            for req in failed_requests:
                print(f"  ❌ {req['method']} {req['url']}")
                print(f"     Failure: {req['failure']}")
        else:
            print("  ✅ No failed requests")
        
        # Test 5: Check error responses
        print("\n📌 Error responses:")
        error_responses = [r for r in responses if r and not r["ok"]]
        if error_responses:
            for res in error_responses[:10]:  # Show first 10
                print(f"  ❌ {res['status']} - {res['url']}")
        else:
            print("  ✅ No error responses")
        
        # Test 6: Try to navigate to login
        print("\n📌 Testing login page...")
        try:
            await page.goto("http://localhost:3000/login", wait_until="networkidle", timeout=30000)
            
            # Check if login form exists
            email_input = await page.query_selector('input[name="email"]')
            password_input = await page.query_selector('input[name="password"]')
            submit_button = await page.query_selector('button[type="submit"]')
            
            if email_input and password_input and submit_button:
                print("✅ Login form elements found")
                
                # Try to login
                await page.fill('input[name="email"]', "admin@example.com")
                await page.fill('input[name="password"]', "password123")
                
                # Capture network activity during login
                login_responses = []
                page.on("response", lambda res: login_responses.append({
                    "url": res.url,
                    "status": res.status,
                    "ok": res.ok
                }) if "/auth/login" in res.url else None)
                
                await page.click('button[type="submit"]')
                
                # Wait a bit for login attempt
                await page.wait_for_timeout(3000)
                
                # Check if we're still on login page
                current_url = page.url
                if "/login" in current_url:
                    print("❌ Still on login page after submit")
                    
                    # Check for error messages
                    error_alert = await page.query_selector('.MuiAlert-root')
                    if error_alert:
                        error_text = await error_alert.text_content()
                        print(f"  Error message: {error_text}")
                else:
                    print(f"✅ Redirected to: {current_url}")
                
                # Check login API responses
                for res in login_responses:
                    print(f"  Login API response: {res['status']} - {res['url']}")
                    
            else:
                print("❌ Login form elements not found")
                missing = []
                if not email_input: missing.append("email input")
                if not password_input: missing.append("password input")
                if not submit_button: missing.append("submit button")
                print(f"  Missing: {', '.join(missing)}")
                
        except Exception as e:
            print(f"❌ Failed to test login: {e}")
        
        # Test 7: Check what's actually rendered
        print("\n📌 Page content check:")
        body_text = await page.text_content("body")
        if body_text:
            if "Loading" in body_text:
                print("⚠️  Page shows 'Loading'")
            if "Error" in body_text or "error" in body_text:
                print("⚠️  Page contains error text")
            if len(body_text.strip()) < 100:
                print(f"⚠️  Page has very little content: {len(body_text)} characters")
                print(f"  Content: {body_text.strip()[:200]}...")
        
        # Take screenshot
        screenshot_path = "test_results/frontend_diagnostic.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n📸 Screenshot saved to: {screenshot_path}")
        
        # Save detailed diagnostics
        diagnostics = {
            "console_messages": console_messages,
            "page_errors": page_errors,
            "failed_requests": failed_requests,
            "error_responses": error_responses,
            "page_url": page.url,
            "page_title": await page.title()
        }
        
        with open("test_results/frontend_diagnostics.json", "w") as f:
            json.dump(diagnostics, f, indent=2)
        
        print("\n💾 Detailed diagnostics saved to: test_results/frontend_diagnostics.json")
        
        # Keep browser open for 10 seconds to observe
        print("\n⏰ Keeping browser open for 10 seconds...")
        await page.wait_for_timeout(10000)
        
        await browser.close()

async def main():
    import os
    os.makedirs("test_results", exist_ok=True)
    await diagnose_frontend()

if __name__ == "__main__":
    asyncio.run(main())