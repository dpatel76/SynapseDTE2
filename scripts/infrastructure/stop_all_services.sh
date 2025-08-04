#!/bin/bash

# SynapseDT - Stop All Services
# This script stops all running services

set -e

echo "========================================="
echo "Stopping SynapseDT Services"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to kill process on port
kill_port() {
    local PORT=$1
    local SERVICE=$2
    if lsof -i :$PORT >/dev/null 2>&1; then
        echo -e "${YELLOW}Stopping $SERVICE on port $PORT...${NC}"
        lsof -ti :$PORT | xargs kill -9 2>/dev/null || true
    else
        echo "$SERVICE on port $PORT is not running"
    fi
}

# 1. Stop Frontend
echo -e "\n${YELLOW}1. Stopping Frontend...${NC}"
kill_port 3000 "Frontend"

# 2. Stop Backend
echo -e "\n${YELLOW}2. Stopping Backend...${NC}"
kill_port 8000 "Backend API"

# 3. Stop Temporal Worker (if running)
echo -e "\n${YELLOW}3. Stopping Temporal Worker...${NC}"
if [ -f services.pid ]; then
    source services.pid
    if [ "${WORKER_PID:-0}" -ne 0 ]; then
        kill -9 $WORKER_PID 2>/dev/null || echo "Temporal Worker already stopped"
    fi
fi

# 4. Stop Docker containers
echo -e "\n${YELLOW}4. Stopping Docker containers...${NC}"

# Stop Temporal UI
if docker ps | grep -q temporal-ui; then
    echo "Stopping Temporal UI..."
    docker stop temporal-ui
    docker rm temporal-ui
else
    echo "Temporal UI is not running"
fi

# Stop Temporal Server
if docker ps | grep -q temporal; then
    echo "Stopping Temporal Server..."
    docker stop temporal
    docker rm temporal
else
    echo "Temporal Server is not running"
fi

# Optional: Stop PostgreSQL (uncomment if you want to stop it)
# if docker ps | grep -q postgres_synapse; then
#     echo "Stopping PostgreSQL..."
#     docker stop postgres_synapse
#     docker rm postgres_synapse
# else
#     echo "PostgreSQL is not running"
# fi

# Clean up PID file
rm -f services.pid

# Clean up log files (optional)
read -p "Do you want to clean up log files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f backend.log frontend.log temporal_worker.log
    echo -e "${GREEN}Log files cleaned${NC}"
fi

echo -e "\n${GREEN}========================================="
echo "All services stopped successfully!"
echo "=========================================${NC}"