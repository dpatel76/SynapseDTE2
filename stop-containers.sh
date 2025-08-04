#!/bin/bash

# SynapseDTE Container Stop Script

set -e

echo "🛑 Stopping SynapseDTE Containerized Environment..."

# Stop all services
docker-compose -f docker-compose.container.yml down

echo "✅ All services stopped"
echo ""
echo "💡 To completely remove volumes and data, run:"
echo "   docker-compose -f docker-compose.container.yml down -v"
echo ""