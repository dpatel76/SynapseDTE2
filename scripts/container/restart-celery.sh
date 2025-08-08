#!/bin/bash

# Restart Celery Worker service
echo "Restarting Celery Worker container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml restart celery-worker

if [ $? -eq 0 ]; then
    echo "✅ Celery Worker restarted successfully"
else
    echo "❌ Failed to restart Celery Worker"
    exit 1
fi