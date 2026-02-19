# OBD SuperStar Agent -- Complete Technical Architecture

**Version:** 2.0 | **Last updated:** February 2026
**Repository:** [github.com/Akaditya12/OBD-SuperStarAgent](https://github.com/Akaditya12/OBD-SuperStarAgent)

---

## Table of Contents

1. [What This System Does](#1-what-this-system-does)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Technology Stack](#3-technology-stack)
4. [The 7-Step AI Pipeline](#4-the-7-step-ai-pipeline)
5. [Backend Deep Dive](#5-backend-deep-dive)
6. [Frontend Deep Dive](#6-frontend-deep-dive)
7. [Multi-Voice Audio System](#7-multi-voice-audio-system)
8. [Authentication & Collaboration](#8-authentication--collaboration)
9. [Data Storage & Persistence](#9-data-storage--persistence)
10. [API Reference](#10-api-reference)
11. [Deployment](#11-deployment)
12. [Configuration Reference](#12-configuration-reference)
13. [File Map](#13-file-map)

---

## 1. What This System Does

OBD SuperStar Agent is an AI-powered platform that generates **outbound dialer (OBD) promotional campaigns** end-to-end. You upload a product document, pick a target country and telco, and the system:

1. Analyzes the product to extract features, pricing, and USPs
2. Researches the target market -- demographics, cultural nuances, language, consumer psychology
3. Writes 5 unique script variants (hook + body + CTA + fallbacks + closure)
4. Evaluates scripts with a 10-persona AI panel (psychologist, copywriter, cultural consultant, etc.)
5. Revises scripts based on panel feedback
6. Selects optimal TTS voices for the market
7. Generates broadcast-ready audio files with 3 different voices per variant, mixed with background music

The output is a set of downloadable MP3 files ready for telecom OBD systems.

---

## 2. High-Level Architecture

```
                     +-------------------+
                     |   Next.js 15 UI   |
                     |  (React 19 + TW)  |
                     +--------+----------+
                              |
                   REST + WebSocket (real-time progress)
                              |
                     +--------v----------+
                     |  FastAPI Backend   |
                     |  (Python 3.11)    |
                     +--------+----------+
                              |
              +---------------+---------------+
              |                               |
     +--------v--------+            +--------v--------+
     | Pipeline         |            | Data Layer       |
     | Orchestrator     |            | SQLite + Files   |
     +--------+---------+            +-----------------+
              |
    +---------+---------+---------+---------+---------+---------+
    |         |         |         |         |         |         |
  Agent1   Agent2    Agent3    Agent4    Agent5    Agent6
  Product  Market    Script    Eval     Voice     Audio
  Analyzer Research  Writer    Panel    Selector  Producer
    |         |         |         |         |         |
    +----+----+    Azure OpenAI   +----+----+    TTS APIs
         |         (GPT-5.1)           |      (Murf/ElevenLabs/
         |                             |       edge-tts)
         +-----------------------------+
```

**Data flow:**
1. Frontend sends product text + country + telco + language + TTS engine choice
2. Backend orchestrator runs 7 agents sequentially (steps 1-2 run in parallel)
3. Each agent calls Azure OpenAI, gets structured JSON back
4. Audio producer calls TTS API (Murf AI, ElevenLabs, or edge-tts) for each script
5. Results stream back to frontend via WebSocket in real-time
6. User can edit scripts and regenerate audio for individual variants

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15, React 19, Tailwind CSS | UI, routing, SSR |
| **Backend** | Python 3.11, FastAPI, Uvicorn | REST API, WebSocket, pipeline |
| **LLM** | Azure OpenAI (GPT-5.1-chat) | All 6 AI agents |
| **TTS (Primary)** | Murf AI (Gen2) | Premium voice synthesis |
| **TTS (Fallback 1)** | ElevenLabs (Multilingual v2) | Alternative premium TTS |
| **TTS (Fallback 2)** | edge-tts (Microsoft) | Free, unlimited TTS |
| **Audio Processing** | pydub + ffmpeg | BGM mixing, format conversion |
| **Database** | SQLite | Campaign persistence |
| **Auth** | JWT (PyJWT) | Optional team authentication |
| **Deployment** | Docker, Render.com | Combined frontend+backend container |

---

## 4. The 7-Step AI Pipeline

### Step 1: Product Analysis (`ProductAnalyzerAgent`)

**Input:** Raw product documentation text (up to 50,000 chars)
**Output:** Structured product brief

The agent extracts:
- Product name, type, description
- Key features and USPs
- Pricing model and price points
- Target audience
- Value propositions
- Subscription mechanism (DTMF, SMS, USSD)
- Technical notes

**LLM prompt approach:** System prompt positions the AI as a "telecom VAS product analyst." User prompt contains the raw product text. Output is strict JSON.

### Step 2: Market Research (`MarketResearcherAgent`)

**Input:** Country, telco, product brief summary
**Output:** Comprehensive market analysis

Runs **in parallel** with Step 1. Produces:
- Market overview (population, mobile penetration, languages, ARPU)
- Cultural insights (communication style, values, taboos, humor, trust signals)
- Current affairs (trending topics, economic climate)
- Target audience psyche (pain points, aspirations, spending behavior)
- Competitive landscape
- Promotion recommendations (best call time, tone, emotional triggers, local references)

### Step 3: Script Writing (`ScriptWriterAgent`)

**Input:** Product brief + market analysis + optional language override
**Output:** 5 unique script variants

Each variant contains:
- **Hook** (0-5s): Attention-grabbing opener using cultural references
- **Body** (5-23s): Compelling product pitch focused on benefits
- **CTA** (23-30s): Clear DTMF-based call to action ("Press 1 to activate")
- **Fallback 1**: Urgency-based follow-up if no response
- **Fallback 2**: Psychological persuasion techniques
- **Polite closure**: Graceful exit
- **Full script**: Complete concatenated version for TTS
- Metadata: word count, estimated duration, audio tags used

Scripts are generated in batches (2-3 per LLM call) with different creative angles. If a language override is specified (e.g., Tamil), a "CRITICAL LANGUAGE REQUIREMENT" is injected into the prompt.

### Step 4: Evaluation Panel (`EvalPanelAgent`)

**Input:** Scripts + product brief + market analysis
**Output:** Scores, critiques, and revision instructions

10 AI evaluator personas score each variant:

| # | Persona | Focus |
|---|---------|-------|
| 1 | Radio Jingle Writer | Sonic appeal, rhythm, memorability |
| 2 | Consumer Psychologist | Emotional triggers, decision-making |
| 3 | Behavioral Economist | Pricing framing, loss aversion |
| 4 | Direct Response Copywriter | CTA strength, urgency |
| 5 | Brand Storytelling Specialist | Emotional connection, narrative |
| 6 | Local Market Expert | Cultural accuracy, language naturalness |
| 7 | Persuasion Expert | NLP, scarcity, social proof |
| 8 | Telco Marketing Director | OBD effectiveness, pickup rates |
| 9 | Voice UX Designer | Pacing, DTMF clarity, audio tags |
| 10 | Cultural Consultant | Cultural norms, taboos, references |

Output includes per-variant scores, strengths/weaknesses, and a consensus with ranking, critical improvements, and revision instructions.

### Step 5: Script Revision (`ScriptWriterAgent` again)

**Input:** Original scripts + evaluation feedback
**Output:** Revised scripts

The script writer receives the panel's revision instructions and rewrites all 5 variants. This loop runs `EVAL_FEEDBACK_ROUNDS` times (default: 1).

### Step 6: Voice Selection (`VoiceSelectorAgent`)

**Input:** Final scripts + market analysis + country + language
**Output:** Voice configuration and rationale

The agent:
1. Fetches available voices from ElevenLabs API
2. Analyzes scripts, market, and cultural context
3. Recommends a primary voice with settings (stability, similarity boost, style, speed)
4. Suggests alternative voices with reasons
5. Provides production notes

### Step 7: Audio Production (`AudioProducerAgent`)

**Input:** Final scripts + voice selection + TTS engine choice
**Output:** MP3 files with background music

For each of the 5 variants:
- **Main script** (full_script): Generated with **3 different voices** (e.g., female conversational, male promo, different accent)
- **Fallback 1, Fallback 2, Closure**: Generated with voice 1 only

Total: 5 variants x (3 main + 1 fallback1 + 1 fallback2 + 1 closure) = **30 audio files**

Each file goes through:
1. Text cleaning (strip `[tags]`, markdown, fix acronyms)
2. TTS API call (Murf, ElevenLabs, or edge-tts)
3. Background music generation (synthesized upbeat track)
4. Audio mixing (voice at full volume, BGM at -30dB)
5. Export as stereo MP3 (320kbps, 44.1kHz)

---

## 5. Backend Deep Dive

### Base Agent (`backend/agents/base.py`)

All agents inherit from `BaseAgent` which provides:
- Lazy-initialized `AsyncAzureOpenAI` client
- `call_llm(system_prompt, user_prompt, max_tokens, json_output)` -- unified LLM interface
- `parse_json(text)` -- robust JSON extraction (handles markdown fences, partial JSON)
- Token usage logging (prompt, completion, reasoning tokens)
- Prompt storage for UI visibility (`last_system_prompt`, `last_user_prompt`)

### Orchestrator (`backend/orchestrator.py`)

`PipelineOrchestrator` chains all agents:
1. Steps 1+2 run in parallel via `asyncio.gather()`
2. Steps 3-5 run sequentially (revision loop)
3. Steps 6-7 run sequentially
4. Progress callbacks fire at each step start/complete
5. Audio errors are caught but don't fail the pipeline (scripts still available)

### Audio Producer (`backend/agents/audio_producer.py`)

The most complex agent. Key components:

**TTS Engine Selection (priority):**
1. User's explicit choice (from UI selector)
2. Murf AI (if `MURF_API_KEY` set)
3. ElevenLabs (if key + credits available)
4. edge-tts (always available, free)

**Voice Pools (3 voices per locale):**
- `EDGE_VOICE_POOL`: Maps locale -> 3 Microsoft Neural voices (male, female, alt)
- `MURF_VOICE_POOL`: Maps language -> 3 Murf voices with style (Conversational, Promo)
- ElevenLabs: Uses primary + 2 alternative voices from VoiceSelector

**Text Cleaning (`_clean_text_for_tts`):**
1. Convert known tags to speech (`[laughs]` -> "ha ha,")
2. Strip ALL remaining `[anything]` tags
3. Remove markdown bold/italic
4. Fix acronym pronunciation (IVR -> "I V R") -- but NOT "EVA" (it's a product name)
5. Clean whitespace artifacts

**Background Music:**
Synthesized programmatically (no external files):
- Warm bass pad (low chord)
- Bright melodic shimmer (arpeggiated notes)
- Gentle rhythmic pulse (kick-like thump)
- Soft hi-hat pattern
- BPM: 110, mixed at -30dB below voice

### Main API (`backend/main.py`)

FastAPI application with:
- REST endpoints for pipeline, sessions, campaigns, auth
- WebSocket endpoints for real-time progress and collaboration
- Background task pipeline (`_run_pipeline_bg`) with progress broadcasting
- In-memory session store for active pipeline results
- Static file serving for generated audio (`/outputs/`)

---

## 6. Frontend Deep Dive

### Page Structure

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | `page.tsx` | Main campaign generator (3-step wizard) |
| `/login` | `login/page.tsx` | Authentication |
| `/dashboard` | `dashboard/page.tsx` | Campaign management + collaboration |
| `/product/[id]` | `product/[id]/page.tsx` | Product detail pages |

### Main Page Wizard (`frontend/src/app/page.tsx`)

**Step 1 - Configure:**
- Product preset selection (EVA, CallSignature, MagicVoice, MagicCall, Custom)
- Product documentation upload/paste (PDF, DOCX, PPTX, TXT, MD)
- Promotion type (Standard OBD, Named CLI, IVR Flow, SMS Follow-up, USSD Push)
- Country + Telco + Language dropdowns (22 countries, 160+ telcos)
- TTS engine selector (Auto / Murf AI / ElevenLabs / Free TTS)

**Step 2 - Generate:**
- Real-time progress via WebSocket (`/ws/progress/:sessionId`)
- 7-step timeline with status indicators (pending, running, complete, error)
- Session persistence in localStorage for page refresh recovery

**Step 3 - Results:**
- Voice analytics panel (voice name, parameters, rationale)
- Script cards (expandable, with inline editing)
- Audio files grouped by variant with voice tabs
- Save to dashboard
- Download scripts (JSON/Text)

### Script Editing Flow

1. User clicks "Edit Script" on a variant
2. All 7 sections become editable textareas
3. "Save" calls `PUT /api/sessions/:id/scripts/:variantId`
4. Variant gets "edited" badge
5. "Re-generate Audio" button appears
6. Clicking it calls `POST /api/sessions/:id/regenerate-audio/:variantId`
7. New audio files replace old ones in the UI

### Key Components

| Component | Purpose |
|-----------|---------|
| `CountryTelcoSelect` | Cascading country -> telco -> language dropdowns |
| `ProductPresets` | BNG product cards with full descriptions |
| `ProductUpload` | Drag-drop file upload + text paste |
| `PromotionTypeSelect` | OBD/IVR/SMS promotion type cards |
| `PipelineProgress` | Real-time step timeline with status |
| `VoiceInfoPanel` | Voice details, parameters, rationale |
| `ScriptReview` | Read-only script display with tag highlighting |
| `StatsCards` | Dashboard statistics (campaigns, content assets, online users) |
| `CommentThread` | Campaign comment thread with real-time updates |
| `PresenceBar` | Online user avatars with activity indicators |
| `ActivityFeed` | Recent collaboration events |
| `Sidebar` | Collapsible navigation with product links |
| `ThemeProvider/Picker` | 6 themes (Midnight, Ocean, Ember, Forest, Lavender, Light) |
| `ToastProvider` | Global toast notifications |

---

## 7. Multi-Voice Audio System

### How 3 Voices Are Selected

**Murf AI:**
```
Language -> MURF_VOICE_POOL -> 3 voices
Example (Hindi):
  Voice 1: hi-IN-ayushi (Female, Conversational)
  Voice 2: hi-IN-kabir (Male, Conversational)
  Voice 3: en-IN-arohi (Female, Promo)
```

**edge-tts:**
```
Locale -> EDGE_VOICE_POOL -> 3 voices
Example (en-IN):
  Voice 1: en-IN-NeerjaNeural (Female)
  Voice 2: en-IN-PrabhatNeural (Male)
  Voice 3: en-IN-NeerjaExpressiveNeural (Female Expressive)
```

**ElevenLabs:**
```
VoiceSelector primary + 2 alternatives from voice_selection.alternative_voices
```

### File Naming Convention

```
variant_{variantId}_voice{1|2|3}_{type}.mp3

Examples:
  variant_1_voice1_main.mp3      (Variant 1, Voice 1, full script)
  variant_1_voice2_main.mp3      (Variant 1, Voice 2, full script)
  variant_1_voice3_main.mp3      (Variant 1, Voice 3, full script)
  variant_1_voice1_fallback1.mp3 (Variant 1, Voice 1, fallback 1)
  variant_1_voice1_fallback2.mp3 (Variant 1, Voice 1, fallback 2)
  variant_1_voice1_closure.mp3   (Variant 1, Voice 1, polite closure)
```

### Audio Pipeline Per File

```
Script text
    |
    v
[Clean text] -- strip tags, fix acronyms, remove markdown
    |
    v
[TTS API call] -- Murf/ElevenLabs/edge-tts
    |
    v
[Raw voice MP3]
    |
    v
[Generate BGM] -- synthesized upbeat track matching voice duration
    |
    v
[Mix] -- voice at 0dB + BGM at -30dB
    |
    v
[Export] -- stereo MP3, 320kbps, 44.1kHz
```

---

## 8. Authentication & Collaboration

### Authentication

- **Optional:** Only active when `LOGIN_USERNAME` + `LOGIN_PASSWORD` env vars are set
- **JWT-based:** 72-hour tokens stored in `obd_token` cookie
- **Middleware:** Protects `/api/*`, `/ws/*`, `/outputs/*` paths
- **Public paths:** `/api/health`, `/api/auth/login`, `/api/auth/me`

### Real-Time Collaboration

- **WebSocket rooms:** Each campaign has a collaboration room (`/ws/collaborate/:campaignId`)
- **Presence:** Online users tracked with colored avatars and activity timestamps
- **Comments:** Real-time comment threads on campaigns
- **Activity feed:** Events broadcast to all connected users (campaign created, comments, joins/leaves)

---

## 9. Data Storage & Persistence

### In-Memory (Lost on Restart)

| Data | Storage | Lifetime |
|------|---------|----------|
| Active pipeline sessions | `sessions` dict in `main.py` | Until server restart |
| Pipeline state/progress | `pipelines` dict in `main.py` | Until server restart |
| Online presence | `_presence` dict in `collaboration.py` | Until server restart |
| Collaboration rooms | `_rooms` dict in `collaboration.py` | Until server restart |
| Activity feed | `_activity_feed` list in `collaboration.py` | Until server restart |

### SQLite (Persists Locally)

| Table | Fields | Purpose |
|-------|--------|---------|
| `campaigns` | id, name, created_by, created_at, country, telco, language, result_json, script_count, has_audio | Saved campaigns with full pipeline results |
| `campaign_comments` | id, campaign_id, username, text, created_at | Comments on campaigns |

**Location:** `backend/campaigns.db`
**On Render:** Ephemeral (lost on redeploy)

### File System

| Path | Content | Lifetime |
|------|---------|----------|
| `backend/outputs/{session_id}/` | Generated MP3 audio files | Until deleted or redeploy |

---

## 10. API Reference

### Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/generate/start` | Start pipeline (background). Body: `{product_text, country, telco, language?, tts_engine?}`. Returns `{session_id}` |
| `GET` | `/api/generate/{id}/status` | Pipeline status + progress log + result |
| `POST` | `/api/generate` | Start pipeline (synchronous, form-data) |
| `WS` | `/ws/progress/{id}` | Real-time pipeline progress |

### Sessions & Scripts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/sessions/{id}` | Full session result |
| `GET` | `/api/sessions/{id}/scripts?fmt=json\|text` | Download scripts |
| `PUT` | `/api/sessions/{id}/scripts/{variantId}` | Edit a script variant |
| `POST` | `/api/sessions/{id}/regenerate-audio/{variantId}` | Regenerate audio for one variant |

### Audio

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/sessions/{id}/audio` | List audio files |
| `GET` | `/api/audio/{id}/{filename}` | Download audio file |
| `GET` | `/outputs/{id}/{filename}` | Direct audio file access (static) |

### Campaigns

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/campaigns` | List all campaigns |
| `POST` | `/api/campaigns` | Save campaign. Body: `{session_id, name}` |
| `GET` | `/api/campaigns/{id}` | Get campaign with full result |
| `DELETE` | `/api/campaigns/{id}` | Delete campaign |
| `POST` | `/api/campaigns/{id}/comments` | Add comment |
| `GET` | `/api/campaigns/{id}/comments` | List comments |
| `DELETE` | `/api/campaigns/{id}/comments/{commentId}` | Delete comment |

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login. Body: `{username, password}` |
| `GET` | `/api/auth/me` | Check auth status |
| `POST` | `/api/auth/logout` | Logout (clears cookie) |

### Collaboration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/presence` | Online users |
| `GET` | `/api/activity` | Recent activity events |
| `WS` | `/ws/collaborate/{campaignId}` | Real-time collaboration room |

### Utility

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/upload/extract-text` | Extract text from PDF/DOCX/PPTX |

---

## 11. Deployment

### Local Development

```bash
# Backend
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend && npm install && npm run dev

# Open http://localhost:3000
```

### Render.com (Production)

The repo includes `Dockerfile` (combined build), `render.yaml` (blueprint), and `render-start.sh` (startup script).

**Docker build:**
1. Stage 1: Build Next.js frontend (standalone output)
2. Stage 2: Install Python dependencies
3. Stage 3: Final image with Node.js + Python + ffmpeg

**Runtime:** `render-start.sh` starts both:
- Backend: `uvicorn backend.main:app` on port 8000
- Frontend: `node server.js` on port $PORT (Render routes traffic here)
- Frontend proxies `/api/*` and `/ws/*` to backend via Next.js rewrites

**Required env vars on Render:**
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`
- `MURF_API_KEY` (optional), `ELEVENLABS_API_KEY` (optional)
- `LOGIN_USERNAME`, `LOGIN_PASSWORD` (optional, enables auth)
- `DEFAULT_LLM_PROVIDER` = `azure_openai`

---

## 12. Configuration Reference

All configuration is in `backend/config.py`, loaded from `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | `""` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | `""` | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | `"gpt-5.1-chat"` | Model deployment name |
| `AZURE_OPENAI_API_VERSION` | `"2025-01-01-preview"` | API version |
| `DEFAULT_LLM_PROVIDER` | `"azure_openai"` | LLM provider |
| `ELEVENLABS_API_KEY` | `""` | ElevenLabs API key |
| `ELEVENLABS_BASE_URL` | `"https://api.elevenlabs.io"` | ElevenLabs base URL |
| `ELEVENLABS_TTS_MODEL` | `"eleven_multilingual_v2"` | ElevenLabs model |
| `MURF_API_KEY` | `""` | Murf AI API key |
| `OUTPUTS_DIR` | `backend/outputs/` | Audio output directory |
| `MAX_SCRIPT_WORDS` | `75` | Max words per script (~30s) |
| `EVAL_FEEDBACK_ROUNDS` | `1` | Evaluation-revision cycles |
| `NUM_SCRIPT_VARIANTS` | `5` | Script variants to generate |
| `NUM_FALLBACKS_PER_SCRIPT` | `2` | Fallback CTAs per script |

---

## 13. File Map

```
OBD_SuperStarAgent/
├── .env                          # API keys (not in git)
├── .env.example                  # Template for .env
├── .gitignore
├── .dockerignore
├── Dockerfile                    # Combined build (frontend + backend)
├── render.yaml                   # Render.com blueprint
├── render-start.sh               # Startup script for Render
├── start.sh / stop.sh            # Local dev launcher scripts
├── README.md                     # Quick start guide
├── PROJECT.md                    # Continuity & expansion guide
├── ARCHITECTURE.md               # This document
│
├── backend/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app, all REST + WS endpoints
│   ├── orchestrator.py           # Pipeline orchestrator (chains 7 agents)
│   ├── config.py                 # Configuration (env vars, constants)
│   ├── auth.py                   # JWT authentication
│   ├── database.py               # SQLite campaign persistence
│   ├── collaboration.py          # Real-time collaboration (presence, rooms)
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # Backend-only Dockerfile
│   ├── outputs/                  # Generated audio files (gitignored)
│   ├── campaigns.db              # SQLite database (gitignored)
│   └── agents/
│       ├── __init__.py           # Agent exports
│       ├── base.py               # BaseAgent (LLM interface)
│       ├── product_analyzer.py   # Agent 1: Product analysis
│       ├── market_researcher.py  # Agent 2: Market research
│       ├── script_writer.py      # Agent 3: Script generation + revision
│       ├── eval_panel.py         # Agent 4: 10-persona evaluation
│       ├── voice_selector.py     # Agent 5: Voice selection
│       └── audio_producer.py     # Agent 6: TTS + audio mixing
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts            # API rewrites to backend
│   ├── tailwind.config.ts        # Tailwind + CSS variable themes
│   ├── Dockerfile                # Frontend-only Dockerfile
│   ├── public/
│   │   └── manifest.json
│   └── src/
│       ├── app/
│       │   ├── layout.tsx        # Root layout (providers, sidebar)
│       │   ├── page.tsx          # Main generator (3-step wizard)
│       │   ├── error.tsx         # Error boundary
│       │   ├── login/page.tsx    # Login page
│       │   ├── dashboard/page.tsx # Campaign dashboard
│       │   └── product/[id]/page.tsx # Product detail pages
│       ├── components/
│       │   ├── Sidebar.tsx       # Navigation sidebar
│       │   ├── CountryTelcoSelect.tsx # Country/telco/language dropdowns
│       │   ├── ProductPresets.tsx # BNG product cards
│       │   ├── ProductUpload.tsx # File upload + text paste
│       │   ├── PromotionTypeSelect.tsx # Promotion type selector
│       │   ├── PipelineProgress.tsx # Real-time progress timeline
│       │   ├── VoiceInfoPanel.tsx # Voice analytics display
│       │   ├── ScriptReview.tsx  # Read-only script display
│       │   ├── StatsCards.tsx    # Dashboard statistics
│       │   ├── CommentThread.tsx # Campaign comments
│       │   ├── PresenceBar.tsx   # Online user avatars
│       │   ├── ActivityFeed.tsx  # Collaboration activity feed
│       │   ├── AudioPlayer.tsx   # Audio playback component
│       │   ├── BNGLogo.tsx       # BNG branding logo
│       │   ├── ThemeProvider.tsx  # Theme context provider
│       │   ├── ThemePicker.tsx   # Theme selector UI
│       │   └── ToastProvider.tsx # Toast notification system
│       └── lib/
│           ├── types.ts          # TypeScript types (mirrors backend)
│           └── utils.ts          # Utility functions
│
└── sample_products/
    └── eva_ai_on_call.txt        # EVA product description
```

---

## Summary

OBD SuperStar Agent is a full-stack AI application that automates the entire OBD campaign creation workflow. It uses 6 specialized AI agents powered by Azure OpenAI, generates audio with 3 different voices per script variant via Murf AI/ElevenLabs/edge-tts, and provides a modern React UI with real-time progress tracking, inline script editing, and team collaboration features. The system is deployable to Render.com via Docker and all code is version-controlled on GitHub.
