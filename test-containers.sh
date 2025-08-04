#!/bin/bash

# SynapseDTE Container Test Script
# This script tests all containerized services

set -e

echo "🧪 Testing SynapseDTE Containerized Services..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_service() {
    local name=$1
    local url=$2
    local expected_code=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response, expected $expected_code)"
        return 1
    fi
}

# Test database connection
test_database() {
    echo -n "Testing PostgreSQL connection... "
    
    if docker-compose -f docker-compose.container.yml exec -T postgres pg_isready -U synapse_user > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        
        # Check if tables exist
        echo -n "Checking database tables... "
        table_count=$(docker-compose -f docker-compose.container.yml exec -T postgres psql -U synapse_user -d synapse_dt -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
        
        if [ "$table_count" -gt "0" ]; then
            echo -e "${GREEN}✓ OK${NC} ($table_count tables found)"
        else
            echo -e "${RED}✗ FAILED${NC} (No tables found)"
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
    fi
}

# Test Redis connection
test_redis() {
    echo -n "Testing Redis connection... "
    
    if docker-compose -f docker-compose.container.yml exec -T redis redis-cli --no-auth-warning -a "${REDIS_PASSWORD:-synapse_redis_password}" ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ FAILED${NC}"
    fi
}

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run tests
echo ""
echo "📋 Service Health Checks:"
echo "------------------------"

# Test each service
test_service "Frontend" "http://localhost:3001" "200"
test_service "Backend Health" "http://localhost:8001/api/v1/health" "200"
test_service "Backend Docs" "http://localhost:8001/docs" "200"
test_service "Temporal UI" "http://localhost:8089" "200"

if [ -n "${NGINX_HTTP_PORT}" ]; then
    test_service "Nginx Proxy" "http://localhost:${NGINX_HTTP_PORT:-81}/health" "200"
fi

echo ""
echo "📋 Database Checks:"
echo "------------------"
test_database

echo ""
echo "📋 Cache Checks:"
echo "---------------"
test_redis

# Test API authentication
echo ""
echo "📋 API Authentication Test:"
echo "--------------------------"
echo -n "Testing login endpoint... "

login_response=$(curl -s -X POST "http://localhost:8001/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=tester@example.com&password=password123" \
    -w "\n%{http_code}")

http_code=$(echo "$login_response" | tail -n1)
response_body=$(echo "$login_response" | head -n-1)

if [ "$http_code" = "200" ] && echo "$response_body" | grep -q "access_token"; then
    echo -e "${GREEN}✓ OK${NC} (Login successful)"
    
    # Extract token for further tests
    token=$(echo "$response_body" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    # Test authenticated endpoint
    echo -n "Testing authenticated endpoint... "
    auth_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $token" \
        "http://localhost:8001/api/v1/users/me")
    
    if [ "$auth_response" = "200" ]; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $auth_response)"
    fi
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
fi

# Check Docker container health
echo ""
echo "📋 Container Health Status:"
echo "-------------------------"
docker-compose -f docker-compose.container.yml ps

# Summary
echo ""
echo "🎯 Test Summary"
echo "=============="
echo ""
echo "If all tests passed, your containerized SynapseDTE is ready to use!"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:3001"
echo "  API Docs: http://localhost:8001/docs"
echo ""