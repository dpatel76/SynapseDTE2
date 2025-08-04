# SynapseDT - End-to-End Testing Suite

## Overview

This comprehensive E2E testing suite validates the complete SynapseDT Data Testing Platform functionality, covering all core workflows, role-based interactions, LLM integrations, and system integrations.

## Test Coverage

### 🔄 Complete Workflow Testing (`complete-workflow.spec.ts`)
- **16 comprehensive test cases** covering the entire 24-step data testing workflow
- **Test Cycle Management**: Creation, report assignment, tester assignments
- **Multi-Phase Testing Process**:
  - Planning Phase with LLM-assisted attribute generation
  - Scoping Phase with LLM recommendations and approvals
  - Data Provider Identification with CDO involvement
  - Sample Selection with LLM generation and approvals
  - Request for Information with document uploads
  - Testing Execution with LLM document extraction
  - Multi-level review cycles (Data Provider → CDO approval)
  - Observation Management with categorization and final approvals

### 👥 Role-Based Testing (`role-based-testing.spec.ts`)
- **6 distinct role test suites** with comprehensive functionality coverage
- **Test Manager**: Cycle management, progress monitoring, reporting
- **Tester**: Complete lifecycle management, all phase activities
- **Report Owner**: Approval workflows, rejection handling
- **CDO**: Data provider assignments, result approvals
- **Data Provider**: Document uploads, result responses
- **Cross-Role Collaboration**: Notification flows, multi-role interactions
- **Security & Access Control**: Role-based restrictions, data isolation

### 🤖 LLM Integration Testing (`llm-integration.spec.ts`)
- **13 comprehensive test scenarios** for AI/ML functionality
- **Attribute Generation**: Regulatory specs, CDE integration, historical issues
- **Scoping Recommendations**: Prioritization, review workflows
- **Sample Generation**: Stratification, validation, adjustments
- **Document Extraction**: Confidence scoring, manual review flows
- **Performance Monitoring**: Response times, accuracy tracking
- **Error Handling**: Service failures, rate limiting, low confidence scenarios

### 🔐 Authentication & Authorization (`auth.spec.ts`)
- Login/logout functionality
- Role-based access control
- Protected route handling
- Session management

### 📊 Dashboard Testing (`dashboard.spec.ts`)
- Overview display and navigation
- Workflow phase management
- Notifications and search functionality
- Responsive design validation

### ♿ Accessibility Testing (`accessibility.spec.ts`)
- WCAG compliance validation
- Keyboard navigation support
- Screen reader compatibility
- Color contrast and focus management
- Mobile accessibility

### ⚡ Performance Testing (`performance.spec.ts`)
- Page load time optimization
- Core Web Vitals monitoring
- Bundle size efficiency
- Memory usage validation
- Mobile performance

## Test Data & Setup

### Test Users (6 Roles)
```typescript
- testmanager@synapse.com (Test Manager)
- tester@synapse.com (Tester)
- reportowner@synapse.com (Report Owner)
- reportownerexec@synapse.com (Report Owner Executive)
- cdo@synapse.com (CDO)
- dataprovider@synapse.com (Data Provider)
```

### Test Data
- **3 Test LOBs**: Retail Banking, Commercial Banking, Investment Banking
- **3 Test Reports**: Loan Portfolio Analysis, Credit Risk Assessment, Customer Deposit Report
- **3 Data Sources**: Customer Database, Loan Management System, Risk Data Warehouse

## Configuration

### Browser Support
- ✅ Chromium (Desktop)
- ✅ Firefox (Desktop)
- ✅ WebKit/Safari (Desktop)
- ✅ Mobile Chrome (Pixel 5)
- ✅ Mobile Safari (iPhone 12)
- ✅ Microsoft Edge
- ✅ Google Chrome

### Test Environment
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Global Setup**: Database seeding, test user creation
- **Global Teardown**: Environment cleanup

## Running Tests

### Prerequisites
```bash
cd frontend
npm install
```

### Commands
```bash
# Run all tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test complete-workflow.spec.ts

# Run specific test
npx playwright test -g "Test Manager creates Test Cycle"

# Run tests for specific browser
npx playwright test --project=chromium

# Generate HTML report
npx playwright show-report
```

### Test Configuration
- **Parallel Execution**: Tests run in parallel for efficiency
- **Retries**: 2 retries on CI, 0 locally
- **Timeouts**: 60s test timeout, 30s action timeout
- **Screenshots**: Captured on failure
- **Videos**: Recorded on failure
- **Traces**: Collected on retry

## Key Features Tested

### 🔄 Complete Workflow Integration
1. **Test Cycle Creation** → Report Assignment → Tester Assignment
2. **Planning Phase** → LLM Attribute Generation → Regulatory Integration
3. **Scoping Phase** → LLM Recommendations → Report Owner Approval
4. **Data Provider ID** → CDO Assignment → Multi-LOB Support
5. **Sample Selection** → LLM Generation → Approval Workflows
6. **Request for Info** → Document Upload → Data Source Integration
7. **Testing Execution** → LLM Extraction → Confidence Scoring
8. **Result Review** → Data Provider Response → CDO Approval
9. **Observation Mgmt** → Categorization → Final Approval

### 🤖 LLM Integration Points
- **Attribute Generation**: Uses regulatory specifications and CDE lists
- **Scoping Recommendations**: Prioritizes based on risk and complexity
- **Sample Selection**: Generates stratified samples with business logic
- **Document Extraction**: Processes uploaded documents with confidence scoring
- **Error Handling**: Graceful degradation when LLM services fail

### 🔐 Security & Access Control
- **Role-Based Menus**: Dynamic navigation based on user role
- **Page-Level Access**: Restricted routes based on permissions
- **Data Isolation**: Users only see data relevant to their role
- **API Security**: Token-based authentication validation

### 📈 Performance & Monitoring
- **SLA Tracking**: Monitors workflow phase deadlines
- **Escalation Management**: Automated notifications for overdue tasks
- **Usage Analytics**: Tracks LLM service usage and costs
- **Performance Metrics**: Response times, accuracy scores

## Test Architecture

### Page Objects
- Centralized element selectors and actions
- Reusable components across test files
- Maintainable test structure

### Test Utilities
- Common authentication helpers
- Data creation utilities
- API mocking functions
- Assertion libraries

### Mock Services
- LLM service responses
- File upload simulation
- Notification system
- External API integration

## Continuous Integration

### CI/CD Integration
- **Parallel Execution**: Optimized for CI environments
- **Failure Reporting**: JUnit XML and JSON reports
- **Artifact Collection**: Screenshots, videos, and traces
- **Browser Matrix**: Tests across all supported browsers

### Quality Gates
- **Test Coverage**: All critical user journeys covered
- **Performance Thresholds**: Page load times under 3 seconds
- **Accessibility Standards**: WCAG AA compliance
- **Cross-Browser Compatibility**: Consistent behavior across browsers

## Troubleshooting

### Common Issues
1. **Test Timeouts**: Increase timeout values in playwright.config.ts
2. **Service Dependencies**: Ensure both frontend and backend are running
3. **Database State**: Global setup creates clean test environment
4. **Browser Installation**: Run `npx playwright install` if browsers missing

### Debug Mode
```bash
# Run with browser visible and dev tools
npm run test:e2e:debug

# Run specific test in debug mode
npx playwright test --debug -g "specific test name"

# Generate and view trace
npx playwright test --trace on
npx playwright show-trace trace.zip
```

## Contributing

### Adding New Tests
1. Follow existing test file patterns
2. Use appropriate test data from global setup
3. Include error handling scenarios
4. Add accessibility checks where relevant
5. Update this README with new test coverage

### Test Data Management
- Use existing test users and data where possible
- Create minimal additional test data
- Clean up any test-specific data in afterEach hooks
- Document any new test data requirements

## Metrics & Reporting

### Test Execution Metrics
- **Total Tests**: 630 test cases across 7 files
- **Browser Coverage**: 7 different browser configurations
- **Execution Time**: ~15-20 minutes for full suite
- **Success Rate**: Target 100% pass rate

### Coverage Areas
- ✅ **Complete Workflow**: 16 comprehensive scenarios
- ✅ **Role-Based Functionality**: 6 user roles fully covered
- ✅ **LLM Integrations**: 13 AI/ML scenarios
- ✅ **Authentication**: Login/logout and session management
- ✅ **Dashboard**: Core navigation and display
- ✅ **Accessibility**: WCAG compliance validation
- ✅ **Performance**: Load times and Core Web Vitals

This comprehensive test suite ensures robust validation of the entire SynapseDT platform, providing confidence in all core functionality, role-based interactions, and system integrations. 