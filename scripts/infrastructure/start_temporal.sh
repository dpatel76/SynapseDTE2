#!/bin/bash

# Script to start Temporal workflow engine for SynapseDTE

echo "Starting Temporal workflow engine..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

# Create network if it doesn't exist
docker network create synapse-network 2>/dev/null || true

# Start Temporal services
echo "Starting Temporal services..."
docker-compose -f docker-compose.temporal.yml up -d

# Wait for Temporal to be ready
echo "Waiting for Temporal to be ready..."
sleep 10

# Check if Temporal is running
if docker-compose -f docker-compose.temporal.yml ps | grep -q "temporal-server.*Up"; then
    echo "✓ Temporal server is running on http://localhost:7233"
    echo "✓ Temporal UI is available at http://localhost:8088"
    echo ""
    echo "To start the SynapseDTE Temporal worker, run:"
    echo "  python -m app.temporal.worker"
    echo ""
    echo "To view logs:"
    echo "  docker-compose -f docker-compose.temporal.yml logs -f"
else
    echo "✗ Failed to start Temporal services"
    echo "Check logs with: docker-compose -f docker-compose.temporal.yml logs"
    exit 1
fi