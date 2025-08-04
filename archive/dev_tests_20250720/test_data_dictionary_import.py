#!/usr/bin/env python3
"""
Test script to verify data dictionary import functionality
"""

import asyncio
import aiohttp
import json

async def test_data_dictionary_import():
    """Test the data dictionary import endpoint"""
    
    # First authenticate
    login_data = {
        "email": "data.provider@example.com",
        "password": "password123"
    }
    
    async with aiohttp.ClientSession() as session:
        # Login
        async with session.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                print(f"❌ Login failed: {response.status}")
                return
            
            data = await response.json()
            token = data.get("access_token")
            if not token:
                print("❌ No token received")
                return
            
            print("✅ Authentication successful")
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Test data dictionary endpoint
            async with session.get(
                "http://localhost:8000/api/v1/data-dictionary/?per_page=5",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Data dictionary retrieved: {data.get('total', 0)} total entries")
                    
                    # If we have entries, test import
                    if data.get('items') and len(data['items']) > 0:
                        dict_entry = data['items'][0]
                        dict_id = dict_entry['dict_id']
                        
                        # Test import with a small sample
                        import_data = {
                            "selected_dict_ids": [dict_id],
                            "cycle_id": 55,  # Use the cycle from the error
                            "report_id": 156  # Use the report from the error
                        }
                        
                        async with session.post(
                            "http://localhost:8000/api/v1/data-dictionary/import/",
                            json=import_data,
                            headers=headers
                        ) as import_response:
                            import_result = await import_response.json()
                            print(f"📊 Import response status: {import_response.status}")
                            print(f"📊 Import result: {json.dumps(import_result, indent=2)}")
                            
                            if import_response.status == 200:
                                if import_result.get('success'):
                                    print(f"✅ Import successful: {import_result.get('imported_count')} imported")
                                else:
                                    print(f"⚠️ Import had errors: {import_result.get('error_count')} errors")
                                    print(f"📝 Messages: {import_result.get('messages', [])}")
                            else:
                                print(f"❌ Import failed: {import_result}")
                    else:
                        print("⚠️ No data dictionary entries found to test import")
                else:
                    error_data = await response.text()
                    print(f"❌ Data dictionary failed: {response.status} - {error_data}")

if __name__ == "__main__":
    asyncio.run(test_data_dictionary_import())