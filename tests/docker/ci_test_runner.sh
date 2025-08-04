#!/bin/bash
#
# CI/CD Test Runner for SynapseDTE Docker Tests
# Designed for use in continuous integration pipelines
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TEST_PROJECT_NAME="synapse-ci-test"
COMPOSE_FILE="docker-compose.yml"
LOG_DIR="ci_test_logs"
REPORT_DIR="ci_test_reports"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to cleanup on exit
cleanup() {
    print_status "$YELLOW" "🧹 Cleaning up..."
    docker-compose -p "$TEST_PROJECT_NAME" down -v --remove-orphans || true
    docker system prune -f || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Print header
print_status "$GREEN" "======================================"
print_status "$GREEN" "🚀 SynapseDTE CI/CD Test Runner"
print_status "$GREEN" "======================================"
echo "Start time: $(date)"
echo "Test project: $TEST_PROJECT_NAME"
echo ""

# Check Docker is available
print_status "$YELLOW" "🔍 Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_status "$RED" "❌ Docker not found!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_status "$RED" "❌ Docker Compose not found!"
    exit 1
fi

# Check Docker daemon
if ! docker ps &> /dev/null; then
    print_status "$RED" "❌ Docker daemon not running!"
    exit 1
fi

print_status "$GREEN" "✅ Prerequisites checked"

# Build containers
print_status "$YELLOW" "🔨 Building containers..."
docker build -f Dockerfile.backend -t synapse-backend:ci . > "$LOG_DIR/build_backend.log" 2>&1 || {
    print_status "$RED" "❌ Backend build failed! Check $LOG_DIR/build_backend.log"
    exit 1
}
docker build -f Dockerfile.frontend -t synapse-frontend:ci . > "$LOG_DIR/build_frontend.log" 2>&1 || {
    print_status "$RED" "❌ Frontend build failed! Check $LOG_DIR/build_frontend.log"
    exit 1
}
docker build -f Dockerfile.worker -t synapse-worker:ci . > "$LOG_DIR/build_worker.log" 2>&1 || {
    print_status "$RED" "❌ Worker build failed! Check $LOG_DIR/build_worker.log"
    exit 1
}
print_status "$GREEN" "✅ Containers built successfully"

# Run tests
FAILED_TESTS=()

# Function to run a test suite
run_test_suite() {
    local test_name=$1
    local test_script=$2
    local test_type=$3  # required or optional
    
    print_status "$YELLOW" "📋 Running $test_name..."
    
    if python "$test_script" > "$LOG_DIR/${test_script%.py}.log" 2>&1; then
        print_status "$GREEN" "✅ $test_name passed"
        
        # Copy report if exists
        if [ -f "${test_script%.py}_report.json" ]; then
            mv "${test_script%.py}_report.json" "$REPORT_DIR/"
        fi
    else
        print_status "$RED" "❌ $test_name failed"
        FAILED_TESTS+=("$test_name")
        
        # Show last 20 lines of log
        echo "Last 20 lines of log:"
        tail -20 "$LOG_DIR/${test_script%.py}.log"
        
        # Exit if required test failed
        if [ "$test_type" = "required" ]; then
            exit 1
        fi
    fi
}

# Run test suites
run_test_suite "Build Tests" "test_build.py" "required"
run_test_suite "Health Tests" "test_health.py" "required"
run_test_suite "Integration Tests" "test_integration.py" "required"

# Optional tests (don't fail CI if they fail)
if [ -z "$QUICK_TESTS" ]; then
    run_test_suite "E2E Tests" "test_e2e.py" "optional"
    run_test_suite "Performance Tests" "test_performance.py" "optional"
fi

# Generate summary report
print_status "$YELLOW" "📊 Generating summary report..."

SUMMARY_REPORT="$REPORT_DIR/ci_summary.json"
cat > "$SUMMARY_REPORT" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "project": "$TEST_PROJECT_NAME",
  "total_tests": 5,
  "failed_tests": ${#FAILED_TESTS[@]},
  "failed_test_names": [$(printf '"%s",' "${FAILED_TESTS[@]}" | sed 's/,$//')],
  "status": "$([ ${#FAILED_TESTS[@]} -eq 0 ] && echo "passed" || echo "failed")"
}
EOF

# Print summary
echo ""
print_status "$GREEN" "======================================"
print_status "$GREEN" "📊 TEST SUMMARY"
print_status "$GREEN" "======================================"
echo "Total test suites: 5"
echo "Failed test suites: ${#FAILED_TESTS[@]}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo ""
    print_status "$RED" "Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
fi

echo ""
echo "Logs saved to: $LOG_DIR/"
echo "Reports saved to: $REPORT_DIR/"
echo "End time: $(date)"

# Exit with appropriate code
if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
    print_status "$GREEN" "✅ ALL REQUIRED TESTS PASSED!"
    exit 0
else
    print_status "$RED" "❌ SOME TESTS FAILED!"
    exit 1
fi