#!/bin/bash

# SynapseDTE Container Startup Script
# This script starts all services with proper configuration

set -e

echo "🚀 Starting SynapseDTE Containerized Environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.container .env
    echo "⚠️  Please edit .env file to set your API keys and other configurations"
    echo "   Then run this script again."
    exit 1
fi

# Source environment variables
set -a
source .env
set +a

# Check required environment variables
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY not set in .env file"
    echo "   Please set your Anthropic API key before starting containers"
    exit 1
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p uploads logs

# Pull latest images
echo "🐳 Pulling latest Docker images..."
docker-compose -f docker-compose.container.yml pull

# Build custom images
echo "🔨 Building custom Docker images..."
docker-compose -f docker-compose.container.yml build

# Start services
echo "🎯 Starting services..."
docker-compose -f docker-compose.container.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."

# Function to check service health
check_service() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.container.yml ps $service | grep -q "healthy"; then
            echo "✅ $service is healthy"
            return 0
        fi
        echo "   Waiting for $service... ($attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service failed to become healthy"
    return 1
}

# Check each service
check_service postgres
check_service redis
check_service backend
check_service temporal

# Display service URLs
echo ""
echo "🎉 SynapseDTE is ready!"
echo ""
echo "📍 Service URLs:"
echo "   Frontend:     http://localhost:${FRONTEND_PORT:-3001}"
echo "   Backend API:  http://localhost:${BACKEND_PORT:-8001}/api/v1"
echo "   Temporal UI:  http://localhost:${TEMPORAL_UI_PORT:-8089}"
echo "   Nginx Proxy:  http://localhost:${NGINX_HTTP_PORT:-81}"
echo ""
echo "🔐 Default test credentials:"
echo "   Email:    tester@example.com"
echo "   Password: password123"
echo ""
echo "📋 Useful commands:"
echo "   View logs:    docker-compose -f docker-compose.container.yml logs -f [service]"
echo "   Stop all:     docker-compose -f docker-compose.container.yml down"
echo "   Clean all:    docker-compose -f docker-compose.container.yml down -v"
echo ""