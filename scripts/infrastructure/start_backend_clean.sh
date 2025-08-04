#!/bin/bash

# Kill any existing processes on port 8001
lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null

# Wait a moment for the port to be freed
sleep 2

# Start the backend with clean architecture
echo "Starting clean architecture backend on port 8001..."
cd /Users/dineshpatel/code/projects/SynapseDTE
uvicorn app.main:app --reload --port 8001 --log-level info