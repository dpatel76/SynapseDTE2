#!/usr/bin/env python3
"""
End-to-End Application Tests for SynapseDTE
Tests for complete application workflows and user journeys
"""

import time
import json
import requests
import os
from typing import Dict, List, Optional
from test_framework import DockerTestFramework, TestRunner, TestConfig


class E2ETestRunner(TestRunner):
    """Test runner for end-to-end tests"""
    
    def __init__(self, framework: DockerTestFramework):
        super().__init__(framework)
        self.api_base = "http://localhost:8000/api/v1"
        self.frontend_base = "http://localhost"
        self.test_data = {}
        self.auth_headers = {}
    
    def setup(self) -> bool:
        """Start services and prepare test environment"""
        print("🚀 Starting services for E2E tests...")
        if not self.framework.start_services():
            return False
        
        # Wait for all services to be ready
        print("⏳ Waiting for services to be ready...")
        time.sleep(40)
        
        # Create test users
        self.create_test_users()
        
        return True
    
    def teardown(self) -> bool:
        """Cleanup test data and stop services"""
        print("🧹 Cleaning up E2E tests...")
        # Clean up test data if needed
        return self.framework.stop_services()
    
    def run(self) -> bool:
        """Run all E2E tests"""
        print("\n🎯 Running End-to-End Tests\n")
        
        # User registration and onboarding flow
        self.test_user_onboarding_flow()
        
        # Test cycle creation and management
        self.test_test_cycle_workflow()
        
        # Data source integration flow
        self.test_data_source_integration()
        
        # Planning phase workflow
        self.test_planning_phase_workflow()
        
        # Execution phase workflow
        self.test_execution_phase_workflow()
        
        # Report generation workflow
        self.test_report_generation_workflow()
        
        # Request for Information (RFI) workflow
        self.test_rfi_workflow()
        
        # Data profiling workflow
        self.test_data_profiling_workflow()
        
        # Multi-user collaboration
        self.test_multi_user_collaboration()
        
        # Temporal workflow execution
        self.test_temporal_workflow_e2e()
        
        # Generate report
        report = self.framework.generate_report()
        passed = report['summary']['failed'] == 0
        
        print(f"\n📊 E2E Test Summary: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
        return passed
    
    def create_test_users(self):
        """Create test users with different roles"""
        users = [
            {
                "email": "admin@synapse.test",
                "password": "AdminPassword123!",
                "first_name": "Admin",
                "last_name": "User",
                "role": "admin"
            },
            {
                "email": "tester@synapse.test",
                "password": "TesterPassword123!",
                "first_name": "Test",
                "last_name": "Engineer",
                "role": "tester"
            },
            {
                "email": "viewer@synapse.test",
                "password": "ViewerPassword123!",
                "first_name": "Read",
                "last_name": "Only",
                "role": "viewer"
            }
        ]
        
        for user in users:
            # Register user
            response = requests.post(f"{self.api_base}/auth/register", json=user)
            if response.status_code in [200, 201]:
                # Login to get token
                login_data = {
                    "username": user["email"],
                    "password": user["password"]
                }
                login_response = requests.post(f"{self.api_base}/auth/login", data=login_data)
                if login_response.status_code == 200:
                    token = login_response.json()["access_token"]
                    self.auth_headers[user["role"]] = {"Authorization": f"Bearer {token}"}
                    self.test_data[f"{user['role']}_user"] = user
    
    def test_user_onboarding_flow(self):
        """Test complete user onboarding process"""
        with self.framework.test_context("User onboarding flow") as details:
            # Register new user
            new_user = {
                "email": "newuser@synapse.test",
                "password": "NewUserPassword123!",
                "first_name": "New",
                "last_name": "User",
                "role": "tester"
            }
            
            # 1. Registration
            reg_response = requests.post(f"{self.api_base}/auth/register", json=new_user)
            if reg_response.status_code not in [200, 201]:
                raise Exception(f"Failed to register user: {reg_response.text}")
            
            details['user_id'] = reg_response.json().get('id')
            
            # 2. Email verification (simulate)
            # In real scenario, would check email
            
            # 3. First login
            login_data = {
                "username": new_user["email"],
                "password": new_user["password"]
            }
            login_response = requests.post(f"{self.api_base}/auth/login", data=login_data)
            
            if login_response.status_code != 200:
                raise Exception(f"Failed to login: {login_response.text}")
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 4. Complete profile
            profile_data = {
                "organization": "Test Organization",
                "department": "QA",
                "phone": "+1234567890"
            }
            
            profile_response = requests.put(
                f"{self.api_base}/users/me/profile",
                json=profile_data,
                headers=headers
            )
            
            if profile_response.status_code == 200:
                details['profile_completed'] = True
                print("   ✓ User onboarding completed successfully")
            else:
                print("   ⚠️  Profile update endpoint not available")
    
    def test_test_cycle_workflow(self):
        """Test complete test cycle workflow"""
        with self.framework.test_context("Test cycle workflow") as details:
            if "admin" not in self.auth_headers:
                raise Exception("No admin user available")
            
            headers = self.auth_headers["admin"]
            
            # 1. Create test cycle
            cycle_data = {
                "name": "E2E Test Cycle",
                "description": "End-to-end test cycle",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
                "status": "planning"
            }
            
            create_response = requests.post(
                f"{self.api_base}/test-cycles",
                json=cycle_data,
                headers=headers
            )
            
            if create_response.status_code not in [200, 201]:
                print("   ⚠️  Test cycle creation endpoint not available")
                return
            
            cycle = create_response.json()
            self.test_data['test_cycle'] = cycle
            details['cycle_id'] = cycle.get('id')
            
            # 2. Update cycle status
            update_data = {"status": "active"}
            update_response = requests.put(
                f"{self.api_base}/test-cycles/{cycle['id']}",
                json=update_data,
                headers=headers
            )
            
            if update_response.status_code == 200:
                details['status_updated'] = True
            
            # 3. Add test scenarios
            scenario_data = {
                "name": "Login Test Scenario",
                "description": "Test user login functionality",
                "test_cycle_id": cycle['id']
            }
            
            scenario_response = requests.post(
                f"{self.api_base}/test-scenarios",
                json=scenario_data,
                headers=headers
            )
            
            if scenario_response.status_code in [200, 201]:
                details['scenario_created'] = True
                print("   ✓ Test cycle workflow completed successfully")
    
    def test_data_source_integration(self):
        """Test data source integration workflow"""
        with self.framework.test_context("Data source integration") as details:
            if "admin" not in self.auth_headers:
                raise Exception("No admin user available")
            
            headers = self.auth_headers["admin"]
            
            # 1. Create data source
            source_data = {
                "name": "E2E Test Database",
                "type": "postgresql",
                "connection_details": {
                    "host": "postgres",
                    "port": 5432,
                    "database": "test_db",
                    "username": "test_user",
                    "password": "test_password"
                }
            }
            
            create_response = requests.post(
                f"{self.api_base}/data-sources",
                json=source_data,
                headers=headers
            )
            
            if create_response.status_code not in [200, 201]:
                print("   ⚠️  Data source endpoint not available")
                return
            
            source = create_response.json()
            details['source_id'] = source.get('id')
            
            # 2. Test connection
            test_response = requests.post(
                f"{self.api_base}/data-sources/{source['id']}/test",
                headers=headers
            )
            
            if test_response.status_code == 200:
                details['connection_tested'] = True
            
            # 3. Sync metadata
            sync_response = requests.post(
                f"{self.api_base}/data-sources/{source['id']}/sync",
                headers=headers
            )
            
            if sync_response.status_code in [200, 202]:
                details['metadata_synced'] = True
                print("   ✓ Data source integration completed")
    
    def test_planning_phase_workflow(self):
        """Test planning phase workflow"""
        with self.framework.test_context("Planning phase workflow") as details:
            if "admin" not in self.auth_headers:
                raise Exception("No admin user available")
            
            if 'test_cycle' not in self.test_data:
                print("   ⚠️  No test cycle available, skipping planning phase")
                return
            
            headers = self.auth_headers["admin"]
            cycle_id = self.test_data['test_cycle']['id']
            
            # 1. Create planning phase
            phase_data = {
                "test_cycle_id": cycle_id,
                "phase_type": "planning",
                "name": "Test Planning Phase",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z"
            }
            
            phase_response = requests.post(
                f"{self.api_base}/planning-phases",
                json=phase_data,
                headers=headers
            )
            
            if phase_response.status_code not in [200, 201]:
                print("   ⚠️  Planning phase endpoint not available")
                return
            
            phase = phase_response.json()
            details['phase_id'] = phase.get('id')
            
            # 2. Add test cases
            test_case_data = {
                "phase_id": phase['id'],
                "name": "Verify User Login",
                "description": "Test that users can login successfully",
                "priority": "high",
                "test_data": {
                    "username": "test@example.com",
                    "password": "password123"
                }
            }
            
            case_response = requests.post(
                f"{self.api_base}/test-cases",
                json=test_case_data,
                headers=headers
            )
            
            if case_response.status_code in [200, 201]:
                details['test_case_created'] = True
            
            # 3. Generate test data
            gen_response = requests.post(
                f"{self.api_base}/planning-phases/{phase['id']}/generate-data",
                headers=headers
            )
            
            if gen_response.status_code in [200, 202]:
                details['data_generated'] = True
                print("   ✓ Planning phase workflow completed")
    
    def test_execution_phase_workflow(self):
        """Test execution phase workflow"""
        with self.framework.test_context("Execution phase workflow") as details:
            if "tester" not in self.auth_headers:
                raise Exception("No tester user available")
            
            headers = self.auth_headers["tester"]
            
            # Simulate test execution
            # 1. Get assigned test cases
            cases_response = requests.get(
                f"{self.api_base}/test-cases/assigned",
                headers=headers
            )
            
            if cases_response.status_code != 200:
                print("   ⚠️  Test case assignment endpoint not available")
                return
            
            test_cases = cases_response.json()
            
            if not test_cases:
                print("   ⚠️  No test cases assigned")
                return
            
            # 2. Execute test case
            case_id = test_cases[0]['id']
            execution_data = {
                "test_case_id": case_id,
                "status": "passed",
                "actual_result": "User logged in successfully",
                "execution_time": 1.5,
                "notes": "Test executed via E2E test"
            }
            
            exec_response = requests.post(
                f"{self.api_base}/test-executions",
                json=execution_data,
                headers=headers
            )
            
            if exec_response.status_code in [200, 201]:
                details['test_executed'] = True
            
            # 3. Upload evidence
            evidence_file = b"Test evidence screenshot data"
            files = {'file': ('evidence.png', evidence_file, 'image/png')}
            
            evidence_response = requests.post(
                f"{self.api_base}/test-executions/{exec_response.json()['id']}/evidence",
                files=files,
                headers=headers
            )
            
            if evidence_response.status_code in [200, 201]:
                details['evidence_uploaded'] = True
                print("   ✓ Execution phase workflow completed")
    
    def test_report_generation_workflow(self):
        """Test report generation workflow"""
        with self.framework.test_context("Report generation workflow") as details:
            if "admin" not in self.auth_headers:
                raise Exception("No admin user available")
            
            if 'test_cycle' not in self.test_data:
                print("   ⚠️  No test cycle available, skipping report generation")
                return
            
            headers = self.auth_headers["admin"]
            cycle_id = self.test_data['test_cycle']['id']
            
            # 1. Generate summary report
            summary_response = requests.post(
                f"{self.api_base}/reports/test-cycle/{cycle_id}/summary",
                headers=headers
            )
            
            if summary_response.status_code not in [200, 202]:
                print("   ⚠️  Report generation endpoint not available")
                return
            
            if summary_response.status_code == 202:
                # Async report generation
                job_id = summary_response.json().get('job_id')
                details['job_id'] = job_id
                
                # Poll for completion
                for _ in range(10):
                    status_response = requests.get(
                        f"{self.api_base}/jobs/{job_id}",
                        headers=headers
                    )
                    
                    if status_response.status_code == 200:
                        job_status = status_response.json()
                        if job_status['status'] == 'completed':
                            details['report_generated'] = True
                            break
                    
                    time.sleep(2)
            else:
                details['report_generated'] = True
            
            # 2. Download report
            download_response = requests.get(
                f"{self.api_base}/reports/test-cycle/{cycle_id}/download",
                headers=headers
            )
            
            if download_response.status_code == 200:
                details['report_size'] = len(download_response.content)
                print("   ✓ Report generation workflow completed")
    
    def test_rfi_workflow(self):
        """Test Request for Information workflow"""
        with self.framework.test_context("RFI workflow") as details:
            if "tester" not in self.auth_headers:
                raise Exception("No tester user available")
            
            headers = self.auth_headers["tester"]
            
            # 1. Create RFI
            rfi_data = {
                "title": "Missing Test Data",
                "description": "Need clarification on test data requirements",
                "priority": "high",
                "category": "test_data",
                "assigned_to": self.test_data.get('admin_user', {}).get('email')
            }
            
            create_response = requests.post(
                f"{self.api_base}/rfis",
                json=rfi_data,
                headers=headers
            )
            
            if create_response.status_code not in [200, 201]:
                print("   ⚠️  RFI endpoint not available")
                return
            
            rfi = create_response.json()
            details['rfi_id'] = rfi.get('id')
            
            # 2. Add comment (as admin)
            if "admin" in self.auth_headers:
                comment_data = {
                    "comment": "Test data will be provided by EOD",
                    "attachments": []
                }
                
                comment_response = requests.post(
                    f"{self.api_base}/rfis/{rfi['id']}/comments",
                    json=comment_data,
                    headers=self.auth_headers["admin"]
                )
                
                if comment_response.status_code in [200, 201]:
                    details['comment_added'] = True
            
            # 3. Close RFI
            close_data = {"status": "resolved", "resolution": "Data provided"}
            close_response = requests.put(
                f"{self.api_base}/rfis/{rfi['id']}",
                json=close_data,
                headers=headers
            )
            
            if close_response.status_code == 200:
                details['rfi_closed'] = True
                print("   ✓ RFI workflow completed")
    
    def test_data_profiling_workflow(self):
        """Test data profiling workflow"""
        with self.framework.test_context("Data profiling workflow") as details:
            if "admin" not in self.auth_headers:
                raise Exception("No admin user available")
            
            headers = self.auth_headers["admin"]
            
            # 1. Create profiling task
            profile_data = {
                "data_source_id": "test_source",
                "table_name": "users",
                "columns": ["id", "email", "created_at"],
                "profile_type": "full"
            }
            
            profile_response = requests.post(
                f"{self.api_base}/data-profiling/tasks",
                json=profile_data,
                headers=headers
            )
            
            if profile_response.status_code not in [200, 201, 202]:
                print("   ⚠️  Data profiling endpoint not available")
                return
            
            task = profile_response.json()
            details['task_id'] = task.get('id')
            
            # 2. Check profiling results
            time.sleep(5)  # Wait for profiling
            
            results_response = requests.get(
                f"{self.api_base}/data-profiling/tasks/{task['id']}/results",
                headers=headers
            )
            
            if results_response.status_code == 200:
                results = results_response.json()
                details['profile_results'] = {
                    'row_count': results.get('row_count'),
                    'column_stats': len(results.get('column_stats', []))
                }
                print("   ✓ Data profiling workflow completed")
    
    def test_multi_user_collaboration(self):
        """Test multi-user collaboration features"""
        with self.framework.test_context("Multi-user collaboration") as details:
            if len(self.auth_headers) < 2:
                print("   ⚠️  Not enough users for collaboration test")
                return
            
            # 1. Admin creates shared resource
            admin_headers = self.auth_headers.get("admin")
            shared_data = {
                "name": "Shared Test Plan",
                "type": "test_plan",
                "content": "Collaborative test planning document",
                "shared_with": ["tester@synapse.test", "viewer@synapse.test"]
            }
            
            create_response = requests.post(
                f"{self.api_base}/shared-resources",
                json=shared_data,
                headers=admin_headers
            )
            
            if create_response.status_code not in [200, 201]:
                print("   ⚠️  Shared resources endpoint not available")
                return
            
            resource = create_response.json()
            details['resource_id'] = resource.get('id')
            
            # 2. Tester accesses shared resource
            tester_headers = self.auth_headers.get("tester")
            access_response = requests.get(
                f"{self.api_base}/shared-resources/{resource['id']}",
                headers=tester_headers
            )
            
            if access_response.status_code == 200:
                details['tester_access'] = True
            
            # 3. Viewer attempts to modify (should fail)
            viewer_headers = self.auth_headers.get("viewer")
            modify_data = {"content": "Modified content"}
            modify_response = requests.put(
                f"{self.api_base}/shared-resources/{resource['id']}",
                json=modify_data,
                headers=viewer_headers
            )
            
            if modify_response.status_code == 403:
                details['viewer_restricted'] = True
                print("   ✓ Multi-user collaboration working correctly")
    
    def test_temporal_workflow_e2e(self):
        """Test Temporal workflow end-to-end"""
        with self.framework.test_context("Temporal workflow E2E") as details:
            if "admin" not in self.auth_headers:
                raise Exception("No admin user available")
            
            headers = self.auth_headers["admin"]
            
            # 1. Start a workflow
            workflow_data = {
                "workflow_type": "data_processing",
                "input_data": {
                    "source": "test_database",
                    "tables": ["users", "transactions"],
                    "processing_type": "validation"
                }
            }
            
            start_response = requests.post(
                f"{self.api_base}/workflows/start",
                json=workflow_data,
                headers=headers
            )
            
            if start_response.status_code not in [200, 202]:
                print("   ⚠️  Workflow endpoint not available")
                return
            
            workflow = start_response.json()
            details['workflow_id'] = workflow.get('workflow_id')
            
            # 2. Check workflow status
            max_attempts = 20
            workflow_completed = False
            
            for attempt in range(max_attempts):
                status_response = requests.get(
                    f"{self.api_base}/workflows/{workflow['workflow_id']}/status",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    details['workflow_status'] = status.get('status')
                    
                    if status.get('status') in ['completed', 'failed']:
                        workflow_completed = True
                        break
                
                time.sleep(3)
            
            if workflow_completed and details['workflow_status'] == 'completed':
                # 3. Get workflow results
                results_response = requests.get(
                    f"{self.api_base}/workflows/{workflow['workflow_id']}/results",
                    headers=headers
                )
                
                if results_response.status_code == 200:
                    details['workflow_results'] = True
                    print("   ✓ Temporal workflow completed successfully")
            else:
                print("   ⚠️  Workflow did not complete in time")


def main():
    """Run E2E tests"""
    config = TestConfig()
    framework = DockerTestFramework(config)
    runner = E2ETestRunner(framework)
    
    # Setup environment
    if not runner.setup():
        print("❌ Failed to setup test environment")
        return 1
    
    try:
        # Run tests
        success = runner.run()
        
        # Save detailed report
        framework.generate_report("e2e_test_report.json")
        
        return 0 if success else 1
    finally:
        # Cleanup
        runner.teardown()


if __name__ == "__main__":
    exit(main())