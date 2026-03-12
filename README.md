# OBD SuperStar Agent

AI-powered multi-agent system that generates culturally relevant **OBD (Outbound Dialer)** promotional scripts and broadcast-quality audio. Upload product documentation, select country/telco/language, and run the pipeline—or use **Script to Voice** to turn any pasted script into audio with region-aware voices.

**Branding:** blackNgreen · Touching Billions of Lives

---

## Current status (develop)

| Area | Status |
|------|--------|
| **Main OBD pipeline** | 6 agents orchestrated via WebSocket; cache-aware skip/rerun; session persistence (sessionStorage) |
| **Script to Voice** | Paste script → 3 voice previews (or 1 if voice locked) → final audio with BGM; **lock voice** for next scripts |
| **TTS** | **Auto** prefers **ElevenLabs** (`eleven_v3`) → Murf → edge-tts; region-based voice pools + accent priming for African/APAC/LATAM/ME |
| **Persistence** | **Supabase** when `SUPABASE_URL` + key set; else **SQLite** (`backend/campaigns.db`) |
| **Auth** | JWT via Supabase; login required when configured; sidebar hidden on login |
| **Themes** | Multiple themes; default **Light** |

---

## Features

### Main campaign flow

- **Product Analyzer** — Structured brief from product docs  
- **Market Researcher** — Country/telco/culture analysis  
- **Script Writer** — Multiple variants (hook/body/CTA/fallbacks); language override with **transliterated local language** (Latin script) when chosen  
- **Eval Panel** — Multi-persona scoring and feedback  
- **Script revision** — Optional loop based on eval  
- **Voice Selector** — LLM picks market-appropriate voice + alternatives  
- **Audio Producer** — TTS + BGM mix; hook previews (2F+1M balance for ElevenLabs pool)  
- **Smart pipeline** — Cache banner; skip/rerun steps when reusing saved analysis  
- **Voice Analytics** — Rationale, engine, accent tags per voice  

### Script to Voice (`/script-to-voice`)

- Paste or upload `.txt`; pick **country** (drives accent/voice pool), language, TTS engine (Auto / ElevenLabs / Murf / edge-tts)  
- **Speech speed** slider (e.g. 0.7x–1.3x) for ElevenLabs v3  
- **Full script** sent to TTS (no truncation)  
- **Use Same Voice for Next Script** — locks `voice_id` + label; next run uses one preview only, then generate  
- **Unlock** — back to 3-voice audition  
- Save to dashboard as campaign type `script_to_voice`  

### Dashboard & translation

- Dashboard lists campaigns; expand to play/download  
- **Translate to English** for transliterated scripts (translator prompt handles transliterated input)  

---

## Architecture

```
Product Doc + Country + Telco (+ Language)
        |
        v
[1 Product Analyzer]  → structured brief
[2 Market Researcher] → market analysis
[3 Script Writer]     → variants (+ optional revision)
[4 Eval Panel]        → scores & feedback
[5 Voice Selector]    → primary + alternative voices
[6 Audio Producer]    → TTS (ElevenLabs / Murf / edge-tts) + BGM
        |
        v
Final scripts + audio (download / save to dashboard)
```

**Script to Voice** reuses Agent 6 only: same TTS stack, country-aware pools, optional locked voice.

---

## Tech stack

| Layer | Stack |
|-------|--------|
| Backend | Python **FastAPI**, WebSockets, async TTS |
| Frontend | **Next.js 15**, React 19, Tailwind |
| LLM | **Azure OpenAI** (agents + translation) |
| TTS | **ElevenLabs** (`eleven_v3`), **Murf AI**, **edge-tts** |
| DB | **Supabase** (PostgreSQL) + optional SQLite fallback |
| Storage | Supabase Storage for audio when configured |
| Deploy | Docker + Render (`render.yaml`, `Dockerfile`) |

---

## Quick start

```bash
cd OBD_SuperStarAgent
cp .env.example .env   # edit with keys
```

**Backend**

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd frontend && npm install && npm run dev
```

Open **http://localhost:3000**

---

## Verify services (no start)

```bash
lsof -i :8000
lsof -i :3000
nc -z 127.0.0.1 8000 && echo backend up
nc -z 127.0.0.1 3000 && echo frontend up
curl -s -o /dev/null -w "backend %{http_code}\n" http://127.0.0.1:8000/docs
curl -s -o /dev/null -w "frontend %{http_code}\n" http://127.0.0.1:3000/
```

---

## API keys & env

| Variable | Required | Purpose |
|----------|----------|---------|
| `AZURE_OPENAI_*` | Yes | All LLM agents + translation |
| `ELEVENLABS_API_KEY` | Recommended | Primary TTS in Auto; best multilingual |
| `MURF_API_KEY` | Optional | Murf TTS |
| Supabase URL + service key | Optional | Campaigns + auth + storage |
| `LOGIN_USERNAME` / `LOGIN_PASSWORD` | Optional | Legacy simple auth if no Supabase |

Full list: `.env.example`

---

## API endpoints (selected)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/auth/me` | Current user |
| `WS` | `/ws/generate` | Pipeline with live progress |
| `POST` | `/api/script-to-voice/preview` | Start preview job (optional `locked_voice_id`) |
| `GET` | `/api/script-to-voice/jobs/{job_id}` | Poll job status |
| `POST` | `/api/script-to-voice/generate` | Final audio (optional `locked_voice_id`) |
| `POST` | `/api/script-to-voice/save` | Save as dashboard campaign |
| `POST` | `/api/script-to-voice/upload-bgm` | Custom BGM file |

---

## Sample products

`sample_products/` — e.g. `eva_ai_on_call.txt` for EVA AI On Call demos.

---

## Deploy

- **Render**: Blueprint / Dockerfile; set env in dashboard; health `/api/health`  
- Ephemeral disk on free tier — use Supabase for durable campaigns/audio  

See **`PROJECT.md`** for continuity, extending agents, and where data lives.

---

## Repo

**GitHub:** `Akaditya12/OBD-SuperStarAgent` — default branch workflow; `develop` used for active integration.
