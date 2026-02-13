#!/bin/bash
# ============================================================
#  Render.com Startup Script
#  Starts both backend (FastAPI) and frontend (Next.js)
#  Render exposes $PORT -- we run frontend on $PORT, backend on 8000
# ============================================================

set -e

FRONTEND_PORT="${PORT:-3000}"
BACKEND_PORT=8000

echo "=== OBD SuperStar Agent ==="
echo "Frontend port: $FRONTEND_PORT"
echo "Backend port:  $BACKEND_PORT"

# Start the FastAPI backend in the background
echo "Starting backend..."
cd /app
uvicorn backend.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# Start the Next.js frontend (Render routes traffic to $PORT)
echo "Starting frontend..."
cd /app/frontend-standalone
HOSTNAME=0.0.0.0 PORT=$FRONTEND_PORT BACKEND_URL=http://localhost:$BACKEND_PORT node server.js &
FRONTEND_PID=$!

echo "Both services started (backend=$BACKEND_PID, frontend=$FRONTEND_PID)"

# Handle shutdown
cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait
}
trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait -n $BACKEND_PID $FRONTEND_PID
echo "A service exited unexpectedly. Shutting down..."
cleanup
