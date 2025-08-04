import { test, expect, Page } from '@playwright/test';
import { 
  loginAsUser, 
  loginAsAdmin,
  loginAsTester, 
  testUsers, 
  waitForPageLoad, 
  navigateAndWait,
  clickAndWait,
  fillField,
  checkForErrors,
  getLOBIds,
  createTestReport,
  retry,
  waitForApiRequest
} from './test-utils';

// Test data
const testCycleData = {
  name: 'Q4 2024 Testing Cycle',
  description: 'Comprehensive quarterly testing cycle',
  startDate: '2024-01-01',
  endDate: '2024-03-31'
};

const testReportData = {
  name: 'Loan Portfolio Report',
  reportCode: 'LPR-001',
  description: 'Monthly loan portfolio regulatory report'
};

const testAttributes = [
  {
    name: 'loan_id',
    description: 'Unique identifier for each loan',
    type: 'String',
    flag: 'Mandatory',
    cdeFlag: true,
    historicalIssuesFlag: false
  },
  {
    name: 'borrower_name',
    description: 'Full name of the borrower',
    type: 'String', 
    flag: 'Mandatory',
    cdeFlag: false,
    historicalIssuesFlag: true
  },
  {
    name: 'loan_amount',
    description: 'Original loan amount',
    type: 'Number',
    flag: 'Mandatory', 
    cdeFlag: true,
    historicalIssuesFlag: false
  },
  {
    name: 'interest_rate',
    description: 'Annual percentage rate',
    type: 'Number',
    flag: 'Conditional',
    cdeFlag: false,
    historicalIssuesFlag: true
  }
];

test.describe('Complete Testing Workflow', () => {
  let testCycleId: string;
  let reportId: string;
  let lobIds: Record<string, number>;

  test.beforeAll(async () => {
    // Get current LOB IDs dynamically
    lobIds = await getLOBIds();
  });

  test('1. Test Manager creates Test Cycle', async ({ page }) => {
    await loginAsUser(page, testUsers.testManager);
    
    // Navigate to test cycles
    await clickAndWait(page, '[data-testid="nav-cycles"]');
    await expect(page).toHaveURL(/\/cycles/);
    
    // Create new test cycle with error handling
    await retry(async () => {
      await page.click('[data-testid="create-cycle-button"]');
      await fillField(page, '[data-testid="cycle-name-input"]', testCycleData.name);
      await fillField(page, '[data-testid="cycle-description-input"]', testCycleData.description);
      await fillField(page, '[data-testid="cycle-start-date"]', testCycleData.startDate);
      await fillField(page, '[data-testid="cycle-end-date"]', testCycleData.endDate);
      await page.selectOption('[data-testid="test-manager-select"]', testUsers.testManager.name);
      await page.click('[data-testid="save-cycle-button"]');
    });
    
    // Wait for creation to complete
    await waitForPageLoad(page);
    
    // Check for errors
    const error = await checkForErrors(page);
    if (error) {
      console.warn(`Cycle creation error: ${error}`);
    }
    
    // Verify cycle creation
    await expect(page.locator(`text=${testCycleData.name}`)).toBeVisible();
    
    // Store cycle ID for later tests
    const cycleRow = page.locator(`[data-testid="cycle-row"]:has-text("${testCycleData.name}")`);
    testCycleId = await cycleRow.getAttribute('data-cycle-id') || '1';
  });

  test('2. Test Manager adds reports to test cycle', async ({ page }) => {
    await loginAsUser(page, testUsers.testManager);
    
    // Navigate to specific test cycle
    await navigateAndWait(page, `/cycles/${testCycleId}`);
    
    // Add report to cycle with error handling
    await retry(async () => {
      await page.click('[data-testid="add-report-button"]');
      await page.selectOption('[data-testid="report-select"]', testReportData.name);
      await page.selectOption('[data-testid="tester-select"]', testUsers.tester.name);
      await page.click('[data-testid="assign-report-button"]');
    });
    
    // Wait for assignment to complete
    await waitForPageLoad(page);
    
    // Verify report assignment
    await expect(page.locator(`text=${testReportData.name}`)).toBeVisible();
    await expect(page.locator(`text=${testUsers.tester.name}`)).toBeVisible();
    
    // Store report ID
    const reportRow = page.locator(`[data-testid="report-row"]:has-text("${testReportData.name}")`);
    reportId = await reportRow.getAttribute('data-report-id') || '1';
  });

  test('3. Tester starts testing for a report', async ({ page }) => {
    await loginAsTester(page);
    
    // Navigate to assigned reports
    await navigateAndWait(page, '/dashboard');
    await clickAndWait(page, '[data-testid="my-assignments"]');
    
    // Start testing for the report with error handling
    const reportCard = page.locator(`[data-testid="report-card-${reportId}"]`);
    await retry(async () => {
      await reportCard.locator('[data-testid="start-testing-button"]').click();
      await page.click('[data-testid="confirm-start-button"]');
    });
    
    // Wait for status update
    await waitForPageLoad(page);
    
    // Verify status update
    await expect(reportCard.locator('[data-testid="status"]')).toHaveText('In Progress');
    await expect(reportCard.locator('[data-testid="current-phase"]')).toHaveText('Planning');
  });

  test('4. Planning Phase - Upload documents and define attributes', async ({ page }) => {
    await loginAsTester(page);
    
    await navigateAndWait(page, `/phases/planning?reportId=${reportId}`);
    
    // Upload regulatory specification with error handling
    await retry(async () => {
      await page.click('[data-testid="upload-regulatory-spec-button"]');
      const regSpecInput = page.locator('[data-testid="regulatory-spec-input"]');
      await regSpecInput.setInputFiles('tests/fixtures/regulatory-specification.pdf');
      await page.click('[data-testid="upload-file-button"]');
    });
    
    await waitForPageLoad(page);
    
    // Upload CDE list
    await retry(async () => {
      await page.click('[data-testid="upload-cde-list-button"]');
      const cdeInput = page.locator('[data-testid="cde-list-input"]');
      await cdeInput.setInputFiles('tests/fixtures/cde-list.xlsx');
      await page.click('[data-testid="upload-cde-button"]');
    });
    
    await waitForPageLoad(page);
    
    // Add attributes manually
    for (const attr of testAttributes) {
      await retry(async () => {
        await page.click('[data-testid="add-attribute-button"]');
        await fillField(page, '[data-testid="attr-name-input"]', attr.name);
        await fillField(page, '[data-testid="attr-description-input"]', attr.description);
        await page.selectOption('[data-testid="attr-type-select"]', attr.type);
        await page.selectOption('[data-testid="attr-flag-select"]', attr.flag);
        
        if (attr.cdeFlag) {
          await page.check('[data-testid="attr-cde-flag"]');
        }
        if (attr.historicalIssuesFlag) {
          await page.check('[data-testid="attr-historical-flag"]');
        }
        
        await page.click('[data-testid="save-attribute-button"]');
      });
      
      await waitForPageLoad(page);
      
      // Verify attribute was added
      await expect(page.locator(`[data-testid="attribute-${attr.name}"]`)).toBeVisible();
    }
    
    // Complete planning phase
    await retry(async () => {
      await page.click('[data-testid="complete-planning-button"]');
      await page.click('[data-testid="confirm-complete-button"]');
    });
    
    await waitForPageLoad(page);
    await expect(page.locator('[data-testid="planning-status"]')).toHaveText('Complete');
  });

  test('5. Scoping Phase - Generate and approve scoping recommendations', async ({ page }) => {
    await loginAsTester(page);
    
    await navigateAndWait(page, `/phases/scoping?reportId=${reportId}`);
    
    // Generate scoping recommendations
    await retry(async () => {
      await page.click('[data-testid="generate-scoping-recommendations-button"]');
      await fillField(page, '[data-testid="scoping-context-input"]', 'Focus on CDE attributes and those with historical data quality issues');
      await page.click('[data-testid="generate-scoping-button"]');
    });
    
    // Wait for recommendations
    await waitForApiRequest(page, '/api/v1/llm/generate-scoping', 15000);
    await expect(page.locator('[data-testid="scoping-recommendations"]')).toBeVisible({ timeout: 15000 });
    
    // Approve high-priority recommendations
    const recommendationRows = page.locator('[data-testid="recommendation-row"]');
    const count = await recommendationRows.count();
    
    for (let i = 0; i < Math.min(count, 3); i++) {
      const row = recommendationRows.nth(i);
      await retry(async () => {
        await row.locator('[data-testid="approve-button"]').click();
      });
    }
    
    // Submit for approval
    await retry(async () => {
      await page.click('[data-testid="submit-for-approval-button"]');
      await fillField(page, '[data-testid="submission-notes"]', 'Scoping complete based on LLM recommendations and business priorities');
      await page.click('[data-testid="confirm-submit-button"]');
    });
    
    await waitForPageLoad(page);
    await expect(page.locator('[data-testid="scoping-status"]')).toHaveText('Pending Approval');
  });

  test('6. Report Owner approves scoping', async ({ page }) => {
    await loginAsUser(page, testUsers.reportOwner);
    
    await navigateAndWait(page, '/dashboard');
    await clickAndWait(page, '[data-testid="pending-approvals"]');
    
    // Find and review scoping submission
    const scopingCard = page.locator(`[data-testid="scoping-approval-${reportId}"]`);
    await scopingCard.click();
    
    // Review scoping details
    await expect(page.locator('[data-testid="scoping-summary"]')).toBeVisible();
    await expect(page.locator('[data-testid="approved-attributes"]')).toBeVisible();
    
    // Approve scoping
    await retry(async () => {
      await page.click('[data-testid="approve-scoping-button"]');
      await fillField(page, '[data-testid="approval-comments"]', 'Scoping approved - proceed with data provider identification');
      await page.click('[data-testid="confirm-approval-button"]');
    });
    
    await waitForPageLoad(page);
    await expect(page.locator('[data-testid="approval-success"]')).toBeVisible();
  });

  test('7. Data Provider Phase - Identify and configure data sources', async ({ page }) => {
    await loginAsTester(page);
    
    await navigateAndWait(page, `/phases/data-provider?reportId=${reportId}`);
    
    // Add data provider with dynamic LOB ID
    await retry(async () => {
      await page.click('[data-testid="add-data-provider-button"]');
      await fillField(page, '[data-testid="provider-name-input"]', 'Core Banking System');
      await fillField(page, '[data-testid="provider-description-input"]', 'Primary source for loan data');
      await page.selectOption('[data-testid="provider-lob-select"]', lobIds.retailbanking.toString());
      await page.selectOption('[data-testid="provider-type-select"]', 'Database');
      await page.click('[data-testid="save-provider-button"]');
    });
    
    await waitForPageLoad(page);
    
    // Map attributes to data provider
    for (const attr of testAttributes.slice(0, 2)) { // Map first 2 attributes
      await retry(async () => {
        const attrRow = page.locator(`[data-testid="attribute-mapping-${attr.name}"]`);
        await attrRow.locator('[data-testid="map-provider-button"]').click();
        await page.selectOption('[data-testid="provider-select"]', 'Core Banking System');
        await fillField(page, '[data-testid="source-field-input"]', `${attr.name}_field`);
        await page.click('[data-testid="confirm-mapping-button"]');
      });
      
      await waitForPageLoad(page);
    }
    
    // Complete data provider phase
    await retry(async () => {
      await page.click('[data-testid="complete-data-provider-button"]');
      await page.click('[data-testid="confirm-complete-button"]');
    });
    
    await waitForPageLoad(page);
    await expect(page.locator('[data-testid="data-provider-status"]')).toHaveText('Complete');
  });

  test('8. Sample Selection Phase - Generate and review samples', async ({ page }) => {
    await loginAsTester(page);
    
    await navigateAndWait(page, `/phases/sample-selection?reportId=${reportId}`);
    
    // Configure sample parameters
    await retry(async () => {
      await fillField(page, '[data-testid="sample-size-input"]', '100');
      await page.selectOption('[data-testid="sampling-method-select"]', 'Stratified');
      await fillField(page, '[data-testid="stratification-criteria"]', 'loan_amount, risk_category');
      await page.click('[data-testid="generate-sample-button"]');
    });
    
    // Wait for sample generation
    await waitForApiRequest(page, '/api/v1/samples/generate', 10000);
    await expect(page.locator('[data-testid="sample-results"]')).toBeVisible({ timeout: 10000 });
    
    // Review sample quality
    await expect(page.locator('[data-testid="sample-count"]')).toHaveText('100');
    await expect(page.locator('[data-testid="coverage-analysis"]')).toBeVisible();
    
    // Approve sample
    await retry(async () => {
      await page.click('[data-testid="approve-sample-button"]');
      await fillField(page, '[data-testid="sample-notes"]', 'Sample provides good coverage across risk categories');
      await page.click('[data-testid="confirm-sample-button"]');
    });
    
    await waitForPageLoad(page);
    await expect(page.locator('[data-testid="sample-status"]')).toHaveText('Approved');
  });

  // Continue with remaining workflow phases...
  test('9. Complete workflow verification', async ({ page }) => {
    await loginAsTester(page);
    
    // Navigate to report dashboard to verify overall progress
    await navigateAndWait(page, `/reports/${reportId}/dashboard`);
    
    // Verify all completed phases
    await expect(page.locator('[data-testid="phase-planning"] [data-testid="status"]')).toHaveText('Complete');
    await expect(page.locator('[data-testid="phase-scoping"] [data-testid="status"]')).toHaveText('Approved');
    await expect(page.locator('[data-testid="phase-data-provider"] [data-testid="status"]')).toHaveText('Complete');
    await expect(page.locator('[data-testid="phase-sample-selection"] [data-testid="status"]')).toHaveText('Approved');
    
    // Verify overall report status
    await expect(page.locator('[data-testid="report-status"]')).toHaveText('In Progress');
    await expect(page.locator('[data-testid="current-phase"]')).toHaveText('Request Info');
    
    // Check progress indicators
    await expect(page.locator('[data-testid="progress-bar"]')).toHaveAttribute('aria-valuenow', '50'); // 4 of 8 phases complete
    
    // Verify key metrics
    await expect(page.locator('[data-testid="total-attributes"]')).toHaveText('4');
    await expect(page.locator('[data-testid="scoped-attributes"]')).toHaveText('3');
    await expect(page.locator('[data-testid="mapped-attributes"]')).toHaveText('2');
    await expect(page.locator('[data-testid="sample-size"]')).toHaveText('100');
  });
});

test.describe('Role-based Access Control', () => {
  test('Verify role permissions across workflow', async ({ page }) => {
    // Test Tester cannot create test cycles
    await loginAsUser(page, testUsers.tester);
    await page.goto('/cycles');
    await expect(page.locator('[data-testid="create-cycle-button"]')).not.toBeVisible();
    
    // Test Data Provider cannot approve scoping
    await loginAsUser(page, testUsers.dataProvider);
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="scoping-approvals"]')).not.toBeVisible();
    
    // Test Report Owner cannot assign data providers
    await loginAsUser(page, testUsers.reportOwner);
    await page.goto('/dashboard'); 
    await expect(page.locator('[data-testid="data-provider-assignments"]')).not.toBeVisible();
  });
});

test.describe('Error Handling and Edge Cases', () => {
  test('Handle LLM service failures gracefully', async ({ page }) => {
    await loginAsUser(page, testUsers.tester);
    await page.goto(`/phases/planning?reportId=1`);
    
    // Simulate LLM service unavailable
    await page.route('**/api/v1/llm/**', route => route.abort());
    
    await page.click('[data-testid="generate-attributes-llm-button"]');
    await expect(page.locator('[data-testid="llm-error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="fallback-manual-entry"]')).toBeVisible();
  });
  
  test('Handle approval rejections and resubmissions', async ({ page }) => {
    await loginAsUser(page, testUsers.reportOwner);
    await page.goto('/dashboard');
    await page.click('[data-testid="pending-approvals"]');
    
    // Reject scoping
    const approvalCard = page.locator('[data-testid="scoping-approval-1"]');
    await approvalCard.click();
    await page.click('[data-testid="reject-scoping-button"]');
    await page.fill('[data-testid="rejection-comments"]', 'Scope needs refinement');
    await page.click('[data-testid="confirm-rejection-button"]');
    
    // Verify tester receives rejection notification
    await loginAsUser(page, testUsers.tester);
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="rejection-notification"]')).toBeVisible();
  });
});

test.describe('SLA Monitoring and Escalations', () => {
  test('SLA violation tracking and escalations', async ({ page }) => {
    await loginAsUser(page, testUsers.testManager);
    
    // Configure SLA for testing phases
    await page.goto('/admin/sla-configuration');
    await page.click('[data-testid="add-sla-config-button"]');
    await page.selectOption('[data-testid="sla-type"]', 'testing_completion');
    await page.fill('[data-testid="sla-hours"]', '72');
    await page.fill('[data-testid="warning-hours"]', '24');
    await page.click('[data-testid="save-sla-button"]');
    
    // Simulate SLA breach
    await page.goto('/admin/sla-violations');
    await expect(page.locator('[data-testid="violations-dashboard"]')).toBeVisible();
    
    // Check escalation emails
    await page.click('[data-testid="escalation-logs"]');
    await expect(page.locator('[data-testid="escalation-history"]')).toBeVisible();
  });
}); 