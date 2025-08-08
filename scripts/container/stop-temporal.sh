#!/bin/bash

# Stop Temporal services
echo "Stopping Temporal services..."
cd /Users/dineshpatel/code/projects/SynapseDTE2

# Stop in reverse order
echo "Stopping Temporal UI..."
docker-compose -f docker-compose.container.yml stop temporal-ui

echo "Stopping Temporal Server..."
docker-compose -f docker-compose.container.yml stop temporal

echo "Stopping Temporal PostgreSQL..."
docker-compose -f docker-compose.container.yml stop temporal-postgres

echo "✅ All Temporal services stopped"