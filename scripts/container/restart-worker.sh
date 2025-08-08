#!/bin/bash

# Restart Worker service
echo "Restarting Worker container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml restart worker

if [ $? -eq 0 ]; then
    echo "✅ Worker restarted successfully"
else
    echo "❌ Failed to restart Worker"
    exit 1
fi