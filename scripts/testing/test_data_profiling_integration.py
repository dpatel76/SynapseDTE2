#!/usr/bin/env python3
"""
Test Data Profiling Integration
Tests the complete workflow with the new Data Profiling phase
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials
TEST_USERS = {
    "tester": {"username": "tester@synapse.com", "password": "TestUser123!"},
    "report_owner": {"username": "owner@synapse.com", "password": "TestUser123!"},
    "test_executive": {"username": "testmgr@synapse.com", "password": "TestUser123!"}
}

class DataProfilingIntegrationTest:
    def __init__(self):
        self.session = None
        self.tokens = {}
        self.cycle_id = None
        self.report_id = None
        self.phase_id = None
        
    async def setup(self):
        """Setup test session and authenticate users"""
        self.session = aiohttp.ClientSession()
        
        # Authenticate all test users
        for role, creds in TEST_USERS.items():
            token = await self.authenticate(creds["username"], creds["password"])
            self.tokens[role] = token
            print(f"✓ Authenticated {role}: {creds['username']}")
    
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
    
    async def authenticate(self, username, password):
        """Authenticate user and get token"""
        async with self.session.post(f"{BASE_URL}/auth/login", json={
            "email": username,
            "password": password
        }) as resp:
            if resp.status != 200:
                raise Exception(f"Authentication failed: {await resp.text()}")
            data = await resp.json()
            return data["access_token"]
    
    async def api_request(self, method, endpoint, token_role="tester", **kwargs):
        """Make API request with authentication"""
        headers = {
            "Authorization": f"Bearer {self.tokens[token_role]}",
            "Content-Type": "application/json"
        }
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]
        
        url = f"{BASE_URL}{endpoint}"
        async with self.session.request(method, url, headers=headers, **kwargs) as resp:
            text = await resp.text()
            if resp.status >= 400:
                print(f"❌ API Error {resp.status}: {text}")
                raise Exception(f"API request failed: {text}")
            return json.loads(text) if text else None
    
    async def test_workflow_with_data_profiling(self):
        """Test complete workflow including Data Profiling phase"""
        print("\n=== Testing Complete Workflow with Data Profiling ===\n")
        
        # 1. Create test cycle
        print("1. Creating test cycle...")
        cycle_data = {
            "cycle_name": f"Data Profiling Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": None,
            "description": "Testing Data Profiling phase integration"
        }
        cycle = await self.api_request("POST", "/cycles", json=cycle_data, token_role="test_executive")
        self.cycle_id = cycle["cycle_id"]
        print(f"   ✓ Created cycle: {cycle['cycle_name']} (ID: {self.cycle_id})")
        
        # 2. Add report to cycle
        print("\n2. Adding report to cycle...")
        # Get available reports
        reports = await self.api_request("GET", "/reports?skip=0&limit=10")
        if not reports["reports"]:
            raise Exception("No reports available")
        
        report = reports["reports"][0]
        self.report_id = report["report_id"]
        
        # Get tester user ID
        users_resp = await self.api_request("GET", "/users?skip=0&limit=100", token_role="test_executive")
        users = users_resp.get("users", users_resp.get("items", []))
        tester_user = next((u for u in users if u["email"] == "tester@synapse.com"), None)
        if not tester_user:
            raise Exception("Tester user not found")
        
        # Add report to cycle with tester assignment
        await self.api_request("POST", f"/cycles/{self.cycle_id}/reports", json={
            "report_id": self.report_id,
            "tester_id": tester_user["user_id"]
        }, token_role="test_executive")
        print(f"   ✓ Added report: {report['report_name']} (ID: {self.report_id})")
        
        # 3. Start workflow
        print("\n3. Starting workflow...")
        workflow_resp = await self.api_request("POST", f"/cycles/{self.cycle_id}/reports/{self.report_id}/start-workflow")
        print(f"   ✓ Workflow started: {workflow_resp['workflow_id']}")
        
        # 4. Complete Planning Phase
        print("\n4. Completing Planning Phase...")
        # Start planning
        await self.api_request("POST", f"/planning/cycles/{self.cycle_id}/reports/{self.report_id}/start", token_role="test_executive")
        
        # Create some attributes
        attributes = [
            {
                "attribute_name": "Customer_ID",
                "description": "Unique customer identifier",
                "data_type": "Integer",
                "is_primary_key": True,
                "mandatory_flag": "Mandatory",
                "cde_flag": False
            },
            {
                "attribute_name": "Account_Balance",
                "description": "Current account balance",
                "data_type": "Decimal",
                "is_primary_key": False,
                "mandatory_flag": "Mandatory",
                "cde_flag": True
            },
            {
                "attribute_name": "Transaction_Date",
                "description": "Date of transaction",
                "data_type": "Date",
                "is_primary_key": False,
                "mandatory_flag": "Mandatory",
                "cde_flag": False
            }
        ]
        
        for attr in attributes:
            await self.api_request("POST", f"/planning/cycles/{self.cycle_id}/reports/{self.report_id}/attributes", json=attr, token_role="test_executive")
        print(f"   ✓ Created {len(attributes)} attributes")
        
        # Complete planning
        await self.api_request("POST", f"/planning/cycles/{self.cycle_id}/reports/{self.report_id}/complete", json={
            "completion_notes": "Planning completed for Data Profiling test"
        }, token_role="test_executive")
        print("   ✓ Planning phase completed")
        
        # 5. Test Data Profiling Phase
        print("\n5. Testing Data Profiling Phase...")
        
        # Start Data Profiling
        print("   a. Starting Data Profiling phase...")
        await self.api_request("POST", f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/start")
        print("      ✓ Data Profiling phase started")
        
        # Get status
        status = await self.api_request("GET", f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/status")
        print(f"      Phase status: {status['phase_status']}")
        
        # Request data from Report Owner
        print("   b. Requesting data from Report Owner...")
        await self.api_request("POST", f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/request-data", json={
            "message": "Please upload test data files for profiling"
        })
        print("      ✓ Data request sent")
        
        # Upload file as Report Owner
        print("   c. Uploading data file (as Report Owner)...")
        # Create test CSV content
        csv_content = """Customer_ID,Account_Balance,Transaction_Date
1,1000.50,2024-01-01
2,2500.75,2024-01-02
3,500.00,2024-01-03
4,,2024-01-04
5,3000.00,2024-01-05"""
        
        # Upload file using multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field('file', csv_content.encode(), filename='test_data.csv', content_type='text/csv')
        form_data.add_field('delimiter', ',')
        
        headers = {"Authorization": f"Bearer {self.tokens['report_owner']}"}
        async with self.session.post(
            f"{BASE_URL}/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/upload-file",
            data=form_data,
            headers=headers
        ) as resp:
            if resp.status != 200:
                raise Exception(f"File upload failed: {await resp.text()}")
            upload_result = await resp.json()
        
        print(f"      ✓ File uploaded: {upload_result['file_name']} ({upload_result['row_count']} rows)")
        
        # Validate files
        print("   d. Validating uploaded files...")
        validation = await self.api_request("POST", f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/validate-files")
        print(f"      ✓ Files validated: {validation['valid_files']}/{validation['total_files']} valid")
        
        # Generate profiling rules
        print("   e. Generating profiling rules...")
        rule_job = await self.api_request("POST", f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/generate-rules", json={
            "preferred_provider": "claude"
        })
        job_id = rule_job["job_id"]
        print(f"      ✓ Rule generation started (Job ID: {job_id})")
        
        # Wait for job completion
        await self.wait_for_job(job_id)
        
        # Get rules
        rules = await self.api_request("GET", f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/rules")
        print(f"      ✓ Generated {len(rules)} profiling rules")
        
        # Approve rules as Test Executive
        print("   f. Approving profiling rules (as Test Executive)...")
        approved_count = 0
        for rule in rules:
            if rule["status"] == "pending":
                await self.api_request(
                    "PUT", 
                    f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/rules/{rule['rule_id']}/approve",
                    token_role="test_executive",
                    json={"approval_notes": "Approved for testing"}
                )
                approved_count += 1
        print(f"      ✓ Approved {approved_count} rules")
        
        # Execute profiling
        print("   g. Executing profiling...")
        exec_job = await self.api_request("POST", f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/execute-profiling")
        exec_job_id = exec_job["job_id"]
        print(f"      ✓ Profiling execution started (Job ID: {exec_job_id})")
        
        # Wait for execution
        await self.wait_for_job(exec_job_id)
        
        # Get results
        results = await self.api_request("GET", f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/results")
        print(f"      ✓ Profiling completed with {len(results)} results")
        
        # Get quality scores
        scores = await self.api_request("GET", f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/quality-scores")
        print(f"      ✓ Quality scores calculated for {len(scores)} attributes")
        
        # Display quality scores
        print("\n   Quality Scores:")
        for score in scores:
            print(f"      - {score['attribute_name']}: {score['overall_quality_score']:.1f}%")
        
        # Complete Data Profiling phase
        print("   h. Completing Data Profiling phase...")
        await self.api_request("POST", f"/data-profiling/cycles/{self.cycle_id}/reports/{self.report_id}/complete")
        print("      ✓ Data Profiling phase completed")
        
        # 6. Verify workflow progression
        print("\n6. Verifying workflow progression...")
        workflow_status = await self.api_request("GET", f"/cycles/{self.cycle_id}/reports/{self.report_id}/workflow/status")
        
        print("\n   Workflow Phase Status:")
        for phase in workflow_status["phases"]:
            status_icon = "✓" if phase["status"] == "Complete" else "○"
            print(f"      {status_icon} {phase['phase_name']}: {phase['status']}")
        
        # Check if Scoping phase is ready to start
        scoping_available = any(p["phase_name"] == "Scoping" and p["status"] == "Not Started" for p in workflow_status["phases"])
        if scoping_available:
            print("\n   ✓ Scoping phase is now available to start!")
        
        print("\n✅ Data Profiling integration test completed successfully!")
    
    async def wait_for_job(self, job_id, max_wait=60):
        """Wait for background job to complete"""
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < max_wait:
            try:
                job_status = await self.api_request("GET", f"/jobs/{job_id}/status")
                
                if job_status["status"] == "completed":
                    return True
                elif job_status["status"] == "failed":
                    raise Exception(f"Job failed: {job_status.get('error', 'Unknown error')}")
                
                # Show progress
                progress = job_status.get("progress_percentage", 0)
                print(f"      Progress: {progress}% - {job_status.get('current_step', 'Processing...')}", end="\r")
                
                await asyncio.sleep(2)
            except Exception as e:
                # Job endpoint might not exist, just wait
                await asyncio.sleep(2)
        
        raise Exception(f"Job {job_id} timed out after {max_wait} seconds")
    
    async def run(self):
        """Run all tests"""
        try:
            await self.setup()
            await self.test_workflow_with_data_profiling()
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main entry point"""
    print("=" * 80)
    print("Data Profiling Integration Test")
    print("=" * 80)
    
    test = DataProfilingIntegrationTest()
    await test.run()


if __name__ == "__main__":
    asyncio.run(main())