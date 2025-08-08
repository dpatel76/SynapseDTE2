#!/bin/bash

# Restart Redis service
echo "Restarting Redis container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml restart redis

if [ $? -eq 0 ]; then
    echo "✅ Redis restarted successfully"
else
    echo "❌ Failed to restart Redis"
    exit 1
fi