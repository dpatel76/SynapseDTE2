const fetch = require('node-fetch');

async function testWorkflowEndpoints() {
  // Login first
  const loginResponse = await fetch('http://localhost:8001/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'tester@example.com',
      password: 'password123'
    })
  });

  if (!loginResponse.ok) {
    console.error('Login failed:', await loginResponse.text());
    return;
  }

  const { access_token } = await loginResponse.json();
  console.log('✅ Logged in successfully\n');

  const endpoints = [
    { 
      name: 'Sample Selection Status',
      url: 'http://localhost:8001/api/v1/sample-selection/9/reports/156/status'
    },
    {
      name: 'Data Provider ID Status',
      url: 'http://localhost:8001/api/v1/data-owner/9/reports/156/status'
    },
    {
      name: 'Request Info',
      url: 'http://localhost:8001/api/v1/request-info/9/reports/156'
    },
    {
      name: 'Test Execution Status',
      url: 'http://localhost:8001/api/v1/test-execution/9/reports/156/status'
    },
    {
      name: 'Observations',
      url: 'http://localhost:8001/api/v1/observation-management/9/reports/156/observations'
    }
  ];

  for (const endpoint of endpoints) {
    console.log(`\nTesting ${endpoint.name}...`);
    console.log('URL:', endpoint.url);
    
    try {
      const response = await fetch(endpoint.url, {
        headers: {
          'Authorization': `Bearer ${access_token}`
        }
      });

      console.log('Status:', response.status, response.statusText);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Response:', JSON.stringify(data, null, 2));
      } else {
        const error = await response.text();
        console.log('Error:', error);
      }
    } catch (error) {
      console.error('Request failed:', error.message);
    }
  }
}

testWorkflowEndpoints().catch(console.error);