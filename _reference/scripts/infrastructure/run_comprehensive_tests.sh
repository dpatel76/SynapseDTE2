#!/bin/bash
# Run comprehensive UI and API tests for SynapseDTE

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== SynapseDTE Comprehensive Test Runner ===${NC}"
echo

# Check if running from correct directory
if [ ! -f "app/main.py" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Create test results directory
mkdir -p test_results

# Check if backend is running
echo -e "${YELLOW}Checking if backend is running...${NC}"
if ! curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
    echo -e "${RED}Error: Backend is not running. Please start it first with:${NC}"
    echo "  ./restart_backend.sh"
    exit 1
fi

# Check if frontend is running
echo -e "${YELLOW}Checking if frontend is running...${NC}"
if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${RED}Error: Frontend is not running. Please start it first with:${NC}"
    echo "  ./restart_frontend.sh or npm start (from frontend directory)"
    exit 1
fi

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -r tests/requirements-test.txt

# Install playwright browsers if not already installed
echo -e "${YELLOW}Installing Playwright browsers...${NC}"
playwright install chromium

# Create test users if they don't exist
echo -e "${YELLOW}Ensuring test users exist...${NC}"
python scripts/create_test_users.py

# Run the comprehensive test suite
echo -e "${GREEN}Starting comprehensive test suite...${NC}"
echo -e "${BLUE}This will test all UI pages and API endpoints for every role${NC}"
echo

cd tests
python comprehensive_test_system.py

# Open the HTML report
if [ -f "../test_results/test_report.html" ]; then
    echo
    echo -e "${GREEN}Test completed! Opening test report...${NC}"
    if command -v open > /dev/null 2>&1; then
        open ../test_results/test_report.html
    elif command -v xdg-open > /dev/null 2>&1; then
        xdg-open ../test_results/test_report.html
    else
        echo -e "${YELLOW}Report available at: test_results/test_report.html${NC}"
    fi
else
    echo -e "${RED}Test report not generated. Check logs for errors.${NC}"
fi