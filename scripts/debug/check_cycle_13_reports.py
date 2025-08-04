"""
Check reports in cycle 13
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8001/api/v1"

async def check_cycle_13():
    """Check reports in cycle 13"""
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
        
        # Get reports for cycle 13
        print("\n=== Reports in Cycle 13 ===")
        response = await client.get(
            f"{BASE_URL}/cycles/13/reports", 
            headers=headers,
            follow_redirects=True
        )
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            reports = response.json()
            print(f"Found {len(reports)} reports")
            for report in reports:
                print(f"  Report {report['report_id']}: {report['report_name']}")
                
                # Check workflow phases for this report
                response2 = await client.get(
                    f"{BASE_URL}/cycles/13/reports/{report['report_id']}/workflow",
                    headers=headers,
                    follow_redirects=True
                )
                if response2.status_code == 200:
                    phases = response2.json()
                    print(f"    Workflow phases: {len(phases.get('phases', []))}")
                    for phase in phases.get('phases', []):
                        print(f"      - {phase['phase_name']}: {phase['status']}")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(check_cycle_13())