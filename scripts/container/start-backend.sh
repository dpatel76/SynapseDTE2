#!/bin/bash

# Start Backend service
echo "Starting Backend container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml up -d backend

# Wait for service to be ready
echo "Waiting for Backend to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -s http://localhost:8001/api/v1/health >/dev/null 2>&1; then
        echo "✅ Backend is ready!"
        exit 0
    fi
    echo "Waiting for Backend... ($timeout seconds remaining)"
    sleep 2
    ((timeout-=2))
done

echo "❌ Backend failed to start within 60 seconds"
exit 1