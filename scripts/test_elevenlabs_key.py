#!/usr/bin/env python3
"""Test ElevenLabs API key from the same .env the backend uses. Run from project root.
200 = full access. 401 with missing_permissions/voices_read = TTS-only (key valid; app uses curated voices)."""
import json
import os
import sys
from pathlib import Path

# Load .env like the backend
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
os.chdir(root)

from dotenv import load_dotenv
load_dotenv(root / ".env")

key = os.getenv("ELEVENLABS_API_KEY", "").strip()
if not key or len(key) < 10:
    print("ELEVENLABS_API_KEY not set or too short in .env")
    sys.exit(1)

# Same normalization as backend
key = "".join(c for c in key if ord(c) >= 32 and ord(c) <= 126).strip()
print(f"Key length: {len(key)}, prefix: {key[:8]}..., suffix: ...{key[-4:]}")

import httpx
headers = {
    "xi-api-key": key,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
r = httpx.get("https://api.elevenlabs.io/v2/voices", headers=headers, params={"page_size": 1}, timeout=10)
print(f"GET /v2/voices -> {r.status_code}")

def is_tts_only_401(text):
    try:
        data = json.loads(text)
        detail = data.get("detail") or {}
        return detail.get("status") == "missing_permissions" or "voices_read" in (detail.get("message") or "").lower()
    except Exception:
        return False

if r.status_code == 200:
    print("OK — key has full access (voices + TTS).")
elif r.status_code == 401 and is_tts_only_401(r.text):
    print("OK — key is TTS-only (no voices_read). App will use curated default voices; TTS will work.")
else:
    print(f"Response: {r.text[:300]}")
    sys.exit(1)
