#!/bin/bash

# Stop Backend service
echo "Stopping Backend container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml stop backend

if [ $? -eq 0 ]; then
    echo "✅ Backend stopped successfully"
else
    echo "❌ Failed to stop Backend"
    exit 1
fi