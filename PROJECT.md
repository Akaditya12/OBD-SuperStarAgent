# OBD SuperStar Agent — Project continuity & expansion

This doc is for you (or your team) to keep the project running and growing **even if you change machines, lose Cursor access, or switch accounts**. Everything you need is in this repo.

---

## Where is our progress saved?

| What | Where | Survives account/machine change? |
|------|--------|----------------------------------|
| **All source code** | GitHub: `Akaditya12/OBD-SuperStarAgent` | ✅ Yes. Clone the repo anytime. |
| **API keys / secrets** | Your machine: `.env` (never committed) | ❌ No. You must re-create `.env` from `.env.example` on a new machine. |
| **Campaigns & scripts (dashboard)** | **Local only**: SQLite `backend/campaigns.db` + `backend/outputs/` | ❌ On Render, disk is ephemeral — data is lost on redeploy. Locally it persists until you delete the files. |

So: **code and docs are safe on GitHub.** Secrets and runtime data you need to recreate or accept as ephemeral on Render.

---

## How the project works (high level)

1. **Frontend** (Next.js, `frontend/`) — Upload product doc, pick country/telco/language, start pipeline. Shows progress via WebSocket, then results + dashboard.
2. **Backend** (FastAPI, `backend/main.py`) — REST + WebSocket API. Runs the pipeline: product analysis → market research → script writing (with optional language override) → eval panel → script revision → voice selection → audio production (TTS).
3. **Agents** (`backend/agents/`) — Each step is an agent: `product_analyzer`, `market_researcher`, `script_writer`, `evaluator`, `voice_selector`, `audio_producer`. Orchestration is in `backend/orchestrator.py`.
4. **TTS** — Priority: Murf AI (if `MURF_API_KEY` set) → ElevenLabs (if key + credits) → edge-tts (free). Audio is mixed with BGM and saved under `backend/outputs/`.
5. **Auth** — Optional. If `LOGIN_USERNAME` and `LOGIN_PASSWORD` are set (e.g. on Render), login is required; otherwise the app is open.
6. **Dashboard** — Campaign list comes from SQLite (`campaigns.db`). Saving a campaign stores full result JSON there. Comments and collaboration use the same DB.

---

## How to run it again (new machine / no Cursor)

1. **Clone the repo**
   ```bash
   git clone https://github.com/Akaditya12/OBD-SuperStarAgent.git
   cd OBD-SuperStarAgent
   ```
2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env: add Azure OpenAI keys, and optionally MURF_API_KEY or ELEVENLABS_API_KEY
   ```
3. **Backend**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. **Frontend** (new terminal)
   ```bash
   cd frontend && npm install && npm run dev
   ```
5. Open **http://localhost:3000**

No Cursor or special account needed — any editor (VS Code, etc.) works.

---

## How to deploy to Render

- Repo is already set up for Render: `render.yaml` + root `Dockerfile` + `render-start.sh`.
- In Render: connect `Akaditya12/OBD-SuperStarAgent`, use the blueprint (or add a Web Service with the repo’s Dockerfile and start command).
- Set **Environment** variables in the Render dashboard (see README for the list). No need to commit secrets — they’re set in the UI.
- Deploy = build from the branch you push to (e.g. `main`). Suspend when not in use to avoid charges; resume when needed.

---

## How to keep expanding

- **Codebase layout**: `backend/agents/` for pipeline logic, `backend/main.py` for routes and WebSockets, `frontend/src/` for UI. Types and shared structures: `frontend/src/lib/types.ts`, backend Pydantic in the API.
- **Adding a new agent**: Add a module under `backend/agents/`, then call it from `backend/orchestrator.py` in the right place in the pipeline.
- **Changing TTS**: Edit `backend/agents/audio_producer.py` (engine selection, voice maps, and text cleaning for TTS).
- **Changing prompts**: Script content and style come from `backend/agents/script_writer.py`; evaluation from the evaluator agent; product/market from their respective agents.
- **UI changes**: React components in `frontend/src/components/`, pages in `frontend/src/app/`. API calls and WebSocket URL come from `BACKEND_URL` and the rewrites in `frontend/next.config.ts`.

Whenever you make progress you want to keep: **commit and push to GitHub.** That’s your single source of truth. This project will keep working and can keep expanding as long as the repo is available and you have the API keys and env setup.
