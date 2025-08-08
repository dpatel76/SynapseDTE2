#!/bin/bash

# Start Redis service
echo "Starting Redis container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml up -d redis

# Wait for service to be healthy
echo "Waiting for Redis to be healthy..."
timeout=30
while [ $timeout -gt 0 ]; do
    if docker-compose -f docker-compose.container.yml exec redis redis-cli --no-auth-warning -a synapse_redis_password ping >/dev/null 2>&1; then
        echo "✅ Redis is ready!"
        exit 0
    fi
    echo "Waiting for Redis... ($timeout seconds remaining)"
    sleep 1
    ((timeout--))
done

echo "❌ Redis failed to start within 30 seconds"
exit 1