#!/bin/bash
# ============================================================
#  Railway Startup Script
#  Starts both backend and frontend in a single container
# ============================================================

echo "Starting OBD SuperStar Agent..."

# Start the FastAPI backend in the background
echo "Starting backend on port 8000..."
cd /app
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

# Start the Next.js frontend
echo "Starting frontend on port ${PORT:-3000}..."
cd /app/frontend-standalone
HOSTNAME=0.0.0.0 PORT=${PORT:-3000} BACKEND_URL=http://localhost:8000 node server.js &
FRONTEND_PID=$!

echo "Both services started."
echo "  Backend PID: $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"

# Wait for either process to exit
wait -n $BACKEND_PID $FRONTEND_PID

# If one exits, kill the other
echo "A service exited. Shutting down..."
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
wait
