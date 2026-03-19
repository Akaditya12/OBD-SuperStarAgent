#!/usr/bin/env bash
# Start backend in background with no TTY attachment so it never suspends.
# Use this or restart_app.sh — do NOT run uvicorn in the foreground without
# redirecting output, or the process can suspend during "Generate Full Audio".

set -e
cd "$(dirname "$0")/.."
ROOT="$PWD"
LOG="${ROOT}/backend.log"

# Venv so uvicorn and deps are available
if [ -f "$ROOT/venv/bin/activate" ]; then
  source "$ROOT/venv/bin/activate" 2>/dev/null || true
elif [ -f "$ROOT/.venv/bin/activate" ]; then
  source "$ROOT/.venv/bin/activate" 2>/dev/null || true
fi

# Fully detach: stdin closed, stdout/stderr to file. No TTY = no suspension.
nohup python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 \
  </dev/null >>"$LOG" 2>&1 &

echo "Backend starting (PID $!). Logs: $LOG"
echo "  tail -f $LOG   # watch live"
