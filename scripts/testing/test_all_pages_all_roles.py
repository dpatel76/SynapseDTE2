#!/usr/bin/env python3
"""Comprehensive test for all roles and pages with data verification."""
import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import os

# Test users for each role - using the working example credentials
TEST_USERS = {
    "Tester": {
        "email": "tester@example.com",
        "password": "password123"
    },
    "Test Executive": {
        "email": "testmgr@synapse.com", 
        "password": "TestUser123!"
    },
    "Report Owner": {
        "email": "owner@synapse.com",
        "password": "TestUser123!"
    },
    "Report Owner Executive": {
        "email": "exec@synapse.com",
        "password": "TestUser123!"
    },
    "Data Owner": {
        "email": "provider@synapse.com",
        "password": "TestUser123!"
    },
    "Data Executive": {
        "email": "cdo@synapse.com",
        "password": "TestUser123!"
    }
}

# Pages to test for each role
ROLE_PAGES = {
    "Tester": [
        "/dashboard",
        "/tester-dashboard",
        "/cycles",
        "/cycles/9/reports/156/planning",
        "/cycles/9/reports/156/scoping", 
        "/cycles/9/reports/156/sample-selection",
        "/cycles/9/reports/156/data-provider-id",
        "/cycles/9/reports/156/request-info",
        "/cycles/9/reports/156/test-execution",
        "/cycles/9/reports/156/observation-management"
    ],
    "Test Executive": [
        "/dashboard",
        "/executive-dashboard",
        "/cycles",
        "/cycles/9/reports/156/planning",
        "/cycles/9/reports/156/scoping",
        "/cycles/9/reports/156/sample-selection", 
        "/cycles/9/reports/156/data-provider-id",
        "/cycles/9/reports/156/request-info",
        "/cycles/9/reports/156/test-execution",
        "/cycles/9/reports/156/observation-management",
        "/users",
        "/metrics"
    ],
    "Report Owner": [
        "/dashboard",
        "/report-owner-dashboard",
        "/cycles",
        "/cycles/9/reports/156/planning",
        "/cycles/9/reports/156/scoping",
        "/cycles/9/reports/156/observation-management"
    ],
    "Report Owner Executive": [
        "/dashboard", 
        "/executive-dashboard",
        "/cycles",
        "/metrics"
    ],
    "Data Owner": [
        "/dashboard",
        "/data-owner-dashboard",
        "/cycles/9/reports/156/request-info"
    ],
    "Data Executive": [
        "/dashboard",
        "/cdo-dashboard",
        "/metrics"
    ]
}

# Expected data indicators for key pages
DATA_INDICATORS = {
    "/cycles/9/reports/156/sample-selection": [
        "Sample Set", "Sample Type", "Selection Method", "Status"
    ],
    "/cycles/9/reports/156/request-info": [
        "Test Case", "Attribute", "Sample", "Evidence", "Submit"
    ],
    "/cycles/9/reports/156/test-execution": [
        "Test Case", "Sample", "Expected Value", "Actual Value", "Pass", "Fail"
    ],
    "/data-owner-dashboard": [
        "Assigned Test Cases", "Pending Submissions", "Completed"
    ]
}

async def test_page_data_loading(page, url, role):
    """Test if a page loads data correctly."""
    console_errors = []
    network_errors = []
    
    # Capture console errors
    page.on("console", lambda msg: console_errors.append({
        'type': msg.type,
        'text': msg.text
    }) if msg.type == 'error' else None)
    
    # Capture network errors
    def log_response(response):
        if response.status >= 400:
            network_errors.append({
                'url': response.url,
                'status': response.status,
                'method': response.request.method
            })
    page.on("response", log_response)
    
    try:
        # Navigate to page
        await page.goto(f"http://localhost:3001{url}", wait_until="networkidle", timeout=30000)
        
        # Wait a bit for React to render
        await page.wait_for_timeout(2000)
        
        # Check for loading states
        loading_count = await page.locator('text=/Loading|Загрузка/i').count()
        
        # Check for error messages
        error_texts = [
            "Failed to load", "Error loading", "Something went wrong",
            "An error occurred", "Unable to load", "No data available"
        ]
        error_count = 0
        for error_text in error_texts:
            error_count += await page.locator(f'text=/{error_text}/i').count()
        
        # Check for expected data indicators
        data_found = {}
        if url in DATA_INDICATORS:
            for indicator in DATA_INDICATORS[url]:
                count = await page.locator(f'text=/{indicator}/i').count()
                data_found[indicator] = count > 0
        
        # Check for tables and data rows
        table_count = await page.locator('table').count()
        row_count = await page.locator('tbody tr').count()
        
        # Check for cards/content
        card_count = await page.locator('.MuiCard-root').count()
        
        # Take screenshot
        screenshot_dir = "test_results/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_name = f"{role}_{url.replace('/', '_')}.png"
        screenshot_path = os.path.join(screenshot_dir, screenshot_name)
        await page.screenshot(path=screenshot_path)
        
        # Get page title
        title = await page.title()
        
        # Check for specific content based on page
        has_data = False
        if table_count > 0 and row_count > 0:
            has_data = True
        elif card_count > 2:  # More than just header cards
            has_data = True
        elif data_found and any(data_found.values()):
            has_data = True
        
        result = {
            'url': url,
            'role': role,
            'title': title,
            'loading_elements': loading_count,
            'error_elements': error_count,
            'console_errors': len(console_errors),
            'console_error_samples': console_errors[:3],
            'network_errors': len(network_errors),
            'network_error_samples': network_errors[:3],
            'table_count': table_count,
            'row_count': row_count,
            'card_count': card_count,
            'data_indicators': data_found,
            'has_data': has_data,
            'screenshot': screenshot_path,
            'success': error_count == 0 and len(network_errors) == 0 and has_data
        }
        
        return result
        
    except Exception as e:
        return {
            'url': url,
            'role': role,
            'error': str(e),
            'success': False
        }

async def test_role_pages(role, credentials):
    """Test all pages for a specific role."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Login
        print(f"\nTesting {role}...")
        print(f"Logging in as {credentials['email']}...")
        
        await page.goto("http://localhost:3001/login")
        await page.wait_for_load_state("networkidle")
        
        # Remove webpack overlay if present
        await page.evaluate("""
            const overlay = document.querySelector('#webpack-dev-server-client-overlay');
            if (overlay) overlay.remove();
        """)
        
        # Fill login form
        await page.fill('input[name="email"]', credentials['email'])
        await page.fill('input[name="password"]', credentials['password'])
        
        # Click login
        try:
            await page.click('button[type="submit"]', timeout=2000)
        except:
            await page.evaluate("""
                const button = document.querySelector('button[type="submit"]');
                if (button) button.click();
            """)
        
        # Wait for navigation
        try:
            await page.wait_for_url("**/dashboard", timeout=5000)
        except:
            # Try alternative dashboard URLs
            current_url = page.url
            if "dashboard" in current_url or "login" not in current_url:
                print(f"Logged in successfully, redirected to: {current_url}")
            else:
                print(f"Login may have failed, current URL: {current_url}")
        
        # Test each page
        results = []
        pages_to_test = ROLE_PAGES.get(role, [])
        
        for page_url in pages_to_test:
            print(f"  Testing {page_url}...")
            result = await test_page_data_loading(page, page_url, role)
            results.append(result)
            
            # Print immediate feedback
            if result.get('success'):
                print(f"    ✅ Success - Data loaded correctly")
            else:
                print(f"    ❌ Failed - {result.get('error', 'No data or errors detected')}")
                if result.get('console_errors', 0) > 0:
                    print(f"       Console errors: {result['console_errors']}")
                if result.get('network_errors', 0) > 0:
                    print(f"       Network errors: {result['network_errors']}")
                if not result.get('has_data'):
                    print(f"       No data displayed on page")
        
        await browser.close()
        return results

async def run_comprehensive_test():
    """Run comprehensive test for all roles."""
    all_results = {}
    
    # Create results directory
    os.makedirs("test_results", exist_ok=True)
    
    # Test each role
    for role, credentials in TEST_USERS.items():
        try:
            results = await test_role_pages(role, credentials)
            all_results[role] = results
        except Exception as e:
            print(f"Error testing {role}: {str(e)}")
            all_results[role] = [{'error': str(e), 'success': False}]
    
    # Generate summary report
    summary = {
        'test_date': datetime.now().isoformat(),
        'total_tests': sum(len(results) for results in all_results.values()),
        'passed': sum(1 for results in all_results.values() for r in results if r.get('success')),
        'failed': sum(1 for results in all_results.values() for r in results if not r.get('success')),
        'by_role': {}
    }
    
    for role, results in all_results.items():
        summary['by_role'][role] = {
            'total': len(results),
            'passed': sum(1 for r in results if r.get('success')),
            'failed': sum(1 for r in results if not r.get('success')),
            'issues': [r for r in results if not r.get('success')]
        }
    
    # Save detailed results
    with open('test_results/comprehensive_test_results.json', 'w') as f:
        json.dump({
            'summary': summary,
            'detailed_results': all_results
        }, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ({summary['passed']/summary['total_tests']*100:.1f}%)")
    print(f"Failed: {summary['failed']} ({summary['failed']/summary['total_tests']*100:.1f}%)")
    
    print("\nBy Role:")
    for role, stats in summary['by_role'].items():
        print(f"\n{role}:")
        print(f"  Total: {stats['total']}")
        print(f"  Passed: {stats['passed']}")
        print(f"  Failed: {stats['failed']}")
        if stats['issues']:
            print(f"  Failed Pages:")
            for issue in stats['issues']:
                print(f"    - {issue.get('url', 'Unknown')}: {issue.get('error', 'No data or errors')}")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())