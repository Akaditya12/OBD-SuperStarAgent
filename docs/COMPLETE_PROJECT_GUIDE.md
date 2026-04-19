# OBD SuperStar Agent — Complete project guide (top to bottom)

**Branding:** blackNgreen · Touching Billions of Lives  
**Repo:** `Akaditya12/OBD-SuperStarAgent`  
**Typical workflow:** develop on `develop`; merge to `main` when stable.

This document is the **single narrative** of what the product is and how it works end-to-end. For deeper technical detail on any section, see **`ARCHITECTURE.md`**, **`README.md`**, and **`PROJECT.md`**.

---

## 1. What this project is

**OBD SuperStar Agent** is an AI-powered system that helps telecom / VAS teams produce **outbound dialer (OBD)** campaigns: culturally tuned **scripts** and **broadcast-quality audio** (TTS + optional background music).

You can:

- Run a **full pipeline** from product documentation → market insight → multiple script variants → evaluation → revision → voice selection → audio; or  
- Use **Script to Voice** to turn any pasted script into audio with region-aware voices.

The goal is to reduce time from product brief to **downloadable assets** (scripts + MP3/WAV) that fit a **country, telco, and language**.

---

## 2. Who uses it and what they get

| User goal | What they do | What they get |
|-----------|--------------|---------------|
| Campaign manager | Upload product doc, pick country/telco/language, optional flow | Several script variants + hook previews + final audio (main, fallbacks, closure for standard OBD; or per-step audio for **flow** campaigns) |
| Quick audio | Open Script to Voice, paste script, pick country | Previews + final audio with BGM |
| Team / ops | Login, use Dashboard | Saved campaigns, play/download, edit scripts, translate, regenerate audio |

---

## 3. High-level architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Next.js 15 frontend (React 19, Tailwind)                   │
│  /  · /login · /dashboard · /script-to-voice · /product/…   │
└───────────────────────────┬─────────────────────────────────┘
                            │  HTTP /api/* (rewrites to backend)
                            │  WebSocket /ws/* (pipeline progress)
┌───────────────────────────▼─────────────────────────────────┐
│  FastAPI backend (Python, Uvicorn)                          │
│  REST + WebSockets + background tasks                         │
└───────────────────────────┬─────────────────────────────────┘
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
   Azure OpenAI      TTS APIs           Supabase / SQLite
   (all LLM agents)  ElevenLabs,        campaigns, auth,
                     Murf, edge-tts     storage (optional)
```

- **Frontend** talks to the **backend** via same-origin `/api/...` (Next.js rewrites to `BACKEND_URL`, default `http://localhost:8000`).
- **Pipeline** runs on the server; progress is pushed over **WebSocket** (and/or polling).
- **Campaigns** persist in **Supabase** (when configured) or **SQLite** (`backend/campaigns.db`).

---

## 4. The main campaign journey (home page `/`)

### 4.1 Configure

1. Choose a **product** (preset from DB or fallback in code, or custom paste/upload).
2. Set **promotion type** (e.g. standard OBD, IVR flow, etc.).
3. Set **country**, **telco**, **language** (cascading lists).
4. Optional: **TTS engine** (Auto / ElevenLabs / Murf / edge-tts). Auto prefers ElevenLabs when configured, then fallbacks.
5. Optional: **flow config** — if the telco has rows in Supabase `flow_configs`, a dropdown appears. Selecting a flow makes the **Script Writer** produce **multi-step segments** (e.g. welcome → pack details → thanks) instead of only hook/body/CTA-style sections.
6. Optional: **cache** — reuse prior product/market analysis when inputs match.

### 4.2 Generate (pipeline running)

The backend runs an **orchestrated pipeline** (see §5). The UI shows a **progress timeline** (Product Analysis → … → Audio Production).

### 4.3 Results

- **Scripts** — multiple variants; editable; can save to session.
- **Voice selection** — rationale and alternatives from the Voice Selector agent.
- **Hook previews** — short TTS samples so the user can **pick a voice** (1 of 3 per variant pattern).
- **Generate Full Audio** — background job; UI polls until complete. Produces:
  - **Standard (non-flow):** per variant: `main`, `fallback1`, `fallback2`, `closure` (from `full_script`, `fallback_1`, `fallback_2`, `polite_closure`) when those fields exist.
  - **Flow:** one file per step, e.g. `voice1_step_welcome`, `voice1_step_pack_details`, `voice1_step_thanks`.
- **BGM** — preset styles, none, or custom upload.
- **Format** — MP3 or WAV.
- **Save** — store campaign to Dashboard (name + full `result` JSON).

---

## 5. The AI pipeline (agents, in order)

Orchestration lives in **`backend/orchestrator.py`**. Typical order:

| Step | Agent | Role |
|------|--------|------|
| 1 | **Product Analyzer** | Structured brief from product text (features, pricing, audience, etc.) |
| 2 | **Market Researcher** | Country/telco/culture, tone, competition, promotion angles (often parallel with step 1) |
| 3 | **Script Writer** | Multiple variants; standard fields **or** **flow segments** when `flow_config` is passed |
| 4 | **Eval Panel** | Multi-persona scores and revision guidance |
| 5 | **Script Writer (revision)** | Rewrites variants using eval feedback (configurable rounds) |
| 6 | **Voice Selector** | Picks primary + alternative voices and settings for the market |
| 7 | **Audio Producer** | Hook previews first; user then triggers **full audio** (phase 2) with chosen voices + BGM |

All LLM calls use **Azure OpenAI** (configured in `.env`). TTS is implemented in **`backend/agents/audio_producer.py`**.

---

## 6. Audio system (how sound is produced)

1. **Text cleaning** — strip `[tags]`, fix acronyms for speech, etc.
2. **TTS** — ElevenLabs, Murf, or edge-tts depending on user choice and keys.
3. **BGM** — optional synthesized or custom file; mixed under voice.
4. **Output** — files under `backend/outputs/{session_id}/`; optional upload to **Supabase Storage**.

**Important operational note:** Run the backend **detached** from the TTY (e.g. `./scripts/restart_app.sh` or `./scripts/start_backend.sh`) so heavy logging during bulk TTS does not suspend the process. See **`docs/RCA_ELEVENLABS_AND_SUSPENSION.md`**.

---

## 7. Flow configs (multi-step IVR-style scripts)

Stored in Supabase table **`flow_configs`**, keyed by **`account_key`** (aligned with **telco** name in the UI) and **`service_key`**.

Examples (seeded via **`scripts/seed_flow_configs.py`**):

- **BTC / Christianity** — `welcome` → `pack_details` → `thanks`.
- **Vodacom Tanzania / MagicVoice** — `welcome` (no early CTA) → `subscription_doubleconsent` → `thanks` (CTA + shortcode).

The frontend loads flows with **`GET /api/flow-configs?telco=...`**. The selected flow’s `steps` (id, purpose, max_words) drive the script writer and then **one audio file per step**.

---

## 8. Other major surfaces

### 8.1 Script to Voice (`/script-to-voice`)

Skips agents 1–5. Only **Audio Producer**: previews + final audio from pasted/uploaded text; country drives accent pool; optional **locked voice** for repeat runs.

### 8.2 Dashboard (`/dashboard`)

- Lists saved campaigns.
- Expand: play/download audio, **edit scripts** (PUT campaign scripts), **Translate to English**, **Regenerate all** or **per-variant** audio (uses saved scripts + same voice/BGM pattern).
- **Regenerate all** replaces the full audio file list (no duplicate rows from merge).

### 8.3 Login & admin

- **Auth:** Supabase JWT when configured; or legacy env login.
- **Admin:** flow/product/market seeding and management where implemented (`/admin`).

### 8.4 Product pages (`/product/[id]`)

Marketing/detail views for BNG products; content often from **Supabase `product_presets`** or fallbacks in code.

---

## 9. Data & persistence

| Data | Where |
|------|--------|
| Active pipeline result | In-memory `sessions` + `pipelines` on the backend (lost on restart) |
| Saved campaigns | Supabase `campaigns` or SQLite `campaigns.db` |
| Flow definitions | Supabase `flow_configs` |
| Product presets | Supabase `product_presets` (optional) |
| Generated audio files | `backend/outputs/` + optional Supabase Storage |
| Secrets | **`.env`** only (never commit) |

---

## 10. Key API patterns (conceptual)

- **`POST /api/generate/start`** — start pipeline; returns `session_id`.
- **`GET /api/generate/{session_id}/status`** — poll status + result when done.
- **WebSocket** — real-time progress for a session.
- **`POST /api/sessions/{id}/generate-full-audio`** — phase-2 full audio; returns `job_id`; poll **`GET /api/audio-jobs/{job_id}`**.
- **Campaigns** — `GET/POST/PUT/DELETE /api/campaigns`, regenerate audio, script updates.
- **Script-to-voice** — preview/generate job endpoints under `/api/script-to-voice/...`.

Full tables: **`README.md`** and **`ARCHITECTURE.md` §10**.

---

## 11. How to run locally

```bash
cp .env.example .env   # fill Azure OpenAI; optional TTS + Supabase
```

**Recommended:**

```bash
./scripts/restart_app.sh
```

Then open **http://localhost:3000**. Logs: `tail -f backend.log` and `tail -f frontend.log`.

**Manual:** activate venv, `pip install -r backend/requirements.txt`, `./scripts/start_backend.sh`, and in another terminal `cd frontend && npm run dev`.

---

## 12. Deploy & branches

- **Docker / Render** — see `Dockerfile`, `render.yaml`, `render-start.sh`.
- **Branching:** day-to-day on **`develop`**; promote to **`main`** when you want a stable baseline (see conversation in team docs).

---

## 13. Repository map (where to change what)

| Area | Location |
|------|----------|
| HTTP routes, sessions, jobs | `backend/main.py` |
| Pipeline order & agent wiring | `backend/orchestrator.py` |
| LLM agents | `backend/agents/*.py` |
| TTS, BGM, file naming | `backend/agents/audio_producer.py` |
| DB / Supabase helpers | `backend/database.py` |
| Main UI wizard | `frontend/src/app/page.tsx` |
| Dashboard | `frontend/src/app/dashboard/page.tsx` |
| Types | `frontend/src/lib/types.ts` |
| Proxy to backend | `frontend/next.config.ts` (`BACKEND_URL`) |
| Seed flows | `scripts/seed_flow_configs.py` |

---

## 14. Related documentation (drill-down)

| Doc | Use when you need |
|-----|-------------------|
| **`README.md`** | Quick start, env vars, endpoint cheat sheet |
| **`ARCHITECTURE.md`** | Deep dive: agents, APIs, deployment, file map |
| **`PROJECT.md`** | Continuity, new machine, where progress lives |
| **`OPS_GUIDE.md`** | Operations, debugging, ports |
| **`docs/FLOW_CONFIG_VODACOM_TANZANIA_MAGICVOICE.md`** | Vodacom Tanzania MagicVoice flow |
| **`docs/RCA_ELEVENLABS_AND_SUSPENSION.md`** | Backend suspension / TTY |
| **`docs/ADD_BNG_PRODUCT.md`** | Adding/editing products |

---

## 15. One-sentence summary

**OBD SuperStar Agent** turns product and market inputs (and optional telco-specific flows) into **many localized script variants** and **mixed TTS audio**, with a **Next.js** UI and **FastAPI** backend orchestrating **Azure OpenAI** and **commercial/free TTS**, persisting campaigns to **Supabase or SQLite**.

---

*End of complete project guide.*
