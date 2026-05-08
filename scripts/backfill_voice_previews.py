"""Back-fill missing voice preview MP3s for custom voices.

Iterates over `backend/custom_voices.json` and, for any entry whose
`preview_url` is null/empty, calls ElevenLabs TTS once to generate a
short preview, saves it to `backend/outputs/voice_previews/{voice_id}.mp3`,
and updates the JSON entry's `preview_url`.

Idempotent: re-running skips voices that already have a preview file on disk.

Usage:
  python scripts/backfill_voice_previews.py
  python scripts/backfill_voice_previews.py --force   # regenerate even if file exists
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip().strip('"').strip("'")
CUSTOM_VOICES_PATH = PROJECT_ROOT / "backend" / "custom_voices.json"
PREVIEWS_DIR = PROJECT_ROOT / "backend" / "outputs" / "voice_previews"
PREVIEW_TEXT = "Hello, this is a voice preview from ElevenLabs. How does this sound?"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Regenerate even if preview MP3 exists")
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        print("ERROR: ELEVENLABS_API_KEY missing from .env", file=sys.stderr)
        return 2
    if not CUSTOM_VOICES_PATH.exists():
        print(f"ERROR: {CUSTOM_VOICES_PATH} not found", file=sys.stderr)
        return 2

    import httpx

    voices = json.loads(CUSTOM_VOICES_PATH.read_text())
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    targets = []
    for v in voices:
        vid = v.get("voice_id")
        if not vid:
            continue
        path = PREVIEWS_DIR / f"{vid}.mp3"
        has_file = path.exists() and path.stat().st_size > 0
        has_url = bool(v.get("preview_url"))
        if args.force or not has_file or not has_url:
            targets.append(v)

    if not targets:
        print("All custom voices already have previews. Nothing to do.")
        return 0

    print(f"Generating previews for {len(targets)} voice(s)…")
    ok = 0
    failed: list[tuple[str, str]] = []

    with httpx.Client(timeout=30.0) as client:
        for v in targets:
            vid = v["voice_id"]
            name = v.get("name", vid)
            path = PREVIEWS_DIR / f"{vid}.mp3"
            print(f"  → {name} ({vid})")
            try:
                r = client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
                    headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
                    json={"text": PREVIEW_TEXT, "model_id": "eleven_v3"},
                )
                if r.status_code != 200:
                    failed.append((name, f"HTTP {r.status_code}: {r.text[:120]}"))
                    print(f"     FAILED: HTTP {r.status_code}")
                    continue
                path.write_bytes(r.content)
                v["preview_url"] = f"/api/voices/{vid}/preview"
                ok += 1
                print(f"     saved {len(r.content) / 1000:.1f} KB")
            except Exception as e:
                failed.append((name, str(e)))
                print(f"     FAILED: {e}")

    # Persist updated JSON (preserve the same indent style as the original file)
    CUSTOM_VOICES_PATH.write_text(json.dumps(voices, indent=2))

    print()
    print(f"Done. {ok} succeeded, {len(failed)} failed.")
    if failed:
        for name, err in failed:
            print(f"  ✗ {name}: {err}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
