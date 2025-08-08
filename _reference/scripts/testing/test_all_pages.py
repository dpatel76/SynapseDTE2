#!/usr/bin/env python3
"""
Comprehensive Frontend Testing Script
Tests all pages for all user roles to ensure no errors
"""

import asyncio
import sys
from typing import Dict, List, Tuple
from playwright.async_api import async_playwright, Page, ConsoleMessage, Response
import json
from datetime import datetime

# Test users mapped to their roles
TEST_USERS = {
    "Admin": {
        "email": "admin@example.com",
        "password": "password123"
    },
    "Test Executive": {
        "email": "test.manager@example.com", 
        "password": "password123"
    },
    "Tester": {
        "email": "tester@example.com",
        "password": "password123"
    },
    "Data Owner": {
        "email": "data.provider@example.com",
        "password": "password123"
    },
    "Data Executive": {
        "email": "cdo@example.com",
        "password": "password123"
    },
    "Report Owner": {
        "email": "report.owner@example.com",
        "password": "password123"
    },
    "Report Owner Executive": {
        "email": "report_owner_executive@example.com",
        "password": "password123"
    }
}

# All pages to test for each role
PAGES_TO_TEST = [
    ("/", "Dashboard"),
    ("/dashboard", "Dashboard"),
    ("/phases/planning", "Planning Phase"),
    ("/phases/simplified-planning", "Simplified Planning"),
    ("/phases/scoping", "Scoping Phase"), 
    ("/phases/data-provider-identification", "Data Provider Identification"),
    ("/phases/sample-selection", "Sample Selection"),
    ("/phases/request-information", "Request Information"),
    ("/phases/test-execution", "Test Execution"),
    ("/phases/observation-management", "Observation Management"),
    ("/phases/data-profiling", "Data Profiling"),
    ("/admin/users", "User Management"),
    ("/admin/reports", "Report Management"),
    ("/admin/system", "System Settings"),
    ("/workflows", "Workflows"),
    ("/reports", "Reports"),
    ("/profile", "Profile"),
    ("/settings", "Settings"),
    ("/help", "Help")
]

class PageTester:
    def __init__(self):
        self.results = {}
        self.console_errors = []
        self.network_errors = []
        
    async def test_all_roles(self):
        """Test all pages for all user roles"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for role, credentials in TEST_USERS.items():
                print(f"\n{'='*60}")
                print(f"Testing role: {role}")
                print(f"User: {credentials['email']}")
                print(f"{'='*60}")
                
                context = await browser.new_context()
                page = await context.new_page()
                
                # Set up error monitoring
                self.setup_error_monitoring(page, role)
                
                # Login
                login_success = await self.login(page, credentials['email'], credentials['password'])
                if not login_success:
                    print(f"❌ Login failed for {role}")
                    await context.close()
                    continue
                
                # Test all pages
                role_results = await self.test_pages_for_role(page, role)
                self.results[role] = role_results
                
                await context.close()
            
            await browser.close()
            
        # Generate report
        self.generate_report()
    
    def setup_error_monitoring(self, page: Page, role: str):
        """Set up console and network error monitoring"""
        async def handle_console(msg: ConsoleMessage):
            if msg.type in ['error', 'warning']:
                self.console_errors.append({
                    'role': role,
                    'url': page.url,
                    'type': msg.type,
                    'text': msg.text,
                    'timestamp': datetime.now().isoformat()
                })
        
        async def handle_response(response: Response):
            if response.status >= 400:
                self.network_errors.append({
                    'role': role,
                    'url': response.url,
                    'status': response.status,
                    'timestamp': datetime.now().isoformat()
                })
        
        page.on('console', handle_console)
        page.on('response', handle_response)
    
    async def login(self, page: Page, email: str, password: str) -> bool:
        """Login with given credentials"""
        try:
            await page.goto('http://localhost:3000/login', wait_until='networkidle')
            
            # Fill login form
            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            
            # Click login button
            await page.click('button[type="submit"]')
            
            # Wait for navigation by waiting for URL change
            await page.wait_for_url(lambda url: '/login' not in url, timeout=10000)
            
            # Check if login was successful
            if '/login' in page.url:
                return False
                
            print(f"✅ Login successful")
            return True
            
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    async def test_pages_for_role(self, page: Page, role: str) -> List[Dict]:
        """Test all pages for a specific role"""
        results = []
        
        for path, name in PAGES_TO_TEST:
            print(f"\nTesting {name} ({path})...")
            result = await self.test_page(page, path, name, role)
            results.append(result)
            
            # Print immediate feedback
            if result['success']:
                print(f"  ✅ Success - Loaded in {result['load_time']:.2f}s")
            else:
                print(f"  ❌ Failed - {result['error']}")
                
            if result['console_errors']:
                print(f"  ⚠️  {len(result['console_errors'])} console errors")
                
            if result['network_errors']:
                print(f"  ⚠️  {len(result['network_errors'])} network errors")
        
        return results
    
    async def test_page(self, page: Page, path: str, name: str, role: str) -> Dict:
        """Test a single page"""
        start_time = datetime.now()
        console_errors_before = len(self.console_errors)
        network_errors_before = len(self.network_errors)
        
        result = {
            'path': path,
            'name': name,
            'role': role,
            'success': False,
            'error': None,
            'load_time': 0,
            'console_errors': [],
            'network_errors': [],
            'has_data': False,
            'elements_found': {}
        }
        
        try:
            # Navigate to page
            response = await page.goto(f'http://localhost:3000{path}', 
                                     wait_until='networkidle',
                                     timeout=30000)
            
            # Check if redirected (might not have access)
            if page.url != f'http://localhost:3000{path}' and '/login' not in page.url:
                result['redirected'] = True
                result['redirected_to'] = page.url
            
            # Wait for content to load
            await page.wait_for_load_state('networkidle')
            
            # Check for common elements
            result['elements_found'] = {
                'has_header': await page.locator('header').count() > 0,
                'has_sidebar': await page.locator('[class*="sidebar"], [class*="Sidebar"], aside').count() > 0,
                'has_main_content': await page.locator('main, [role="main"]').count() > 0,
                'has_data_tables': await page.locator('table').count() > 0,
                'has_charts': await page.locator('canvas, svg[class*="chart"]').count() > 0,
                'has_loading_indicators': await page.locator('[class*="loading"], [class*="spinner"], [class*="skeleton"]').count() > 0
            }
            
            # Check if page has meaningful content
            text_content = await page.text_content('body')
            result['has_data'] = len(text_content.strip()) > 100
            
            result['success'] = True
            result['load_time'] = (datetime.now() - start_time).total_seconds()
            
        except Exception as e:
            result['error'] = str(e)
            result['load_time'] = (datetime.now() - start_time).total_seconds()
        
        # Collect errors that occurred during this page load
        result['console_errors'] = self.console_errors[console_errors_before:]
        result['network_errors'] = self.network_errors[network_errors_before:]
        
        return result
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary
        total_tests = sum(len(results) for results in self.results.values())
        total_failures = sum(1 for role_results in self.results.values() 
                           for result in role_results if not result['success'])
        
        print(f"\n📊 SUMMARY")
        print(f"  Total tests: {total_tests}")
        print(f"  Passed: {total_tests - total_failures}")
        print(f"  Failed: {total_failures}")
        if total_tests > 0:
            print(f"  Success rate: {((total_tests - total_failures) / total_tests * 100):.1f}%")
        else:
            print(f"  Success rate: N/A (no tests completed)")
        
        # Results by role
        print(f"\n📋 RESULTS BY ROLE")
        for role, results in self.results.items():
            failures = [r for r in results if not r['success']]
            console_error_count = sum(len(r['console_errors']) for r in results)
            network_error_count = sum(len(r['network_errors']) for r in results)
            
            print(f"\n  {role}:")
            print(f"    ✅ Passed: {len(results) - len(failures)}/{len(results)}")
            if failures:
                print(f"    ❌ Failed pages:")
                for failure in failures:
                    print(f"       - {failure['name']} ({failure['path']}): {failure['error']}")
            if console_error_count:
                print(f"    ⚠️  Console errors: {console_error_count}")
            if network_error_count:
                print(f"    ⚠️  Network errors: {network_error_count}")
        
        # Page performance
        print(f"\n⚡ PAGE PERFORMANCE")
        all_results = [r for results in self.results.values() for r in results if r['success']]
        if all_results:
            sorted_by_time = sorted(all_results, key=lambda x: x['load_time'], reverse=True)
            print(f"  Slowest pages:")
            for result in sorted_by_time[:5]:
                print(f"    - {result['name']}: {result['load_time']:.2f}s ({result['role']})")
        
        # Console errors
        if self.console_errors:
            print(f"\n⚠️  CONSOLE ERRORS ({len(self.console_errors)} total)")
            # Group by page
            errors_by_page = {}
            for error in self.console_errors:
                page_url = error['url']
                if page_url not in errors_by_page:
                    errors_by_page[page_url] = []
                errors_by_page[page_url].append(error)
            
            for url, errors in list(errors_by_page.items())[:5]:
                print(f"\n  {url}:")
                for error in errors[:3]:
                    print(f"    [{error['type']}] {error['text'][:100]}...")
        
        # Network errors
        if self.network_errors:
            print(f"\n❌ NETWORK ERRORS ({len(self.network_errors)} total)")
            # Group by status code
            errors_by_status = {}
            for error in self.network_errors:
                status = error['status']
                if status not in errors_by_status:
                    errors_by_status[status] = []
                errors_by_status[status].append(error)
            
            for status, errors in errors_by_status.items():
                print(f"\n  Status {status}: {len(errors)} errors")
                for error in errors[:3]:
                    print(f"    - {error['url']} ({error['role']})")
        
        # Save detailed results to file
        with open('test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed': total_tests - total_failures,
                    'failed': total_failures,
                    'timestamp': datetime.now().isoformat()
                },
                'results': self.results,
                'console_errors': self.console_errors,
                'network_errors': self.network_errors
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to test_results.json")

async def main():
    """Main test runner"""
    print("🚀 Starting comprehensive frontend tests...")
    print("This will test all pages for all user roles.")
    print("Please ensure the frontend is running on http://localhost:3000")
    
    tester = PageTester()
    await tester.test_all_roles()

if __name__ == "__main__":
    asyncio.run(main())