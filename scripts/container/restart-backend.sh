#!/bin/bash

# Restart Backend service
echo "Restarting Backend container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml restart backend

if [ $? -eq 0 ]; then
    echo "✅ Backend restarted successfully"
    echo "Waiting for Backend to be ready..."
    sleep 5
    if curl -s http://localhost:8001/api/v1/health >/dev/null 2>&1; then
        echo "✅ Backend is responding"
    else
        echo "⚠️  Backend restarted but may not be fully ready yet"
    fi
else
    echo "❌ Failed to restart Backend"
    exit 1
fi