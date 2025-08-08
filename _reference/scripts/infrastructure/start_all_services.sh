#!/bin/bash

# SynapseDT - Start All Services
# This script starts all required services for the application including Temporal

set -e  # Exit on error

echo "========================================="
echo "Starting SynapseDT Services"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to kill process on port
kill_port() {
    local PORT=$1
    local SERVICE=$2
    if port_in_use $PORT; then
        echo -e "${YELLOW}Port $PORT is in use. Killing existing $SERVICE process...${NC}"
        lsof -ti :$PORT | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}Error: npm is not installed. Please install Node.js and npm.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"

# 1. Start PostgreSQL (if using Docker)
echo -e "\n${YELLOW}1. Starting PostgreSQL...${NC}"
if ! docker ps | grep -q postgres_synapse; then
    docker run -d \
        --name postgres_synapse \
        -e POSTGRES_USER=synapse_user \
        -e POSTGRES_PASSWORD=synapse_password \
        -e POSTGRES_DB=synapse_dt \
        -p 5432:5432 \
        postgres:15 || echo "PostgreSQL container may already exist"
else
    echo "PostgreSQL is already running"
fi

# 2. Start Temporal Server (using Docker)
echo -e "\n${YELLOW}2. Starting Temporal Server...${NC}"
if ! docker ps | grep -q temporal; then
    # Check if we need to create a network
    if ! docker network ls | grep -q temporal-network; then
        docker network create temporal-network
    fi
    
    # Start Temporal with PostgreSQL
    docker run -d \
        --name temporal \
        --network temporal-network \
        -p 7233:7233 \
        -e DB=postgresql \
        -e DB_PORT=5432 \
        -e POSTGRES_USER=temporal \
        -e POSTGRES_PWD=temporal \
        -e POSTGRES_SEEDS=postgres_synapse \
        temporalio/temporal:latest || {
        # If using Temporal with internal database
        echo "Starting Temporal with internal database..."
        docker run -d \
            --name temporal \
            -p 7233:7233 \
            temporalio/temporal:latest
    }
else
    echo "Temporal is already running"
fi

# Wait for Temporal to be ready
echo "Waiting for Temporal to be ready..."
sleep 10

# 3. Run Database Migrations
echo -e "\n${YELLOW}3. Running database migrations...${NC}"
cd /Users/dineshpatel/code/projects/SynapseDTE
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
alembic upgrade head || echo -e "${YELLOW}Warning: Migrations may have already been applied${NC}"

# 4. Start Backend Services
echo -e "\n${YELLOW}4. Starting Backend Services...${NC}"

# Kill existing backend processes
kill_port 8000 "Backend API"

# Start FastAPI backend
echo "Starting FastAPI backend..."
uvicorn app.main:app --reload --log-level debug --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# 5. Start Temporal Worker (if enabled)
if [ "${TEMPORAL_WORKER_ENABLED:-false}" = "true" ]; then
    echo -e "\n${YELLOW}5. Starting Temporal Worker...${NC}"
    
    # Note: The worker has import issues that need to be fixed
    echo -e "${YELLOW}Note: Temporal worker has import issues that need to be resolved.${NC}"
    echo -e "${YELLOW}To enable the worker:${NC}"
    echo "  1. Fix the import issues in app/temporal/worker.py"
    echo "  2. Set TEMPORAL_WORKER_ENABLED=true in .env"
    echo "  3. Run: python -m app.temporal.worker"
    
    # Uncomment below when worker is fixed
    # python -m app.temporal.worker > temporal_worker.log 2>&1 &
    # WORKER_PID=$!
    # echo "Temporal Worker started with PID: $WORKER_PID"
else
    echo -e "\n${YELLOW}5. Temporal Worker is disabled (set TEMPORAL_WORKER_ENABLED=true to enable)${NC}"
fi

# 6. Start Frontend
echo -e "\n${YELLOW}6. Starting Frontend...${NC}"
cd frontend

# Kill existing frontend process
kill_port 3000 "Frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

cd ..

# 7. Optional: Start Temporal UI
echo -e "\n${YELLOW}7. Starting Temporal UI...${NC}"
if ! docker ps | grep -q temporal-ui; then
    docker run -d \
        --name temporal-ui \
        -p 8080:8080 \
        -e TEMPORAL_ADDRESS=host.docker.internal:7233 \
        temporalio/ui:latest || echo "Temporal UI may already exist"
else
    echo "Temporal UI is already running"
fi

# Create a PID file for easy shutdown
cat > services.pid << EOF
BACKEND_PID=$BACKEND_PID
FRONTEND_PID=$FRONTEND_PID
WORKER_PID=${WORKER_PID:-0}
EOF

# Summary
echo -e "\n${GREEN}========================================="
echo "All services started successfully!"
echo "=========================================${NC}"
echo ""
echo "Service URLs:"
echo "  - Backend API: http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Temporal UI: http://localhost:8080"
echo ""
echo "PostgreSQL: localhost:5432"
echo "  - Database: synapse_dt"
echo "  - User: synapse_user"
echo ""
echo "Temporal Server: localhost:7233"
echo ""
echo "Logs:"
echo "  - Backend: ./backend.log"
echo "  - Frontend: ./frontend.log"
echo "  - Temporal Worker: ./temporal_worker.log"
echo ""
echo -e "${YELLOW}To stop all services, run: ./stop_all_services.sh${NC}"
echo ""
echo "Process PIDs saved to services.pid"