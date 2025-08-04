import { FullConfig } from '@playwright/test';

const API_BASE_URL = 'http://localhost:8001/api/v1';

/**
 * Global setup for E2E tests
 * Runs once before all tests to prepare the testing environment
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global E2E test setup...');

  // Wait for services to be ready
  await waitForServices(config);
  
  // Seed test database
  await seedDatabase();
  
  // Create test users with different roles
  await createTestUsers();
  
  // Set up test data
  await setupTestData();
  
  console.log('✅ Global E2E test setup completed');
}

async function waitForServices(config: FullConfig) {
  const baseURL = config.projects[0].use.baseURL || 'http://localhost:3000';
  const apiURL = 'http://localhost:8001';
  
  console.log('⏳ Waiting for services to be ready...');
  
  // Wait for frontend
  await waitForURL(baseURL + '/login', 'Frontend');
  
  // Wait for API
  await waitForURL(apiURL + '/api/v1/health', 'API');
  
  console.log('✅ All services are ready');
}

async function waitForURL(url: string, serviceName: string) {
  const maxAttempts = 60; // 2 minutes with 2-second intervals
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        console.log(`✅ ${serviceName} is ready at ${url}`);
        return;
      }
    } catch (error) {
      // Service not ready yet
    }
    
    attempts++;
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  throw new Error(`❌ ${serviceName} failed to start within timeout at ${url}`);
}

async function seedDatabase() {
  console.log('🌱 Seeding test database...');
  
  try {
    const response = await fetch('http://localhost:8001/api/v1/test/seed-database', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        environment: 'test',
        clearExisting: true
      })
    });
    
    if (!response.ok) {
      throw new Error(`Database seeding failed: ${response.statusText}`);
    }
    
    console.log('✅ Test database seeded successfully');
  } catch (error) {
    console.error('❌ Database seeding failed:', error);
    throw error;
  }
}

async function createTestUsers() {
  console.log('👥 Creating test users...');
  
  // First, get the current LOB IDs from the database
  const lobsResponse = await fetch(`${API_BASE_URL}/test/get-lobs`);
  let retailBankingLobId = 25; // fallback
  let commercialBankingLobId = 26; // fallback
  
  if (lobsResponse.ok) {
    const lobs = await lobsResponse.json();
    const retailLob = lobs.find((lob: any) => lob.lob_name === 'Retail Banking');
    const commercialLob = lobs.find((lob: any) => lob.lob_name === 'Commercial Banking');
    
    if (retailLob) retailBankingLobId = retailLob.lob_id;
    if (commercialLob) commercialBankingLobId = commercialLob.lob_id;
    
    console.log(`📋 Using LOB IDs: Retail Banking=${retailBankingLobId}, Commercial Banking=${commercialBankingLobId}`);
  } else {
    console.log('⚠️ Could not fetch LOBs, using fallback IDs');
  }
  
  const testUsers = [
    {
      first_name: 'Admin',
      last_name: 'User',
      email: 'admin@synapsedt.com',
      password: 'admin123',
      role: 'Test Manager',
      lob_id: retailBankingLobId
    },
    {
      first_name: 'Test',
      last_name: 'Manager',
      email: 'test.manager@example.com',
      password: 'TestManager123!',
      role: 'Test Manager',
      lob_id: retailBankingLobId
    },
    {
      first_name: 'Jane',
      last_name: 'Doe',
      email: 'tester@example.com',
      password: 'Tester123!',
      role: 'Tester',
      lob_id: retailBankingLobId
    },
    {
      first_name: 'Mike',
      last_name: 'Johnson',
      email: 'report.owner@example.com',
      password: 'ReportOwner123!',
      role: 'Report Owner',
      lob_id: retailBankingLobId
    },
    {
      first_name: 'Sarah',
      last_name: 'Wilson',
      email: 'report.exec@example.com',
      password: 'ReportExec123!',
      role: 'Report Owner Executive',
      lob_id: retailBankingLobId
    },
    {
      first_name: 'David',
      last_name: 'Brown',
      email: 'cdo@example.com',
      password: 'CDO123!',
      role: 'CDO',
      lob_id: retailBankingLobId
    },
    {
      first_name: 'Lisa',
      last_name: 'Chen',
      email: 'data.provider@example.com',
      password: 'DataProvider123!',
      role: 'Data Provider',
      lob_id: retailBankingLobId
    }
  ];
  
  for (const user of testUsers) {
    try {
      const response = await fetch('http://localhost:8001/api/v1/test/create-user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(user)
      });
      
      if (!response.ok) {
        console.warn(`⚠️ Failed to create user ${user.email}: ${response.statusText}`);
      } else {
        console.log(`✅ Created test user: ${user.email} (${user.role})`);
      }
    } catch (error) {
      console.warn(`⚠️ Error creating user ${user.email}:`, error);
    }
  }
}

async function setupTestData() {
  console.log('📊 Setting up test data...');
  
  try {
    // Create test LOBs
    await createTestLOBs();
    
    // Create test reports
    await createTestReports();
    
    // Create test data sources
    await createTestDataSources();
    
    console.log('✅ Test data setup completed');
  } catch (error) {
    console.error('❌ Test data setup failed:', error);
    throw error;
  }
}

async function createTestLOBs() {
  const lobs = [
    {
      name: 'Retail Banking',
      description: 'Retail banking operations and services',
      is_active: true
    },
    {
      name: 'Commercial Banking',
      description: 'Commercial and corporate banking services',
      is_active: true
    },
    {
      name: 'Investment Banking',
      description: 'Investment banking and capital markets',
      is_active: true
    }
  ];
  
  for (const lob of lobs) {
    try {
      const response = await fetch('http://localhost:8001/api/v1/test/create-lob', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(lob)
      });
      
      if (response.ok) {
        console.log(`✅ Created test LOB: ${lob.name}`);
      }
    } catch (error) {
      console.warn(`⚠️ Error creating LOB ${lob.name}:`, error);
    }
  }
}

async function createTestReports() {
  // Get current LOB IDs
  const lobsResponse = await fetch(`${API_BASE_URL}/test/get-lobs`);
  let retailBankingLobId = 25; // fallback
  let commercialBankingLobId = 26; // fallback
  
  if (lobsResponse.ok) {
    const lobs = await lobsResponse.json();
    const retailLob = lobs.find((lob: any) => lob.lob_name === 'Retail Banking');
    const commercialLob = lobs.find((lob: any) => lob.lob_name === 'Commercial Banking');
    
    if (retailLob) retailBankingLobId = retailLob.lob_id;
    if (commercialLob) commercialBankingLobId = commercialLob.lob_id;
  }

  // Get the Report Owner user ID dynamically
  let reportOwnerUserId = 4; // fallback
  try {
    const usersResponse = await fetch(`${API_BASE_URL}/test/get-users`);
    if (usersResponse.ok) {
      const users = await usersResponse.json();
      const reportOwner = users.find((user: any) => user.email === 'report.owner@example.com');
      if (reportOwner) {
        reportOwnerUserId = reportOwner.user_id;
      }
    }
  } catch (error) {
    console.warn('Failed to get Report Owner user ID, using fallback:', error);
  }

  const reports = [
    {
      report_name: 'Monthly Loan Portfolio Report',
      regulation: 'FR Y-9C',
      description: 'Monthly regulatory report for loan portfolio',
      frequency: 'Monthly',
      report_owner_id: reportOwnerUserId,
      lob_id: retailBankingLobId,
      is_active: true
    },
    {
      report_name: 'Credit Risk Assessment Report',
      regulation: 'Basel III',
      description: 'Quarterly credit risk assessment',
      frequency: 'Quarterly',
      report_owner_id: reportOwnerUserId,
      lob_id: retailBankingLobId,
      is_active: true
    },
    {
      report_name: 'Customer Deposit Summary',
      regulation: 'Call Report',
      description: 'Monthly customer deposit summary report',
      frequency: 'Monthly',
      report_owner_id: reportOwnerUserId,
      lob_id: commercialBankingLobId,
      is_active: true
    }
  ];
  
  for (const report of reports) {
    try {
      const response = await fetch('http://localhost:8001/api/v1/test/create-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(report)
      });
      
      if (response.ok) {
        console.log(`✅ Created test report: ${report.report_name}`);
      } else {
        console.warn(`⚠️ Failed to create report ${report.report_name}: ${response.statusText}`);
      }
    } catch (error) {
      console.warn(`⚠️ Error creating report ${report.report_name}:`, error);
    }
  }
}

async function createTestDataSources() {
  const dataSources = [
    {
      name: 'Customer Database',
      description: 'Primary customer information database',
      connection_type: 'PostgreSQL',
      host: 'localhost',
      port: 5432,
      database_name: 'customer_db',
      is_active: true
    },
    {
      name: 'Loan Management System',
      description: 'Core loan processing and management system',
      connection_type: 'Oracle',
      host: 'localhost',
      port: 1521,
      database_name: 'loan_db',
      is_active: true
    },
    {
      name: 'Risk Data Warehouse',
      description: 'Enterprise risk data warehouse',
      connection_type: 'SQL Server',
      host: 'localhost',
      port: 1433,
      database_name: 'risk_dw',
      is_active: true
    }
  ];
  
  for (const dataSource of dataSources) {
    try {
      const response = await fetch('http://localhost:8001/api/v1/test/create-data-source', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataSource)
      });
      
      if (response.ok) {
        console.log(`✅ Created test data source: ${dataSource.name}`);
      }
    } catch (error) {
      console.warn(`⚠️ Error creating data source ${dataSource.name}:`, error);
    }
  }
}

export default globalSetup; 