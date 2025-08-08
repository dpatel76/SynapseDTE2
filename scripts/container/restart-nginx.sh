#!/bin/bash

# Restart Nginx service
echo "Restarting Nginx container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml restart nginx

if [ $? -eq 0 ]; then
    echo "✅ Nginx restarted successfully"
    echo "   Nginx available at: http://localhost:81"
else
    echo "❌ Failed to restart Nginx"
    exit 1
fi