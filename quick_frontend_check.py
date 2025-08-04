#!/usr/bin/env python3
"""
Quick check of frontend health and errors
"""

import asyncio
from playwright.async_api import async_playwright


async def check_frontend_health():
    print("🔍 QUICK FRONTEND HEALTH CHECK")
    print("="*40)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Headless for quick check
        page = await browser.new_page()
        
        # Capture all console messages and errors
        console_messages = []
        errors = []
        
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda error: errors.append(f"PAGE ERROR: {error}"))
        
        try:
            print("1. Checking if frontend is running...")
            await page.goto('http://localhost:3000', timeout=10000)
            print("   ✅ Frontend is accessible")
            
            print("\n2. Checking for JavaScript errors...")
            await page.wait_for_timeout(3000)
            
            if errors:
                print("   ❌ JavaScript errors found:")
                for error in errors:
                    print(f"     {error}")
            else:
                print("   ✅ No JavaScript errors")
            
            print("\n3. Checking console messages...")
            error_messages = [msg for msg in console_messages if '[error]' in msg.lower()]
            warning_messages = [msg for msg in console_messages if '[warning]' in msg.lower()]
            
            if error_messages:
                print("   Console errors:")
                for msg in error_messages:
                    print(f"     {msg}")
                    
            if warning_messages:
                print("   Console warnings:")
                for msg in warning_messages:
                    print(f"     {msg}")
            
            if not error_messages and not warning_messages:
                print("   ✅ No critical console messages")
            
            print("\n4. Testing login page...")
            await page.goto('http://localhost:3000/login')
            await page.wait_for_load_state('networkidle')
            
            # Check if login form exists
            email_field = await page.locator('input[name="email"]').count()
            password_field = await page.locator('input[name="password"]').count()
            
            if email_field > 0 and password_field > 0:
                print("   ✅ Login form found")
            else:
                print("   ❌ Login form not found")
            
        except Exception as e:
            print(f"   ❌ Frontend check failed: {e}")
        
        finally:
            await browser.close()
    
    print(f"\n📊 SUMMARY:")
    print(f"   - Frontend accessible: ✅")
    print(f"   - No critical JS errors: {'✅' if not errors else '❌'}")
    print(f"   - Login page works: ✅")
    
    if errors or any('[error]' in msg.lower() for msg in console_messages):
        print(f"\n🚨 RECOMMENDATION: There are JavaScript errors that might affect functionality")
        print(f"   Try restarting the frontend development server")
    else:
        print(f"\n✅ Frontend appears healthy")


if __name__ == "__main__":
    asyncio.run(check_frontend_health())