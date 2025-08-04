/**
 * Global teardown for E2E tests
 * Runs once after all tests to clean up the testing environment
 */
async function globalTeardown() {
  console.log('🧹 Starting global E2E test teardown...');

  try {
    // Clean up test database
    await cleanupDatabase();
    
    // Clean up uploaded test files
    await cleanupTestFiles();
    
    // Reset SLA configurations
    await resetSLAConfigurations();
    
    console.log('✅ Global E2E test teardown completed');
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw error to avoid masking test failures
  }
}

async function cleanupDatabase() {
  console.log('🗑️ Cleaning up test database...');
  
  try {
    const response = await fetch('http://localhost:8001/api/v1/test/cleanup-database', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (response.ok) {
      console.log('✅ Test database cleaned up successfully');
    } else {
      console.warn('⚠️ Database cleanup response was not OK:', response.statusText);
    }
  } catch (error) {
    console.error('⚠️ Database cleanup error:', error);
  }
}

async function cleanupTestFiles() {
  console.log('📁 Cleaning up test files...');
  
  try {
    const response = await fetch('http://localhost:8001/api/v1/test/cleanup-files', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (response.ok) {
      console.log('✅ Test files cleaned up successfully');
    } else {
      console.warn('⚠️ File cleanup response was not OK:', response.statusText);
    }
  } catch (error) {
    console.error('⚠️ File cleanup error:', error);
  }
}

async function resetSLAConfigurations() {
  console.log('⏰ Resetting SLA configurations...');
  
  try {
    const response = await fetch('http://localhost:8001/api/v1/test/reset-sla', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (response.ok) {
      console.log('✅ SLA configurations reset successfully');
    } else {
      console.warn('⚠️ SLA reset response was not OK:', response.statusText);
    }
  } catch (error) {
    console.error('⚠️ SLA reset error:', error);
  }
}

export default globalTeardown; 