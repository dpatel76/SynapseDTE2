#!/bin/bash

# Start Temporal services (postgres, server, ui)
echo "Starting Temporal services..."
cd /Users/dineshpatel/code/projects/SynapseDTE2

# Start Temporal PostgreSQL first
echo "Starting Temporal PostgreSQL..."
docker-compose -f docker-compose.container.yml up -d temporal-postgres

# Wait for Temporal PostgreSQL to be ready
echo "Waiting for Temporal PostgreSQL to be healthy..."
sleep 5

# Start Temporal Server
echo "Starting Temporal Server..."
docker-compose -f docker-compose.container.yml up -d temporal

# Wait for Temporal Server to be ready
echo "Waiting for Temporal Server to be ready..."
sleep 10

# Start Temporal UI
echo "Starting Temporal UI..."
docker-compose -f docker-compose.container.yml up -d temporal-ui

# Check if all services are running
sleep 5
if docker-compose -f docker-compose.container.yml ps | grep -q "temporal.*Up" && \
   docker-compose -f docker-compose.container.yml ps | grep -q "temporal-postgres.*Up" && \
   docker-compose -f docker-compose.container.yml ps | grep -q "temporal-ui.*Up"; then
    echo "✅ All Temporal services started successfully"
    echo "   Temporal UI available at: http://localhost:8089"
else
    echo "⚠️  Some Temporal services may not have started properly"
    docker-compose -f docker-compose.container.yml ps | grep temporal
fi