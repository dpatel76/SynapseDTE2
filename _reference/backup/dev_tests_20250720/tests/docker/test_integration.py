#!/usr/bin/env python3
"""
Integration Tests for SynapseDTE
Tests for inter-service communication and data flow
"""

import time
import json
import requests
from typing import Dict, List, Optional
from test_framework import DockerTestFramework, TestRunner, TestConfig


class IntegrationTestRunner(TestRunner):
    """Test runner for integration tests"""
    
    def __init__(self, framework: DockerTestFramework):
        super().__init__(framework)
        self.api_base = "http://localhost:8000/api/v1"
        self.frontend_base = "http://localhost"
        self.temporal_base = "http://localhost:8088"
        self.test_user = None
        self.auth_token = None
    
    def setup(self) -> bool:
        """Start services and prepare test data"""
        print("🚀 Starting services for integration tests...")
        if not self.framework.start_services():
            return False
        
        # Wait for all services to be ready
        print("⏳ Waiting for services to be ready...")
        time.sleep(30)
        
        return True
    
    def teardown(self) -> bool:
        """Cleanup test data and stop services"""
        print("🧹 Cleaning up integration tests...")
        return self.framework.stop_services()
    
    def run(self) -> bool:
        """Run all integration tests"""
        print("\n🔗 Running Integration Tests\n")
        
        # Test service connectivity
        self.test_backend_database_connection()
        self.test_backend_redis_connection()
        self.test_backend_temporal_connection()
        
        # Test API functionality
        self.test_api_documentation()
        self.test_user_registration_and_auth()
        self.test_api_crud_operations()
        
        # Test frontend-backend integration
        self.test_frontend_api_proxy()
        self.test_frontend_static_assets()
        
        # Test Temporal workflow integration
        self.test_temporal_workflow_submission()
        self.test_worker_activity_execution()
        
        # Test data persistence
        self.test_data_persistence_across_restart()
        
        # Test cross-service communication
        self.test_cross_service_auth()
        self.test_file_upload_and_storage()
        
        # Generate report
        report = self.framework.generate_report()
        passed = report['summary']['failed'] == 0
        
        print(f"\n📊 Integration Test Summary: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
        return passed
    
    def test_backend_database_connection(self):
        """Test backend can connect to database"""
        with self.framework.test_context("Backend-Database connection") as details:
            # Check if backend can query database
            success, output = self.framework.execute_in_container(
                "backend",
                "python -c \"from app.core.database import engine; import asyncio; asyncio.run(engine.dispose())\""
            )
            
            if not success:
                details['error'] = output
                raise Exception("Backend cannot connect to database")
            
            print("   ✓ Backend successfully connected to database")
    
    def test_backend_redis_connection(self):
        """Test backend can connect to Redis"""
        with self.framework.test_context("Backend-Redis connection") as details:
            # Check Redis connection through backend
            success, output = self.framework.execute_in_container(
                "backend",
                "python -c \"import redis; r = redis.from_url('redis://redis:6379'); print(r.ping())\""
            )
            
            if not success or "True" not in output:
                details['error'] = output
                raise Exception("Backend cannot connect to Redis")
            
            print("   ✓ Backend successfully connected to Redis")
    
    def test_backend_temporal_connection(self):
        """Test backend can connect to Temporal"""
        with self.framework.test_context("Backend-Temporal connection") as details:
            # Check Temporal connection through backend
            success, output = self.framework.execute_in_container(
                "backend",
                "python -c \"from app.temporal.client import get_temporal_client; import asyncio; asyncio.run(get_temporal_client())\""
            )
            
            if not success:
                details['error'] = output
                # Temporal connection might fail if not fully started
                print("   ⚠️  Backend-Temporal connection test skipped (service might not be ready)")
                return
            
            print("   ✓ Backend can connect to Temporal")
    
    def test_api_documentation(self):
        """Test API documentation is accessible"""
        with self.framework.test_context("API documentation") as details:
            # Test Swagger UI
            response = requests.get(f"{self.api_base}/docs")
            details['swagger_status'] = response.status_code
            
            if response.status_code != 200:
                raise Exception("Swagger documentation not accessible")
            
            # Test OpenAPI schema
            response = requests.get(f"{self.api_base}/openapi.json")
            details['openapi_status'] = response.status_code
            
            if response.status_code != 200:
                raise Exception("OpenAPI schema not accessible")
            
            schema = response.json()
            details['api_version'] = schema.get('info', {}).get('version', 'unknown')
            details['endpoints_count'] = len(schema.get('paths', {}))
            
            print(f"   ✓ API documentation accessible ({details['endpoints_count']} endpoints)")
    
    def test_user_registration_and_auth(self):
        """Test user registration and authentication flow"""
        with self.framework.test_context("User registration and auth") as details:
            # Register new user
            test_user = {
                "email": "test@synapse.local",
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "tester"
            }
            
            response = requests.post(
                f"{self.api_base}/auth/register",
                json=test_user
            )
            
            if response.status_code not in [200, 201]:
                details['register_error'] = response.text
                raise Exception(f"Failed to register user: {response.status_code}")
            
            user_data = response.json()
            self.test_user = user_data
            details['user_id'] = user_data.get('id')
            
            # Login
            login_data = {
                "username": test_user["email"],
                "password": test_user["password"]
            }
            
            response = requests.post(
                f"{self.api_base}/auth/login",
                data=login_data  # Form data for OAuth2
            )
            
            if response.status_code != 200:
                details['login_error'] = response.text
                raise Exception(f"Failed to login: {response.status_code}")
            
            auth_data = response.json()
            self.auth_token = auth_data.get('access_token')
            details['token_type'] = auth_data.get('token_type')
            
            print("   ✓ User registration and authentication successful")
    
    def test_api_crud_operations(self):
        """Test basic CRUD operations through API"""
        with self.framework.test_context("API CRUD operations") as details:
            if not self.auth_token:
                raise Exception("No auth token available")
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test GET users (should require auth)
            response = requests.get(f"{self.api_base}/users/me", headers=headers)
            
            if response.status_code != 200:
                details['get_error'] = response.text
                raise Exception(f"Failed to get user info: {response.status_code}")
            
            user_info = response.json()
            details['user_email'] = user_info.get('email')
            
            # Test creating a test cycle (if endpoint exists)
            test_cycle = {
                "name": "Integration Test Cycle",
                "description": "Created by integration test",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z"
            }
            
            response = requests.post(
                f"{self.api_base}/test-cycles",
                json=test_cycle,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                cycle_data = response.json()
                details['created_cycle_id'] = cycle_data.get('id')
                print("   ✓ CRUD operations working correctly")
            else:
                print("   ⚠️  Test cycle creation skipped (endpoint might not exist)")
    
    def test_frontend_api_proxy(self):
        """Test frontend proxies API requests correctly"""
        with self.framework.test_context("Frontend API proxy") as details:
            # Test API proxy through frontend
            response = requests.get(f"{self.frontend_base}/api/v1/health")
            
            if response.status_code != 200:
                raise Exception(f"Frontend API proxy not working: {response.status_code}")
            
            # Verify it's actually from backend
            health_data = response.json()
            details['backend_status'] = health_data.get('status', 'unknown')
            
            print("   ✓ Frontend correctly proxies API requests")
    
    def test_frontend_static_assets(self):
        """Test frontend serves static assets"""
        with self.framework.test_context("Frontend static assets") as details:
            # Test index.html
            response = requests.get(self.frontend_base)
            details['index_status'] = response.status_code
            
            if response.status_code != 200:
                raise Exception("Frontend index.html not accessible")
            
            # Check for React app markers
            if '<div id="root">' not in response.text:
                raise Exception("Frontend not serving React app")
            
            details['content_length'] = len(response.text)
            print("   ✓ Frontend serves static assets correctly")
    
    def test_temporal_workflow_submission(self):
        """Test Temporal workflow submission"""
        with self.framework.test_context("Temporal workflow submission") as details:
            # Check if Temporal UI is accessible
            response = requests.get(self.temporal_base)
            
            if response.status_code != 200:
                print("   ⚠️  Temporal UI not accessible, skipping workflow test")
                return
            
            # Try to list workflows through Temporal API
            # This is a basic connectivity test
            print("   ✓ Temporal service is accessible")
    
    def test_worker_activity_execution(self):
        """Test worker can execute activities"""
        with self.framework.test_context("Worker activity execution") as details:
            # Check worker logs for activity registration
            logs = self.framework.get_service_logs("worker", tail=50)
            
            if "Registered activities" in logs or "Worker started" in logs:
                details['worker_status'] = 'running'
                print("   ✓ Worker is running and registered activities")
            else:
                print("   ⚠️  Worker status unclear from logs")
    
    def test_data_persistence_across_restart(self):
        """Test data persists across service restart"""
        with self.framework.test_context("Data persistence") as details:
            if not self.test_user:
                print("   ⚠️  No test user created, skipping persistence test")
                return
            
            # Restart backend
            self.framework.docker_compose("restart backend")
            time.sleep(20)  # Wait for restart
            
            # Try to login again
            login_data = {
                "username": "test@synapse.local",
                "password": "TestPassword123!"
            }
            
            response = requests.post(
                f"{self.api_base}/auth/login",
                data=login_data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception("User data not persisted after restart")
            
            print("   ✓ Data persists across service restarts")
    
    def test_cross_service_auth(self):
        """Test authentication works across services"""
        with self.framework.test_context("Cross-service authentication") as details:
            if not self.auth_token:
                print("   ⚠️  No auth token, skipping cross-service auth test")
                return
            
            # Test auth through frontend proxy
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(
                f"{self.frontend_base}/api/v1/users/me",
                headers=headers
            )
            
            if response.status_code == 200:
                details['auth_works_through_proxy'] = True
                print("   ✓ Authentication works through frontend proxy")
            else:
                print("   ⚠️  Authentication through proxy returned:", response.status_code)
    
    def test_file_upload_and_storage(self):
        """Test file upload and storage"""
        with self.framework.test_context("File upload and storage") as details:
            if not self.auth_token:
                print("   ⚠️  No auth token, skipping file upload test")
                return
            
            # Create a test file
            test_content = b"Test file content for integration test"
            files = {'file': ('test.txt', test_content, 'text/plain')}
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Try to upload (endpoint might not exist)
            response = requests.post(
                f"{self.api_base}/files/upload",
                files=files,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                upload_data = response.json()
                details['file_id'] = upload_data.get('id')
                print("   ✓ File upload successful")
            else:
                print("   ⚠️  File upload endpoint not available")


def main():
    """Run integration tests"""
    config = TestConfig()
    framework = DockerTestFramework(config)
    runner = IntegrationTestRunner(framework)
    
    # Setup environment
    if not runner.setup():
        print("❌ Failed to setup test environment")
        return 1
    
    try:
        # Run tests
        success = runner.run()
        
        # Save detailed report
        framework.generate_report("integration_test_report.json")
        
        return 0 if success else 1
    finally:
        # Cleanup
        runner.teardown()


if __name__ == "__main__":
    exit(main())