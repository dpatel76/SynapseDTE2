#\!/bin/bash

# Kill any existing frontend processes
echo "Stopping existing frontend processes..."
lsof -ti:3001 | xargs kill -9 2>/dev/null

# Start frontend
echo "Starting frontend service..."
cd frontend && npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$\!

echo "Frontend service started with PID: $FRONTEND_PID"
echo "Logs are being written to frontend.log"

# Wait a bit to see if it starts successfully
sleep 10

# Check if the process is still running
if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ Frontend service started successfully\!"
    echo "🌐 Application running at http://localhost:3001"
    echo "📋 Monitor logs: tail -f frontend.log"
else
    echo "❌ Frontend service failed to start. Check frontend.log for errors."
fi
EOF < /dev/null