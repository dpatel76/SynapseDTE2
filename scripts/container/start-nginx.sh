#!/bin/bash

# Start Nginx service
echo "Starting Nginx container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml up -d nginx

# Check if started
sleep 2
if curl -s http://localhost:81 >/dev/null 2>&1; then
    echo "✅ Nginx started successfully"
    echo "   Nginx available at: http://localhost:81"
else
    echo "⚠️  Nginx started but may not be fully ready yet"
fi