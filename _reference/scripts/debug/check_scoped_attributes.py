"""
Check scoped attributes for report
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8001/api/v1"

async def check_attributes():
    """Check scoped attributes"""
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
        
        # Get scoped attributes
        print("\n=== Scoped Attributes for Report 156 ===")
        response = await client.get(
            f"{BASE_URL}/scoping/cycles/13/reports/156/attributes",
            headers=headers,
            follow_redirects=True
        )
        
        if response.status_code == 200:
            data = response.json()
            # Handle both list and dict responses
            if isinstance(data, list):
                attributes = data
            else:
                attributes = data.get('attributes', [])
            
            scoped_attrs = [attr for attr in attributes if attr.get('is_scoped')]
            print(f"Total attributes: {len(attributes)}")
            print(f"Found {len(scoped_attrs)} scoped attributes")
            for attr in scoped_attrs[:5]:  # Show first 5
                print(f"  - {attr['attribute_name']} (data_type={attr.get('data_type', 'None')}) - Primary Key: {attr.get('is_primary_key', False)}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(check_attributes())