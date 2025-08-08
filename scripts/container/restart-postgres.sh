#!/bin/bash

# Restart PostgreSQL service
echo "Restarting PostgreSQL container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml restart postgres

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL restarted successfully"
else
    echo "❌ Failed to restart PostgreSQL"
    exit 1
fi