#!/usr/bin/env python3
"""
Simple test to verify Celery tasks are working
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001"

# Login first
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={"email": "tester@example.com", "password": "password123"}
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("✅ Logged in successfully")

# Test 1: Planning MapPDE
print("\n🧪 Test 1: Planning MapPDE")
response = requests.post(
    f"{BASE_URL}/api/v1/planning/cycles/2/reports/3/pde-mappings/auto-map",
    headers=headers,
    json={}
)
print(f"Response status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ MapPDE job started: {data.get('job_id')}")
    print(f"   Message: {data.get('message')}")
else:
    print(f"❌ Failed: {response.text}")

# Test 2: Check Celery workers
print("\n🧪 Checking Celery worker health...")
import subprocess
result = subprocess.run(
    ["docker-compose", "-f", "docker-compose.container.yml", "exec", "celery-worker", "celery", "-A", "app.core.celery_app", "inspect", "active"],
    capture_output=True,
    text=True
)
if result.returncode == 0:
    print("✅ Celery worker is responsive")
else:
    print("❌ Celery worker not responding")

print("\n✅ Basic tests completed!")