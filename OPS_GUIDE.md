# OBD SuperStar Agent -- Operations Guide

Complete reference for running, restarting, debugging, and maintaining the application locally.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [First-Time Setup](#2-first-time-setup)
3. [Starting the Application](#3-starting-the-application)
4. [Stopping & Restarting](#4-stopping--restarting)
5. [Port Management](#5-port-management)
6. [Common Errors & Fixes](#6-common-errors--fixes)
7. [Environment Variables](#7-environment-variables)
8. [Database Operations](#8-database-operations)
9. [Git & Branch Management](#9-git--branch-management)
10. [Logs & Debugging](#10-logs--debugging)
11. [Dependency Management](#11-dependency-management)
12. [Audio Output & Cleanup](#12-audio-output--cleanup)
13. [Frontend Build & Cache](#13-frontend-build--cache)
14. [Health Checks](#14-health-checks)
15. [Quick Reference Card](#15-quick-reference-card)

---

## 1. Prerequisites

| Tool       | Minimum Version | Check Command            |
|------------|-----------------|--------------------------|
| Python     | 3.9+            | `python3 --version`      |
| Node.js    | 18+             | `node --version`         |
| npm        | 9+              | `npm --version`          |
| ffmpeg     | any             | `ffmpeg -version`        |
| Git        | 2.x             | `git --version`          |
| GitHub CLI | 2.x (optional)  | `gh --version`           |

**Note**: On macOS, the command is `python3`, not `python`.

Install ffmpeg (required for audio mixing):
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

---

## 2. First-Time Setup

### Clone the repository
```bash
git clone https://github.com/AdiKrishnav/OBD_SuperStarAgent.git
cd OBD_SuperStarAgent
```

### Backend setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt
```

### Frontend setup
```bash
cd frontend
npm install
cd ..
```

### Environment file
```bash
cp .env.example .env
# Edit .env and fill in your API keys (see Section 7)
```

---

## 3. Starting the Application

You need **two terminals** -- one for the backend, one for the frontend.

### Terminal 1: Backend
```bash
cd /Users/adityakrishnav/Desktop/CURSOR_PROJ/OBD_SuperStarAgent
source venv/bin/activate
python3 -m uvicorn backend.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Terminal 2: Frontend
```bash
cd /Users/adityakrishnav/Desktop/CURSOR_PROJ/OBD_SuperStarAgent/frontend
npm run dev
```

Expected output:
```
▲ Next.js 15.5.12
- Local:   http://localhost:3000
✓ Ready in Xs
```

### Open the app
Go to **http://localhost:3000** in your browser.

---

## 4. Stopping & Restarting

### Stop a server
In the terminal where it's running, press `Ctrl+C`.

### Restart backend only
```bash
# In the backend terminal:
# Ctrl+C to stop, then:
python3 -m uvicorn backend.main:app --reload --port 8000
```

### Restart frontend only
```bash
# In the frontend terminal:
# Ctrl+C to stop, then:
npm run dev
```

### Full restart (both)
```bash
# Stop both with Ctrl+C in each terminal, then start each again
```

### Force kill if Ctrl+C doesn't work
```bash
# Kill backend (port 8000)
lsof -ti:8000 | xargs kill -9

# Kill frontend (port 3000)
lsof -ti:3000 | xargs kill -9
```

---

## 5. Port Management

### Check what's using a port
```bash
lsof -i:8000    # Check backend port
lsof -i:3000    # Check frontend port
```

### Free a port
```bash
lsof -ti:8000 | xargs kill -9    # Free port 8000
lsof -ti:3000 | xargs kill -9    # Free port 3000
```

### Use a different port
```bash
# Backend on port 8080
python3 -m uvicorn backend.main:app --reload --port 8080

# Frontend on port 3001
npx next dev -p 3001
```

If you change the backend port, update the frontend proxy in `frontend/next.config.ts`.

---

## 6. Common Errors & Fixes

### `zsh: command not found: python`
Use `python3` instead of `python` on macOS.

### `ModuleNotFoundError: No module named 'backend'`
You must run the backend from the **project root**, not from inside `backend/`:
```bash
cd /Users/adityakrishnav/Desktop/CURSOR_PROJ/OBD_SuperStarAgent
python3 -m uvicorn backend.main:app --reload --port 8000
```

### `Address already in use` (port conflict)
```bash
# Find and kill the process using the port
lsof -ti:8000 | xargs kill -9   # for backend
lsof -ti:3000 | xargs kill -9   # for frontend
# Then restart
```

### `__webpack_modules__[moduleId] is not a function`
Stale Next.js cache. Fix:
```bash
rm -rf frontend/.next
# Then restart the frontend:
cd frontend && npm run dev
```

### `CORS errors in browser console`
The backend allows `localhost:3000` and `localhost:8000` by default. If you're using a different port, update `ALLOWED_ORIGINS` in `.env`:
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### `pydub / ffmpeg errors during audio generation`
```bash
# Verify ffmpeg is installed
ffmpeg -version

# If not installed:
brew install ffmpeg    # macOS
```

### `openssl / LibreSSL warning`
```
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+
```
This is a warning, not an error. The app works fine. To suppress, you can ignore it.

### `supabase / bcrypt ImportError`
If you don't have Supabase configured, the app falls back to SQLite automatically. To install the optional packages:
```bash
source venv/bin/activate
pip install supabase bcrypt
```

### `No scripts available` error during audio generation
The backend session was lost (common after a `--reload` restart). Generate a new campaign from scratch.

### Frontend shows blank page / loading spinner forever
1. Check the backend is running: `curl http://localhost:8000/api/health`
2. Check the browser console (F12 > Console) for errors
3. Clear cache: `rm -rf frontend/.next && cd frontend && npm run dev`

### Login redirect loop
1. Check if auth is enabled: `curl http://localhost:8000/api/auth/me`
2. If using local dev without Supabase, set in `.env`:
   ```
   LOGIN_USERNAME=admin
   LOGIN_PASSWORD=admin123
   ```
3. Restart the backend

---

## 7. Environment Variables

All keys go in the `.env` file at the project root.

### Required (LLM)
```bash
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-5.1-chat
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

### TTS Engines (at least one recommended)
```bash
MURF_API_KEY=your-murf-key           # Primary TTS
ELEVENLABS_API_KEY=your-eleven-key   # Fallback TTS
# If neither is set, free edge-tts is used automatically
```

### Authentication
```bash
# Option A: Supabase (production multi-user)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
JWT_SECRET=your-secret-key

# Option B: Simple local auth (single user)
LOGIN_USERNAME=admin
LOGIN_PASSWORD=yourpassword
```

### Verify keys are loaded
```bash
# From project root, with venv activated:
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print('Azure:', 'OK' if os.getenv('AZURE_OPENAI_API_KEY') else 'MISSING'); print('Murf:', 'OK' if os.getenv('MURF_API_KEY') else 'MISSING'); print('ElevenLabs:', 'OK' if os.getenv('ELEVENLABS_API_KEY') else 'MISSING'); print('Supabase:', 'OK' if os.getenv('SUPABASE_URL') else 'MISSING')"
```

---

## 8. Database Operations

### SQLite (local development)
The local database is at `backend/campaigns.db`. Created automatically on first run.

```bash
# View campaigns
python3 -c "import sqlite3; conn = sqlite3.connect('backend/campaigns.db'); print([r[0] for r in conn.execute('SELECT name FROM campaigns').fetchall()])"

# Reset database (delete all campaigns)
rm backend/campaigns.db
# It will be recreated on next backend start
```

### Supabase (production)
When `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set, all data goes to Supabase PostgreSQL.

```bash
# Create admin user
python3 scripts/create_admin.py

# View schema
cat scripts/supabase_schema.sql
```

---

## 9. Git & Branch Management

### Current branch status
```bash
git status
git branch -a
git log --oneline -10
```

### Branch strategy
```
main      -- stable, production-ready
develop   -- integration branch for testing
feature/* -- individual feature branches
```

### Safe workflow for changes
```bash
# 1. Create a feature branch
git checkout develop
git pull origin develop
git checkout -b feature/my-change

# 2. Make changes and commit
git add -A
git commit -m "description of change"

# 3. Push to remote
git push -u origin feature/my-change

# 4. Create PR to develop
gh pr create --base develop --title "My change" --body "Description"

# 5. After testing, merge develop into main
git checkout main
git merge develop
git push origin main
```

### Tag a stable version (before risky changes)
```bash
git tag -a v1.1-stable -m "Before XYZ change"
git push origin v1.1-stable
```

### Rollback to a tag
```bash
git checkout v1.0-stable
```

### Discard all local changes
```bash
git checkout -- .          # Discard file changes
git clean -fd              # Remove untracked files
```

---

## 10. Logs & Debugging

### Backend logs
The backend logs to the terminal where it runs. Look for:
- `INFO` -- normal operations
- `WARNING` -- non-critical issues (e.g., TTS fallback)
- `ERROR` -- failures that need attention

### Increase log verbosity
```bash
python3 -m uvicorn backend.main:app --reload --port 8000 --log-level debug
```

### Check API health
```bash
curl http://localhost:8000/api/health
# Expected: {"status": "ok", ...}
```

### Check auth status
```bash
curl http://localhost:8000/api/auth/me
```

### Test a specific endpoint
```bash
# List campaigns
curl http://localhost:8000/api/campaigns

# Check session
curl http://localhost:8000/api/sessions/SESSION_ID
```

### Frontend debugging
1. Open browser DevTools: `F12` or `Cmd+Option+I`
2. **Console** tab: JavaScript errors
3. **Network** tab: API call failures (look for red rows)
4. **Application** tab: Check localStorage for `obd_active_session`

### TypeScript type check (no build needed)
```bash
cd frontend
npx tsc --noEmit
```

---

## 11. Dependency Management

### Add a Python package
```bash
source venv/bin/activate
pip install package-name
pip freeze | grep package-name >> backend/requirements.txt
```

### Add a frontend package
```bash
cd frontend
npm install package-name
```

### Update all Python dependencies
```bash
source venv/bin/activate
pip install --upgrade -r backend/requirements.txt
```

### Update all frontend dependencies
```bash
cd frontend
npm update
```

### Rebuild from scratch
```bash
# Backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Frontend
rm -rf frontend/node_modules frontend/.next frontend/package-lock.json
cd frontend && npm install
```

---

## 12. Audio Output & Cleanup

Generated audio files are stored in `backend/outputs/SESSION_ID/`.

### List generated audio
```bash
ls -la backend/outputs/
```

### Play an audio file (macOS)
```bash
afplay backend/outputs/SESSION_ID/variant_1_voice1_main.mp3
```

### Clean up all audio files
```bash
rm -rf backend/outputs/*
```

### Check disk usage
```bash
du -sh backend/outputs/
```

---

## 13. Frontend Build & Cache

### Clear Next.js cache (fixes most frontend issues)
```bash
rm -rf frontend/.next
```

### Production build (test before deploying)
```bash
cd frontend
npm run build
npm start    # Serves production build on port 3000
```

### Clear everything and rebuild
```bash
rm -rf frontend/.next frontend/node_modules/.cache
cd frontend && npm run dev
```

---

## 14. Health Checks

Quick commands to verify everything is working:

```bash
# Backend alive?
curl -s http://localhost:8000/api/health | python3 -m json.tool

# Frontend alive?
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000

# Auth working?
curl -s http://localhost:8000/api/auth/me | python3 -m json.tool

# Database connected?
curl -s http://localhost:8000/api/campaigns | python3 -m json.tool

# Ports in use?
lsof -i:8000,3000
```

---

## 15. Quick Reference Card

| Action                        | Command                                                              |
|-------------------------------|----------------------------------------------------------------------|
| **Start backend**             | `source venv/bin/activate && python3 -m uvicorn backend.main:app --reload --port 8000` |
| **Start frontend**            | `cd frontend && npm run dev`                                         |
| **Stop a server**             | `Ctrl+C` in its terminal                                            |
| **Kill port 8000**            | `lsof -ti:8000 \| xargs kill -9`                                    |
| **Kill port 3000**            | `lsof -ti:3000 \| xargs kill -9`                                    |
| **Clear frontend cache**      | `rm -rf frontend/.next`                                              |
| **Type check frontend**       | `cd frontend && npx tsc --noEmit`                                    |
| **Check backend health**      | `curl http://localhost:8000/api/health`                               |
| **Check API keys**            | `python3 -c "from dotenv import load_dotenv; ..."`  (see Section 7)  |
| **View git status**           | `git status && git log --oneline -5`                                 |
| **Reset local DB**            | `rm backend/campaigns.db`                                            |
| **Clean audio files**         | `rm -rf backend/outputs/*`                                           |
| **Full rebuild (backend)**    | `rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt` |
| **Full rebuild (frontend)**   | `rm -rf frontend/node_modules frontend/.next && cd frontend && npm install` |
| **Open app**                  | http://localhost:3000                                                |
| **Dashboard**                 | http://localhost:3000/dashboard                                      |
| **Admin panel**               | http://localhost:3000/admin (admin role only)                        |
