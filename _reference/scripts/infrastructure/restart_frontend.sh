#!/bin/bash

# Kill any existing npm processes
echo "Stopping existing frontend processes..."
pkill -f "node.*react-scripts start" || true

# Wait a moment to ensure processes are stopped
sleep 2

# Start the frontend with logs redirected
echo "Starting frontend service..."
PORT=3001 npm start > frontend.log 2>&1 &

# Get the process ID
FRONTEND_PID=$!

# Save the PID to a file for future reference
echo $FRONTEND_PID > frontend.pid

echo "Frontend service started with PID: $FRONTEND_PID"
echo "Logs are being written to frontend.log" 