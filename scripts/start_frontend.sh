#!/usr/bin/env bash
# Start frontend in background with no TTY attachment.
# Logs go to frontend.log in project root.

set -e
cd "$(dirname "$0")/.."
LOG="${PWD}/frontend.log"

# Fully detach: stdin closed, stdout/stderr to file.
nohup npm run dev --prefix frontend >>"$LOG" 2>&1 </dev/null &

echo "Frontend starting (PID $!). Logs: $LOG"
echo "  tail -f $LOG   # watch live"
