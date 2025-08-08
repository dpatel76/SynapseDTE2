#!/usr/bin/env python3
"""
Test Data Provider Status with Authentication
Test the status endpoint with proper auth headers
"""

import requests
import json

def test_with_auth():
    """Test status endpoint with authentication"""
    print("=== TESTING STATUS ENDPOINT WITH AUTHENTICATION ===")
    
    # You'll need to get your auth token from browser dev tools
    print("\n📋 INSTRUCTIONS:")
    print("1. Open browser dev tools (F12)")
    print("2. Go to Network tab")
    print("3. Refresh the data provider page")
    print("4. Find any successful API request")
    print("5. Copy the 'Authorization' header value")
    print("6. Paste it below when prompted")
    
    try:
        auth_token = input("\n🔑 Enter your Authorization header (Bearer xxxxx): ").strip()
        
        if not auth_token:
            print("❌ No token provided")
            return
            
        if not auth_token.startswith("Bearer "):
            auth_token = f"Bearer {auth_token}"
        
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        
        # Test both cycle/report combinations
        test_cases = [
            (4, 156, "Cycle with scoped attributes"),
            (8, 160, "Recent cycle")
        ]
        
        for cycle_id, report_id, description in test_cases:
            print(f"\n--- Testing {description}: cycle_id={cycle_id}, report_id={report_id} ---")
            
            url = f"http://localhost:8000/api/v1/data-owner/{cycle_id}/reports/{report_id}/status"
            print(f"URL: {url}")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print("✅ SUCCESS! Response data:")
                        print(json.dumps(data, indent=2, default=str))
                    except json.JSONDecodeError:
                        print("❌ Response is not valid JSON:")
                        print(response.text[:500])
                else:
                    print("❌ ERROR Response:")
                    try:
                        error_data = response.json()
                        print(json.dumps(error_data, indent=2))
                    except:
                        print(response.text[:500])
                        
            except requests.exceptions.ConnectionError:
                print("❌ Connection Error: Backend server not running")
                return
            except requests.exceptions.Timeout:
                print("❌ Timeout Error: Request took too long")
            except Exception as e:
                print(f"❌ Unexpected Error: {e}")
                
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_with_auth() 