import asyncio
import aiohttp
import json

async def test_auth_and_planning():
    """Test the authentication flow and planning API access"""
    print("Testing authentication and planning API flow...")
    
    base_url = "http://localhost:8000/api/v1"
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Try to login with the correct tester
        print("\n1. Testing login...")
        login_data = {
            "email": "admin@example.com",
            "password": "AdminUser123!"
        }
        
        try:
            async with session.post(f"{base_url}/auth/login", json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get("access_token")
                    user = result.get("user")
                    print(f"✅ Login successful")
                    print(f"   Token: {token[:20]}...")
                    print(f"   User: {user.get('email')} ({user.get('role')})")
                else:
                    print(f"❌ Login failed: {response.status}")
                    text = await response.text()
                    print(f"   Error: {text}")
                    return
        except Exception as e:
            print(f"❌ Login error: {e}")
            return
        
        # Step 2: Test planning API access
        print("\n2. Testing planning API access...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test getting attributes
        try:
            async with session.get(f"{base_url}/planning/1/reports/12/attributes", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    attributes = result.get("attributes", [])
                    print(f"✅ Planning API access successful")
                    print(f"   Current attributes: {len(attributes)}")
                else:
                    print(f"❌ Planning API failed: {response.status}")
                    text = await response.text()
                    print(f"   Error: {text}")
        except Exception as e:
            print(f"❌ Planning API error: {e}")
        
        # Step 3: Test LLM API access
        print("\n3. Testing LLM API access...")
        llm_data = {
            "regulatory_context": "CECL testing",
            "report_type": "CECL Report",
            "preferred_provider": "gemini"
        }
        
        try:
            async with session.post(f"{base_url}/llm/generate-attributes", json=llm_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ LLM API access successful")
                    print(f"   Success: {result.get('success')}")
                    print(f"   Discovered: {result.get('discovered_count')}")
                    print(f"   Detailed: {result.get('detailed_count')}")
                else:
                    print(f"❌ LLM API failed: {response.status}")
                    text = await response.text()
                    print(f"   Error: {text}")
        except Exception as e:
            print(f"❌ LLM API error: {e}")
        
        # Step 4: Test creating a single attribute
        print("\n4. Testing attribute creation...")
        test_attr = {
            "attribute_name": "test_attribute_" + str(int(asyncio.get_event_loop().time())),
            "description": "Test attribute for debugging",
            "data_type": "String",
            "mandatory_flag": "Optional",
            "cde_flag": False,
            "historical_issues_flag": False,
            "tester_notes": "Created by test script",
            "validation_rules": "Test validation",
            "typical_source_documents": "Test documents",
            "keywords_to_look_for": "test keywords",
            "testing_approach": "test approach"
        }
        
        try:
            async with session.post(f"{base_url}/planning/1/reports/12/attributes", json=test_attr, headers=headers) as response:
                if response.status == 200 or response.status == 201:
                    result = await response.json()
                    print(f"✅ Attribute creation successful")
                    print(f"   Created: {result.get('attribute_name')}")
                else:
                    print(f"❌ Attribute creation failed: {response.status}")
                    text = await response.text()
                    print(f"   Error: {text}")
        except Exception as e:
            print(f"❌ Attribute creation error: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth_and_planning()) 