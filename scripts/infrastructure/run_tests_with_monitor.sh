#!/bin/bash
# Run comprehensive tests with real-time progress monitoring

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== SynapseDTE Test Suite with Progress Monitor ===${NC}"
echo

# Check if running from correct directory
if [ ! -f "app/main.py" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Install aiohttp dependencies for progress server
echo -e "${YELLOW}Installing progress server dependencies...${NC}"
pip install aiohttp aiohttp-cors aiofiles

# Start the progress monitoring server in background
echo -e "${GREEN}Starting progress monitoring server...${NC}"
cd tests
python test_progress_server.py &
PROGRESS_PID=$!
cd ..

# Give the server time to start
sleep 2

# Open the progress monitor in browser
echo -e "${GREEN}Opening progress monitor in browser...${NC}"
if command -v open > /dev/null 2>&1; then
    open http://localhost:8888
elif command -v xdg-open > /dev/null 2>&1; then
    xdg-open http://localhost:8888
else
    echo -e "${YELLOW}Progress monitor available at: http://localhost:8888${NC}"
fi

echo
echo -e "${BLUE}Progress monitor is running at: http://localhost:8888${NC}"
echo -e "${YELLOW}Starting tests in 5 seconds...${NC}"
sleep 5

# Run the actual tests
./scripts/run_comprehensive_tests.sh

# Stop the progress server
echo
echo -e "${YELLOW}Stopping progress monitor...${NC}"
kill $PROGRESS_PID 2>/dev/null || true

echo -e "${GREEN}Test suite completed!${NC}"