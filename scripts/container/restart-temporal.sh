#!/bin/bash

# Restart Temporal services
echo "Restarting Temporal services..."
cd /Users/dineshpatel/code/projects/SynapseDTE2

echo "Restarting Temporal PostgreSQL..."
docker-compose -f docker-compose.container.yml restart temporal-postgres
sleep 5

echo "Restarting Temporal Server..."
docker-compose -f docker-compose.container.yml restart temporal
sleep 10

echo "Restarting Temporal UI..."
docker-compose -f docker-compose.container.yml restart temporal-ui

echo "✅ All Temporal services restarted"
echo "   Temporal UI available at: http://localhost:8089"