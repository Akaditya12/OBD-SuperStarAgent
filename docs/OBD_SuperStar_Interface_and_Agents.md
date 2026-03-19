# OBD SuperStar Agent  
## Interface, logic & agent system

**blackNgreen · Touching Billions of Lives**

---

## 1. Brief explanation of the project

**OBD SuperStar Agent** is an AI-powered application for telecom and VAS teams who need **outbound dialer (OBD)** campaigns: short, persuasive call scripts and **broadcast-quality audio** in the right language and regional style.

Users provide **product documentation** (or paste an existing script), choose **country**, **operator (telco)**, and **language**. The system runs a chain of six specialised AI agents that:

- Analyse the product and research the market  
- Write and evaluate scripts (with an optional feedback loop)  
- Select a market-appropriate voice  
- Produce mixed audio (voice + optional background music)  

**What you get:** Multiple script variants tuned to the market, audio files ready for your OBD platform, and optional save to a dashboard for your team.

**Script to Voice** is a separate flow: paste any script → pick country and voice → generate audio without running the full pipeline. Ideal when the script is already written.

---

## 2. High-level architecture (flow)

```
Web UI  →  FastAPI Backend  →  Agent 1  →  Agent 2  →  Agent 3  ⇄  Agent 4  →  Agent 5  →  Agent 6  →  Web UI
         (orchestration)      Product     Market      Script     Eval        Voice      Audio
                               Analyzer   Researcher  Writer     Panel       Selector   Producer
```

- **Agent 3 (Script Writer)** and **Agent 4 (Eval Panel)** form a **feedback loop**: scripts are evaluated; feedback is sent back for revision (configurable rounds).  
- Once scripts are approved, the flow continues to **Voice Selector** and **Audio Producer**.  
- Final output (scripts + audio) is returned to the **Web UI** for download and optional save to the dashboard.

*A flowchart diagram of this architecture is included in the PDF version of this document.*

---

## 3. User interface (Web UI)

The application is a **Next.js** single-page-style app with a sidebar and main content area.

### 3.1 Home (main campaign flow)

| Step        | What the user sees | Logic |
|------------|--------------------|--------|
| **1. Configure** | Product input (preset products or custom text), country, telco, language, promotion type, TTS engine (Auto / ElevenLabs / Murf / Free TTS), cache/rerun options. | User fills required fields; optional cache check shows if analysis for same country/telco exists so the pipeline can skip Product Analysis + Market Research. |
| **2. Generate**  | “Generating Your Campaign” with a **Pipeline Progress** list (7 steps: Product Analysis → … → Audio Production). Real-time updates via WebSocket; “Back to configure” if stuck. | Frontend calls `POST /api/generate/start`; receives `session_id`; connects to `WS /ws/progress/{session_id}` and/or polls `GET /api/generate/{id}/status`. Progress steps map to agent completions. |
| **3. Results**   | Scripts (expand/copy/edit), voice rationale, hook previews (play/pick voice), “Generate Full Audio” with BGM/style, save to dashboard, download scripts/audio. | Result payload includes scripts, voice selection, hook preview URLs; full audio is generated on demand and can be saved as a campaign. |

### 3.2 Script to Voice

- **Route:** `/script-to-voice`  
- **Logic:** Paste or upload script → choose country (drives accent/voice pool), language, TTS engine, speech speed → generate **voice previews** (3, or 1 if “Use Same Voice” is locked) → pick voice → generate final audio (with optional BGM) → download or save to dashboard.  
- **No agents 1–5:** Only the **Audio Producer** (Agent 6) runs, using the same TTS stack and region-aware voices.

### 3.3 Dashboard

- Lists saved campaigns; expand to play or download scripts and audio.  
- Optional “Translate to English” for transliterated scripts.

### 3.4 Admin Panel

- **Pipeline settings:** Max script words, variants, eval rounds, TTS model (e.g. Eleven v3), voice speed slider, stability/similarity/style, BGM volume, etc.  
- **User management** when auth is enabled (Supabase/JWT).  
- **Agent prompts:** Override system prompts for each agent (stored in DB).

---

## 4. Backend logic (FastAPI)

- **REST:** e.g. `/api/generate/start`, `/api/generate/{session_id}/status`, `/api/cache/check`, `/api/campaigns`, `/api/auth/*`, `/api/admin/*`.  
- **WebSocket:** `/ws/progress/{session_id}` streams progress messages so the UI can show “Product Analysis”, “Market Research”, … “Audio Production” in real time.  
- **Orchestration:** A background task runs the six-agent pipeline; each agent’s completion is pushed to a `progress_log` and broadcast to WebSocket subscribers.  
- **Persistence:** Supabase (when configured) or SQLite for campaigns, config, and auth.

---

## 5. The six-agent system (detail)

| # | Agent | Role | Input → Output |
|---|--------|------|------------------|
| **1** | **Product Analyzer** | Turn unstructured product material into a clear brief. | **In:** Product document (text). **Out:** Structured brief—features, benefits, pricing hooks, IVR angles—so later agents work from a single source of truth. |
| **2** | **Market Researcher** | Build a market picture for the chosen country and telco. | **In:** Brief + country + telco. **Out:** Audience traits, cultural notes, tone guidance, promotion ideas—so scripts sound local and relevant. |
| **3** | **Script Writer** | Write OBD scripts in the required language and length. | **In:** Brief + market analysis + language. **Out:** Multiple variants: hook (~5s), body (~18s), CTA with DTMF, fallbacks, polite close—formatted for TTS. |
| **4** | **Eval Panel** | Quality-check scripts before audio is produced. | **In:** Script variants. **Out:** Scores and written feedback from multiple “personas” (clarity, cultural fit, CTA strength). Feeds back into Agent 3 for revision (feedback loop). |
| **3 again** | **Script revision** | Rewrite using eval feedback. | **In:** Scripts + eval feedback. **Out:** Revised variants that keep structure but address weaknesses. |
| **5** | **Voice Selector** | Choose which voice fits the market and script tone. | **In:** Scripts + market context + available voices (from API or curated list). **Out:** Primary voice + alternatives + rationale; region-aware (e.g. African, South Asian, British for some markets). |
| **6** | **Audio Producer** | Generate speech and mix for broadcast. | **In:** Final script text + chosen voice + country (accent/voice pool) + BGM choice. **Out:** Hook previews (multiple voices), then full MP3/WAV via TTS (ElevenLabs preferred, then Murf, then edge-tts) + optional background music. |

**Feedback loop:** Agent 3 → Agent 4 → (optional revision) → Agent 3 again → … until configured rounds are done, then → Agent 5 → Agent 6.

---

## 6. Technology stack (summary)

| Layer   | Technology |
|--------|------------|
| Frontend | Next.js 15, React 19, Tailwind |
| Backend  | Python FastAPI, WebSockets, async TTS |
| LLM     | Azure OpenAI (all agents + translation) |
| TTS     | ElevenLabs (eleven_v3), Murf AI, edge-tts |
| DB      | Supabase (PostgreSQL) or SQLite fallback |
| Auth    | JWT via Supabase when configured |

---

## 7. Generating a PDF from this document

**Recommended (one-click PDF):**

1. Copy your architecture flowchart image into this folder as **`docs/architecture-flow.png`** (e.g. from your screenshot or the image you used in the diagram).
2. Open **`docs/OBD_SuperStar_Interface_and_Agents.html`** in a browser.
3. Use **File → Print** (or Ctrl/Cmd+P) → choose **Save as PDF** or **Print to PDF**.

The HTML is styled for print (page breaks, no cut-off tables).

**Alternative:** From the Markdown file, use [pandoc](https://pandoc.org/) or any Markdown-to-PDF tool; add the flowchart image into the document where Section 2 (architecture) is described.

---

*OBD SuperStar Agent · blackNgreen*
