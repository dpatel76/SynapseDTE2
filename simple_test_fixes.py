#!/usr/bin/env python3
"""
Simple test for all implemented fixes using API calls.
"""

import requests
import json
from datetime import datetime
import time

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Test Configuration
TEST_CYCLE_ID = "test_cycle_2025"
TEST_REPORT_ID = "test_report_001"
ADMIN_EMAIL = "admin@example.com"
REPORT_OWNER_EMAIL = "report_owner@example.com"
PASSWORD = "password123"

# Color codes for terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'


def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*60}{END}")
    print(f"{BOLD}{BLUE}{text.center(60)}{END}")
    print(f"{BOLD}{BLUE}{'='*60}{END}\n")


def print_test(test_name):
    print(f"\n{BOLD}{YELLOW}Test: {test_name}{END}")
    print("-" * 40)


def print_success(message):
    print(f"{GREEN}✓ {message}{END}")


def print_error(message):
    print(f"{RED}✗ {message}{END}")


def print_warning(message):
    print(f"{YELLOW}! {message}{END}")


def get_token(email):
    """Get authentication token."""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": email, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print_error(f"Failed to get token for {email}: {response.status_code}")
        return None


def run_tests():
    """Run all tests."""
    print_header("COMPREHENSIVE FIX TESTING SUITE")
    
    # Get tokens
    print("Setting up test environment...")
    admin_token = get_token(ADMIN_EMAIL)
    ro_token = get_token(REPORT_OWNER_EMAIL)
    
    if not admin_token or not ro_token:
        print_error("Failed to get authentication tokens")
        return
    
    print_success("Authentication successful")
    
    test_results = []
    
    # Test 1: Sample Selection Report Owner Feedback Tab
    print_test("1. Sample Selection - Report Owner Feedback Tab")
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Check current samples
        response = requests.get(
            f"{API_BASE_URL}/sample-selection/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/samples",
            headers=headers
        )
        
        if response.status_code == 404:
            print_warning("No samples found - generating samples first")
            # Generate samples
            gen_response = requests.post(
                f"{API_BASE_URL}/sample-selection/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/generate",
                headers=headers,
                json={
                    "sample_size": 50,
                    "attributes": ["Credit Limit", "Annual Revenue", "Industry Type"]
                }
            )
            if gen_response.status_code in [200, 201]:
                print_success("Samples generated successfully")
            else:
                print_error(f"Failed to generate samples: {gen_response.status_code}")
                test_results.append(("Sample Selection Feedback", "FAILED", "Sample generation failed"))
        
        # Get report owner feedback
        response = requests.get(
            f"{API_BASE_URL}/sample-selection/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/report-owner-feedback",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "version_number" in data:
                print_success(f"Version indicator present: v{data['version_number']}")
            else:
                print_warning("No version indicator (no RO review yet)")
            
            if "samples" in data and isinstance(data["samples"], list):
                print_success(f"Samples data structure correct ({len(data['samples'])} samples)")
                
                # Check for duplicates
                sample_ids = [s.get("sample_id") for s in data["samples"]]
                if len(sample_ids) == len(set(sample_ids)):
                    print_success("No duplicate samples")
                    test_results.append(("Sample Selection Feedback", "PASSED", "All checks passed"))
                else:
                    print_error("Duplicate samples detected")
                    test_results.append(("Sample Selection Feedback", "FAILED", "Duplicate samples"))
            else:
                print_success("No RO feedback yet (expected)")
                test_results.append(("Sample Selection Feedback", "PASSED", "No RO review yet"))
        else:
            print_error(f"API error: {response.status_code}")
            test_results.append(("Sample Selection Feedback", "FAILED", f"API error: {response.status_code}"))
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        test_results.append(("Sample Selection Feedback", "FAILED", str(e)))
    
    # Test 2: Scoping Report Owner Feedback
    print_test("2. Scoping - Report Owner Feedback")
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{API_BASE_URL}/scoping/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/report-owner-feedback",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "version_number" in data:
                print_success(f"Version indicator present: v{data['version_number']}")
                test_results.append(("Scoping Feedback", "PASSED", "Version indicator present"))
            else:
                print_warning("No version indicator (no RO review yet)")
                test_results.append(("Scoping Feedback", "PASSED", "No RO review yet"))
        else:
            print_error(f"API error: {response.status_code}")
            test_results.append(("Scoping Feedback", "FAILED", f"API error: {response.status_code}"))
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        test_results.append(("Scoping Feedback", "FAILED", str(e)))
    
    # Test 3: Data Profiling Report Owner Feedback
    print_test("3. Data Profiling - Report Owner Feedback")
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{API_BASE_URL}/data-profiling/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/report-owner-feedback",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "version_number" in data:
                print_success(f"Version indicator present: v{data['version_number']}")
                test_results.append(("Data Profiling Feedback", "PASSED", "Version indicator present"))
            else:
                print_warning("No version indicator (no RO review yet)")
                test_results.append(("Data Profiling Feedback", "PASSED", "No RO review yet"))
        else:
            print_error(f"API error: {response.status_code}")
            test_results.append(("Data Profiling Feedback", "FAILED", f"API error: {response.status_code}"))
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        test_results.append(("Data Profiling Feedback", "FAILED", str(e)))
    
    # Test 4: 404 Error Check
    print_test("4. 404 Error Check")
    endpoints = [
        (f"/sample-selection/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/samples", "Sample Selection - Samples"),
        (f"/sample-selection/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/report-owner-feedback", "Sample Selection - RO Feedback"),
        (f"/scoping/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/attributes", "Scoping - Attributes"),
        (f"/scoping/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/report-owner-feedback", "Scoping - RO Feedback"),
        (f"/data-profiling/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/attributes", "Data Profiling - Attributes"),
        (f"/data-profiling/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/report-owner-feedback", "Data Profiling - RO Feedback"),
    ]
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    errors_found = []
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
            
            if response.status_code == 404:
                errors_found.append(name)
                print_error(f"404 error: {name}")
            else:
                print_success(f"{name} - Status: {response.status_code}")
                
        except Exception as e:
            errors_found.append(f"{name} (Connection error)")
            print_error(f"Error: {name} - {str(e)}")
    
    if not errors_found:
        print_success("No 404 errors found")
        test_results.append(("404 Error Check", "PASSED", "No 404 errors"))
    else:
        test_results.append(("404 Error Check", "FAILED", f"{len(errors_found)} endpoints with errors"))
    
    # Test 5: Version-based Submission
    print_test("5. Version-based Submission")
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{API_BASE_URL}/sample-selection/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/samples",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            current_version = data.get("version_number", 1)
            version_id = data.get("version_id")
            
            print(f"Current version: v{current_version}")
            
            # Test submission
            submit_response = requests.post(
                f"{API_BASE_URL}/sample-selection/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/submit",
                headers=headers,
                json={
                    "version_id": version_id,
                    "assignee_email": REPORT_OWNER_EMAIL
                }
            )
            
            if submit_response.status_code in [200, 201]:
                print_success("Assignment created successfully")
                test_results.append(("Version-based Submission", "PASSED", "Assignment created"))
            elif submit_response.status_code == 409:
                print_warning("Assignment already exists")
                test_results.append(("Version-based Submission", "PASSED", "Assignment already exists"))
            else:
                print_error(f"Submission failed: {submit_response.status_code}")
                test_results.append(("Version-based Submission", "FAILED", f"API error: {submit_response.status_code}"))
        else:
            print_error("Could not get current version")
            test_results.append(("Version-based Submission", "FAILED", "Could not get version"))
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        test_results.append(("Version-based Submission", "FAILED", str(e)))
    
    # Test 6: General Workflow
    print_test("6. General Workflow")
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        passed_checks = 0
        total_checks = 0
        
        phases = [
            ("Sample Selection", [
                f"/sample-selection/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/samples",
                f"/sample-selection/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/report-owner-feedback"
            ]),
            ("Scoping", [
                f"/scoping/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/attributes",
                f"/scoping/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/report-owner-feedback"
            ]),
            ("Data Profiling", [
                f"/data-profiling/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/attributes",
                f"/data-profiling/{TEST_CYCLE_ID}/{TEST_REPORT_ID}/report-owner-feedback"
            ])
        ]
        
        for phase_name, endpoints in phases:
            print(f"\nChecking {phase_name}...")
            for endpoint in endpoints:
                total_checks += 1
                response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
                
                if response.status_code in [200, 201]:
                    print_success(f"{endpoint} - OK")
                    passed_checks += 1
                else:
                    print_error(f"{endpoint} - Status: {response.status_code}")
        
        if passed_checks == total_checks:
            print_success(f"All workflow endpoints working ({passed_checks}/{total_checks})")
            test_results.append(("General Workflow", "PASSED", "All endpoints working"))
        else:
            print_error(f"Some endpoints failed ({passed_checks}/{total_checks})")
            test_results.append(("General Workflow", "FAILED", f"{total_checks - passed_checks} endpoints failed"))
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        test_results.append(("General Workflow", "FAILED", str(e)))
    
    # Print Summary
    print_header("TEST SUMMARY")
    
    passed = 0
    failed = 0
    
    print("\nTest Results:")
    print("-" * 60)
    print(f"{'Test Name':<30} {'Status':<15} {'Details':<30}")
    print("-" * 60)
    
    for test_name, status, details in test_results:
        if status == "PASSED":
            status_display = f"{GREEN}✓ PASSED{END}"
            passed += 1
        else:
            status_display = f"{RED}✗ FAILED{END}"
            failed += 1
        
        print(f"{test_name:<30} {status_display:<25} {details:<30}")
    
    print("-" * 60)
    total = passed + failed
    
    if failed == 0:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED! ({passed}/{total}){END}")
    else:
        print(f"\n{RED}{BOLD}⚠️  {failed} TESTS FAILED ({passed}/{total} passed){END}")
    
    print(f"\n{YELLOW}{BOLD}📋 Additional Manual Checks Required:{END}")
    print("1. Open browser developer tools (F12) and check Console tab")
    print("2. Navigate through all phases and tabs")
    print("3. Look for any JavaScript errors or warnings")
    print("4. Test the 'Make Changes' functionality")
    print("5. Verify UI responsiveness and loading times")
    
    print(f"\n{BLUE}{BOLD}💡 To run browser console test:{END}")
    print("1. Open browser console (F12)")
    print("2. Copy and paste the contents of frontend_console_test.js")
    print("3. Run: testNavigation()")
    print("4. Run: testSummary()")


if __name__ == "__main__":
    run_tests()