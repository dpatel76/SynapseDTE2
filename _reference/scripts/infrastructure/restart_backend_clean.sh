#!/bin/bash

# Kill any existing uvicorn processes
echo "Stopping existing backend processes..."
pkill -f "uvicorn app.main:app" || true
pkill -f "uvicorn app.main_clean:app" || true

# Wait a moment to ensure processes are stopped
sleep 2

# Start the clean architecture backend with logs redirected
echo "Starting clean architecture backend service..."
uvicorn app.main_clean:app --host 0.0.0.0 --port 8001 --log-level info > backend.log 2>&1 &

# Get the process ID
BACKEND_PID=$!

# Save the PID to a file for future reference
echo $BACKEND_PID > backend.pid

echo "Clean architecture backend service started with PID: $BACKEND_PID"
echo "Logs are being written to backend.log"

# Wait a moment and verify the server started successfully
sleep 3
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Clean architecture backend service started successfully!"
    echo "🌐 Server running at http://localhost:8001"
    echo "📋 Monitor logs: tail -f backend.log"
else
    echo "❌ Backend service failed to start. Check backend.log for errors."
    exit 1
fi