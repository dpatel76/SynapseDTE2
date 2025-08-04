# SynapseDTE Comprehensive Testing System

## Overview

This document describes the comprehensive testing system that covers every UI page and API endpoint for all user roles in the SynapseDTE application. The system provides automated testing with real-time progress monitoring and detailed reporting.

## Testing Architecture

### Components

1. **Comprehensive Test System** (`tests/comprehensive_test_system.py`)
   - Main test orchestrator
   - Tests all UI pages for each role
   - Tests all API endpoints with role-based permissions
   - Generates detailed test reports

2. **Progress Monitoring Server** (`tests/test_progress_server.py`)
   - Real-time web-based progress tracking
   - Live test status updates
   - Failed test monitoring
   - Log streaming

3. **Test Runners**
   - `scripts/run_comprehensive_tests.sh` - Basic test runner
   - `scripts/run_tests_with_monitor.sh` - Test runner with progress monitor

## User Roles Tested

The system tests all functionality for these 6 user roles:

1. **Admin** - Full system access
2. **Test Manager** - Manages test cycles and workflows
3. **Tester** - Executes testing activities
4. **Report Owner** - Reviews and approves reports
5. **Report Owner Executive** - Strategic oversight
6. **CDO** - Manages LOBs and data providers
7. **Data Provider** - Provides data and uploads

## Test Coverage

### UI Pages Tested (by Category)

#### Main Pages
- Login page
- Dashboard (role-based)
- Test Cycles
- Reports
- Analytics
- Users

#### Workflow Phase Pages (7-Phase System)
1. Planning Phase
2. Scoping Phase
3. Data Provider ID Phase
4. Sample Selection Phase
5. Request for Information Phase
6. Testing Execution Phase
7. Observation Management Phase

#### Admin Pages
- User Management
- LOB Management
- Report Management
- Data Sources
- SLA Configuration
- RBAC Management
- System Settings

#### Role-Specific Dashboards
- Tester Dashboard
- Report Owner Dashboard
- CDO Dashboard
- Data Provider Dashboard
- Test Manager Dashboard

### API Endpoints Tested

#### Core Endpoints
- Authentication (`/auth/*`)
- User Management (`/users/*`)
- Cycle Management (`/cycles/*`)
- Report Management (`/reports/*`)
- LOB Management (`/lobs/*`)

#### Workflow Endpoints
- Planning (`/planning/*`)
- Scoping (`/scoping/*`)
- Data Provider (`/data-provider/*`)
- Sample Selection (`/sample-selection/*`)
- Request Info (`/request-info/*`)
- Testing Execution (`/testing-execution/*`)
- Observation Management (`/observation-management/*`)

#### Service Endpoints
- SLA Management (`/sla/*`)
- Metrics (`/metrics/*`)
- Dashboards (`/dashboards/*`)
- LLM Integration (`/llm/*`)

## Running the Tests

### Prerequisites

1. Backend server running on http://localhost:8001
2. Frontend running on http://localhost:3000
3. Test users created in the database

### Basic Test Run

```bash
# From project root directory
./scripts/run_comprehensive_tests.sh
```

This will:
- Install test dependencies
- Create test users if needed
- Run all UI and API tests
- Generate HTML report
- Open report in browser

### Test Run with Progress Monitor

```bash
# From project root directory
./scripts/run_tests_with_monitor.sh
```

This will:
- Start the progress monitoring server
- Open real-time progress dashboard at http://localhost:8888
- Run all tests while showing live progress
- Generate comprehensive reports

## Test Results

### Output Directory Structure

```
test_results/
├── comprehensive_test.log      # Detailed test logs
├── test_summary.json          # Summary statistics
├── test_results.json          # Detailed test results
├── test_report.html           # HTML report
├── screenshots/               # UI test screenshots
│   └── UI_<page>_<role>.png
└── api_responses/             # API response data
    └── API_<endpoint>_<role>.json
```

### HTML Report

The HTML report includes:
- Overall test summary
- Success rates by type (UI/API)
- Results by role
- Failed test details
- Visual progress indicators

### Test Result Structure

Each test result contains:
- **test_name**: Unique test identifier
- **test_type**: "ui" or "api"
- **role**: User role being tested
- **status**: passed/failed/skipped
- **duration**: Test execution time
- **error**: Error details (if failed)
- **screenshot**: Screenshot path (for UI tests)
- **request_data**: API request details
- **response_data**: API response details

## Test Credentials

Default test user credentials:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | Adminpass1! |
| Test Manager | testmanager | Testmanager1! |
| Tester | tester | Tester123! |
| Report Owner | reportowner | Reportowner1! |
| Report Owner Executive | reportexec | Reportexec1! |
| CDO | cdo | Cdo12345! |
| Data Provider | dataprovider | Dataprovider1! |

## Progress Monitoring

The real-time progress monitor provides:

### Metrics Dashboard
- Total tests count
- Completed tests
- Passed/Failed/Skipped counts
- Success rate percentage
- Execution duration

### Live Updates
- Overall progress bar
- Currently running tests
- Failed test details with errors
- Recent log entries
- Auto-refresh every 2 seconds

### Access
- URL: http://localhost:8888
- No authentication required
- Works on all modern browsers

## Extending the Test System

### Adding New UI Pages

Edit `UIPageInventory.PAGES_BY_ROLE` in `comprehensive_test_system.py`:

```python
UserRole.TESTER: [
    "/existing-page",
    "/new-page",  # Add new page here
]
```

### Adding New API Endpoints

Edit `APIEndpointInventory.ENDPOINTS`:

```python
"new_category": {
    "list": ("GET", "/api/v1/new-endpoint", ["allowed", "roles"]),
    "create": ("POST", "/api/v1/new-endpoint", ["Admin"]),
}
```

### Custom Test Data

Modify `get_test_data_for_endpoint()` method to provide endpoint-specific test data.

## Troubleshooting

### Common Issues

1. **Tests failing to start**
   - Ensure backend is running: `./restart_backend.sh`
   - Ensure frontend is running: `./restart_frontend.sh`
   - Check test users exist: `python scripts/create_test_users.py`

2. **UI tests timing out**
   - Increase `UI_TIMEOUT` in test system
   - Check frontend console for errors
   - Ensure browser drivers are installed: `playwright install chromium`

3. **API tests failing with 401**
   - Test user credentials may be incorrect
   - Authentication tokens may be expired
   - Check backend logs for auth errors

4. **Progress monitor not updating**
   - Check if test_results directory exists
   - Ensure progress server is running on port 8888
   - Check browser console for errors

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
./scripts/run_comprehensive_tests.sh
```

## Best Practices

1. **Run tests regularly** - At least daily in CI/CD
2. **Monitor trends** - Track success rates over time
3. **Fix failures quickly** - Don't let test debt accumulate
4. **Keep tests updated** - Update when adding new features
5. **Use test results** - Incorporate into deployment decisions

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Comprehensive Tests
on:
  schedule:
    - cron: '0 2 * * *'  # Run at 2 AM daily
  push:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
          playwright install chromium
      - name: Start services
        run: |
          docker-compose up -d
          ./scripts/wait-for-services.sh
      - name: Run tests
        run: ./scripts/run_comprehensive_tests.sh
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_results/
```

## Performance Considerations

- Tests run in parallel where possible
- UI tests use headless browser for speed
- API tests use connection pooling
- Results are cached to avoid redundant tests
- Screenshots only taken on failure (configurable)

## Security Notes

- Test credentials are for testing only
- Never use production data in tests
- API tokens are short-lived
- Test data is cleaned up after runs
- No sensitive data in test results

## Future Enhancements

1. **Test Data Generation** - Faker integration for realistic data
2. **Visual Regression** - Screenshot comparison
3. **Performance Testing** - Load and stress testing
4. **Accessibility Testing** - WCAG compliance checks
5. **Mobile Testing** - Responsive design validation
6. **API Contract Testing** - Schema validation
7. **Integration with APM** - Performance monitoring
8. **Test Parallelization** - Distributed test execution