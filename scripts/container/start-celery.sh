#!/bin/bash

# Start Celery Worker service
echo "Starting Celery Worker container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml up -d celery-worker

# Check if started
sleep 3
if docker-compose -f docker-compose.container.yml ps celery-worker | grep -q "Up"; then
    echo "✅ Celery Worker started successfully"
else
    echo "❌ Failed to start Celery Worker"
    exit 1
fi