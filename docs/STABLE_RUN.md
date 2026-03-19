# Stable run (demos / “best working state”)

Use this to run the app so the pipeline and dashboard stay stable and the backend does not suspend.

## 1. Start backend (no TTY — prevents suspension)

From the **project root**:

```bash
./scripts/start_backend.sh
```

Or manually:

```bash
nohup uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 </dev/null >> backend.log 2>&1 &
```

- Logs go to **`backend.log`** in the project root (not in the terminal).
- Watch logs: `tail -f backend.log`.
- The `</dev/null` is important: it detaches the process from the terminal so you never get “suspended (tty output)”.

## 2. Start frontend (optional, same idea)

```bash
./scripts/start_frontend.sh
```

Or:

```bash
nohup npm run dev --prefix frontend </dev/null >> frontend.log 2>&1 &
```

## 3. “Best working state” behavior

- **Pipeline:** Product Analysis → … → Voice Selection → Hook previews (15 for 5 variants × 3 voices) → Auto full audio (15 for flow: 3 steps × 5 variants, or 20 for non-flow: 4 sections × 5 variants). Same voice and BGM for full audio as for previews.
- **ElevenLabs 401:** If the API key is rejected, the app falls back to Edge TTS and logs it; audio still generates.
- **Dashboard:** Edit scripts (per variant or per step for flow) → Save scripts → Regenerate audio (same saved voice) → Download scripts/audio. Single-variant regenerate supported.

## 4. Full restart (e.g. after changing `.env`)

To pick up new config (e.g. `ELEVENLABS_API_KEY`), do a **complete restart** from project root:

```bash
./scripts/restart_app.sh
```

This stops backend (port 8000) and frontend (port 3000), waits for ports to release, then starts both with a fresh load of `.env`. Check `backend.log` for “ElevenLabs API key valid” or the 401 diagnostic.

## 5. If something still fails

- Confirm the backend is running: `curl -s http://localhost:8000/api/health`.
- Check logs: `tail -100 backend.log`.
- Full restart: `./scripts/restart_app.sh`.
- **"Blocked by Azure's content policy" during Generate:** The pipeline uses Azure OpenAI; sometimes long or instruction-like text in the product description triggers a safety check. Use **Start New Campaign** and try again with a **shorter or simpler product description**, or rephrase any sentences that could be read as instructions. If it keeps happening, contact your Azure OpenAI admin.
