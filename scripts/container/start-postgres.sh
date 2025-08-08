#!/bin/bash

# Start PostgreSQL service
echo "Starting PostgreSQL container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml up -d postgres

# Wait for service to be healthy
echo "Waiting for PostgreSQL to be healthy..."
timeout=30
while [ $timeout -gt 0 ]; do
    if docker-compose -f docker-compose.container.yml exec postgres pg_isready -U synapse_user >/dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        exit 0
    fi
    echo "Waiting for PostgreSQL... ($timeout seconds remaining)"
    sleep 1
    ((timeout--))
done

echo "❌ PostgreSQL failed to start within 30 seconds"
exit 1