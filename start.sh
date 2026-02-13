#!/bin/bash
# ============================================================
#  OBD SuperStar Agent — One-Click Launcher
#  Usage:  double-click this file  OR  run ./start.sh
# ============================================================

# Colors for output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     OBD SuperStar Agent — Starting...    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Setup Homebrew (needed for Node on Mac)
if [ -f /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# ── Kill any existing processes on our ports ──
echo -e "${YELLOW}[1/4]${NC} Cleaning up old processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
sleep 1

# ── Start Backend ──
echo -e "${YELLOW}[2/4]${NC} Starting backend (FastAPI on port 8000)..."
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
sleep 3

# Check if backend started
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${GREEN}  ✓ Backend running (PID: $BACKEND_PID)${NC}"
else
    echo "  ✗ Backend failed to start. Check your Python environment."
    exit 1
fi

# ── Start Frontend ──
echo -e "${YELLOW}[3/4]${NC} Starting frontend (Next.js on port 3000)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"
sleep 5

# Check if frontend started
if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${GREEN}  ✓ Frontend running (PID: $FRONTEND_PID)${NC}"
else
    echo "  ✗ Frontend failed to start. Check Node.js installation."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# ── Open browser ──
echo -e "${YELLOW}[4/4]${NC} Opening browser..."
sleep 1
open http://localhost:3000

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        ✓ Everything is running!          ║${NC}"
echo -e "${GREEN}║                                          ║${NC}"
echo -e "${GREEN}║   Frontend:  http://localhost:3000        ║${NC}"
echo -e "${GREEN}║   Backend:   http://localhost:8000        ║${NC}"
echo -e "${GREEN}║                                          ║${NC}"
echo -e "${GREEN}║   Press Ctrl+C to stop everything        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── Handle Ctrl+C gracefully ──
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    echo -e "${GREEN}✓ All stopped. See you next time!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script alive (waits for Ctrl+C)
wait
