#!/bin/bash

# Stop Frontend service
echo "Stopping Frontend container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml stop frontend

if [ $? -eq 0 ]; then
    echo "✅ Frontend stopped successfully"
else
    echo "❌ Failed to stop Frontend"
    exit 1
fi