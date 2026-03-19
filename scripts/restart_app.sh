#!/usr/bin/env bash
# Full restart: stop backend + frontend, then start both with fresh config (.env).
# Backend is started detached (no TTY) so it won't suspend during "Generate Full Audio".
# Use this after changing .env or if you see "suspended (tty output)" in the terminal.

set -e
cd "$(dirname "$0")/.."
ROOT="$PWD"

echo "=== Stopping existing processes ==="

# Stop backend (port 8000)
if command -v lsof >/dev/null 2>&1; then
  BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null || true)
  if [ -n "$BACKEND_PIDS" ]; then
    echo "Stopping backend (port 8000)..."
    echo "$BACKEND_PIDS" | xargs kill -TERM 2>/dev/null || true
  else
    echo "No process on port 8000."
  fi
else
  pkill -f "uvicorn backend.main" 2>/dev/null && echo "Stopped uvicorn." || echo "No uvicorn process found."
fi

# Stop frontend (port 3000)
if command -v lsof >/dev/null 2>&1; then
  FRONTEND_PIDS=$(lsof -ti:3000 2>/dev/null || true)
  if [ -n "$FRONTEND_PIDS" ]; then
    echo "Stopping frontend (port 3000)..."
    echo "$FRONTEND_PIDS" | xargs kill -TERM 2>/dev/null || true
  else
    echo "No process on port 3000."
  fi
else
  pkill -f "next-server" 2>/dev/null && echo "Stopped Next.js." || echo "No Next.js process found."
fi

# Give processes time to exit and release ports
echo "Waiting for ports to release..."
sleep 3

# Force kill if still bound (optional)
if command -v lsof >/dev/null 2>&1; then
  for port in 8000 3000; do
    PIDS=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
      echo "Force-killing remaining process on port $port..."
      echo "$PIDS" | xargs kill -9 2>/dev/null || true
      sleep 1
    fi
  done
fi

echo ""
echo "=== Starting application (fresh .env load) ==="

# Use venv if present so uvicorn and deps are available
if [ -f "$ROOT/venv/bin/activate" ]; then
  set +e
  source "$ROOT/venv/bin/activate"
  set -e
  echo "Using venv at $ROOT/venv"
elif [ -f "$ROOT/.venv/bin/activate" ]; then
  set +e
  source "$ROOT/.venv/bin/activate"
  set -e
  echo "Using venv at $ROOT/.venv"
fi

# Start backend (python3 -m uvicorn so venv Python is used when activated)
LOG_BACKEND="${ROOT}/backend.log"
cd "$ROOT"
nohup python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 \
  </dev/null >>"$LOG_BACKEND" 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID). Logs: $LOG_BACKEND"

# Brief pause so backend can bind before frontend starts
sleep 2

# Start frontend
LOG_FRONTEND="${ROOT}/frontend.log"
nohup npm run dev --prefix frontend >>"$LOG_FRONTEND" 2>&1 </dev/null &
FRONTEND_PID=$!
echo "Frontend started (PID $FRONTEND_PID). Logs: $LOG_FRONTEND"

echo ""
echo "=== Restart complete ==="
echo "  Backend:  http://127.0.0.1:8000   (tail -f $LOG_BACKEND)"
echo "  Frontend: http://127.0.0.1:3000   (tail -f $LOG_FRONTEND)"
echo "  If login says 'Connection failed', check backend: tail -f $LOG_BACKEND"
echo "  No venv? Create one: python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
