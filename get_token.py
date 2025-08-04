import requests

# Login as tester
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "tester@example.com", "password": "password123"}
)

if response.status_code == 200:
    data = response.json()
    print(f"TOKEN={data['access_token']}")
else:
    print(f"Login failed: {response.text}")