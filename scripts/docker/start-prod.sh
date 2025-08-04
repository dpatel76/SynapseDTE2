#!/bin/bash
# Start SynapseDTE in production mode

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting SynapseDTE in production mode...${NC}"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed. Aborting.${NC}" >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose is required but not installed. Aborting.${NC}" >&2; exit 1; }

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env from .env.docker.example and configure it${NC}"
    exit 1
fi

# Validate required environment variables
required_vars=("SECRET_KEY" "DATABASE_PASSWORD" "REDIS_PASSWORD" "ANTHROPIC_API_KEY" "GOOGLE_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=.*change-this" .env || grep -q "^${var}=your-" .env; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}Error: The following required variables are not properly set in .env:${NC}"
    printf '%s\n' "${missing_vars[@]}"
    echo -e "${YELLOW}Please update these values before running in production${NC}"
    exit 1
fi

# Create required directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p uploads logs temporal/dynamicconfig

# Create temporal production config if it doesn't exist
if [ ! -f temporal/dynamicconfig/production.yaml ]; then
    echo -e "${GREEN}Creating Temporal production config...${NC}"
    cat > temporal/dynamicconfig/production.yaml <<EOF
# Temporal dynamic configuration for production
system.forceSearchAttributesCacheRefreshOnRead:
  - value: true
    
limit.maxIDLength:
  - value: 1000
    
frontend.enableClientVersionCheck:
  - value: true

history.persistenceMaxQPS:
  - value: 10000

frontend.persistenceMaxQPS:
  - value: 10000

frontend.historyMgrNumConns:
  - value: 100

frontend.throttledLogRPS:
  - value: 100

history.historyMgrNumConns:
  - value: 500

system.advancedVisibilityWritingMode:
  - value: "on"

history.defaultActivityRetryPolicy:
  - value:
      InitialIntervalInSeconds: 1
      MaximumIntervalCoefficient: 100.0
      BackoffCoefficient: 2.0
      MaximumAttempts: 3

history.defaultWorkflowRetryPolicy:
  - value:
      InitialIntervalInSeconds: 1
      MaximumIntervalCoefficient: 100.0
      BackoffCoefficient: 2.0
      MaximumAttempts: 1
EOF
fi

# Build images
echo -e "${GREEN}Building Docker images...${NC}"
./scripts/docker/build.sh

# Start services
echo -e "${GREEN}Starting Docker containers...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "${GREEN}Waiting for services to be ready...${NC}"
attempts=0
max_attempts=30

while [ $attempts -lt $max_attempts ]; do
    if docker-compose ps | grep -q "unhealthy"; then
        echo -n "."
        sleep 2
        attempts=$((attempts + 1))
    else
        echo ""
        break
    fi
done

if [ $attempts -eq $max_attempts ]; then
    echo -e "${RED}Services failed to become healthy. Check logs with: docker-compose logs${NC}"
    exit 1
fi

# Check service status
echo -e "${GREEN}Service status:${NC}"
docker-compose ps

# Show access information
echo ""
echo -e "${GREEN}SynapseDTE is running!${NC}"
echo ""
echo -e "${GREEN}Access points:${NC}"
echo "  - Application: http://localhost"
echo "  - API Documentation: http://localhost/api/v1/docs"
echo "  - Temporal UI: http://localhost:8088"
echo ""
echo -e "${YELLOW}Monitor logs:${NC}"
echo "  docker-compose logs -f [service-name]"
echo ""
echo -e "${YELLOW}View all logs:${NC}"
echo "  docker-compose logs -f"
echo ""
echo -e "${YELLOW}Stop services:${NC}"
echo "  docker-compose down"
echo ""
echo -e "${YELLOW}Stop and remove volumes:${NC}"
echo "  docker-compose down -v"