#!/usr/bin/env python3
"""
Comprehensive test script for all roles and pages
Tests both frontend and backend for every role
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from playwright.async_api import async_playwright, Page, BrowserContext

# Configuration
BASE_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"

# Test user credentials
TEST_USERS = {
    "tester": {
        "email": "tester@example.com",
        "password": "password123",
        "role": "Tester"
    },
    "test_executive": {
        "email": "test_executive@example.com",
        "password": "password123",
        "role": "Test Executive"
    },
    "report_owner": {
        "email": "report_owner@example.com",
        "password": "password123",
        "role": "Report Owner"
    },
    "report_owner_executive": {
        "email": "report_owner_executive@example.com",
        "password": "password123",
        "role": "Report Owner Executive"  
    },
    "data_owner": {
        "email": "data_owner@example.com",
        "password": "password123",
        "role": "Data Owner"
    },
    "data_executive": {
        "email": "data_executive@example.com",
        "password": "password123",
        "role": "Data Executive"
    }
}

# Pages to test for each role
ROLE_PAGES = {
    "Tester": [
        "/dashboard",
        "/cycles",
        "/cycles/1/reports/1",
        "/cycles/1/reports/1/scoping",
        "/cycles/1/reports/1/planning",
        "/cycles/1/reports/1/sample-selection",
        "/cycles/1/reports/1/test-execution",
        "/cycles/1/reports/1/observation-management"
    ],
    "Test Executive": [
        "/dashboard", 
        "/cycles",
        "/users",
        "/metrics",
        "/cycles/1/reports/1",
        "/cycles/1/reports/1/scoping",
        "/cycles/1/reports/1/planning",
        "/cycles/1/reports/1/sample-selection",
        "/cycles/1/reports/1/data-owner",
        "/cycles/1/reports/1/request-info",
        "/cycles/1/reports/1/test-execution",
        "/cycles/1/reports/1/observation-management"
    ],
    "Report Owner": [
        "/dashboard",
        "/cycles",
        "/cycles/1/reports/1",
        "/cycles/1/reports/1/scoping",
        "/cycles/1/reports/1/planning",
        "/cycles/1/reports/1/observation-management"
    ],
    "Report Owner Executive": [
        "/dashboard",
        "/cycles",
        "/metrics",
        "/cycles/1/reports/1",
        "/cycles/1/reports/1/scoping",
        "/cycles/1/reports/1/planning",
        "/cycles/1/reports/1/observation-management"
    ],
    "Data Owner": [
        "/dashboard",
        "/cycles/1/reports/1/request-info",
        "/cycles/1/reports/1/data-owner"
    ],
    "Data Executive": [
        "/dashboard",
        "/cycles/1/reports/1/data-owner"
    ]
}

# Test results storage
test_results = {
    "started_at": datetime.now().isoformat(),
    "backend_status": {},
    "frontend_tests": {},
    "console_errors": {},
    "api_errors": {},
    "summary": {}
}

async def check_backend_health():
    """Check if backend is running"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Backend is running")
                test_results["backend_status"] = {"status": "healthy", "response": response.json()}
                return True
            else:
                print(f"❌ Backend returned status {response.status_code}")
                test_results["backend_status"] = {"status": "unhealthy", "status_code": response.status_code}
                return False
    except Exception as e:
        print(f"❌ Backend is not running: {e}")
        test_results["backend_status"] = {"status": "error", "error": str(e)}
        return False

async def login_user(email: str, password: str) -> Optional[str]:
    """Login a user and return access token"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            else:
                print(f"❌ Login failed for {email}: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
    except Exception as e:
        print(f"❌ Login error for {email}: {e}")
        return None

async def test_api_endpoints(role: str, token: str):
    """Test API endpoints for a specific role"""
    api_tests = []
    
    # Define endpoints to test based on role
    endpoints = {
        "Tester": [
            ("/api/v1/cycles", "GET"),
            ("/api/v1/cycles/1", "GET"),
            ("/api/v1/cycles/1/reports", "GET"),
            ("/api/v1/dashboards/tester", "GET")
        ],
        "Test Executive": [
            ("/api/v1/cycles", "GET"),
            ("/api/v1/users", "GET"),
            ("/api/v1/metrics/overview", "GET"),
            ("/api/v1/dashboards/test-executive", "GET")
        ],
        "Report Owner": [
            ("/api/v1/cycles", "GET"),
            ("/api/v1/dashboards/report-owner", "GET")
        ],
        "Report Owner Executive": [
            ("/api/v1/cycles", "GET"),
            ("/api/v1/metrics/overview", "GET"),
            ("/api/v1/dashboards/report-owner-executive", "GET")
        ],
        "Data Owner": [
            ("/api/v1/dashboards/data-owner", "GET"),
            ("/api/v1/data-owner/requests", "GET")
        ],
        "Data Executive": [
            ("/api/v1/dashboards/data-executive", "GET"),
            ("/api/v1/data-owner/assignments", "GET")
        ]
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        for endpoint, method in endpoints.get(role, []):
            try:
                if method == "GET":
                    response = await client.get(f"{BASE_URL}{endpoint}", headers=headers)
                
                api_tests.append({
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 201, 204]
                })
                
                if response.status_code not in [200, 201, 204]:
                    print(f"   ⚠️  {endpoint}: {response.status_code}")
            except Exception as e:
                api_tests.append({
                    "endpoint": endpoint,
                    "method": method,
                    "error": str(e),
                    "success": False
                })
                print(f"   ❌ {endpoint}: {e}")
    
    return api_tests

async def test_frontend_page(page: Page, url: str) -> Dict:
    """Test a single frontend page"""
    console_errors = []
    api_errors = []
    
    # Set up console error listener
    page.on("console", lambda msg: console_errors.append({
        "type": msg.type,
        "text": msg.text,
        "location": msg.location
    }) if msg.type in ["error", "warning"] else None)
    
    # Set up request failure listener
    page.on("requestfailed", lambda request: api_errors.append({
        "url": request.url,
        "failure": request.failure
    }))
    
    try:
        # Navigate to page
        response = await page.goto(f"{FRONTEND_URL}{url}", wait_until="networkidle")
        
        # Wait for content to load
        await page.wait_for_timeout(2000)
        
        # Check if redirected to login
        current_url = page.url
        if "/login" in current_url and "/login" not in url:
            return {
                "url": url,
                "status": "redirected_to_login",
                "success": False,
                "console_errors": console_errors,
                "api_errors": api_errors
            }
        
        # Check for error messages
        error_elements = await page.query_selector_all('[class*="error"], [class*="Error"]')
        error_texts = []
        for elem in error_elements:
            text = await elem.text_content()
            if text and len(text.strip()) > 0:
                error_texts.append(text.strip())
        
        # Take screenshot
        screenshot_path = f"test_results/screenshots/{url.replace('/', '_')}.png"
        Path("test_results/screenshots").mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=screenshot_path)
        
        return {
            "url": url,
            "status": "loaded",
            "success": len(console_errors) == 0 and len(api_errors) == 0,
            "console_errors": console_errors,
            "api_errors": api_errors,
            "error_texts": error_texts,
            "screenshot": screenshot_path
        }
        
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "success": False,
            "error": str(e),
            "console_errors": console_errors,
            "api_errors": api_errors
        }

async def test_role(role: str, email: str, password: str):
    """Test all functionality for a specific role"""
    print(f"\n{'='*60}")
    print(f"Testing {role}")
    print(f"{'='*60}")
    
    role_results = {
        "login": False,
        "api_tests": [],
        "frontend_tests": []
    }
    
    # Test login
    print(f"1. Testing login for {email}...")
    token = await login_user(email, password)
    if token:
        print(f"   ✅ Login successful")
        role_results["login"] = True
    else:
        print(f"   ❌ Login failed")
        test_results["frontend_tests"][role] = role_results
        return
    
    # Test API endpoints
    print(f"2. Testing API endpoints...")
    api_results = await test_api_endpoints(role, token)
    role_results["api_tests"] = api_results
    api_success = sum(1 for r in api_results if r.get("success", False))
    print(f"   ✅ {api_success}/{len(api_results)} API endpoints working")
    
    # Test frontend pages
    print(f"3. Testing frontend pages...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Set authentication token in localStorage
        await context.add_init_script(f"""
            window.localStorage.setItem('access_token', '{token}');
        """)
        
        page = await context.new_page()
        
        pages_to_test = ROLE_PAGES.get(role, [])
        for page_url in pages_to_test:
            print(f"   Testing {page_url}...")
            result = await test_frontend_page(page, page_url)
            role_results["frontend_tests"].append(result)
            
            if result["success"]:
                print(f"      ✅ Page loaded successfully")
            else:
                print(f"      ❌ Page has issues")
                if result.get("console_errors"):
                    print(f"         Console errors: {len(result['console_errors'])}")
                if result.get("api_errors"):
                    print(f"         API errors: {len(result['api_errors'])}")
        
        await browser.close()
    
    test_results["frontend_tests"][role] = role_results
    
    # Summary for role
    frontend_success = sum(1 for r in role_results["frontend_tests"] if r.get("success", False))
    total_pages = len(role_results["frontend_tests"])
    print(f"\n{role} Summary:")
    print(f"  - Login: {'✅' if role_results['login'] else '❌'}")
    print(f"  - API: {api_success}/{len(api_results)} endpoints working")
    print(f"  - Frontend: {frontend_success}/{total_pages} pages working")

async def main():
    """Run comprehensive tests for all roles"""
    print("🚀 Starting Comprehensive Role & Page Testing")
    print("=" * 60)
    
    # Check backend health
    print("Checking backend health...")
    if not await check_backend_health():
        print("❌ Backend is not running. Please start the backend first.")
        sys.exit(1)
    
    # Test each role
    for role_key, user_info in TEST_USERS.items():
        await test_role(
            user_info["role"],
            user_info["email"],
            user_info["password"]
        )
    
    # Generate summary
    print(f"\n{'='*60}")
    print("📊 OVERALL SUMMARY")
    print(f"{'='*60}")
    
    total_success = 0
    total_tests = 0
    
    for role, results in test_results["frontend_tests"].items():
        role_success = 0
        role_total = 0
        
        # Count API tests
        api_tests = results.get("api_tests", [])
        api_success = sum(1 for t in api_tests if t.get("success", False))
        role_success += api_success
        role_total += len(api_tests)
        
        # Count frontend tests
        frontend_tests = results.get("frontend_tests", [])
        frontend_success = sum(1 for t in frontend_tests if t.get("success", False))
        role_success += frontend_success
        role_total += len(frontend_tests)
        
        total_success += role_success
        total_tests += role_total
        
        print(f"\n{role}:")
        print(f"  - Total: {role_success}/{role_total} tests passed")
        print(f"  - API: {api_success}/{len(api_tests)}")
        print(f"  - Frontend: {frontend_success}/{len(frontend_tests)}")
        
        # Show failed pages
        failed_pages = [t["url"] for t in frontend_tests if not t.get("success", False)]
        if failed_pages:
            print(f"  - Failed pages: {', '.join(failed_pages)}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_success}/{total_tests} tests passed ({total_success/total_tests*100:.1f}%)")
    print(f"{'='*60}")
    
    # Save detailed results
    test_results["summary"] = {
        "total_success": total_success,
        "total_tests": total_tests,
        "success_rate": total_success/total_tests if total_tests > 0 else 0,
        "completed_at": datetime.now().isoformat()
    }
    
    with open("test_results/comprehensive_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to test_results/comprehensive_test_results.json")
    print(f"📸 Screenshots saved to test_results/screenshots/")

if __name__ == "__main__":
    asyncio.run(main())