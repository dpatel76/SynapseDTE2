#!/usr/bin/env python3
"""
Test all Celery task implementations
Tests each background job capability in autonomous mode
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# API Configuration
BASE_URL = "http://localhost:8001"
TEST_USER = {
    "email": "tester@example.com",
    "password": "password123"
}

# Test Configuration
CYCLE_ID = 2
REPORT_ID = 3
PHASE_IDS = {
    "Planning": None,  # Will be fetched
    "Data Profiling": None,
    "Scoping": None,
    "Test Execution": None
}

# Global auth token
TOKEN = None


def login() -> str:
    """Login and get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json=TEST_USER
    )
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        sys.exit(1)
    
    token = response.json()["access_token"]
    print(f"✅ Logged in successfully")
    return token


def get_headers() -> Dict[str, str]:
    """Get headers with authentication"""
    return {"Authorization": f"Bearer {TOKEN}"}


def get_phase_id(phase_name: str) -> int:
    """Get phase ID for a given phase name"""
    # First try the status endpoint which includes phase information
    response = requests.get(
        f"{BASE_URL}/api/v1/status/cycles/{CYCLE_ID}/reports/{REPORT_ID}/phases/{phase_name}/status",
        headers=get_headers()
    )
    if response.status_code == 200:
        data = response.json()
        if "phase_id" in data:
            return data["phase_id"]
    
    # Alternative: Query the database directly through SQL endpoint (if available)
    # For now, we'll use hardcoded phase IDs based on common patterns
    # In a real scenario, you'd query the workflow_phases table
    print(f"⚠️  Using hardcoded phase mapping for '{phase_name}'")
    
    # These are the actual phase IDs for cycle 2, report 3
    phase_mapping = {
        "Planning": 12,
        "Data Profiling": 13,
        "Scoping": 14,
        "Test Execution": 18  # "Testing" phase
    }
    
    return phase_mapping.get(phase_name)


def wait_for_job(job_id: str, max_wait: int = 300, check_interval: int = 5) -> Dict[str, Any]:
    """Wait for a background job to complete"""
    print(f"⏳ Waiting for job {job_id} to complete...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{BASE_URL}/api/v1/jobs/{job_id}/status",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            job_data = response.json()
            status = job_data.get("status", "unknown")
            progress = job_data.get("progress_percentage", 0)
            current_step = job_data.get("current_step", "")
            
            print(f"  Status: {status} | Progress: {progress}% | Step: {current_step}")
            
            if status in ["completed", "failed", "error"]:
                elapsed = int(time.time() - start_time)
                print(f"  Job {status} after {elapsed} seconds")
                return job_data
        
        time.sleep(check_interval)
    
    print(f"❌ Job {job_id} timed out after {max_wait} seconds")
    return {"status": "timeout"}


def test_planning_mapPDE() -> bool:
    """Test Planning MapPDE Celery task"""
    print("\n" + "="*60)
    print("🧪 Testing Planning MapPDE Celery Task")
    print("="*60)
    
    phase_id = PHASE_IDS["Planning"]
    if not phase_id:
        print("❌ Planning phase not found")
        return False
    
    try:
        # Start MapPDE job
        response = requests.post(
            f"{BASE_URL}/api/v1/planning/cycles/{CYCLE_ID}/reports/{REPORT_ID}/pde-mappings/auto-map",
            headers=get_headers(),
            json={}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to start MapPDE job: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        job_id = result.get("job_id")
        print(f"✅ Started MapPDE job: {job_id}")
        
        # Wait for completion
        job_result = wait_for_job(job_id)
        
        if job_result.get("status") == "completed":
            print(f"✅ MapPDE job completed successfully")
            if "result" in job_result:
                mapped_count = job_result["result"].get("mapped_count", 0)
                print(f"  Mapped {mapped_count} attributes")
            return True
        else:
            print(f"❌ MapPDE job failed: {job_result}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing MapPDE: {str(e)}")
        return False


def test_data_profiling_llm_generation() -> bool:
    """Test Data Profiling LLM Rules Generation Celery task"""
    print("\n" + "="*60)
    print("🧪 Testing Data Profiling LLM Rules Generation Celery Task")
    print("="*60)
    
    phase_id = PHASE_IDS["Data Profiling"]
    if not phase_id:
        print("❌ Data Profiling phase not found")
        return False
    
    try:
        # Create initial version (triggers LLM generation)
        response = requests.post(
            f"{BASE_URL}/api/v1/data-profiling/cycles/{CYCLE_ID}/reports/{REPORT_ID}/versions",
            headers=get_headers(),
            json={
                "carry_forward_all": True
            }
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create profiling version: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        version_id = result.get("version_id")
        job_id = result.get("generation_job_id")
        print(f"✅ Created profiling version: {version_id}")
        print(f"✅ Started LLM generation job: {job_id}")
        
        # Wait for completion
        job_result = wait_for_job(job_id, max_wait=600)  # Allow more time for LLM
        
        if job_result.get("status") == "completed":
            print(f"✅ LLM rules generation completed successfully")
            if "result" in job_result:
                rules_created = job_result["result"].get("rules_created", 0)
                print(f"  Generated {rules_created} profiling rules")
            return True
        else:
            print(f"❌ LLM generation job failed: {job_result}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing data profiling LLM generation: {str(e)}")
        return False


def test_data_profiling_execution() -> bool:
    """Test Data Profiling Rules Execution Celery task"""
    print("\n" + "="*60)
    print("🧪 Testing Data Profiling Rules Execution Celery Task")
    print("="*60)
    
    phase_id = PHASE_IDS["Data Profiling"]
    if not phase_id:
        print("❌ Data Profiling phase not found")
        return False
    
    try:
        # Get latest version
        response = requests.get(
            f"{BASE_URL}/api/v1/data-profiling/cycles/{CYCLE_ID}/reports/{REPORT_ID}/versions",
            headers=get_headers()
        )
        
        if response.status_code != 200 or not response.json():
            print("❌ No data profiling versions found")
            return False
        
        version_id = response.json()[0]["version_id"]
        
        # Execute rules
        response = requests.post(
            f"{BASE_URL}/api/v1/data-profiling/versions/{version_id}/execute",
            headers=get_headers(),
            json={}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to start rule execution: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        job_id = result.get("job_id")
        print(f"✅ Started rule execution job: {job_id}")
        
        # Wait for completion
        job_result = wait_for_job(job_id)
        
        if job_result.get("status") == "completed":
            print(f"✅ Rule execution completed successfully")
            return True
        else:
            print(f"❌ Rule execution job failed: {job_result}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing data profiling execution: {str(e)}")
        return False


def test_scoping_llm_recommendations() -> bool:
    """Test Scoping LLM Recommendations Celery task"""
    print("\n" + "="*60)
    print("🧪 Testing Scoping LLM Recommendations Celery Task")
    print("="*60)
    
    phase_id = PHASE_IDS["Scoping"]
    if not phase_id:
        print("❌ Scoping phase not found")
        return False
    
    try:
        # Create scoping version
        response = requests.post(
            f"{BASE_URL}/api/v1/scoping/versions",
            headers=get_headers(),
            json={
                "name": "Test Scoping Version",
                "phase_id": phase_id
            }
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create scoping version: {response.status_code} - {response.text}")
            return False
        
        version = response.json()
        version_id = version.get("version_id")
        print(f"✅ Created scoping version: {version_id}")
        
        # Generate LLM recommendations
        response = requests.post(
            f"{BASE_URL}/api/v1/scoping/versions/{version_id}/generate-recommendations",
            headers=get_headers(),
            json={}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to start LLM recommendations: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        job_id = result.get("job_id")
        print(f"✅ Started LLM recommendations job: {job_id}")
        
        # Wait for completion
        job_result = wait_for_job(job_id, max_wait=600)  # Allow more time for LLM
        
        if job_result.get("status") == "completed":
            print(f"✅ LLM recommendations completed successfully")
            if "result" in job_result:
                processed = job_result["result"].get("processed", 0)
                print(f"  Generated recommendations for {processed} attributes")
            return True
        else:
            print(f"❌ LLM recommendations job failed: {job_result}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing scoping LLM recommendations: {str(e)}")
        return False


def test_test_execution_background() -> bool:
    """Test Test Execution Background Celery task"""
    print("\n" + "="*60)
    print("🧪 Testing Test Execution Background Celery Task")
    print("="*60)
    
    phase_id = PHASE_IDS["Test Execution"]
    if not phase_id:
        print("❌ Test Execution phase not found")
        return False
    
    try:
        # Create test execution with background flag
        test_data = {
            "test_case_id": "TC_2_3_001",
            "analysis_method": "database_query",  # Use database query instead of LLM
            "configuration": {
                "execute_in_background": True,
                "sample_data": {
                    "sample_value": "12345",
                    "attribute_name": "account_number"
                },
                "evidence": {
                    "query_text": "SELECT account_number FROM accounts WHERE id = 1",
                    "data_source_id": "1"
                }
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/test-execution/cycles/{CYCLE_ID}/reports/{REPORT_ID}/executions",
            headers=get_headers(),
            json=test_data
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create test execution: {response.status_code} - {response.text}")
            # Try without evidence_id if it fails
            if "evidence" in response.text:
                print("  Retrying without evidence_id...")
                test_data.pop("evidence_id", None)
                response = requests.post(
                    f"{BASE_URL}/api/v1/test-execution/cycles/{CYCLE_ID}/reports/{REPORT_ID}/executions",
                    headers=get_headers(),
                    json=test_data
                )
                if response.status_code not in [200, 201]:
                    return False
        
        result = response.json()
        execution_id = result.get("id")
        job_id = result.get("background_job_id")
        
        if not job_id:
            print("❌ No background job ID returned")
            return False
            
        print(f"✅ Created test execution: {execution_id}")
        print(f"✅ Started background execution job: {job_id}")
        
        # Wait for completion
        job_result = wait_for_job(job_id)
        
        if job_result.get("status") == "completed":
            print(f"✅ Test execution completed successfully")
            if "result" in job_result:
                exec_result = job_result["result"]
                print(f"  Execution status: {exec_result.get('status')}")
                print(f"  Test result: {exec_result.get('result')}")
            return True
        else:
            print(f"❌ Test execution job failed: {job_result}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing test execution: {str(e)}")
        return False


def main():
    """Run all Celery task tests"""
    global TOKEN, PHASE_IDS
    
    print("\n🚀 Starting Celery Task Tests")
    print(f"   Cycle ID: {CYCLE_ID}")
    print(f"   Report ID: {REPORT_ID}")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    # Login
    TOKEN = login()
    
    # Get phase IDs
    print("\n📍 Fetching phase IDs...")
    for phase_name in PHASE_IDS.keys():
        phase_id = get_phase_id(phase_name)
        if phase_id:
            PHASE_IDS[phase_name] = phase_id
            print(f"  {phase_name}: {phase_id}")
        else:
            print(f"  {phase_name}: NOT FOUND")
    
    # Run tests
    test_results = []
    
    # Test 1: Planning MapPDE
    result = test_planning_mapPDE()
    test_results.append(("Planning MapPDE", result))
    
    # Test 2: Data Profiling LLM Generation
    result = test_data_profiling_llm_generation()
    test_results.append(("Data Profiling LLM Generation", result))
    
    # Test 3: Data Profiling Rules Execution
    result = test_data_profiling_execution()
    test_results.append(("Data Profiling Rules Execution", result))
    
    # Test 4: Scoping LLM Recommendations
    result = test_scoping_llm_recommendations()
    test_results.append(("Scoping LLM Recommendations", result))
    
    # Test 5: Test Execution Background
    result = test_test_execution_background()
    test_results.append(("Test Execution Background", result))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All Celery tasks are working correctly!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())