#!/bin/bash

# Stop PostgreSQL service
echo "Stopping PostgreSQL container..."
cd /Users/dineshpatel/code/projects/SynapseDTE2
docker-compose -f docker-compose.container.yml stop postgres

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL stopped successfully"
else
    echo "❌ Failed to stop PostgreSQL"
    exit 1
fi