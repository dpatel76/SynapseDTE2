import requests

# Login
response = requests.post("http://localhost:8001/api/v1/auth/login", json={
    "email": "tester@synapse.com",
    "password": "TestUser123\!"
})

print("Login response:", response.status_code)
if response.status_code \!= 200:
    print("Login error:", response.text)
    exit(1)
    
data = response.json()
print("Token:", data.get("access_token"))

# Test analytics endpoint
if data.get("access_token"):
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    response = requests.get(
        "http://localhost:8001/api/v1/sample-selection/cycles/13/reports/156/samples/analytics",
        headers=headers
    )
    print("\nAnalytics response:", response.status_code)
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.text)
