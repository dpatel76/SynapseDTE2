#!/usr/bin/env python3
"""
Comprehensive Frontend Testing for ALL pages and ALL roles
Tests every single page in the application for each user role
"""

import asyncio
from playwright.async_api import async_playwright, Page
import json
from datetime import datetime
from typing import Dict, List, Tuple

# All test users
TEST_USERS = {
    "Admin": {"email": "admin@synapsedt.com", "password": "password123"},
    "Test Executive": {"email": "test.manager@example.com", "password": "password123"},
    "Tester": {"email": "tester@example.com", "password": "password123"},
    "Data Owner": {"email": "data.provider@example.com", "password": "password123"},
    "Data Executive": {"email": "cdo@example.com", "password": "password123"},
    "Report Owner": {"email": "report.owner@example.com", "password": "password123"},
    "Report Owner Executive": {"email": "report_owner_executive@example.com", "password": "password123"}
}

# ALL pages in the application
ALL_PAGES = [
    # Dashboards
    ("/", "Home/Dashboard"),
    ("/dashboard", "Main Dashboard"),
    ("/tester-dashboard", "Tester Dashboard"),
    ("/data-executive-dashboard", "Data Executive Dashboard"),
    ("/report-owner-dashboard", "Report Owner Dashboard"),
    
    # Phase pages
    ("/phases/planning", "Planning Phase"),
    ("/phases/simplified-planning", "Simplified Planning"),
    ("/phases/scoping", "Scoping Phase"),
    ("/phases/data-provider-identification", "Data Provider Identification"),
    ("/phases/sample-selection", "Sample Selection"),
    ("/phases/request-information", "Request Information"),
    ("/phases/test-execution", "Test Execution"),
    ("/phases/observation-management", "Observation Management"),
    ("/phases/data-profiling", "Data Profiling"),
    
    # Admin pages
    ("/admin/users", "User Management"),
    ("/admin/reports", "Report Management"),
    ("/admin/system", "System Settings"),
    
    # Other pages
    ("/workflows", "Workflows"),
    ("/reports", "Reports"),
    ("/profile", "Profile"),
    ("/settings", "Settings"),
    ("/help", "Help"),
    
    # Additional pages that might exist
    ("/metrics", "Metrics"),
    ("/audit-logs", "Audit Logs"),
    ("/notifications", "Notifications"),
]

class ComprehensivePageTester:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
    async def run_comprehensive_tests(self):
        """Run tests for all pages and all roles"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for role, credentials in TEST_USERS.items():
                print(f"\n{'='*80}")
                print(f"🧪 TESTING ROLE: {role}")
                print(f"📧 Email: {credentials['email']}")
                print(f"{'='*80}")
                
                context = await browser.new_context()
                page = await context.new_page()
                
                # Set up monitoring
                console_errors = []
                network_errors = []
                
                page.on('console', lambda msg: console_errors.append({
                    'type': msg.type,
                    'text': msg.text,
                    'location': msg.location
                }) if msg.type in ['error', 'warning'] else None)
                
                page.on('response', lambda response: network_errors.append({
                    'url': response.url,
                    'status': response.status,
                    'statusText': response.status_text
                }) if response.status >= 400 else None)
                
                # Test login
                login_result = await self.test_login(page, credentials)
                
                if not login_result['success']:
                    print(f"❌ Login failed: {login_result['error']}")
                    self.results[role] = {'login_failed': True, 'error': login_result['error']}
                    await context.close()
                    continue
                
                print(f"✅ Login successful")
                
                # Test all pages
                page_results = []
                for path, name in ALL_PAGES:
                    result = await self.test_page(page, path, name, console_errors, network_errors)
                    page_results.append(result)
                    
                    # Clear errors for next page
                    console_errors.clear()
                    network_errors.clear()
                
                self.results[role] = {
                    'login': login_result,
                    'pages': page_results
                }
                
                await context.close()
                await asyncio.sleep(1)  # Brief pause between roles
            
            await browser.close()
        
        # Generate report
        self.generate_detailed_report()
    
    async def test_login(self, page: Page, credentials: Dict) -> Dict:
        """Test login functionality"""
        try:
            await page.goto('http://localhost:3000/login', wait_until='networkidle')
            
            # Fill and submit login form
            await page.fill('input[name="email"]', credentials['email'])
            await page.fill('input[name="password"]', credentials['password'])
            await page.click('button[type="submit"]')
            
            # Wait for navigation
            await page.wait_for_url(lambda url: '/login' not in url, timeout=10000)
            
            return {'success': True, 'redirected_to': page.url}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_page(self, page: Page, path: str, name: str, 
                       console_errors: List, network_errors: List) -> Dict:
        """Test a single page"""
        result = {
            'path': path,
            'name': name,
            'accessible': False,
            'load_time': 0,
            'console_errors': 0,
            'network_errors': 0,
            'error': None,
            'redirected': False,
            'elements': {}
        }
        
        start = datetime.now()
        
        try:
            # Navigate to page
            response = await page.goto(f'http://localhost:3000{path}', 
                                     wait_until='networkidle', 
                                     timeout=15000)
            
            result['load_time'] = (datetime.now() - start).total_seconds()
            
            # Check if redirected
            if path not in page.url:
                result['redirected'] = True
                result['redirected_to'] = page.url
            
            # Count page elements
            result['elements'] = {
                'tables': await page.locator('table').count(),
                'buttons': await page.locator('button').count(),
                'forms': await page.locator('form').count(),
                'charts': await page.locator('canvas, svg.recharts-surface').count(),
                'cards': await page.locator('[class*="card"], [class*="Card"]').count(),
            }
            
            result['accessible'] = True
            result['console_errors'] = len(console_errors)
            result['network_errors'] = len(network_errors)
            
            # Print immediate feedback
            status = "✅" if not network_errors else "⚠️"
            print(f"  {status} {name:40} {'(redirected)' if result['redirected'] else ''}")
            
            if console_errors:
                print(f"     ⚠️  {len(console_errors)} console errors")
            if network_errors:
                print(f"     ❌ {len(network_errors)} network errors")
                for err in network_errors[:2]:  # Show first 2
                    print(f"        - {err['status']} {err['url'][:60]}...")
            
        except Exception as e:
            result['error'] = str(e)
            result['load_time'] = (datetime.now() - start).total_seconds()
            print(f"  ❌ {name:40} - {str(e)[:50]}...")
        
        return result
    
    def generate_detailed_report(self):
        """Generate comprehensive test report"""
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        print(f"\n{'='*80}")
        print(f"📊 COMPREHENSIVE TEST REPORT")
        print(f"{'='*80}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total test time: {total_time:.1f} seconds")
        print(f"Roles tested: {len(self.results)}")
        print(f"Pages tested per role: {len(ALL_PAGES)}")
        
        # Summary statistics
        total_pages_tested = 0
        total_accessible = 0
        total_errors = 0
        
        print(f"\n📈 RESULTS BY ROLE")
        print(f"{'='*80}")
        
        for role, results in self.results.items():
            print(f"\n👤 {role}")
            
            if 'login_failed' in results:
                print(f"   ❌ Login failed: {results['error']}")
                continue
            
            pages = results['pages']
            accessible = sum(1 for p in pages if p['accessible'])
            with_errors = sum(1 for p in pages if p['console_errors'] > 0 or p['network_errors'] > 0)
            
            print(f"   ✅ Accessible pages: {accessible}/{len(pages)}")
            print(f"   ⚠️  Pages with errors: {with_errors}")
            
            # Show inaccessible pages
            inaccessible = [p for p in pages if not p['accessible']]
            if inaccessible:
                print(f"   ❌ Inaccessible pages:")
                for p in inaccessible:
                    print(f"      - {p['name']}: {p['error']}")
            
            # Show pages with network errors
            with_network_errors = [p for p in pages if p['network_errors'] > 0]
            if with_network_errors:
                print(f"   🔴 Pages with network errors:")
                for p in with_network_errors[:5]:  # Show first 5
                    print(f"      - {p['name']}: {p['network_errors']} errors")
            
            total_pages_tested += len(pages)
            total_accessible += accessible
            total_errors += sum(p['console_errors'] + p['network_errors'] for p in pages)
        
        # Overall summary
        print(f"\n📊 OVERALL SUMMARY")
        print(f"{'='*80}")
        print(f"Total pages tested: {total_pages_tested}")
        print(f"Total accessible: {total_accessible}")
        print(f"Total errors found: {total_errors}")
        print(f"Success rate: {(total_accessible/total_pages_tested*100):.1f}%")
        
        # Page performance
        print(f"\n⚡ PAGE PERFORMANCE")
        print(f"{'='*80}")
        
        all_page_loads = []
        for role, results in self.results.items():
            if 'pages' in results:
                for page in results['pages']:
                    if page['accessible']:
                        all_page_loads.append((page['name'], page['load_time'], role))
        
        slowest = sorted(all_page_loads, key=lambda x: x[1], reverse=True)[:10]
        print("Slowest loading pages:")
        for name, time, role in slowest:
            print(f"  - {name}: {time:.2f}s ({role})")
        
        # Common errors
        print(f"\n🔍 COMMON ISSUES")
        print(f"{'='*80}")
        
        error_patterns = {}
        for role, results in self.results.items():
            if 'pages' in results:
                for page in results['pages']:
                    if page['network_errors'] > 0:
                        key = f"{page['path']} - Network errors"
                        error_patterns[key] = error_patterns.get(key, 0) + 1
        
        for pattern, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {pattern}: {count} occurrences")
        
        # Save detailed results
        with open('comprehensive_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'duration': total_time,
                'summary': {
                    'total_pages_tested': total_pages_tested,
                    'total_accessible': total_accessible,
                    'total_errors': total_errors,
                    'success_rate': total_accessible/total_pages_tested*100 if total_pages_tested > 0 else 0
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: comprehensive_test_results.json")

async def main():
    """Run comprehensive tests"""
    print("🚀 Starting COMPREHENSIVE frontend testing...")
    print("This will test EVERY page for EVERY user role.")
    print("Please ensure frontend is running on http://localhost:3000")
    
    tester = ComprehensivePageTester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())