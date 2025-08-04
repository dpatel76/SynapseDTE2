# Docker Test Suite for SynapseDTE

This directory contains comprehensive tests for the containerized SynapseDTE application.

## Test Suites

1. **Build Tests** (`test_build.py`)
   - Validates Dockerfile syntax and best practices
   - Checks image sizes and layer optimization
   - Security scanning (if Trivy is installed)

2. **Health Tests** (`test_health.py`)
   - Verifies all services start correctly
   - Checks service health endpoints
   - Validates port accessibility
   - Tests restart resilience

3. **Integration Tests** (`test_integration.py`)
   - Tests inter-service communication
   - API endpoint functionality
   - Database connections
   - Frontend-backend integration

4. **End-to-End Tests** (`test_e2e.py`)
   - Complete user workflows
   - Multi-user collaboration
   - Data processing pipelines
   - Report generation

5. **Performance Tests** (`test_performance.py`)
   - API response time baselines
   - Throughput testing
   - Resource usage monitoring
   - Memory leak detection

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install docker psycopg2-binary redis requests

# Install optional tools
brew install hadolint  # Dockerfile linting (macOS)
brew install aquasecurity/trivy/trivy  # Security scanning
```

### Running Tests

#### Run all tests:
```bash
python run_all_tests.py
```

#### Run quick tests only (build, health, integration):
```bash
python run_all_tests.py --quick
```

#### Run specific test suites:
```bash
python run_all_tests.py --only integration e2e
```

#### Build containers before testing:
```bash
python run_all_tests.py --build
```

#### Keep containers running after tests:
```bash
python run_all_tests.py --keep-containers
```

### Individual Test Suites

Run a specific test suite:
```bash
python test_health.py
python test_integration.py
python test_e2e.py
```

### CI/CD Integration

For CI pipelines, use the provided script:
```bash
./ci_test_runner.sh
```

Or for quick tests only:
```bash
QUICK_TESTS=1 ./ci_test_runner.sh
```

## Test Configuration

### Environment Variables

- `TEST_API_BASE`: Override API base URL (default: http://localhost:8000)
- `TEST_FRONTEND_URL`: Override frontend URL (default: http://localhost)
- `TEST_TIMEOUT`: Global timeout for operations (default: 300s)
- `TEST_PROJECT_NAME`: Docker Compose project name (default: synapse-test)

### Custom Configuration

Create a custom test configuration:

```python
from test_framework import TestConfig

config = TestConfig(
    compose_file="docker-compose.test.yml",
    startup_timeout=600,
    api_base_url="http://localhost:8001"
)
```

## Test Reports

Test results are saved as JSON reports:

- `build_test_report.json` - Build test results
- `health_test_report.json` - Health check results
- `integration_test_report.json` - Integration test results
- `e2e_test_report.json` - E2E test results
- `performance_test_report.json` - Performance test results
- `final_test_report.json` - Comprehensive summary

## Troubleshooting

### Tests fail with "Docker daemon not running"
Ensure Docker Desktop is running or Docker daemon is started.

### Port conflicts
Check if ports are already in use:
```bash
lsof -i :8000  # Backend
lsof -i :80    # Frontend
lsof -i :5432  # PostgreSQL
```

### Container startup timeout
Increase timeout in test configuration or wait longer:
```python
config = TestConfig(startup_timeout=600)  # 10 minutes
```

### View test logs
All test output is captured:
```bash
# View specific test logs
docker-compose -p synapse-test logs backend

# View all logs
docker-compose -p synapse-test logs
```

### Clean up stuck containers
```bash
docker-compose -p synapse-test down -v
docker system prune -a
```

## Performance Baselines

Default performance baselines (can be customized):

- Health check: < 50ms
- User login: < 200ms
- Data query: < 500ms
- Report generation: < 5000ms
- Concurrent users: 50
- Requests per second: 100

## Security Scanning

Install Trivy for security scanning:
```bash
# macOS
brew install aquasecurity/trivy/trivy

# Linux
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
```

## Contributing

When adding new tests:

1. Extend `TestRunner` base class
2. Use `test_context` for proper error handling
3. Add test to appropriate suite
4. Update test documentation
5. Set appropriate baselines

Example:
```python
def test_new_feature(self):
    with self.framework.test_context("New feature test") as details:
        # Test implementation
        result = self.call_api_endpoint()
        
        if not result.success:
            raise Exception("Feature test failed")
        
        details['result'] = result.data
        print("   ✓ New feature working correctly")
```

## License

See main project LICENSE file.