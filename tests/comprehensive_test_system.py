"""
Comprehensive Testing System for SynapseDTE
Covers all UI pages for every role and tests every API endpoint
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
from playwright.async_api import async_playwright, Page, Browser
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results/comprehensive_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Test Configuration
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8001')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
API_TIMEOUT = 30  # seconds
UI_TIMEOUT = 30000  # milliseconds

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

class UserRole(Enum):
    ADMIN = "Admin"
    TEST_EXECUTIVE = "Test Executive"
    TESTER = "Tester"
    REPORT_OWNER = "Report Owner"
    REPORT_OWNER_EXECUTIVE = "Report Owner Executive"
    DATA_EXECUTIVE = "Data Executive"
    DATA_OWNER = "Data Owner"

@dataclass
class TestResult:
    test_name: str
    test_type: str  # 'ui' or 'api'
    role: Optional[str]
    status: TestStatus
    duration: float
    error: Optional[str] = None
    screenshot: Optional[str] = None
    request_data: Optional[Dict] = None
    response_data: Optional[Dict] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class TestProgress:
    total_tests: int
    completed_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    start_time: datetime
    end_time: Optional[datetime] = None
    
    @property
    def progress_percentage(self) -> float:
        if self.total_tests == 0:
            return 0
        return (self.completed_tests / self.total_tests) * 100
    
    @property
    def success_rate(self) -> float:
        if self.completed_tests == 0:
            return 0
        return (self.passed_tests / self.completed_tests) * 100
    
    @property
    def duration(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

class TestCredentials:
    """Test user credentials for each role"""
    USERS = {
        UserRole.ADMIN: {
            "email": "admin@example.com",
            "password": "password123"
        },
        UserRole.TEST_EXECUTIVE: {
            "email": "testmgr@synapsefinancial.com",
            "password": "Test123!"
        },
        UserRole.TESTER: {
            "email": "tester@synapsefinancial.com",
            "password": "Test123!"
        },
        UserRole.REPORT_OWNER: {
            "email": "reportowner@synapsefinancial.com",
            "password": "Test123!"
        },
        UserRole.REPORT_OWNER_EXECUTIVE: {
            "email": "reportexec@synapsefinancial.com",
            "password": "Test123!"
        },
        UserRole.DATA_EXECUTIVE: {
            "email": "dataexec@synapsefinancial.com",
            "password": "Test123!"
        },
        UserRole.DATA_OWNER: {
            "email": "dataowner@synapsefinancial.com",
            "password": "Test123!"
        }
    }

class UIPageInventory:
    """Inventory of all UI pages accessible by each role"""
    PAGES_BY_ROLE = {
        UserRole.ADMIN: [
            # Admin has access to all pages
            "/",
            "/login",
            "/dashboard",
            "/cycles",
            "/reports",
            "/analytics",
            "/users",
            "/admin/users",
            "/admin/lobs",
            "/admin/reports",
            "/admin/data-sources",
            "/admin/sla-configuration",
            "/admin/rbac",
            "/admin/settings",
            # Plus all workflow phase pages (with test data)
        ],
        UserRole.TEST_EXECUTIVE: [
            "/",
            "/dashboard",
            "/cycles",
            "/reports",
            "/analytics",
            "/users",
            # Workflow phase pages (with test data)
        ],
        UserRole.TESTER: [
            "/",
            "/tester-dashboard",
            "/cycles",
            "/reports",
            # Specific workflow phase pages
        ],
        UserRole.REPORT_OWNER: [
            "/",
            "/report-owner-dashboard",
            "/reports",
            # Scoping review pages
        ],
        UserRole.REPORT_OWNER_EXECUTIVE: [
            "/",
            "/report-owner-dashboard",
            "/reports",
            "/analytics",
        ],
        UserRole.DATA_EXECUTIVE: [
            "/",
            "/cdo-dashboard",
            # CDO assignment pages
        ],
        UserRole.DATA_OWNER: [
            "/",
            "/data-owner-dashboard",
            # Data provider phase pages
        ]
    }

class APIEndpointInventory:
    """Inventory of all API endpoints"""
    ENDPOINTS = {
        # Authentication
        "auth": {
            "login": ("POST", "/api/v1/auth/login", None),
            "logout": ("POST", "/api/v1/auth/logout", "all"),
            "change_password": ("POST", "/api/v1/auth/change-password", "all"),
        },
        # Users
        "users": {
            "list": ("GET", "/api/v1/users", ["Admin", "Test Executive"]),
            "create": ("POST", "/api/v1/users", ["Admin"]),
            "read": ("GET", "/api/v1/users/{user_id}", ["Admin", "Test Executive"]),
            "update": ("PUT", "/api/v1/users/{user_id}", ["Admin"]),
            "delete": ("DELETE", "/api/v1/users/{user_id}", ["Admin"]),
        },
        # Cycles
        "cycles": {
            "list": ("GET", "/api/v1/cycles", "all"),
            "create": ("POST", "/api/v1/cycles", ["Admin", "Test Executive"]),
            "read": ("GET", "/api/v1/cycles/{cycle_id}", "all"),
            "update": ("PUT", "/api/v1/cycles/{cycle_id}", ["Admin", "Test Executive"]),
            "delete": ("DELETE", "/api/v1/cycles/{cycle_id}", ["Admin"]),
        },
        # Reports
        "reports": {
            "list": ("GET", "/api/v1/reports", "all"),
            "create": ("POST", "/api/v1/reports", ["Admin"]),
            "read": ("GET", "/api/v1/reports/{report_id}", "all"),
            "update": ("PUT", "/api/v1/reports/{report_id}", ["Admin"]),
            "delete": ("DELETE", "/api/v1/reports/{report_id}", ["Admin"]),
        },
        # Planning Phase
        "planning": {
            "create": ("POST", "/api/v1/planning/cycles/{cycle_id}/reports/{report_id}/attributes", ["Test Executive", "Tester"]),
            "list": ("GET", "/api/v1/planning/cycles/{cycle_id}/reports/{report_id}/attributes", "all"),
            "update": ("PUT", "/api/v1/planning/cycles/{cycle_id}/reports/{report_id}/attributes/{attribute_id}", ["Test Executive", "Tester"]),
            "complete": ("POST", "/api/v1/planning/cycles/{cycle_id}/reports/{report_id}/complete", ["Test Executive"]),
        },
        # Scoping Phase
        "scoping": {
            "cycle_report_sample_selection_samples": ("GET", "/api/v1/scoping/cycles/{cycle_id}/reports/{report_id}/samples", "all"),
            "create_samples": ("POST", "/api/v1/scoping/cycles/{cycle_id}/reports/{report_id}/samples", ["Test Executive", "Tester"]),
            "approve": ("POST", "/api/v1/scoping/cycles/{cycle_id}/reports/{report_id}/approve", ["Report Owner", "Report Owner Executive"]),
        },
        # Testing Execution
        "testing": {
            "test_cases": ("GET", "/api/v1/testing-execution/cycles/{cycle_id}/reports/{report_id}/test-cases", ["Tester", "Test Executive"]),
            "execute": ("POST", "/api/v1/testing-execution/test-cases/{test_case_id}/execute", ["Tester"]),
            "results": ("GET", "/api/v1/testing-execution/test-cases/{test_case_id}/results", "all"),
        },
        # Observations
        "observations": {
            "list": ("GET", "/api/v1/observation-management/cycles/{cycle_id}/reports/{report_id}/observations", "all"),
            "create": ("POST", "/api/v1/observation-management/observations", ["Tester", "Test Executive"]),
            "update": ("PUT", "/api/v1/observation-management/observations/{observation_id}", ["Tester", "Test Executive"]),
            "approve": ("POST", "/api/v1/observation-management/observations/{observation_id}/approve", ["Report Owner", "Report Owner Executive"]),
        },
        # Dashboards
        "dashboards": {
            "executive": ("GET", "/api/v1/dashboards/executive", ["Report Owner Executive", "Admin"]),
            "cdo": ("GET", "/api/v1/dashboards/cdo", ["Data Executive"]),
            "data_owner": ("GET", "/api/v1/dashboards/data-owner", ["Data Owner"]),
        }
    }

class ComprehensiveTestSystem:
    def __init__(self, results_dir: str = "test_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        self.test_results: List[TestResult] = []
        self.progress = TestProgress(
            total_tests=0,
            completed_tests=0,
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            start_time=datetime.now()
        )
        
        # Create subdirectories for screenshots and logs
        (self.results_dir / "screenshots").mkdir(exist_ok=True)
        (self.results_dir / "api_responses").mkdir(exist_ok=True)
        
    async def run_all_tests(self):
        """Run all UI and API tests for every role"""
        logger.info("Starting comprehensive test suite")
        self.progress.start_time = datetime.now()
        
        # Calculate total tests
        ui_tests = sum(len(pages) for pages in UIPageInventory.PAGES_BY_ROLE.values())
        api_tests = sum(len(endpoints) for endpoints in APIEndpointInventory.ENDPOINTS.values()) * len(UserRole)
        self.progress.total_tests = ui_tests + api_tests
        
        # Run API tests first (faster)
        logger.info(f"Running {api_tests} API tests...")
        await self.run_api_tests()
        
        # Run UI tests
        logger.info(f"Running {ui_tests} UI tests...")
        await self.run_ui_tests()
        
        # Finalize results
        self.progress.end_time = datetime.now()
        await self.generate_report()
        
    async def run_api_tests(self):
        """Test all API endpoints for each role"""
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            for role in UserRole:
                logger.info(f"Testing API endpoints for role: {role.value}")
                
                # Login as this role
                token = await self.api_login(client, role)
                if not token:
                    logger.error(f"Failed to login as {role.value}")
                    continue
                
                # Test each endpoint category
                for category, endpoints in APIEndpointInventory.ENDPOINTS.items():
                    for endpoint_name, (method, path, allowed_roles) in endpoints.items():
                        test_name = f"API_{category}_{endpoint_name}_{role.value}"
                        
                        # Skip if role not allowed
                        if allowed_roles and allowed_roles != "all" and role.value not in allowed_roles:
                            await self.record_test_result(
                                TestResult(
                                    test_name=test_name,
                                    test_type="api",
                                    role=role.value,
                                    status=TestStatus.SKIPPED,
                                    duration=0,
                                    error="Role not authorized for this endpoint"
                                )
                            )
                            continue
                        
                        # Run the test
                        await self.test_api_endpoint(
                            client, token, test_name, method, path, role
                        )
    
    async def run_ui_tests(self):
        """Test all UI pages for each role"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            for role, pages in UIPageInventory.PAGES_BY_ROLE.items():
                logger.info(f"Testing UI pages for role: {role.value}")
                
                # Create a new context for each role
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True
                )
                page = await context.new_page()
                
                # Login as this role
                if await self.ui_login(page, role):
                    # Test each page
                    for page_path in pages:
                        test_name = f"UI_{page_path.replace('/', '_')}_{role.value}"
                        await self.test_ui_page(page, test_name, page_path, role)
                else:
                    logger.error(f"Failed to login as {role.value}")
                
                await context.close()
            
            await browser.close()
    
    async def api_login(self, client: httpx.AsyncClient, role: UserRole) -> Optional[str]:
        """Login via API and return auth token"""
        creds = TestCredentials.USERS.get(role)
        if not creds:
            return None
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"email": creds["email"], "password": creds["password"]}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
        except Exception as e:
            logger.error(f"API login failed for {role.value}: {e}")
        
        return None
    
    async def ui_login(self, page: Page, role: UserRole) -> bool:
        """Login via UI"""
        creds = TestCredentials.USERS.get(role)
        if not creds:
            return False
        
        try:
            await page.goto(f"{FRONTEND_URL}/login")
            await page.fill('input[name="email"]', creds["email"])
            await page.fill('input[name="password"]', creds["password"])
            await page.click('button[type="submit"]')
            
            # Wait for navigation
            await page.wait_for_navigation(timeout=UI_TIMEOUT)
            return True
        except Exception as e:
            logger.error(f"UI login failed for {role.value}: {e}")
            return False
    
    async def test_api_endpoint(
        self,
        client: httpx.AsyncClient,
        token: str,
        test_name: str,
        method: str,
        path: str,
        role: UserRole
    ):
        """Test a single API endpoint"""
        start_time = time.time()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Prepare test data based on endpoint
        test_data = self.get_test_data_for_endpoint(path, method)
        
        # Replace path parameters with test values
        test_path = self.prepare_test_path(path)
        
        try:
            # Make the request
            if method == "GET":
                response = await client.get(f"{BASE_URL}{test_path}", headers=headers)
            elif method == "POST":
                response = await client.post(f"{BASE_URL}{test_path}", headers=headers, json=test_data)
            elif method == "PUT":
                response = await client.put(f"{BASE_URL}{test_path}", headers=headers, json=test_data)
            elif method == "DELETE":
                response = await client.delete(f"{BASE_URL}{test_path}", headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            duration = time.time() - start_time
            
            # Determine test result
            if response.status_code < 400:
                status = TestStatus.PASSED
                error = None
            else:
                status = TestStatus.FAILED
                error = f"HTTP {response.status_code}: {response.text[:200]}"
            
            # Save response data
            response_file = self.results_dir / "api_responses" / f"{test_name}.json"
            response_file.write_text(json.dumps({
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }, indent=2, default=str))
            
            await self.record_test_result(
                TestResult(
                    test_name=test_name,
                    test_type="api",
                    role=role.value,
                    status=status,
                    duration=duration,
                    error=error,
                    request_data={"method": method, "path": test_path, "data": test_data},
                    response_data={"status_code": response.status_code}
                )
            )
            
        except Exception as e:
            duration = time.time() - start_time
            await self.record_test_result(
                TestResult(
                    test_name=test_name,
                    test_type="api",
                    role=role.value,
                    status=TestStatus.FAILED,
                    duration=duration,
                    error=str(e)
                )
            )
    
    async def test_ui_page(self, page: Page, test_name: str, page_path: str, role: UserRole):
        """Test a single UI page"""
        start_time = time.time()
        
        try:
            # Navigate to page
            await page.goto(f"{FRONTEND_URL}{page_path}", wait_until="networkidle", timeout=UI_TIMEOUT)
            
            # Wait for page to fully load
            await page.wait_for_load_state("domcontentloaded")
            
            # Take screenshot
            screenshot_path = self.results_dir / "screenshots" / f"{test_name}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
            # Basic checks
            # 1. Check page loaded without errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            
            # 2. Check for common error indicators
            error_indicators = await page.locator("text=/error|failed|exception/i").count()
            
            # 3. Check page has content
            body_text = await page.text_content("body")
            has_content = len(body_text.strip()) > 100
            
            duration = time.time() - start_time
            
            # Determine test result
            if error_indicators > 0 or console_errors or not has_content:
                status = TestStatus.FAILED
                error = f"Page errors: {error_indicators}, Console errors: {len(console_errors)}, Has content: {has_content}"
            else:
                status = TestStatus.PASSED
                error = None
            
            await self.record_test_result(
                TestResult(
                    test_name=test_name,
                    test_type="ui",
                    role=role.value,
                    status=status,
                    duration=duration,
                    error=error,
                    screenshot=str(screenshot_path.relative_to(self.results_dir))
                )
            )
            
        except Exception as e:
            duration = time.time() - start_time
            await self.record_test_result(
                TestResult(
                    test_name=test_name,
                    test_type="ui",
                    role=role.value,
                    status=TestStatus.FAILED,
                    duration=duration,
                    error=str(e)
                )
            )
    
    async def record_test_result(self, result: TestResult):
        """Record a test result and update progress"""
        self.test_results.append(result)
        self.progress.completed_tests += 1
        
        if result.status == TestStatus.PASSED:
            self.progress.passed_tests += 1
        elif result.status == TestStatus.FAILED:
            self.progress.failed_tests += 1
        elif result.status == TestStatus.SKIPPED:
            self.progress.skipped_tests += 1
        
        # Log progress
        logger.info(
            f"[{self.progress.completed_tests}/{self.progress.total_tests}] "
            f"{result.test_name}: {result.status.value} "
            f"({self.progress.progress_percentage:.1f}% complete)"
        )
    
    def get_test_data_for_endpoint(self, path: str, method: str) -> Dict:
        """Generate test data for different endpoints"""
        if "login" in path:
            return {"username": "test", "password": "test"}
        elif "users" in path and method == "POST":
            return {
                "username": f"testuser_{int(time.time())}",
                "email": f"test_{int(time.time())}@example.com",
                "password": "TestPass123!",
                "role": "Tester"
            }
        elif "cycles" in path and method == "POST":
            return {
                "name": f"Test Cycle {int(time.time())}",
                "description": "Automated test cycle",
                "start_date": datetime.now().isoformat(),
                "end_date": datetime.now().isoformat()
            }
        # Add more test data as needed
        return {}
    
    def prepare_test_path(self, path: str) -> str:
        """Replace path parameters with test values"""
        # Replace common parameters
        replacements = {
            "{user_id}": "1",
            "{cycle_id}": "1",
            "{report_id}": "1",
            "{attribute_id}": "1",
            "{test_case_id}": "1",
            "{observation_id}": "1"
        }
        
        for param, value in replacements.items():
            path = path.replace(param, value)
        
        return path
    
    async def generate_report(self):
        """Generate comprehensive test report"""
        # Summary report
        summary = {
            "test_run": {
                "start_time": self.progress.start_time.isoformat(),
                "end_time": self.progress.end_time.isoformat() if self.progress.end_time else None,
                "duration_seconds": self.progress.duration,
                "total_tests": self.progress.total_tests,
                "completed_tests": self.progress.completed_tests,
                "passed_tests": self.progress.passed_tests,
                "failed_tests": self.progress.failed_tests,
                "skipped_tests": self.progress.skipped_tests,
                "success_rate": self.progress.success_rate,
            },
            "by_type": {
                "ui": {
                    "total": len([r for r in self.test_results if r.test_type == "ui"]),
                    "passed": len([r for r in self.test_results if r.test_type == "ui" and r.status == TestStatus.PASSED]),
                    "failed": len([r for r in self.test_results if r.test_type == "ui" and r.status == TestStatus.FAILED]),
                },
                "api": {
                    "total": len([r for r in self.test_results if r.test_type == "api"]),
                    "passed": len([r for r in self.test_results if r.test_type == "api" and r.status == TestStatus.PASSED]),
                    "failed": len([r for r in self.test_results if r.test_type == "api" and r.status == TestStatus.FAILED]),
                }
            },
            "by_role": {}
        }
        
        # Group results by role
        for role in UserRole:
            role_results = [r for r in self.test_results if r.role == role.value]
            summary["by_role"][role.value] = {
                "total": len(role_results),
                "passed": len([r for r in role_results if r.status == TestStatus.PASSED]),
                "failed": len([r for r in role_results if r.status == TestStatus.FAILED]),
                "skipped": len([r for r in role_results if r.status == TestStatus.SKIPPED]),
            }
        
        # Save summary
        summary_file = self.results_dir / "test_summary.json"
        summary_file.write_text(json.dumps(summary, indent=2, default=str))
        
        # Save detailed results
        results_file = self.results_dir / "test_results.json"
        results_data = [asdict(r) for r in self.test_results]
        results_file.write_text(json.dumps(results_data, indent=2, default=str))
        
        # Generate HTML report
        await self.generate_html_report(summary)
        
        logger.info(f"Test report generated: {self.results_dir}")
        logger.info(f"Summary: {summary['test_run']}")
    
    async def generate_html_report(self, summary: Dict):
        """Generate an HTML report with test results"""
        html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>SynapseDTE Comprehensive Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1, h2, h3 { color: #333; }
        .summary { background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .metric-value { font-size: 24px; font-weight: bold; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .skipped { color: #6c757d; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; font-weight: bold; }
        tr:hover { background-color: #f5f5f5; }
        .test-failed { background-color: #ffebee; }
        .test-passed { background-color: #e8f5e9; }
        .test-skipped { background-color: #f5f5f5; }
        .progress-bar { width: 100%; height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background-color: #4caf50; text-align: center; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>SynapseDTE Comprehensive Test Report</h1>
        <div class="summary">
            <h2>Test Summary</h2>
            <div class="metric">
                <div class="metric-value">{total_tests}</div>
                <div>Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value passed">{passed_tests}</div>
                <div>Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value failed">{failed_tests}</div>
                <div>Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value skipped">{skipped_tests}</div>
                <div>Skipped</div>
            </div>
            <div class="metric">
                <div class="metric-value">{success_rate:.1f}%</div>
                <div>Success Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">{duration:.1f}s</div>
                <div>Duration</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress_percentage:.1f}%">
                {progress_percentage:.1f}% Complete
            </div>
        </div>
        
        <h2>Results by Type</h2>
        <table>
            <tr>
                <th>Type</th>
                <th>Total</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Success Rate</th>
            </tr>
            <tr>
                <td>UI Tests</td>
                <td>{ui_total}</td>
                <td class="passed">{ui_passed}</td>
                <td class="failed">{ui_failed}</td>
                <td>{ui_success_rate:.1f}%</td>
            </tr>
            <tr>
                <td>API Tests</td>
                <td>{api_total}</td>
                <td class="passed">{api_passed}</td>
                <td class="failed">{api_failed}</td>
                <td>{api_success_rate:.1f}%</td>
            </tr>
        </table>
        
        <h2>Results by Role</h2>
        <table>
            <tr>
                <th>Role</th>
                <th>Total</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Skipped</th>
                <th>Success Rate</th>
            </tr>
            {role_rows}
        </table>
        
        <h2>Failed Tests</h2>
        <table>
            <tr>
                <th>Test Name</th>
                <th>Type</th>
                <th>Role</th>
                <th>Error</th>
                <th>Duration</th>
            </tr>
            {failed_rows}
        </table>
        
        <p style="text-align: center; margin-top: 40px; color: #666;">
            Generated on {timestamp}
        </p>
    </div>
</body>
</html>
        '''
        
        # Calculate success rates
        ui_success_rate = (summary["by_type"]["ui"]["passed"] / summary["by_type"]["ui"]["total"] * 100) if summary["by_type"]["ui"]["total"] > 0 else 0
        api_success_rate = (summary["by_type"]["api"]["passed"] / summary["by_type"]["api"]["total"] * 100) if summary["by_type"]["api"]["total"] > 0 else 0
        
        # Generate role rows
        role_rows = []
        for role, stats in summary["by_role"].items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            role_rows.append(f'''
            <tr>
                <td>{role}</td>
                <td>{stats["total"]}</td>
                <td class="passed">{stats["passed"]}</td>
                <td class="failed">{stats["failed"]}</td>
                <td class="skipped">{stats["skipped"]}</td>
                <td>{success_rate:.1f}%</td>
            </tr>
            ''')
        
        # Generate failed test rows
        failed_tests = [r for r in self.test_results if r.status == TestStatus.FAILED]
        failed_rows = []
        for test in failed_tests[:50]:  # Show first 50 failures
            failed_rows.append(f'''
            <tr class="test-failed">
                <td>{test.test_name}</td>
                <td>{test.test_type.upper()}</td>
                <td>{test.role}</td>
                <td>{test.error[:100]}...</td>
                <td>{test.duration:.2f}s</td>
            </tr>
            ''')
        
        # Fill template
        html_content = html_template.format(
            total_tests=summary["test_run"]["total_tests"],
            passed_tests=summary["test_run"]["passed_tests"],
            failed_tests=summary["test_run"]["failed_tests"],
            skipped_tests=summary["test_run"]["skipped_tests"],
            success_rate=summary["test_run"]["success_rate"],
            duration=summary["test_run"]["duration_seconds"] or 0,
            progress_percentage=self.progress.progress_percentage,
            ui_total=summary["by_type"]["ui"]["total"],
            ui_passed=summary["by_type"]["ui"]["passed"],
            ui_failed=summary["by_type"]["ui"]["failed"],
            ui_success_rate=ui_success_rate,
            api_total=summary["by_type"]["api"]["total"],
            api_passed=summary["by_type"]["api"]["passed"],
            api_failed=summary["by_type"]["api"]["failed"],
            api_success_rate=api_success_rate,
            role_rows="\n".join(role_rows),
            failed_rows="\n".join(failed_rows) if failed_rows else '<tr><td colspan="5" style="text-align: center;">No failed tests!</td></tr>',
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Save HTML report
        html_file = self.results_dir / "test_report.html"
        html_file.write_text(html_content)
        logger.info(f"HTML report generated: {html_file}")

async def main():
    """Main entry point for running the comprehensive test suite"""
    test_system = ComprehensiveTestSystem()
    await test_system.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())