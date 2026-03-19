# Fix ElevenLabs 401 (key rejected)

When you see **"ElevenLabs API key rejected (401)"**, the API key is being refused by the endpoint we use to validate it. The app falls back to Edge TTS so audio still generates, but to use ElevenLabs you need the key to pass validation.

**TTS-only keys (no `voices_read`):** If your key was **given to you** (no account ownership) and only has **text-to-speech** permission, the API returns 401 on `GET /v2/voices` with `missing_permissions` / `voices_read`. The app **treats that as valid**: it uses the **curated default voices** from `CONFIGURED_VOICES.md` and ElevenLabs TTS works. You should see in logs: **"ElevenLabs API key set (TTS-only; no voices_read). Using curated default voices — TTS enabled."** No fix needed.

**If the key works in curl but the app shows 401:** The app may be sending a different value (invisible characters, encoding) or the API may reject requests without a proper User-Agent. We now send a User-Agent and load the key as ASCII-only. **Try re-pasting the key:** open `.env`, delete the current `ELEVENLABS_API_KEY` line, then paste the **exact** key on a new line as `ELEVENLABS_API_KEY=sk_...` (no quotes, no spaces around `=`). Save, then run `./scripts/restart_app.sh`.

## 1. Check key at startup

Restart the backend and watch the first lines of `backend.log`:

- **"ElevenLabs API key valid — ElevenLabs TTS enabled."** → Full access (voices + TTS).
- **"ElevenLabs API key set (TTS-only; no voices_read). Using curated default voices — TTS enabled."** → Key is valid for TTS only; app uses curated voices. No change needed.
- **"ElevenLabs key not accepted (401). Loaded key: len=…"** → Key invalid or wrong; follow steps below.

## 2. Use a new key from ElevenLabs

1. Open **https://elevenlabs.io/app/settings/api-keys** and sign in.
2. **Create a new API key** (old keys may be revoked or expired).
3. Copy the new key (it usually starts with `sk_`).

## 3. Set it in `.env`

In the **project root** (same folder as `backend/` and `frontend/`), edit `.env`:

```bash
ELEVENLABS_API_KEY=sk_your_new_key_here
```

- **No quotes** around the value (or the app will strip them; avoid `"sk_..."` if you can).
- No spaces before or after `=`.
- Save the file.

## 4. Restart the backend

Full restart (recommended so `.env` is reloaded):

```bash
./scripts/restart_app.sh
```

Then check:

```bash
tail -20 backend.log
```

You should see **"ElevenLabs API key valid — ElevenLabs TTS enabled."**

Optional: check from the API:

```bash
curl -s "http://localhost:8000/api/check-keys?validate=1"
```

You may see `"elevenlabs": "valid"` (full access) or `"elevenlabs": "valid_tts_only"` (TTS-only; curated voices).

## 5. Run a campaign again

Use the same flow as in your “best” campaign (e.g. BTC OBD3): run the pipeline; Voice Selection will use ElevenLabs and audio will be generated with the chosen voice (e.g. Charlotte) and step files (e.g. voice1_step_welcome, voice1_step_pack_details, voice1_step_thanks) as in the screenshot.
