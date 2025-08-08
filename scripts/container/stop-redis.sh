#!/bin/bash

# Stop Redis service
echo "Stopping Redis container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml stop redis

if [ $? -eq 0 ]; then
    echo "✅ Redis stopped successfully"
else
    echo "❌ Failed to stop Redis"
    exit 1
fi