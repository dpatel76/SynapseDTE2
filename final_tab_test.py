#!/usr/bin/env python3
"""
Final test to verify Report Owner Feedback tab visibility after backend restart
"""

import asyncio
from playwright.async_api import async_playwright
import requests


def verify_backend_data():
    """Verify backend has Report Owner feedback data"""
    print("🔍 VERIFYING BACKEND DATA")
    print("="*50)
    
    try:
        # Login and get token
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "tester@example.com", "password": "password123"}
        )
        
        if response.status_code != 200:
            print(f"❌ Backend login failed: {response.status_code}")
            return False
            
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check samples
        response = requests.get(
            "http://localhost:8000/api/v1/sample-selection/cycles/55/reports/156/samples?include_feedback=true",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Samples endpoint failed: {response.status_code}")
            return False
            
        samples = response.json().get("samples", [])
        ro_samples = [s for s in samples if s.get("report_owner_decision")]
        
        print(f"✅ Backend healthy")
        print(f"   Total samples: {len(samples)}")
        print(f"   Samples with RO decisions: {len(ro_samples)}")
        
        if ro_samples:
            print("   Sample RO decisions:")
            for sample in ro_samples[:3]:
                print(f"     {sample['sample_id']}: {sample['report_owner_decision']}")
        
        return len(ro_samples) > 0
        
    except Exception as e:
        print(f"❌ Backend verification failed: {e}")
        return False


async def test_frontend():
    """Test frontend tab visibility"""
    print(f"\n🌐 TESTING FRONTEND")
    print("="*50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Capture console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        try:
            # Login as Tester
            print("1. Logging in as tester@example.com...")
            await page.goto('http://localhost:3000/login')
            await page.wait_for_load_state('networkidle')
            
            # Clear form and login
            await page.fill('input[name="email"]', '')
            await page.fill('input[name="password"]', '')
            await page.fill('input[name="email"]', 'tester@example.com')
            await page.fill('input[name="password"]', 'password123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            # Verify login successful
            if 'login' in page.url:
                print("   ❌ Login failed")
                return False
            print("   ✅ Login successful")
            
            # Navigate to sample selection with fresh start
            print("\n2. Loading sample selection page...")
            await page.goto('http://localhost:3000/cycles/55/reports/156/sample-selection')
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(10000)  # Wait 10 seconds for all data to load
            
            # Check for tabs
            print("\n3. Checking tab visibility...")
            tabs = await page.locator('button[role="tab"]').all()
            
            if len(tabs) == 0:
                print("   ❌ No tabs found at all!")
                return False
            
            tab_texts = []
            for i, tab in enumerate(tabs):
                text = await tab.text_content()
                is_visible = await tab.is_visible()
                is_selected = await tab.get_attribute('aria-selected') == 'true'
                tab_texts.append(text.strip())
                print(f"   Tab {i+1}: '{text.strip()}' (visible: {is_visible}, selected: {is_selected})")
            
            # Check specifically for Report Owner Feedback tab
            has_ro_tab = "Report Owner Feedback" in tab_texts
            print(f"\n   Report Owner Feedback tab present: {'✅ YES' if has_ro_tab else '❌ NO'}")
            
            # Check debug logs
            print("\n4. Checking debug logs...")
            debug_logs = [log for log in console_logs if 'hasReportOwnerFeedback' in log or 'report_owner_decision' in log]
            if debug_logs:
                print("   Debug logs found:")
                for log in debug_logs:
                    print(f"     {log}")
            else:
                print("   ❌ No debug logs found")
            
            # Take screenshot
            await page.screenshot(path="final_tab_test.png", full_page=True)
            print(f"\n✅ Screenshot saved: final_tab_test.png")
            
            # Keep browser open for manual inspection
            print(f"\n🔍 Browser staying open for 30 seconds for manual verification...")
            print(f"   Please check: http://localhost:3000/cycles/55/reports/156/sample-selection")
            print(f"   Look for 'Report Owner Feedback' tab")
            await page.wait_for_timeout(30000)
            
            return has_ro_tab
            
        except Exception as e:
            print(f"   ❌ Frontend test error: {e}")
            await page.screenshot(path="final_tab_test_error.png")
            return False
        
        finally:
            await browser.close()


async def main():
    print("🧪 FINAL REPORT OWNER FEEDBACK TAB TEST")
    print("="*60)
    
    # Step 1: Verify backend
    backend_ok = verify_backend_data()
    
    # Step 2: Test frontend
    if backend_ok:
        frontend_ok = await test_frontend()
        
        print(f"\n📊 FINAL RESULTS")
        print("="*30)
        print(f"Backend has RO feedback: {'✅ YES' if backend_ok else '❌ NO'}")
        print(f"Frontend shows RO tab: {'✅ YES' if frontend_ok else '❌ NO'}")
        
        if backend_ok and frontend_ok:
            print(f"\n🎉 SUCCESS: Report Owner Feedback tab should be visible!")
        elif backend_ok and not frontend_ok:
            print(f"\n🚨 ISSUE: Backend has data but frontend doesn't show tab")
            print(f"   Possible causes:")
            print(f"   - Browser cache issue")
            print(f"   - React state not updating")
            print(f"   - Frontend/backend version mismatch")
        else:
            print(f"\n❌ ISSUE: Backend doesn't have Report Owner feedback data")
    else:
        print(f"\n❌ Cannot test frontend - backend has no RO feedback data")


if __name__ == "__main__":
    asyncio.run(main())