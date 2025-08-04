#!/bin/bash
# Stop script for refactored SynapseDTE system

set -e

echo "=== Stopping Refactored SynapseDTE Services ==="
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop Celery workers
echo -e "${YELLOW}1. Stopping Celery workers...${NC}"
if [ -f celery_worker.pid ]; then
    kill $(cat celery_worker.pid) 2>/dev/null || true
    rm -f celery_worker.pid
    echo -e "${GREEN}Celery worker stopped${NC}"
else
    echo "Celery worker PID file not found"
fi

if [ -f celery_beat.pid ]; then
    kill $(cat celery_beat.pid) 2>/dev/null || true
    rm -f celery_beat.pid
    echo -e "${GREEN}Celery beat stopped${NC}"
else
    echo "Celery beat PID file not found"
fi

# Stop Flower
echo -e "${YELLOW}2. Stopping Flower...${NC}"
pkill -f "flower" 2>/dev/null || echo "Flower not running"

# Stop Docker services
echo -e "${YELLOW}3. Stopping Docker services...${NC}"
docker-compose -f docker-compose.refactor.yml down

echo
echo -e "${GREEN}=== All services stopped ===${NC}"