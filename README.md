# OBD SuperStar Agent

AI-powered multi-agent system that generates culturally-relevant OBD (Outbound Dialer) promotional scripts and audio recordings. Upload your product documentation, select a target country and telco, and the system produces ready-to-deploy OBD audio files.

## Architecture

```
Product Doc + Country + Telco
        |
        v
[Agent 1: Product Analyzer]    -- Extracts structured product brief
        |
        v
[Agent 2: Market Researcher]   -- Country/culture/audience analysis
        |
        v
[Agent 3: Script Writer]       -- Hook + Body + CTA + Fallbacks (x5 variants)
        |
        v
[Agent 4: Eval Panel]          -- 10 AI evaluator personas score & critique
        |
        v (feedback loop)
[Agent 3: Script Writer]       -- Revised scripts based on feedback
        |
        v
[Agent 5: Voice Selector]      -- Picks optimal voice for market
        |
        v
[Agent 6: Audio Producer]      -- TTS: Murf AI → ElevenLabs → edge-tts (free)
        |
        v
    Final Audio Files (downloadable)
```

## Tech Stack

- **Backend**: Python FastAPI with WebSocket support
- **Frontend**: Next.js 15 + React 19 + Tailwind CSS
- **LLM**: Azure OpenAI (GPT-5.1-chat)
- **TTS**: Murf AI (primary), ElevenLabs or edge-tts (free) as fallbacks. Language override supported for scripts.

## Quick Start

### 1. Clone and configure

```bash
cd OBD_SuperStarAgent
cp .env.example .env
# Edit .env with your API keys
```

### 2. Backend setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start the backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Open the app

Visit [http://localhost:3000](http://localhost:3000) in your browser.

## API Keys Required

| Key | Required | Purpose |
|-----|----------|---------|
| `AZURE_OPENAI_API_KEY` | Yes | Azure OpenAI for all LLM agents |
| `AZURE_OPENAI_ENDPOINT` | Yes | Your Azure OpenAI resource URL |
| `AZURE_OPENAI_DEPLOYMENT` | Yes | Deployment name (e.g. `gpt-5.1-chat`) |
| `AZURE_OPENAI_API_VERSION` | Yes | API version (e.g. `2025-01-01-preview`) |
| `MURF_API_KEY` | Optional | Primary TTS (Murf AI). Sign up at [murf.ai](https://murf.ai) |
| `ELEVENLABS_API_KEY` | Optional | Fallback TTS. If neither Murf nor ElevenLabs is set, edge-tts (free) is used |
| `LOGIN_USERNAME` / `LOGIN_PASSWORD` | Optional | If both set, login is required (e.g. on Render) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/generate` | Start pipeline (sync) |
| `WS` | `/ws/generate` | Start pipeline (WebSocket with live progress) |
| `GET` | `/api/sessions/{id}` | Get session results |
| `GET` | `/api/sessions/{id}/scripts` | Download scripts (JSON or text format) |
| `GET` | `/api/sessions/{id}/audio` | List audio files |
| `GET` | `/api/audio/{id}/{file}` | Download audio file |

## How It Works

1. **Product Analyzer**: Parses your product documentation into a structured brief with features, pricing, USPs, and subscription mechanisms.

2. **Market Researcher**: Analyzes the target country and telco -- demographics, cultural nuances, current affairs, consumer psychology, and promotion recommendations.

3. **Script Writer**: Creates 5 unique script variants, each with:
   - **Hook** (5s): Attention-grabbing opener using cultural references
   - **Body** (18s): Compelling product pitch focused on benefits
   - **CTA** (7s): Clear DTMF-based call to action
   - **Fallback 1**: Urgency-based follow-up if no response
   - **Fallback 2**: Psychological persuasion techniques
   - **Polite Closure**: Graceful exit

4. **Eval Panel**: 10 AI evaluator personas (psychologist, copywriters, cultural consultant, etc.) score and critique each script.

5. **Script Revision**: Scripts are revised based on panel feedback.

6. **Voice Selector**: Picks the best voice for the target market (Murf, ElevenLabs, or edge-tts).

7. **Audio Producer**: Generates MP3 files via Murf AI (or ElevenLabs/edge-tts). Script tags like `[excited]` are stripped before TTS; BGM is mixed at low volume.

## Sample Products

The `sample_products/` directory contains product descriptions ready for use:

- **`eva_ai_on_call.txt`** -- EVA AI Personal Assistant (AI On Call) -- an AI-powered IVR/personal call assistant VAS product

To use: Upload the product file in the UI, select your target country and telco, and run the pipeline.

## Dashboard & persistence

- **Dashboard** (`/dashboard`): Lists saved campaigns (name, country, telco, language, script/audio counts). Expand a campaign to see script variants and play/download audio.
- **Saving**: Click "Save to dashboard" on the results page to store the campaign in the local SQLite DB (`backend/campaigns.db`). Comments and collaboration use the same DB.
- **On Render**: The filesystem is ephemeral — `campaigns.db` and `outputs/` are wiped on each deploy. Use Render for demos; for long-term storage consider a hosted DB and object store (see `PROJECT.md`).

## Deploy to Render

1. Connect the GitHub repo at [dashboard.render.com](https://dashboard.render.com) (Blueprint or Web Service).
2. Set environment variables in the Render dashboard (see table above); do not commit `.env`.
3. Deploy uses the repo’s `Dockerfile` and `render-start.sh`. Health check: `/api/health`.

## Deploy to Streamlit Community Cloud

The `streamlit-app` branch contains a Streamlit-based version of the app.

1. Go to [share.streamlit.io](https://share.streamlit.io) and connect the GitHub repo.
2. Set **Branch** to `streamlit-app` and **Main file path** to `streamlit_app/app.py`.
3. Add secrets in the Streamlit Cloud dashboard (Settings > Secrets):
   ```toml
   ADMIN_USERNAME = "admin"
   ADMIN_PASSWORD = "your-secure-password"
   AZURE_OPENAI_API_KEY = "..."
   AZURE_OPENAI_ENDPOINT = "..."
   AZURE_OPENAI_DEPLOYMENT = "gpt-5.1-chat"
   AZURE_OPENAI_API_VERSION = "2025-01-01-preview"
   MURF_API_KEY = "..."
   ELEVENLABS_API_KEY = "..."
   ```
4. Deploy. The admin account is auto-created from secrets on first run.

### Streamlit App Features

- **2-Phase Audio**: Hook previews with 3 voices per variant, then full audio with your chosen voice
- **Admin Auth**: SQLite-based user management -- admin creates accounts for teams
- **Script Editing**: Edit scripts inline before generating final audio
- **Pages**: Generate, Dashboard, Admin (admin-only)

See **`PROJECT.md`** for continuity (running without Cursor, where progress is saved, how to extend the project).
