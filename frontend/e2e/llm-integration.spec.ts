import { test, expect, Page } from '@playwright/test';
import { 
  loginAsTester, 
  testUsers, 
  waitForPageLoad, 
  navigateAndWait,
  clickAndWait,
  fillField,
  checkForErrors,
  retry,
  waitForApiRequest
} from './test-utils';

interface LLMTestContext {
  reportId: string;
  userId: string;
  phase: string;
}

const mockLLMResponses = {
  attributeGeneration: {
    success: {
      attributes: [
        {
          name: 'loan_id',
          description: 'Unique identifier for each loan application',
          type: 'String',
          flag: 'Mandatory',
          cdeFlag: true,
          historicalIssuesFlag: false,
          llmConfidence: 0.95
        },
        {
          name: 'borrower_ssn',
          description: 'Social Security Number of the borrower',
          type: 'String',
          flag: 'Mandatory',
          cdeFlag: true,
          historicalIssuesFlag: true,
          llmConfidence: 0.92
        },
        {
          name: 'loan_amount',
          description: 'Total amount of the loan being requested',
          type: 'Number',
          flag: 'Mandatory',
          cdeFlag: true,
          historicalIssuesFlag: false,
          llmConfidence: 0.98
        }
      ],
      rationale: 'Generated based on regulatory specifications and CDE requirements',
      processingTime: 2.5
    },
    error: {
      error: 'LLM service temporarily unavailable',
      code: 'SERVICE_UNAVAILABLE',
      retry_after: 300
    }
  },
  scopingRecommendations: {
    success: {
      recommendations: [
        {
          attributeName: 'loan_id',
          recommendationScore: 9.5,
          recommendation: 'High Priority - Critical Data Element',
          rationale: 'Primary key field with high regulatory importance and historical data quality issues',
          expectedSources: ['Loan Application System', 'Core Banking Platform'],
          keywords: ['loan identifier', 'application number', 'reference'],
          impactedReports: ['Monthly Loan Report', 'Regulatory Filing', 'Risk Assessment']
        },
        {
          attributeName: 'borrower_ssn',
          recommendationScore: 8.5,
          recommendation: 'High Priority - PII Data Element',
          rationale: 'Sensitive personal information requiring careful validation and compliance checks',
          expectedSources: ['Customer Database', 'KYC System'],
          keywords: ['social security', 'SSN', 'tax ID'],
          impactedReports: ['Customer Profile Report', 'Compliance Report']
        }
      ],
      totalProcessingTime: 3.2,
      confidenceLevel: 0.87
    }
  },
  sampleGeneration: {
    success: {
      samples: [
        {
          sampleId: 1,
          loan_id: 'LN2024001',
          borrower_ssn: '***-**-1234',
          loan_amount: 250000,
          stratificationCriteria: 'High value loan'
        },
        {
          sampleId: 2,
          loan_id: 'LN2024002',
          borrower_ssn: '***-**-5678',
          loan_amount: 150000,
          stratificationCriteria: 'Medium value loan'
        }
      ],
      rationale: 'Sample stratified by loan amount and risk category to ensure comprehensive coverage',
      coverageAnalysis: {
        loanAmountRanges: ['<100k', '100k-500k', '>500k'],
        riskCategories: ['Low', 'Medium', 'High'],
        timeRanges: ['Q1', 'Q2', 'Q3', 'Q4']
      }
    }
  },
  documentExtraction: {
    success: {
      extractedData: {
        loan_id: 'LN2024001',
        borrower_name: 'John Smith',
        loan_amount: 250000,
        extraction_confidence: 0.94
      },
      extractionDetails: {
        sourcePages: [1, 2],
        keyPhrases: ['Loan Number: LN2024001', 'Borrower: John Smith', 'Amount: $250,000'],
        extractionMethod: 'OCR + NLP',
        processingTime: 1.8
      }
    },
    lowConfidence: {
      extractedData: {
        loan_id: 'LN2024001',
        borrower_name: 'John Smith',
        loan_amount: null,
        extraction_confidence: 0.45
      },
      warnings: ['Low confidence in loan amount extraction', 'Manual review recommended']
    }
  }
};

async function setupLLMTest(page: Page, mockResponse: any, endpoint: string) {
  // Mock LLM API responses
  await page.route(`**/api/v1/llm/${endpoint}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockResponse)
    });
  });
}

test.describe('LLM Integration - Attribute Generation', () => {
  test('Successful attribute generation with regulatory specification', async ({ page }) => {
    await setupLLMTest(page, mockLLMResponses.attributeGeneration.success, 'generate-attributes');
    await loginAsTester(page);
    
    await navigateAndWait(page, '/phases/planning?reportId=1');
    
    // Upload regulatory specification with error handling
    await retry(async () => {
      await page.click('[data-testid="upload-regulatory-spec-button"]');
      const regSpecInput = page.locator('[data-testid="regulatory-spec-input"]');
      await regSpecInput.setInputFiles('tests/fixtures/regulatory-specification.pdf');
      await page.click('[data-testid="upload-file-button"]');
    });
    
    // Wait for upload to complete
    await waitForPageLoad(page);
    
    // Trigger LLM attribute generation
    await retry(async () => {
      await page.click('[data-testid="generate-attributes-llm-button"]');
      await fillField(page, '[data-testid="llm-context-input"]', 'Generate comprehensive attribute list for loan portfolio report based on regulatory requirements');
      await page.click('[data-testid="generate-button"]');
    });
    
    // Wait for LLM response with longer timeout
    await waitForApiRequest(page, '/api/v1/llm/generate-attributes', 15000);
    await expect(page.locator('[data-testid="llm-response"]')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('[data-testid="generated-attributes"]')).toBeVisible();
    
    // Verify generated attributes
    await expect(page.locator('[data-testid="attribute-loan_id"]')).toBeVisible();
    await expect(page.locator('[data-testid="attribute-borrower_ssn"]')).toBeVisible();
    await expect(page.locator('[data-testid="attribute-loan_amount"]')).toBeVisible();
    
    // Check LLM confidence scores
    await expect(page.locator('[data-testid="confidence-loan_id"]')).toHaveText('95%');
    await expect(page.locator('[data-testid="confidence-borrower_ssn"]')).toHaveText('92%');
    
    // Verify CDE and historical flags are set correctly
    await expect(page.locator('[data-testid="cde-flag-loan_id"]')).toBeChecked();
    await expect(page.locator('[data-testid="historical-flag-borrower_ssn"]')).toBeChecked();
    
    // Test attribute editing after generation
    await retry(async () => {
      await page.click('[data-testid="edit-attribute-loan_id"]');
      await fillField(page, '[data-testid="edit-description"]', 'Updated description from LLM generation');
      await page.click('[data-testid="save-attribute-button"]');
    });
    
    await waitForPageLoad(page);
    await expect(page.locator('[data-testid="attribute-description-loan_id"]')).toHaveText('Updated description from LLM generation');
  });

  test('LLM attribute generation with CDE and historical issues integration', async ({ page }) => {
    await setupLLMTest(page, mockLLMResponses.attributeGeneration.success, 'generate-attributes');
    await loginAsTester(page);
    
    await navigateAndWait(page, '/phases/planning?reportId=1');
    
    // Upload all required documents with error handling
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
    
    // Upload historical issues
    await retry(async () => {
      await page.click('[data-testid="upload-historical-issues-button"]');
      const historyInput = page.locator('[data-testid="historical-issues-input"]');
      await historyInput.setInputFiles('tests/fixtures/historical-issues.csv');
      await page.click('[data-testid="upload-history-button"]');
    });
    
    await waitForPageLoad(page);
    
    // Generate attributes with all context
    await retry(async () => {
      await page.click('[data-testid="generate-attributes-llm-button"]');
      await fillField(page, '[data-testid="llm-context-input"]', 'Generate attributes considering CDE requirements and historical data quality issues');
      await page.click('[data-testid="generate-button"]');
    });
    
    // Wait for LLM processing
    await waitForApiRequest(page, '/api/v1/llm/generate-attributes', 20000);
    await expect(page.locator('[data-testid="generated-attributes"]')).toBeVisible({ timeout: 20000 });
    
    // Verify CDE integration
    const cdeAttributes = page.locator('[data-testid="attribute-row"][data-cde="true"]');
    await expect(cdeAttributes).toHaveCount(2); // loan_id and borrower_ssn
    
    // Verify historical issues integration
    const historicalAttributes = page.locator('[data-testid="attribute-row"][data-historical="true"]');
    await expect(historicalAttributes).toHaveCount(1); // borrower_ssn
    
    // Check for LLM rationale
    await expect(page.locator('[data-testid="llm-rationale"]')).toContainText('CDE requirements');
    await expect(page.locator('[data-testid="llm-rationale"]')).toContainText('historical data quality');
  });

  test('LLM error handling and retry mechanism', async ({ page }) => {
    // First setup error response
    await setupLLMTest(page, mockLLMResponses.attributeGeneration.error, 'generate-attributes');
    await loginAsTester(page);
    
    await navigateAndWait(page, '/phases/planning?reportId=1');
    
    // Try to generate attributes - should fail
    await retry(async () => {
      await page.click('[data-testid="generate-attributes-llm-button"]');
      await fillField(page, '[data-testid="llm-context-input"]', 'Generate attributes');
      await page.click('[data-testid="generate-button"]');
    });
    
    // Should show error message
    await expect(page.locator('[data-testid="llm-error"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="llm-error"]')).toContainText('LLM service temporarily unavailable');
    
    // Should show retry button
    await expect(page.locator('[data-testid="retry-llm-button"]')).toBeVisible();
    
    // Setup success response for retry
    await setupLLMTest(page, mockLLMResponses.attributeGeneration.success, 'generate-attributes');
    
    // Retry should work
    await retry(async () => {
      await page.click('[data-testid="retry-llm-button"]');
    });
    
    await waitForApiRequest(page, '/api/v1/llm/generate-attributes', 15000);
    await expect(page.locator('[data-testid="generated-attributes"]')).toBeVisible({ timeout: 15000 });
    
    // Check for errors after retry
    const error = await checkForErrors(page);
    if (error) {
      console.warn(`LLM retry error: ${error}`);
    }
  });
});

test.describe('LLM Integration - Scoping Recommendations', () => {
  test('Generate scoping recommendations with context', async ({ page }) => {
    await setupLLMTest(page, mockLLMResponses.scopingRecommendations.success, 'generate-scoping');
    await loginAsTester(page);
    
    await navigateAndWait(page, '/phases/scoping?reportId=1');
    
    // Generate scoping recommendations
    await retry(async () => {
      await page.click('[data-testid="generate-scoping-recommendations-button"]');
      await fillField(page, '[data-testid="scoping-context-input"]', 'Focus on high-risk attributes with regulatory importance and historical data quality issues');
      await page.click('[data-testid="generate-scoping-button"]');
    });
    
    // Wait for LLM response
    await waitForApiRequest(page, '/api/v1/llm/generate-scoping', 15000);
    await expect(page.locator('[data-testid="scoping-recommendations"]')).toBeVisible({ timeout: 15000 });
    
    // Verify recommendations
    await expect(page.locator('[data-testid="recommendation-loan_id"]')).toBeVisible();
    await expect(page.locator('[data-testid="recommendation-borrower_ssn"]')).toBeVisible();
    
    // Check recommendation scores
    await expect(page.locator('[data-testid="score-loan_id"]')).toHaveText('9.5');
    await expect(page.locator('[data-testid="score-borrower_ssn"]')).toHaveText('8.5');
    
    // Verify rationale
    await expect(page.locator('[data-testid="rationale-loan_id"]')).toContainText('Primary key field');
    await expect(page.locator('[data-testid="rationale-borrower_ssn"]')).toContainText('Sensitive personal information');
    
    // Test recommendation approval
    await retry(async () => {
      await page.click('[data-testid="approve-recommendation-loan_id"]');
      await page.click('[data-testid="approve-recommendation-borrower_ssn"]');
    });
    
    await waitForPageLoad(page);
    
    // Verify approved status
    await expect(page.locator('[data-testid="status-loan_id"]')).toHaveText('Approved');
    await expect(page.locator('[data-testid="status-borrower_ssn"]')).toHaveText('Approved');
  });
});

test.describe('LLM Integration - Sample Generation', () => {
  test('Generate stratified sample with LLM recommendations', async ({ page }) => {
    await setupLLMTest(page, mockLLMResponses.sampleGeneration.success, 'generate-sample');
    await loginAsTester(page);
    
    await page.goto('/phases/sample-selection?reportId=1');
    
    // Generate sample using LLM
    await page.click('[data-testid="generate-sample-llm-button"]');
    await page.fill('[data-testid="sample-size-input"]', '100');
    await page.fill('[data-testid="sample-criteria-input"]', 'Generate stratified sample covering all loan types, risk categories, and time periods');
    await page.selectOption('[data-testid="stratification-method"]', 'risk_amount_time');
    await page.click('[data-testid="generate-sample-button"]');
    
    await expect(page.locator('[data-testid="generated-sample"]')).toBeVisible({ timeout: 15000 });
    
    // Verify sample data
    await expect(page.locator('[data-testid="sample-count"]')).toHaveText('2');
    await expect(page.locator('[data-testid="sample-LN2024001"]')).toBeVisible();
    await expect(page.locator('[data-testid="sample-LN2024002"]')).toBeVisible();
    
    // Check stratification criteria
    await expect(page.locator('[data-testid="strata-LN2024001"]')).toHaveText('High value loan');
    await expect(page.locator('[data-testid="strata-LN2024002"]')).toHaveText('Medium value loan');
    
    // Verify LLM rationale
    await expect(page.locator('[data-testid="sample-rationale"]')).toHaveText('Sample stratified by loan amount and risk category to ensure comprehensive coverage');
    
    // Check coverage analysis
    await page.click('[data-testid="view-coverage-analysis"]');
    await expect(page.locator('[data-testid="coverage-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="amount-ranges"]')).toContainText('<100k');
    await expect(page.locator('[data-testid="amount-ranges"]')).toContainText('100k-500k');
    await expect(page.locator('[data-testid="risk-categories"]')).toContainText('Low');
    await expect(page.locator('[data-testid="risk-categories"]')).toContainText('Medium');
    await expect(page.locator('[data-testid="risk-categories"]')).toContainText('High');
    await page.click('[data-testid="close-coverage-modal"]');
  });

  test('Validate and adjust LLM-generated sample', async ({ page }) => {
    await setupLLMTest(page, mockLLMResponses.sampleGeneration.success, 'generate-sample');
    await loginAsTester(page);
    
    await page.goto('/phases/sample-selection?reportId=1');
    
    // Generate sample
    await page.click('[data-testid="generate-sample-llm-button"]');
    await page.fill('[data-testid="sample-size-input"]', '100');
    await page.fill('[data-testid="sample-criteria-input"]', 'Balanced sample across all categories');
    await page.click('[data-testid="generate-sample-button"]');
    
    await expect(page.locator('[data-testid="generated-sample"]')).toBeVisible({ timeout: 15000 });
    
    // Validate sample against scoped attributes
    await page.click('[data-testid="validate-sample-button"]');
    await expect(page.locator('[data-testid="validation-results"]')).toBeVisible();
    await expect(page.locator('[data-testid="validation-status"]')).toHaveText('Valid');
    
    // Add manual sample item
    await page.click('[data-testid="add-manual-sample"]');
    await page.fill('[data-testid="manual-loan-id"]', 'LN2024003');
    await page.fill('[data-testid="manual-loan-amount"]', '75000');
    await page.selectOption('[data-testid="manual-strata"]', 'Low value loan');
    await page.click('[data-testid="save-manual-sample"]');
    
    await expect(page.locator('[data-testid="sample-LN2024003"]')).toBeVisible();
    
    // Remove LLM-generated sample
    await page.click('[data-testid="remove-sample-LN2024002"]');
    await page.click('[data-testid="confirm-remove"]');
    await expect(page.locator('[data-testid="sample-LN2024002"]')).not.toBeVisible();
    
    // Update rationale
    await page.fill('[data-testid="updated-rationale"]', 'LLM-generated sample adjusted with additional low-value loan for better coverage');
    
    // Re-validate final sample
    await page.click('[data-testid="validate-sample-button"]');
    await expect(page.locator('[data-testid="validation-status"]')).toHaveText('Valid');
  });
});

test.describe('LLM Integration - Document Extraction', () => {
  test('Extract data from documents with high confidence', async ({ page }) => {
    await setupLLMTest(page, mockLLMResponses.documentExtraction.success, 'extract-document');
    await loginAsTester(page);
    
    await page.goto('/phases/testing-execution?reportId=1');
    
    // Select test case with document
    const testRow = page.locator('[data-testid="test-case-row"]:first-child');
    await testRow.locator('[data-testid="start-test-button"]').click();
    
    // Use LLM for document extraction
    await testRow.locator('[data-testid="extract-with-llm-button"]').click();
    
    await expect(testRow.locator('[data-testid="llm-extraction-result"]')).toBeVisible({ timeout: 15000 });
    
    // Verify extracted data
    await expect(testRow.locator('[data-testid="extracted-loan_id"]')).toHaveText('LN2024001');
    await expect(testRow.locator('[data-testid="extracted-borrower_name"]')).toHaveText('John Smith');
    await expect(testRow.locator('[data-testid="extracted-loan_amount"]')).toHaveText('250000');
    
    // Check extraction confidence
    await expect(testRow.locator('[data-testid="extraction-confidence"]')).toHaveText('94%');
    await expect(testRow.locator('[data-testid="confidence-indicator"]')).toHaveClass(/high-confidence/);
    
    // View extraction details
    await testRow.locator('[data-testid="view-extraction-details"]').click();
    await expect(page.locator('[data-testid="extraction-details-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="source-pages"]')).toHaveText('Pages: 1, 2');
    await expect(page.locator('[data-testid="key-phrases"]')).toContainText('Loan Number: LN2024001');
    await expect(page.locator('[data-testid="extraction-method"]')).toHaveText('OCR + NLP');
    await expect(page.locator('[data-testid="processing-time"]')).toHaveText('1.8s');
    await page.click('[data-testid="close-details-modal"]');
    
    // Compare with sample value
    await testRow.locator('[data-testid="compare-values-button"]').click();
    await expect(testRow.locator('[data-testid="comparison-result"]')).toHaveText('Match');
    await expect(testRow.locator('[data-testid="comparison-status"]')).toHaveClass(/match/);
  });

  test('Handle low confidence extraction with manual review', async ({ page }) => {
    await setupLLMTest(page, mockLLMResponses.documentExtraction.lowConfidence, 'extract-document');
    await loginAsTester(page);
    
    await page.goto('/phases/testing-execution?reportId=1');
    
    const testRow = page.locator('[data-testid="test-case-row"]:first-child');
    await testRow.locator('[data-testid="start-test-button"]').click();
    
    // Use LLM for document extraction
    await testRow.locator('[data-testid="extract-with-llm-button"]').click();
    
    await expect(testRow.locator('[data-testid="llm-extraction-result"]')).toBeVisible({ timeout: 15000 });
    
    // Check low confidence warning
    await expect(testRow.locator('[data-testid="extraction-confidence"]')).toHaveText('45%');
    await expect(testRow.locator('[data-testid="confidence-indicator"]')).toHaveClass(/low-confidence/);
    await expect(testRow.locator('[data-testid="manual-review-warning"]')).toBeVisible();
    
    // View warnings
    await expect(testRow.locator('[data-testid="extraction-warnings"]')).toContainText('Low confidence in loan amount extraction');
    await expect(testRow.locator('[data-testid="extraction-warnings"]')).toContainText('Manual review recommended');
    
    // Manual review required
    await testRow.locator('[data-testid="start-manual-review"]').click();
    await expect(page.locator('[data-testid="manual-review-modal"]')).toBeVisible();
    
    // Manually correct extracted value
    await page.fill('[data-testid="manual-loan_amount"]', '245000');
    await page.fill('[data-testid="correction-reason"]', 'OCR misread amount due to poor document quality');
    await page.click('[data-testid="save-manual-correction"]');
    
    await expect(testRow.locator('[data-testid="extracted-loan_amount"]')).toHaveText('245000');
    await expect(testRow.locator('[data-testid="manually-corrected-flag"]')).toBeVisible();
  });

  test('Retry extraction with different parameters', async ({ page }) => {
    // First attempt with error
    await page.route('**/api/v1/llm/extract-document', async (route, request) => {
      const postData = request.postData();
      if (postData?.includes('first_attempt')) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Extraction failed', code: 'PROCESSING_ERROR' })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockLLMResponses.documentExtraction.success)
        });
      }
    });
    
    await loginAsTester(page);
    await page.goto('/phases/testing-execution?reportId=1');
    
    const testRow = page.locator('[data-testid="test-case-row"]:first-child');
    await testRow.locator('[data-testid="start-test-button"]').click();
    
    // First extraction attempt (will fail)
    await testRow.locator('[data-testid="extract-with-llm-button"]').click();
    
    await expect(testRow.locator('[data-testid="extraction-error"]')).toBeVisible();
    await expect(testRow.locator('[data-testid="extraction-error"]')).toHaveText('Extraction failed');
    
    // Retry with different parameters
    await testRow.locator('[data-testid="retry-extraction-button"]').click();
    await page.selectOption('[data-testid="extraction-method"]', 'enhanced_ocr');
    await page.selectOption('[data-testid="language-model"]', 'gpt-4');
    await page.click('[data-testid="confirm-retry"]');
    
    await expect(testRow.locator('[data-testid="llm-extraction-result"]')).toBeVisible({ timeout: 15000 });
    await expect(testRow.locator('[data-testid="extracted-loan_id"]')).toHaveText('LN2024001');
    await expect(testRow.locator('[data-testid="retry-success-indicator"]')).toBeVisible();
  });
});

test.describe('LLM Performance and Monitoring', () => {
  test('Monitor LLM response times and accuracy', async ({ page }) => {
    await setupLLMTest(page, mockLLMResponses.attributeGeneration.success, 'generate-attributes');
    await loginAsTester(page);
    
    await page.goto('/phases/planning?reportId=1');
    
    // Track generation time
    const startTime = Date.now();
    await page.click('[data-testid="generate-attributes-llm-button"]');
    await page.fill('[data-testid="llm-context-input"]', 'Generate attributes');
    await page.click('[data-testid="generate-button"]');
    
    await expect(page.locator('[data-testid="llm-response"]')).toBeVisible({ timeout: 10000 });
    const endTime = Date.now();
    
    // Verify performance metrics are displayed
    await expect(page.locator('[data-testid="processing-time"]')).toHaveText('2.5s');
    await expect(page.locator('[data-testid="response-time-acceptable"]')).toBeVisible();
    
    // Check accuracy metrics
    await expect(page.locator('[data-testid="avg-confidence"]')).toContainText('95%');
    await expect(page.locator('[data-testid="high-confidence-count"]')).toHaveText('3');
    
    // Performance threshold check
    const actualResponseTime = (endTime - startTime) / 1000;
    expect(actualResponseTime).toBeLessThan(10); // Should respond within 10 seconds
  });

  test('Handle LLM rate limiting', async ({ page }) => {
    // Mock rate limiting response
    await page.route('**/api/v1/llm/**', async (route) => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Rate limit exceeded',
          retry_after: 60,
          code: 'RATE_LIMITED'
        })
      });
    });
    
    await loginAsTester(page);
    await page.goto('/phases/planning?reportId=1');
    
    await page.click('[data-testid="generate-attributes-llm-button"]');
    await page.fill('[data-testid="llm-context-input"]', 'Generate attributes');
    await page.click('[data-testid="generate-button"]');
    
    // Verify rate limiting message
    await expect(page.locator('[data-testid="rate-limit-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="rate-limit-message"]')).toHaveText('Rate limit exceeded. Please try again in 60 seconds.');
    
    // Verify retry timer
    await expect(page.locator('[data-testid="retry-timer"]')).toBeVisible();
    await expect(page.locator('[data-testid="auto-retry-checkbox"]')).toBeVisible();
    
    // Test manual retry after waiting
    await page.click('[data-testid="manual-retry-button"]');
    await expect(page.locator('[data-testid="rate-limit-message"]')).toBeVisible(); // Should still be rate limited
  });

  test('Track LLM usage and costs', async ({ page }) => {
    await setupLLMTest(page, mockLLMResponses.attributeGeneration.success, 'generate-attributes');
    await loginAsTester(page);
    
    // Navigate to LLM usage dashboard (if available to testers)
    await page.goto('/dashboard');
    await page.click('[data-testid="llm-usage-stats"]');
    
    await expect(page.locator('[data-testid="usage-dashboard"]')).toBeVisible();
    
    // Check usage metrics
    await expect(page.locator('[data-testid="total-requests"]')).toBeVisible();
    await expect(page.locator('[data-testid="successful-requests"]')).toBeVisible();
    await expect(page.locator('[data-testid="failed-requests"]')).toBeVisible();
    await expect(page.locator('[data-testid="avg-response-time"]')).toBeVisible();
    
    // Check per-phase usage
    await expect(page.locator('[data-testid="planning-usage"]')).toBeVisible();
    await expect(page.locator('[data-testid="scoping-usage"]')).toBeVisible();
    await expect(page.locator('[data-testid="sampling-usage"]')).toBeVisible();
    await expect(page.locator('[data-testid="extraction-usage"]')).toBeVisible();
    
    // Check current month usage
    await expect(page.locator('[data-testid="current-month-requests"]')).toBeVisible();
    await expect(page.locator('[data-testid="usage-limit-warning"]')).not.toBeVisible(); // Assuming under limit
  });
}); 