#!/bin/bash

# Start Frontend service
echo "Starting Frontend container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml up -d frontend

# Wait for service to be ready
echo "Waiting for Frontend to be ready..."
timeout=30
while [ $timeout -gt 0 ]; do
    if curl -s http://localhost:3001 >/dev/null 2>&1; then
        echo "✅ Frontend is ready!"
        exit 0
    fi
    echo "Waiting for Frontend... ($timeout seconds remaining)"
    sleep 2
    ((timeout-=2))
done

echo "❌ Frontend failed to start within 30 seconds"
exit 1