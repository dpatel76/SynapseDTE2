#!/bin/bash
# Build all Docker images for SynapseDTE

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building SynapseDTE Docker images...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Copying from .env.docker.example${NC}"
    cp .env.docker.example .env
fi

# Build images
echo -e "${GREEN}Building backend image...${NC}"
docker build -f Dockerfile.backend -t synapse-backend:latest .

echo -e "${GREEN}Building frontend image...${NC}"
docker build -f Dockerfile.frontend -t synapse-frontend:latest .

echo -e "${GREEN}Building worker image...${NC}"
docker build -f Dockerfile.worker -t synapse-worker:latest .

echo -e "${GREEN}All images built successfully!${NC}"

# Display images
echo -e "${GREEN}Docker images:${NC}"
docker images | grep synapse-

echo -e "${GREEN}Build complete!${NC}"