#!/usr/bin/env python3
import requests
import json

# Login first
login_response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={'email': 'tester1@synapse.com', 'password': 'Test123!'}
)

if login_response.status_code != 200:
    print(f'Login failed: {login_response.status_code}')
    print(login_response.text)
    exit(1)

token = login_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Execute test case 436
print('Executing test case 436...')
response = requests.post(
    'http://localhost:8000/api/v1/test-execution/58/reports/156/execute',
    json={
        'test_case_ids': ['436'],
        'execution_reason': 'initial',
        'execution_method': 'automatic',
        'configuration': {
            'priority': 'normal',
            'timeout_seconds': 300,
            'retry_count': 3
        }
    },
    headers=headers
)

print(f'Response status: {response.status_code}')
print(f'Response: {json.dumps(response.json(), indent=2)}')

# Execute test case 437
print('\n\nExecuting test case 437...')
response = requests.post(
    'http://localhost:8000/api/v1/test-execution/58/reports/156/execute',
    json={
        'test_case_ids': ['437'],
        'execution_reason': 'initial',
        'execution_method': 'automatic',
        'configuration': {
            'priority': 'normal',
            'timeout_seconds': 300,
            'retry_count': 3
        }
    },
    headers=headers
)

print(f'Response status: {response.status_code}')
print(f'Response: {json.dumps(response.json(), indent=2)}')