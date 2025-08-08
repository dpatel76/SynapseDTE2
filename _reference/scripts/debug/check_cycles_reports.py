"""
Check existing cycles and reports
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8001/api/v1"

async def check_data():
    """Check existing cycles and reports"""
    async with httpx.AsyncClient() as client:
        # Login
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "tester@synapse.com", "password": "TestUser123!"}
        )
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get cycles
        print("\n=== Test Cycles ===")
        response = await client.get(f"{BASE_URL}/cycles/", headers=headers, follow_redirects=True)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            print(f"Response: {data}")
            
            # Handle different response formats
            if isinstance(data, dict) and 'cycles' in data:
                cycles = data['cycles']
            elif isinstance(data, list):
                cycles = data
            else:
                print("Unexpected response format")
                return
                
            print(f"Found {len(cycles)} cycles")
            for cycle in cycles[:5]:  # Show first 5
                print(f"  Cycle {cycle['cycle_id']}: {cycle['cycle_name']} ({cycle['status']})")
                
                # Get reports for this cycle
                response2 = await client.get(f"{BASE_URL}/cycles/{cycle['cycle_id']}/reports", headers=headers)
                if response2.status_code == 200:
                    reports = response2.json()
                    print(f"    Reports: {len(reports)}")
                    for report in reports[:3]:  # Show first 3
                        print(f"      - Report {report['report_id']}: {report['report_name']}")
        else:
            print(f"Error getting cycles: {response.text}")

if __name__ == "__main__":
    asyncio.run(check_data())