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
[Agent 5: Voice Selector]      -- Picks optimal ElevenLabs voice
        |
        v
[Agent 6: Audio Producer]      -- Generates MP3 files via ElevenLabs V3 TTS
        |
        v
    Final Audio Files (downloadable)
```

## Tech Stack

- **Backend**: Python FastAPI with WebSocket support
- **Frontend**: Next.js 15 + React 19 + Tailwind CSS
- **LLM**: Claude (Anthropic) or GPT-4 (OpenAI) -- configurable
- **TTS**: ElevenLabs V3 with audio tags for expressiveness

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
| `ANTHROPIC_API_KEY` | At least one LLM key | Claude for script generation |
| `OPENAI_API_KEY` | At least one LLM key | GPT-4 as alternative |
| `ELEVENLABS_API_KEY` | Yes | Voice synthesis via ElevenLabs V3 |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/generate` | Start pipeline (sync) |
| `WS` | `/ws/generate` | Start pipeline (WebSocket with live progress) |
| `GET` | `/api/sessions/{id}` | Get session results |
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

6. **Voice Selector**: Queries ElevenLabs for the best voice matching the target market, configures V3 parameters for expressiveness.

7. **Audio Producer**: Generates MP3 files using ElevenLabs V3 TTS with audio tags like `[excited]`, `[whispers]`, `[pause]` for natural delivery.

## ElevenLabs V3 Audio Tags

Scripts are generated with embedded audio tags for expressive delivery:

- `[excited]`, `[curious]`, `[whispers]` -- Emotional states
- `[laughs]`, `[sigh]`, `[pause]` -- Non-verbal cues
- `CAPITALIZED WORDS` -- Emphasis
- `...` (ellipses) -- Dramatic pauses
- `[short pause]`, `[long pause]` -- Timed breaks
