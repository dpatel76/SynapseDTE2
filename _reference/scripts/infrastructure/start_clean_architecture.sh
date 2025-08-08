#!/bin/bash

# Start Clean Architecture Version of SynapseDTE

set -e

echo "🚀 Starting SynapseDTE with Clean Architecture..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.refactor..."
    cp .env.refactor .env
fi

# Source environment variables
source .env

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $port is already in use!"
        return 1
    fi
    return 0
}

# Check required ports
echo "🔍 Checking ports..."
PORTS=(5433 6380 8001 3001 5556)
for port in "${PORTS[@]}"; do
    if ! check_port $port; then
        echo "Please stop the service using port $port or change the port in docker-compose.clean.yml"
        exit 1
    fi
done
echo "✅ All ports are available"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.clean.yml down

# Build and start services
echo "🏗️  Building services..."
docker-compose -f docker-compose.clean.yml build

echo "🚀 Starting services..."
docker-compose -f docker-compose.clean.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."

# Check database
if docker-compose -f docker-compose.clean.yml exec -T postgres pg_isready -U synapse; then
    echo "✅ Database is ready"
else
    echo "❌ Database is not ready"
fi

# Check Redis
if docker-compose -f docker-compose.clean.yml exec -T redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check backend
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Backend API is ready"
else
    echo "⚠️  Backend API is starting..."
fi

# Show service URLs
echo ""
echo "📍 Service URLs:"
echo "   Backend API: http://localhost:8001"
echo "   Frontend: http://localhost:3001"
echo "   Flower (Celery): http://localhost:5556"
echo "   API Documentation: http://localhost:8001/docs"
echo ""

# Show logs command
echo "📋 To view logs:"
echo "   docker-compose -f docker-compose.clean.yml logs -f [service_name]"
echo ""
echo "   Services: postgres, redis, backend, celery_worker, celery_beat, flower, frontend"
echo ""

# Create test users if needed
echo "👤 Creating test users..."
docker-compose -f docker-compose.clean.yml exec -T backend python scripts/create_test_users.py || echo "⚠️  Test users might already exist"

echo ""
echo "✅ SynapseDTE Clean Architecture is running!"
echo ""
echo "🔑 Test Users:"
echo "   Tester: tester@deloitte.com / testpass123"
echo "   Test Executive: test_manager@deloitte.com / testpass123"
echo "   Data Owner: data_provider@deloitte.com / testpass123"
echo "   Data Executive: cdo@deloitte.com / testpass123"
echo ""
echo "To stop all services: docker-compose -f docker-compose.clean.yml down"