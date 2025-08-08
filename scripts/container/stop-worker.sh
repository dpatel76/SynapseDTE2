#!/bin/bash

# Stop Worker service
echo "Stopping Worker container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml stop worker

if [ $? -eq 0 ]; then
    echo "✅ Worker stopped successfully"
else
    echo "❌ Failed to stop Worker"
    exit 1
fi