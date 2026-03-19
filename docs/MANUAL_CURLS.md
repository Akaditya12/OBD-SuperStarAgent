# Manual cURLs – OBD SuperStar Agent API

Use these with the backend running at **http://localhost:8000**. If auth is enabled, call **Login** first and use the returned cookie (or Bearer token) on protected endpoints.

---

## 1. Health (no auth)

```bash
curl -s http://localhost:8000/api/health
```

Expected: `{"status":"ok","service":"OBD SuperStar Agent"}`

---

## 2. Login (when auth is enabled)

```bash
curl -s -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_PASSWORD"}'
```

Then use the session cookie on later requests:

```bash
curl -s -b cookies.txt http://localhost:8000/api/auth/me
```

---

## 3. Start pipeline (Market Researcher → Scripts → Voice → Hook previews)

Starts the full pipeline in the background. Returns a `session_id`; poll status with (4).

```bash
curl -s -X POST http://localhost:8000/api/generate/start \
  -H "Content-Type: application/json" \
  -d '{
    "product_text": "Unlimited weekend data bundle. 5GB for 48 hours. Dial *123# to activate.",
    "country": "Nigeria",
    "telco": "MTN",
    "language": "English",
    "tts_engine": "edge-tts",
    "force_reanalyze": false
  }'
```

Optional body fields: `language`, `provider`, `tts_engine` (e.g. `edge-tts`, `murf`, `elevenlabs`), `force_reanalyze`.

If auth is on, add: `-b cookies.txt`

---

## 4. Poll pipeline status

Replace `SESSION_ID` with the value from (3).

```bash
curl -s http://localhost:8000/api/generate/SESSION_ID/status
```

Response includes `status` (`running` | `done` | `error`), `progress`, and when done, `result` (scripts, voice_selection, hook_previews, etc.).

---

## 5. Get session result (after pipeline is done)

```bash
curl -s http://localhost:8000/api/sessions/SESSION_ID
```

Returns the full session payload (scripts, voice_selection, hook_previews, etc.).

---

## 6. Generate full audio (Phase 2)

After hook previews are ready, send voice choices (variant_id → 1-based voice index) and options. Replace `SESSION_ID` with your session.

```bash
curl -s -X POST http://localhost:8000/api/sessions/SESSION_ID/generate-full-audio \
  -H "Content-Type: application/json" \
  -d '{
    "voice_choices": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
    "bgm_style": "upbeat",
    "audio_format": "mp3",
    "tts_engine": "edge-tts",
    "country": "Nigeria",
    "language": "English"
  }'
```

Returns `{"status":"accepted","job_id":"...","session_id":"..."}`. Poll the job with (7).

---

## 7. Poll audio job status

Replace `JOB_ID` with the value from (6).

```bash
curl -s http://localhost:8000/api/audio-jobs/JOB_ID
```

When `status` is `done`, the response includes the `audio` object (files, summary, etc.).

---

## 8. List audio files for a session

```bash
curl -s http://localhost:8000/api/sessions/SESSION_ID/audio
```

---

## 9. Download a specific audio file

```bash
curl -s -O -J "http://localhost:8000/api/audio/SESSION_ID/FILENAME.mp3?fmt=mp3"
```

Example filename: `variant_1_voice1_main.mp3`

---

## 10. Download scripts (JSON or text)

```bash
# All variants as JSON
curl -s "http://localhost:8000/api/sessions/SESSION_ID/scripts?fmt=json"

# Plain text
curl -s "http://localhost:8000/api/sessions/SESSION_ID/scripts?fmt=text"

# Single variant
curl -s "http://localhost:8000/api/sessions/SESSION_ID/scripts?fmt=json&variant_id=1"
```

---

## 11. Check cache (product + country + telco)

Before starting a pipeline, you can check if analysis is cached:

```bash
curl -s -X POST http://localhost:8000/api/cache/check \
  -H "Content-Type: application/json" \
  -d '{
    "product_text": "Weekend data bundle...",
    "country": "Nigeria",
    "telco": "MTN",
    "language": "English"
  }'
```

---

## 12. Script-to-Voice: preview (3 voices, no BGM)

Standalone flow: send script text and get 3 hook preview URLs.

```bash
curl -s -X POST http://localhost:8000/api/script-to-voice/preview \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Hey! Limited time – double data this weekend. Press 1 to activate now.",
    "country": "Nigeria",
    "language": "English",
    "tts_engine": "edge-tts",
    "speed": 1.0
  }'
```

Returns `job_id`. Poll with (13).

---

## 13. Script-to-Voice: poll preview job

```bash
curl -s http://localhost:8000/api/script-to-voice/jobs/JOB_ID
```

---

## 14. Campaigns (list / get)

```bash
# List saved campaigns
curl -s http://localhost:8000/api/campaigns

# Get one campaign
curl -s http://localhost:8000/api/campaigns/CAMPAIGN_ID
```

---

## 15. BGM preview (short sample)

```bash
curl -s -o bgm_upbeat.mp3 "http://localhost:8000/api/bgm-preview/upbeat"
```

Styles: `upbeat`, `calm`, `corporate`.

---

## Flow summary

1. **Health** → `GET /api/health`
2. **Start pipeline** → `POST /api/generate/start` (product_text, country, telco, language, tts_engine)
3. **Poll until done** → `GET /api/generate/{session_id}/status`
4. **Generate full audio** → `POST /api/sessions/{session_id}/generate-full-audio` (voice_choices, bgm_style, tts_engine, country, language)
5. **Poll audio job** → `GET /api/audio-jobs/{job_id}`
6. **Download files** → `GET /api/sessions/{session_id}/audio` then `GET /api/audio/{session_id}/{filename}`

If auth is enabled, run (2) Login first and add `-b cookies.txt` to all requests in (3)–(15).
