#!/bin/sh
# Health check script for backend service

# Try to reach the health endpoint
response=$(curl -s -f http://localhost:8000/api/v1/health || echo "FAIL")

if [ "$response" = "FAIL" ]; then
    exit 1
fi

# Check if response contains "healthy" or similar positive indicator
if echo "$response" | grep -q "ok\|healthy\|true"; then
    exit 0
else
    exit 1
fi