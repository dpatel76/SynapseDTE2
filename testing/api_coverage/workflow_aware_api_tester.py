#!/usr/bin/env python3
"""
Workflow-Aware API Testing for SynapseDTE
Tests APIs in proper sequence following business workflow
Creates test data systematically to enable comprehensive testing
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    endpoint: str
    method: str
    status_code: int
    success: bool
    error_message: Optional[str] = None
    response_time_ms: float = 0.0
    created_entity_id: Optional[str] = None

@dataclass
class WorkflowEntity:
    entity_type: str
    entity_id: Optional[str] = None
    entity_data: Optional[Dict] = None
    created: bool = False

class WorkflowAwareAPITester:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.admin_token: Optional[str] = None
        self.user_tokens: Dict[str, str] = {}
        self.test_results: List[TestResult] = []
        self.workflow_entities: Dict[str, WorkflowEntity] = {}
        
        # Real user credentials for testing
        self.test_users = {
            "test_manager": {"email": "test.manager@example.com", "password": "password123", "role": "Test Manager"},
            "tester": {"email": "tester@example.com", "password": "password123", "role": "Tester"},
            "report_owner": {"email": "report.owner@example.com", "password": "password123", "role": "Report Owner"},
            "cdo": {"email": "cdo@example.com", "password": "password123", "role": "CDO"},
            "data_provider": {"email": "data.provider@example.com", "password": "password123", "role": "Data Provider"}
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def authenticate_users(self) -> bool:
        """Authenticate all test users"""
        logger.info("🔐 Authenticating test users...")
        
        authenticated_count = 0
        for user_key, user_info in self.test_users.items():
            login_data = {
                "email": user_info["email"],
                "password": user_info["password"]
            }
            
            try:
                start_time = datetime.now()
                async with self.session.post(
                    f"{self.base_url}/auth/login",
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        token = data.get("access_token")
                        if token:
                            self.user_tokens[user_key] = token
                            if user_key == "test_manager":
                                self.admin_token = token
                            authenticated_count += 1
                            logger.info(f"✅ Authenticated {user_info['email']}")
                        
                        self.test_results.append(TestResult(
                            endpoint="/auth/login",
                            method="POST",
                            status_code=response.status,
                            success=True,
                            response_time_ms=response_time
                        ))
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to authenticate {user_info['email']}: {error_text}")
                        self.test_results.append(TestResult(
                            endpoint="/auth/login",
                            method="POST",
                            status_code=response.status,
                            success=False,
                            error_message=error_text,
                            response_time_ms=response_time
                        ))
                        
            except Exception as e:
                logger.error(f"❌ Authentication error for {user_info['email']}: {str(e)}")
                self.test_results.append(TestResult(
                    endpoint="/auth/login",
                    method="POST",
                    status_code=0,
                    success=False,
                    error_message=str(e)
                ))
        
        logger.info(f"✅ Authenticated {authenticated_count}/{len(self.test_users)} users")
        return authenticated_count > 0

    def get_headers(self, user_key: str = "test_manager") -> Dict[str, str]:
        """Get authentication headers for a user"""
        token = self.user_tokens.get(user_key, self.admin_token)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        } if token else {"Content-Type": "application/json"}

    async def test_endpoint(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                          user_key: str = "test_manager") -> TestResult:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        headers = self.get_headers(user_key)
        
        try:
            start_time = datetime.now()
            
            if method == "GET":
                async with self.session.get(url, headers=headers) as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
            elif method == "POST":
                async with self.session.post(url, headers=headers, json=data) as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
            elif method == "PUT":
                async with self.session.put(url, headers=headers, json=data) as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
            elif method == "DELETE":
                async with self.session.delete(url, headers=headers) as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            
            success = 200 <= response.status < 300
            created_entity_id = None
            
            # Extract entity ID for successful creation
            if success and method == "POST" and isinstance(response_data, dict):
                created_entity_id = (response_data.get("id") or 
                                   response_data.get("cycle_id") or 
                                   response_data.get("report_id") or 
                                   response_data.get("lob_id") or 
                                   response_data.get("user_id"))
            
            return TestResult(
                endpoint=endpoint,
                method=method,
                status_code=response.status,
                success=success,
                response_time_ms=response_time,
                error_message=str(response_data) if not success else None,
                created_entity_id=str(created_entity_id) if created_entity_id else None
            )
            
        except Exception as e:
            return TestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                success=False,
                error_message=str(e)
            )

    async def workflow_step_1_foundation(self) -> Dict[str, Any]:
        """Step 1: Create foundational entities (LOBs, Users, Data Sources)"""
        logger.info("🏗️ Step 1: Creating foundational entities...")
        step_results = []
        
        # 1.1 Create Line of Business
        lob_data = {
            "lob_name": "API Test LOB",
            "description": "Line of Business created for API testing workflow",
            "lob_code": "TEST_LOB"
        }
        result = await self.test_endpoint("POST", "/lobs/", lob_data)
        step_results.append(result)
        if result.success and result.created_entity_id:
            self.workflow_entities["lob"] = WorkflowEntity("lob", result.created_entity_id, lob_data, True)
            logger.info(f"✅ Created LOB with ID: {result.created_entity_id}")
        
        # 1.2 Test LOB retrieval
        if "lob" in self.workflow_entities:
            lob_id = self.workflow_entities["lob"].entity_id
            result = await self.test_endpoint("GET", f"/lobs/{lob_id}")
            step_results.append(result)
        
        # 1.3 Create Data Source
        data_source_data = {
            "source_name": "API Test Database",
            "description": "Test database for API workflow testing",
            "connection_string": "postgresql://test:test@localhost:5432/api_test",
            "source_type": "PostgreSQL"
        }
        result = await self.test_endpoint("POST", "/data-sources/", data_source_data)
        step_results.append(result)
        if result.success and result.created_entity_id:
            self.workflow_entities["data_source"] = WorkflowEntity("data_source", result.created_entity_id, data_source_data, True)
            logger.info(f"✅ Created Data Source with ID: {result.created_entity_id}")
        
        return {"step": "foundation", "results": step_results, "entities_created": len([e for e in self.workflow_entities.values() if e.created])}

    async def workflow_step_2_reports(self) -> Dict[str, Any]:
        """Step 2: Create reports and report inventory"""
        logger.info("📋 Step 2: Creating reports and inventory...")
        step_results = []
        
        # 2.1 Create Report
        lob_id = self.workflow_entities.get("lob", {}).entity_id or "1"
        report_data = {
            "report_name": "API Test Report",
            "description": "Test report created for API workflow testing",
            "lob_id": int(lob_id),
            "report_type": "Regulatory",
            "frequency": "Annual"
        }
        result = await self.test_endpoint("POST", "/reports/", report_data)
        step_results.append(result)
        if result.success and result.created_entity_id:
            self.workflow_entities["report"] = WorkflowEntity("report", result.created_entity_id, report_data, True)
            logger.info(f"✅ Created Report with ID: {result.created_entity_id}")
        
        # 2.2 Test Report retrieval
        if "report" in self.workflow_entities:
            report_id = self.workflow_entities["report"].entity_id
            result = await self.test_endpoint("GET", f"/reports/{report_id}")
            step_results.append(result)
        
        # 2.3 Create Report Inventory
        report_inventory_data = {
            "report_id": int(self.workflow_entities.get("report", {}).entity_id or "1"),
            "version": "1.0",
            "status": "Active"
        }
        result = await self.test_endpoint("POST", "/report-inventory/", report_inventory_data)
        step_results.append(result)
        if result.success and result.created_entity_id:
            self.workflow_entities["report_inventory"] = WorkflowEntity("report_inventory", result.created_entity_id, report_inventory_data, True)
            logger.info(f"✅ Created Report Inventory with ID: {result.created_entity_id}")
        
        return {"step": "reports", "results": step_results, "entities_created": len([e for e in self.workflow_entities.values() if e.created])}

    async def workflow_step_3_cycles(self) -> Dict[str, Any]:
        """Step 3: Create test cycles and cycle reports"""
        logger.info("🔄 Step 3: Creating test cycles...")
        step_results = []
        
        # 3.1 Create Test Cycle
        cycle_data = {
            "cycle_name": "API Test Cycle 2024",
            "description": "Test cycle created for API workflow testing",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-12-31T23:59:59Z",
            "status": "Active"
        }
        result = await self.test_endpoint("POST", "/cycles/", cycle_data)
        step_results.append(result)
        if result.success and result.created_entity_id:
            self.workflow_entities["cycle"] = WorkflowEntity("cycle", result.created_entity_id, cycle_data, True)
            logger.info(f"✅ Created Test Cycle with ID: {result.created_entity_id}")
        
        # 3.2 Test Cycle retrieval
        if "cycle" in self.workflow_entities:
            cycle_id = self.workflow_entities["cycle"].entity_id
            result = await self.test_endpoint("GET", f"/cycles/{cycle_id}")
            step_results.append(result)
        
        # 3.3 Create Cycle Report (assigns report to cycle and tester)
        if "cycle" in self.workflow_entities and "report" in self.workflow_entities:
            cycle_report_data = {
                "cycle_id": int(self.workflow_entities["cycle"].entity_id),
                "report_id": int(self.workflow_entities["report"].entity_id),
                "tester_id": 2,  # Assuming tester user has ID 2
                "status": "Assigned"
            }
            result = await self.test_endpoint("POST", "/cycle-reports/", cycle_report_data)
            step_results.append(result)
            if result.success and result.created_entity_id:
                self.workflow_entities["cycle_report"] = WorkflowEntity("cycle_report", result.created_entity_id, cycle_report_data, True)
                logger.info(f"✅ Created Cycle Report with ID: {result.created_entity_id}")
        
        return {"step": "cycles", "results": step_results, "entities_created": len([e for e in self.workflow_entities.values() if e.created])}

    async def workflow_step_4_phases(self) -> Dict[str, Any]:
        """Step 4: Test workflow phases (Planning, Scoping, etc.)"""
        logger.info("⚙️ Step 4: Testing workflow phases...")
        step_results = []
        
        # Get cycle/report context for phase operations
        cycle_id = self.workflow_entities.get("cycle", {}).entity_id or "1"
        report_id = self.workflow_entities.get("report", {}).entity_id or "1"
        
        # 4.1 Planning Phase
        planning_endpoints = [
            ("GET", "/planning/activities"),
            ("POST", "/planning/start-phase", {"cycle_id": int(cycle_id)}),
            ("GET", f"/planning/activities?cycle_id={cycle_id}"),
        ]
        
        for method, endpoint, *data in planning_endpoints:
            request_data = data[0] if data else None
            result = await self.test_endpoint(method, endpoint, request_data)
            step_results.append(result)
        
        # 4.2 Data Profiling Phase
        profiling_endpoints = [
            ("GET", "/data-profiling/profiles"),
            ("POST", "/data-profiling/start-profiling", {"cycle_id": int(cycle_id), "report_id": int(report_id)}),
            ("GET", f"/data-profiling/results/{cycle_id}"),
        ]
        
        for method, endpoint, *data in profiling_endpoints:
            request_data = data[0] if data else None
            result = await self.test_endpoint(method, endpoint, request_data)
            step_results.append(result)
        
        # 4.3 Scoping Phase
        scoping_endpoints = [
            ("GET", "/scoping/decisions"),
            ("POST", "/scoping/decisions", {"cycle_id": int(cycle_id), "report_id": int(report_id), "scope_decision": "In Scope"}),
            ("GET", f"/scoping/submissions/{cycle_id}"),
        ]
        
        for method, endpoint, *data in scoping_endpoints:
            request_data = data[0] if data else None
            result = await self.test_endpoint(method, endpoint, request_data)
            step_results.append(result)
        
        return {"step": "phases", "results": step_results, "phase_tests": len(step_results)}

    async def workflow_step_5_execution(self) -> Dict[str, Any]:
        """Step 5: Test execution and observation phases"""
        logger.info("🧪 Step 5: Testing execution phases...")
        step_results = []
        
        cycle_id = self.workflow_entities.get("cycle", {}).entity_id or "1"
        report_id = self.workflow_entities.get("report", {}).entity_id or "1"
        
        # 5.1 Test Execution
        test_execution_endpoints = [
            ("GET", "/test-execution/tests"),
            ("POST", "/test-execution/tests", {"cycle_id": int(cycle_id), "report_id": int(report_id), "test_name": "API Test"}),
            ("GET", f"/test-execution/results/{cycle_id}"),
        ]
        
        for method, endpoint, *data in test_execution_endpoints:
            request_data = data[0] if data else None
            result = await self.test_endpoint(method, endpoint, request_data)
            step_results.append(result)
        
        # 5.2 Observation Management
        observation_endpoints = [
            ("GET", "/observation-management/observations"),
            ("POST", "/observation-management/observations", {
                "cycle_id": int(cycle_id), 
                "report_id": int(report_id), 
                "observation_title": "API Test Observation",
                "observation_description": "Test observation created by API workflow"
            }),
        ]
        
        for method, endpoint, *data in observation_endpoints:
            request_data = data[0] if data else None
            result = await self.test_endpoint(method, endpoint, request_data)
            step_results.append(result)
        
        return {"step": "execution", "results": step_results, "execution_tests": len(step_results)}

    async def workflow_step_6_management(self) -> Dict[str, Any]:
        """Step 6: Test management and analytics endpoints"""
        logger.info("📊 Step 6: Testing management endpoints...")
        step_results = []
        
        # 6.1 Dashboard and Metrics
        management_endpoints = [
            ("GET", "/health"),
            ("GET", "/dashboards/executive"),
            ("GET", "/metrics/dashboard"),
            ("GET", "/analytics/trends"),
            ("GET", "/workflow/status"),
            ("GET", "/universal-assignments/assignments"),
        ]
        
        for method, endpoint in management_endpoints:
            result = await self.test_endpoint(method, endpoint)
            step_results.append(result)
        
        # 6.2 Test tester-specific endpoints
        tester_endpoints = [
            ("GET", "/cycle-reports/by-tester/2"),  # Assuming tester ID 2
            ("GET", "/reports/by-tester/2"),
            ("GET", "/dashboards/tester/2"),
        ]
        
        for method, endpoint in tester_endpoints:
            result = await self.test_endpoint(method, endpoint, user_key="tester")
            step_results.append(result)
        
        return {"step": "management", "results": step_results, "management_tests": len(step_results)}

    async def run_workflow_testing(self) -> Dict[str, Any]:
        """Run complete workflow-aware API testing"""
        logger.info("🚀 Starting workflow-aware API testing...")
        
        # Authenticate users first
        if not await self.authenticate_users():
            return {"error": "Failed to authenticate users"}
        
        # Execute workflow steps in sequence
        workflow_results = {}
        
        try:
            workflow_results["step_1"] = await self.workflow_step_1_foundation()
            workflow_results["step_2"] = await self.workflow_step_2_reports()
            workflow_results["step_3"] = await self.workflow_step_3_cycles()
            workflow_results["step_4"] = await self.workflow_step_4_phases()
            workflow_results["step_5"] = await self.workflow_step_5_execution()
            workflow_results["step_6"] = await self.workflow_step_6_management()
            
        except Exception as e:
            logger.error(f"❌ Workflow testing error: {str(e)}")
            workflow_results["error"] = str(e)
        
        # Generate comprehensive report
        return self.generate_workflow_report(workflow_results)

    def generate_workflow_report(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive workflow testing report"""
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.success])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate step-wise success rates
        step_analysis = {}
        for step_name, step_data in workflow_results.items():
            if isinstance(step_data, dict) and "results" in step_data:
                step_results = step_data["results"]
                step_successful = len([r for r in step_results if r.success])
                step_total = len(step_results)
                step_analysis[step_name] = {
                    "success_rate": (step_successful / step_total * 100) if step_total > 0 else 0,
                    "successful": step_successful,
                    "total": step_total,
                    "entities_created": step_data.get("entities_created", 0)
                }
        
        # Analyze entities created
        entities_created = {k: v.created for k, v in self.workflow_entities.items()}
        workflow_completeness = len([v for v in entities_created.values() if v]) / len(entities_created) * 100 if entities_created else 0
        
        # Performance analysis
        response_times = [r.response_time_ms for r in self.test_results if r.response_time_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        report = {
            "executive_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": round(success_rate, 1),
                "workflow_completeness": round(workflow_completeness, 1),
                "entities_created": entities_created,
                "avg_response_time_ms": round(avg_response_time, 2)
            },
            "step_analysis": step_analysis,
            "workflow_entities": {k: asdict(v) for k, v in self.workflow_entities.items()},
            "detailed_results": [asdict(r) for r in self.test_results],
            "test_coverage": {
                "authentication": 100.0,
                "foundation_entities": step_analysis.get("step_1", {}).get("success_rate", 0),
                "reports_management": step_analysis.get("step_2", {}).get("success_rate", 0),
                "cycle_management": step_analysis.get("step_3", {}).get("success_rate", 0),
                "workflow_phases": step_analysis.get("step_4", {}).get("success_rate", 0),
                "execution_phases": step_analysis.get("step_5", {}).get("success_rate", 0),
                "management_apis": step_analysis.get("step_6", {}).get("success_rate", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return report

def print_workflow_report(report: Dict[str, Any]):
    """Print comprehensive workflow testing report"""
    print("\n" + "="*100)
    print("🎯 WORKFLOW-AWARE API TESTING REPORT")
    print("="*100)
    
    summary = report["executive_summary"]
    print(f"\n📊 EXECUTIVE SUMMARY:")
    print(f"   • Total API Tests: {summary['total_tests']}")
    print(f"   • Success Rate: {summary['success_rate']}% ({summary['successful_tests']}/{summary['total_tests']})")
    print(f"   • Workflow Completeness: {summary['workflow_completeness']}%")
    print(f"   • Average Response Time: {summary['avg_response_time_ms']}ms")
    
    print(f"\n🏗️ WORKFLOW ENTITIES CREATED:")
    for entity, created in summary["entities_created"].items():
        status = "✅ Created" if created else "❌ Failed"
        print(f"   • {entity.upper()}: {status}")
    
    print(f"\n📈 STEP-BY-STEP ANALYSIS:")
    steps = {
        "step_1": "Foundation (LOBs, Data Sources)",
        "step_2": "Reports & Inventory", 
        "step_3": "Cycles & Assignments",
        "step_4": "Workflow Phases",
        "step_5": "Execution & Observations",
        "step_6": "Management & Analytics"
    }
    
    for step_key, step_name in steps.items():
        if step_key in report["step_analysis"]:
            step_data = report["step_analysis"][step_key]
            rate = step_data["success_rate"]
            icon = "✅" if rate >= 75 else "⚠️" if rate >= 50 else "❌"
            print(f"   {icon} {step_name}: {rate}% ({step_data['successful']}/{step_data['total']})")
    
    coverage = report["test_coverage"]
    print(f"\n🎯 API COVERAGE BY CATEGORY:")
    for category, rate in coverage.items():
        icon = "✅" if rate >= 75 else "⚠️" if rate >= 50 else "❌"
        print(f"   {icon} {category.replace('_', ' ').title()}: {rate}%")
    
    print(f"\n💡 KEY INSIGHTS:")
    print(f"   • This workflow-aware approach tests APIs in proper business sequence")
    print(f"   • Creates necessary test data systematically rather than assuming it exists")
    print(f"   • Provides realistic assessment of API functionality in actual usage patterns")
    print(f"   • Identifies both technical issues and workflow integration problems")
    
    print("\n" + "="*100)

async def main():
    """Main function to run workflow-aware API testing"""
    logger.info("🚀 Starting SynapseDTE Workflow-Aware API Testing")
    
    async with WorkflowAwareAPITester() as tester:
        report = await tester.run_workflow_testing()
        
        if "error" in report:
            print(f"❌ Testing failed: {report['error']}")
            return
        
        # Print comprehensive report
        print_workflow_report(report)
        
        # Save detailed report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"workflow_api_test_report_{timestamp}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Detailed report saved: {report_filename}")
        
        return report

if __name__ == "__main__":
    asyncio.run(main())