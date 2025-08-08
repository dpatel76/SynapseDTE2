#!/bin/bash

# Start Worker service
echo "Starting Worker container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml up -d worker

# Check if started
sleep 3
if docker-compose -f docker-compose.container.yml ps worker | grep -q "Up"; then
    echo "✅ Worker started successfully"
else
    echo "❌ Failed to start Worker"
    exit 1
fi