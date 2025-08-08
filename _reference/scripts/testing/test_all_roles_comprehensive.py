#!/usr/bin/env python3
"""
Comprehensive test of all pages for all roles with console error detection
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Page, ConsoleMessage, Response
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
FRONTEND_URL = "http://localhost:3001"
BACKEND_URL = "http://localhost:8000"
TIMEOUT = 30000  # 30 seconds

# Test credentials for each role
TEST_USERS = {
    "Tester": {
        "email": "tester@synapse.com",
        "password": "TestUser123!"
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
    "Data Executive": {
        "email": "cdo@synapse.com",
        "password": "TestUser123!"
    },
    "Data Owner": {
        "email": "provider@synapse.com",
        "password": "TestUser123!"
    }
}

# Pages to test for each role
PAGES_BY_ROLE = {
    "Tester": [
        "/dashboard",
        "/cycles",
        "/cycles/9/reports/156",
        "/cycles/9/reports/156/planning",
        "/cycles/9/reports/156/scoping", 
        "/cycles/9/reports/156/sample-selection",
        "/cycles/9/reports/156/data-owner",
        "/cycles/9/reports/156/request-info",
        "/cycles/9/reports/156/test-execution",
        "/cycles/9/reports/156/observation-management"
    ],
    "Test Executive": [
        "/dashboard",
        "/cycles",
        "/cycles/9",
        "/reports",
        "/analytics",
        "/users",
        "/admin/sla-configuration"
    ],
    "Report Owner": [
        "/dashboard",
        "/reports",
        "/analytics",
        "/cycles/9/reports/156/request-info",
        "/cycles/9/reports/156/observation-management"
    ],
    "Report Owner Executive": [
        "/dashboard",
        "/reports",
        "/analytics",
        "/executive-dashboard"
    ],
    "Data Executive": [
        "/dashboard",
        "/cdo-dashboard",
        "/cycles/9/reports/156/data-owner"
    ],
    "Data Owner": [
        "/dashboard",
        "/data-owner-dashboard",
        "/cycles/9/reports/156/request-info"
    ]
}

class TestResult:
    def __init__(self):
        self.role = ""
        self.page_url = ""
        self.success = False
        self.console_errors: List[str] = []
        self.network_errors: List[str] = []
        self.page_errors: List[str] = []
        self.screenshot_path: Optional[str] = None
        self.duration = 0.0
        self.timestamp = datetime.now()

class ComprehensivePageTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.console_messages: List[ConsoleMessage] = []
        self.failed_requests: List[Response] = []
        
    async def test_all_roles(self):
        """Test all pages for all roles"""
        logger.info("Starting comprehensive role-based testing")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set to True for CI
            
            for role, credentials in TEST_USERS.items():
                logger.info(f"\n{'='*60}")
                logger.info(f"Testing role: {role}")
                logger.info(f"{'='*60}")
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()
                
                # Set up console error detection
                await self.setup_error_detection(page)
                
                # Login
                login_success = await self.login(page, credentials)
                if not login_success:
                    logger.error(f"Login failed for role: {role}")
                    await context.close()
                    continue
                
                # Test each page for this role
                pages_to_test = PAGES_BY_ROLE.get(role, [])
                for page_url in pages_to_test:
                    await self.test_page(page, role, page_url)
                
                await context.close()
            
            await browser.close()
        
        # Generate report
        self.generate_report()
    
    async def setup_error_detection(self, page: Page):
        """Set up console and network error detection"""
        self.console_messages = []
        self.failed_requests = []
        
        # Capture console messages
        page.on("console", lambda msg: self.console_messages.append(msg))
        
        # Capture failed network requests
        page.on("response", lambda response: self.handle_response(response))
        
        # Capture page errors
        page.on("pageerror", lambda error: logger.error(f"Page error: {error}"))
    
    def handle_response(self, response: Response):
        """Handle network responses"""
        if response.status >= 400:
            self.failed_requests.append(response)
            logger.warning(f"Failed request: {response.status} {response.url}")
    
    async def login(self, page: Page, credentials: Dict[str, str]) -> bool:
        """Login with given credentials"""
        try:
            logger.info(f"Logging in with email: {credentials['email']}")
            
            # Go to login page
            await page.goto(f"{FRONTEND_URL}/login", wait_until="networkidle")
            
            # Fill login form
            await page.fill('input[name="email"]', credentials['email'])
            await page.fill('input[name="password"]', credentials['password'])
            
            # Click login button - handle webpack overlay
            try:
                # Try to remove webpack overlay if present
                await page.evaluate("""
                    const overlay = document.querySelector('#webpack-dev-server-client-overlay');
                    if (overlay) overlay.remove();
                """)
            except:
                pass
            
            # Force click using JavaScript if normal click fails
            await page.evaluate("""
                const button = document.querySelector('button[type="submit"]');
                if (button) button.click();
            """)
            
            # Wait for navigation
            await page.wait_for_load_state("networkidle")
            
            # Check if login was successful
            try:
                # Wait for any dashboard redirect
                await page.wait_for_url("**/dashboard/**", timeout=5000)
                logger.info(f"Login successful - redirected to: {page.url}")
                return True
            except:
                try:
                    # Alternative check for user menu
                    await page.wait_for_selector('[data-testid="user-menu"]', timeout=2000)
                    logger.info("Login successful - user menu found")
                    return True
                except:
                    # Check URL for any dashboard
                    current_url = page.url
                    if any(dashboard in current_url for dashboard in [
                        "/dashboard", "/cdo-dashboard", "/data-owner-dashboard", 
                        "/executive-dashboard", "/tester-dashboard"
                    ]):
                        logger.info(f"Login successful - on dashboard: {current_url}")
                        return True
                    
                    # Take screenshot for debugging
                    await page.screenshot(path="test_results/login_failed.png")
                    logger.error(f"Login failed - current URL: {current_url}")
                    return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    async def test_page(self, page: Page, role: str, page_url: str):
        """Test a single page"""
        result = TestResult()
        result.role = role
        result.page_url = page_url
        
        start_time = datetime.now()
        
        try:
            logger.info(f"\nTesting page: {page_url}")
            
            # Clear previous console messages
            self.console_messages.clear()
            self.failed_requests.clear()
            
            # Navigate to page
            full_url = f"{FRONTEND_URL}{page_url}"
            response = await page.goto(full_url, wait_until="networkidle", timeout=TIMEOUT)
            
            # Wait for content to load
            await page.wait_for_timeout(2000)
            
            # Check for console errors (filter out webpack warnings)
            console_errors = []
            for msg in self.console_messages:
                if msg.type in ["error", "warning"]:
                    # Skip webpack-related warnings
                    if any(skip in msg.text.lower() for skip in [
                        'webpack', 'hot update', 'source map', '[hmr]', 
                        'failed to load', 'devtools', 'react-refresh'
                    ]):
                        continue
                    error_text = f"{msg.type.upper()}: {msg.text}"
                    console_errors.append(error_text)
                    logger.warning(f"Console {error_text}")
            
            result.console_errors = console_errors
            
            # Check for network errors
            network_errors = []
            for failed_req in self.failed_requests:
                error_text = f"{failed_req.status} {failed_req.url}"
                network_errors.append(error_text)
            
            result.network_errors = network_errors
            
            # Check page content
            try:
                # Check for error messages on page
                error_elements = await page.query_selector_all('[class*="error"], [class*="Error"]')
                for element in error_elements:
                    text = await element.text_content()
                    if text and len(text.strip()) > 0:
                        result.page_errors.append(text.strip())
                
                # Check for specific error indicators
                if await page.query_selector('text="403"'):
                    result.page_errors.append("403 Forbidden error on page")
                if await page.query_selector('text="404"'):
                    result.page_errors.append("404 Not Found error on page")
                if await page.query_selector('text="500"'):
                    result.page_errors.append("500 Server error on page")
                    
            except Exception as e:
                logger.error(f"Error checking page content: {e}")
            
            # Take screenshot if there are any errors
            if console_errors or network_errors or result.page_errors:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"test_results/screenshots/{role.replace(' ', '_')}_{page_url.replace('/', '_')}_{timestamp}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                result.screenshot_path = screenshot_path
                logger.info(f"Screenshot saved: {screenshot_path}")
            
            # Determine success
            result.success = (
                len(console_errors) == 0 and 
                len(network_errors) == 0 and 
                len(result.page_errors) == 0
            )
            
            if result.success:
                logger.info(f"✅ Page test passed")
            else:
                logger.error(f"❌ Page test failed")
                
        except Exception as e:
            logger.error(f"Page test error: {e}")
            result.success = False
            result.page_errors.append(str(e))
        
        finally:
            result.duration = (datetime.now() - start_time).total_seconds()
            self.results.append(result)
    
    def generate_report(self):
        """Generate test report"""
        logger.info("\n" + "="*80)
        logger.info("TEST REPORT SUMMARY")
        logger.info("="*80)
        
        # Group results by role
        results_by_role = {}
        for result in self.results:
            if result.role not in results_by_role:
                results_by_role[result.role] = []
            results_by_role[result.role].append(result)
        
        total_tests = len(self.results)
        total_passed = sum(1 for r in self.results if r.success)
        total_failed = total_tests - total_passed
        
        logger.info(f"\nTotal Tests: {total_tests}")
        if total_tests > 0:
            logger.info(f"Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)")
            logger.info(f"Failed: {total_failed} ({total_failed/total_tests*100:.1f}%)")
        else:
            logger.info("No tests were completed")
        
        # Detailed results by role
        for role, results in results_by_role.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Role: {role}")
            logger.info(f"{'='*60}")
            
            for result in results:
                status = "✅ PASS" if result.success else "❌ FAIL"
                logger.info(f"\n{status} {result.page_url}")
                
                if not result.success:
                    if result.console_errors:
                        logger.info("  Console Errors:")
                        for error in result.console_errors:
                            logger.info(f"    - {error}")
                    
                    if result.network_errors:
                        logger.info("  Network Errors:")
                        for error in result.network_errors:
                            logger.info(f"    - {error}")
                    
                    if result.page_errors:
                        logger.info("  Page Errors:")
                        for error in result.page_errors:
                            logger.info(f"    - {error}")
                    
                    if result.screenshot_path:
                        logger.info(f"  Screenshot: {result.screenshot_path}")
        
        # Save detailed report
        report_data = {
            "test_date": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "success_rate": f"{total_passed/total_tests*100:.1f}%" if total_tests > 0 else "0%"
            },
            "results": [
                {
                    "role": r.role,
                    "page": r.page_url,
                    "success": r.success,
                    "console_errors": r.console_errors,
                    "network_errors": r.network_errors,
                    "page_errors": r.page_errors,
                    "screenshot": r.screenshot_path,
                    "duration": r.duration
                }
                for r in self.results
            ]
        }
        
        with open("test_results/comprehensive_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\nDetailed report saved to: test_results/comprehensive_test_report.json")

async def main():
    """Run comprehensive tests"""
    import os
    
    # Create directories
    os.makedirs("test_results/screenshots", exist_ok=True)
    
    # Run tests
    tester = ComprehensivePageTester()
    await tester.test_all_roles()

if __name__ == "__main__":
    asyncio.run(main())