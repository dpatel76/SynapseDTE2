#!/usr/bin/env python3
"""
Test Backend Data Provider Status Error
Make actual HTTP request to identify the error
"""

import requests
import json
import sys

def test_status_endpoint():
    """Test the data provider status endpoint via HTTP"""
    print("=== TESTING DATA PROVIDER STATUS VIA HTTP ===")
    
    # Try different cycle/report combinations
    test_cases = [
        (8, 160, "Recent cycle"),
        (4, 156, "Cycle with scoped attributes")
    ]
    
    base_url = "http://localhost:8000"  # Adjust if your backend runs on different port
    
    for cycle_id, report_id, description in test_cases:
        print(f"\n--- Testing {description}: cycle_id={cycle_id}, report_id={report_id} ---")
        
        url = f"{base_url}/api/v1/data-owner/{cycle_id}/reports/{report_id}/status"
        print(f"URL: {url}")
        
        try:
            # Make request without authentication first to see the error
            response = requests.get(url, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("SUCCESS! Response data:")
                    print(json.dumps(data, indent=2, default=str))
                except json.JSONDecodeError:
                    print("Response is not valid JSON:")
                    print(response.text[:500])
            else:
                print("ERROR Response:")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except:
                    print(response.text[:500])
                    
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Backend server not running or not accessible")
            print("   Make sure your FastAPI server is running on localhost:8000")
            return
        except requests.exceptions.Timeout:
            print("❌ Timeout Error: Request took too long")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_status_endpoint() 