#!/bin/bash

# Stop Nginx service
echo "Stopping Nginx container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml stop nginx

if [ $? -eq 0 ]; then
    echo "✅ Nginx stopped successfully"
else
    echo "❌ Failed to stop Nginx"
    exit 1
fi