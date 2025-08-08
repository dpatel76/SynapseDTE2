#!/bin/bash

# Restart Frontend service
echo "Restarting Frontend container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml restart frontend

if [ $? -eq 0 ]; then
    echo "✅ Frontend restarted successfully"
else
    echo "❌ Failed to restart Frontend"
    exit 1
fi