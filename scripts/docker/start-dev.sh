#!/bin/bash
# Start SynapseDTE in development mode

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting SynapseDTE in development mode...${NC}"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed. Aborting.${NC}" >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose is required but not installed. Aborting.${NC}" >&2; exit 1; }

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.docker.example .env
    echo -e "${YELLOW}Please update .env with your API keys and configuration${NC}"
fi

# Create required directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p uploads logs temporal/dynamicconfig

# Create temporal dynamic config if it doesn't exist
if [ ! -f temporal/dynamicconfig/development.yaml ]; then
    echo -e "${GREEN}Creating Temporal development config...${NC}"
    cat > temporal/dynamicconfig/development.yaml <<EOF
# Temporal dynamic configuration for development
system.forceSearchAttributesCacheRefreshOnRead:
  - value: true
    
limit.maxIDLength:
  - value: 1000
    
frontend.enableClientVersionCheck:
  - value: false

history.persistenceMaxQPS:
  - value: 3000

frontend.persistenceMaxQPS:
  - value: 3000

frontend.historyMgrNumConns:
  - value: 10

frontend.throttledLogRPS:
  - value: 20

history.historyMgrNumConns:
  - value: 50

system.advancedVisibilityWritingMode:
  - value: "on"

history.defaultActivityRetryPolicy:
  - value:
      InitialIntervalInSeconds: 1
      MaximumIntervalCoefficient: 100.0
      BackoffCoefficient: 2.0
      MaximumAttempts: 0

history.defaultWorkflowRetryPolicy:
  - value:
      InitialIntervalInSeconds: 1
      MaximumIntervalCoefficient: 100.0
      BackoffCoefficient: 2.0
      MaximumAttempts: 0
EOF
fi

# Start services
echo -e "${GREEN}Starting Docker containers...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait for services to be healthy
echo -e "${GREEN}Waiting for services to be ready...${NC}"
sleep 5

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
docker-compose ps

# Show logs command
echo -e "${GREEN}Services started!${NC}"
echo ""
echo -e "${GREEN}Access points:${NC}"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Temporal UI: http://localhost:8088"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo "  docker-compose logs -f [service-name]"
echo ""
echo -e "${YELLOW}To stop:${NC}"
echo "  docker-compose down"
echo ""
echo -e "${YELLOW}To run with additional tools (pgAdmin, Redis Commander):${NC}"
echo "  docker-compose --profile tools -f docker-compose.yml -f docker-compose.dev.yml up -d"