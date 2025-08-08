#!/bin/bash
# Setup script for refactored SynapseDTE system

set -e  # Exit on error

echo "=== SynapseDTE Refactored System Setup ==="
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env.refactor exists
if [ ! -f .env.refactor ]; then
    echo -e "${RED}Error: .env.refactor file not found${NC}"
    echo "Please create .env.refactor with your configuration"
    exit 1
fi

# Load environment variables
export $(cat .env.refactor | grep -v '^#' | xargs)

echo -e "${YELLOW}1. Starting Docker services...${NC}"
docker-compose -f docker-compose.refactor.yml up -d postgres-refactor redis-refactor

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}2. Waiting for PostgreSQL to be ready...${NC}"
for i in {1..30}; do
    if docker-compose -f docker-compose.refactor.yml exec -T postgres-refactor pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}PostgreSQL is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Create database if it doesn't exist
echo -e "${YELLOW}3. Creating database...${NC}"
docker-compose -f docker-compose.refactor.yml exec -T postgres-refactor psql -U postgres -c "CREATE DATABASE synapse_dte_refactor;" 2>/dev/null || echo "Database already exists"

# Install Python dependencies
echo -e "${YELLOW}4. Installing Python dependencies...${NC}"
pip install celery[redis] flower

# Run database migrations
echo -e "${YELLOW}5. Running database migrations...${NC}"
DATABASE_URL=$DATABASE_URL alembic upgrade head

# Start Celery workers in background
echo -e "${YELLOW}6. Starting Celery workers...${NC}"
celery -A app.core.celery_app worker --loglevel=info --detach --pidfile=celery_worker.pid
celery -A app.core.celery_app beat --loglevel=info --detach --pidfile=celery_beat.pid

# Start Flower for monitoring (optional)
echo -e "${YELLOW}7. Starting Flower (Celery monitoring)...${NC}"
celery -A app.core.celery_app flower --port=5555 --detach

echo
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo
echo "Services running:"
echo "- PostgreSQL: localhost:5433"
echo "- Redis: localhost:6380"
echo "- Celery Worker: Running in background"
echo "- Celery Beat: Running in background"
echo "- Flower: http://localhost:5555"
echo
echo "To start the refactored backend:"
echo "  uvicorn app.main:app --reload --port 8001"
echo
echo "To start the refactored frontend:"
echo "  cd frontend && PORT=3001 npm start"
echo
echo "To stop services:"
echo "  ./stop_refactored.sh"