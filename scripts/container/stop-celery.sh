#!/bin/bash

# Stop Celery Worker service
echo "Stopping Celery Worker container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml stop celery-worker

if [ $? -eq 0 ]; then
    echo "✅ Celery Worker stopped successfully"
else
    echo "❌ Failed to stop Celery Worker"
    exit 1
fi