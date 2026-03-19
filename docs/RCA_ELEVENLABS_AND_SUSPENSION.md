# RCA: ElevenLabs 401 + Pipeline “Failure” (Process Suspension)

## What you saw

1. **ElevenLabs 401 Unauthorized** when fetching voices and/or generating audio.
2. **Fallback to Edge TTS** (expected when the key is invalid).
3. **Pipeline then “failing”** — Audio Production step never completes; backend appears stuck.
4. **Terminal message:** `[1]  + 45846 suspended (tty output)  uvicorn backend.main:app ...`

## Root causes

### 1. ElevenLabs 401 Unauthorized

- **Cause:** The request to `api.elevenlabs.io` is sent with an API key that the server rejects (invalid, expired, or revoked).
- **Why it can happen even with a key in `.env`:**
  - Key was regenerated or revoked in the ElevenLabs dashboard (old key no longer valid).
  - Key not loaded at runtime (e.g. wrong working directory, `.env` not in project root, or backend started before `.env` was updated).
  - Typo or extra character in `.env` (e.g. space, quote, newline).
- **Effect:** Voice selector and/or audio producer get 401; we correctly fall back to Edge TTS so audio can still be generated.

### 2. Process suspension (“suspended (tty output)”)

- **Cause:** The uvicorn process was **suspended by the OS/shell**, so it stopped running. That’s why the pipeline never finished — the server was no longer executing.
- **Why it happened:** The backend was logging **a lot to stdout** during audio generation:
  - One `INFO` line per TTS segment (e.g. “TTS input (first 120 chars): …”).
  - One `INFO` line per generated file (e.g. “edge-tts: file.mp3 …”, “Murf: …”, “Mixed with music: …”).
  - For 15 hook previews + full audio, that’s dozens of lines in a short time. When the process writes to a **TTY** and the terminal can’t keep up (e.g. buffer full, terminal in background, or no one reading), the **write can block**. In that situation the process may be **suspended** by the shell (e.g. SIGTSTP / “suspended (tty output)”). So the “failure” was not Edge TTS failing — it was the **backend process being suspended** and never completing the work.

## Fixes applied

1. **Log volume reduced**
   - Per-segment and per-file logs that were at `INFO` are now at `DEBUG`:
     - “TTS input (first 120/150 chars)” (Edge and Murf).
     - “edge-tts: …”, “Murf: …”, “Murf response: …”, “Mixed with music: …”.
   - High-level steps stay at `INFO` (e.g. “Generating N hook previews via edge-tts”, “Using edge-tts (FREE): voice=…”).
   - **Effect:** Much less stdout during bulk audio generation, so the process is much less likely to block on the TTY and get suspended.

2. **ElevenLabs**
   - No code change for 401 itself; fallback to Edge TTS was already correct.
   - To use ElevenLabs again: ensure the key in `.env` is valid (create a new key in the ElevenLabs dashboard if needed), restart the backend, and optionally check `GET /api/check-keys` to confirm the key is loaded.

## How to run the backend to avoid suspension

If you see **`[1] + 45154 suspended (tty output) nohup python -m uvicorn ...`** (or similar), the backend was still attached to the terminal and got suspended when it wrote a lot of log output (e.g. during "Generate Full Audio"). Fix: stop it and start with one of the options below so it is fully detached.

- **Recommended — backend + frontend in one go:**
  ```bash
  ./scripts/restart_app.sh
  ```
  Starts both with no TTY attachment. Logs: `tail -f backend.log`, `tail -f frontend.log`.

- **Backend only (fully detached, no TTY):**
  ```bash
  ./scripts/start_backend.sh
  ```
  Runs `nohup python3 -m uvicorn ... </dev/null >> backend.log 2>&1 &` from the project root. Logs: `tail -f backend.log`.

- **Option B (manual):** Run with stdin closed and output to a file:
  ```bash
  nohup python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 </dev/null >> backend.log 2>&1 &
  ```
  The `</dev/null` is required so the process is fully detached from the TTY.

- **Option C:** Run in the foreground in a dedicated terminal and avoid putting that terminal in background (e.g. don’t Ctrl+Z).
- **Option D:** Run under a process manager (e.g. systemd, supervisor) so it’s not attached to a TTY.

With the logging changes and BGM mixing in a thread, using the start script or Option B prevents suspension.
