"""Download all Supabase Storage audio files referenced by saved campaigns
to the local `backend/outputs/{session_id}/{file_name}` layout, so the app
can serve them via FastAPI once Supabase is retired.

After a successful download, optionally rewrites each campaign's
`result_json.audio.audio_files[].public_url` to "" (empty) so the frontend
falls back to the backend's `/api/audio/{session_id}/{file_name}` endpoint.

Env:
  MYSQL_URL           local MySQL connection
  SUPABASE_URL        (optional) only used to build URLs if public_url missing

Usage:
  python scripts/download_supabase_audio.py                    # dry-run, no downloads
  python scripts/download_supabase_audio.py --download         # download only
  python scripts/download_supabase_audio.py --download --rewrite-urls
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse, unquote

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

MYSQL_URL = os.getenv("MYSQL_URL", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
BUCKET = "audio-files"
OUTPUTS_DIR = PROJECT_ROOT / "backend" / "outputs"


def _parse_mysql_url(url: str) -> dict:
    p = urlparse(url)
    return {
        "host": p.hostname,
        "port": p.port or 3306,
        "user": unquote(p.username or ""),
        "password": unquote(p.password or ""),
        "db": (p.path or "/").lstrip("/"),
    }


def _fmt_mb(n: int) -> str:
    return f"{n / 1_000_000:.1f} MB"


def _collect_audio_refs(my) -> list[dict]:
    """Pull every campaign's result_json and return list of
    {campaign_id, session_id, file_name, url, section}."""
    refs: list[dict] = []
    with my.cursor() as mc:
        mc.execute("SELECT id, result_json FROM campaigns WHERE result_json IS NOT NULL")
        for row in mc.fetchall():
            campaign_id, result_raw = row
            try:
                result = json.loads(result_raw) if isinstance(result_raw, (str, bytes)) else result_raw
            except Exception:
                continue
            if not isinstance(result, dict):
                continue
            session_id = result.get("session_id", "")
            if not session_id:
                continue

            for block_key in ("audio", "hook_previews"):
                block = result.get(block_key) or {}
                files = block.get("audio_files") if block_key == "audio" else block.get("hook_previews")
                for af in (files or []):
                    name = af.get("file_name")
                    url = af.get("public_url") or ""
                    if name:
                        refs.append({
                            "campaign_id": campaign_id,
                            "session_id": session_id,
                            "file_name": name,
                            "url": url,
                            "section": block_key,
                        })
    return refs


def _build_fallback_url(session_id: str, file_name: str) -> str:
    if not SUPABASE_URL:
        return ""
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{session_id}/{file_name}"


def _download_one(ref: dict) -> tuple[dict, bool, int, str]:
    import httpx

    target = OUTPUTS_DIR / ref["session_id"] / ref["file_name"]
    if target.exists() and target.stat().st_size > 0:
        return ref, True, target.stat().st_size, "exists"

    url = ref["url"] or _build_fallback_url(ref["session_id"], ref["file_name"])
    if not url:
        return ref, False, 0, "no-url"

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with httpx.stream("GET", url, timeout=60.0, follow_redirects=True) as r:
            if r.status_code != 200:
                return ref, False, 0, f"http-{r.status_code}"
            with open(target, "wb") as f:
                for chunk in r.iter_bytes(chunk_size=64 * 1024):
                    f.write(chunk)
        return ref, True, target.stat().st_size, "downloaded"
    except Exception as e:
        return ref, False, 0, f"err:{type(e).__name__}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Actually download (otherwise just list)")
    parser.add_argument("--rewrite-urls", action="store_true", help="After download, null out public_url so app uses local")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent download workers")
    args = parser.parse_args()

    if not MYSQL_URL:
        print("ERROR: MYSQL_URL missing from .env", file=sys.stderr)
        return 2

    import pymysql

    my = pymysql.connect(**_parse_mysql_url(MYSQL_URL), charset="utf8mb4", autocommit=False)
    try:
        print(f"→ Collecting audio refs from campaigns…")
        refs = _collect_audio_refs(my)
        print(f"  {len(refs)} audio references across campaigns")

        # Dedupe by (session_id, file_name) — same file can be in multiple blocks
        unique = {}
        for r in refs:
            key = (r["session_id"], r["file_name"])
            if key not in unique:
                unique[key] = r
        refs = list(unique.values())
        print(f"  {len(refs)} unique files to fetch")

        already_local = sum(
            1 for r in refs
            if (OUTPUTS_DIR / r["session_id"] / r["file_name"]).exists()
        )
        print(f"  {already_local} already present locally")

        if not args.download:
            print("\nDRY-RUN — pass --download to fetch all files.")
            return 0

        print(f"\n→ Downloading with {args.workers} workers…")
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

        ok = 0
        skipped = 0
        failed: list[tuple[dict, str]] = []
        total_bytes = 0

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(_download_one, r): r for r in refs}
            for i, fut in enumerate(as_completed(futures), 1):
                ref, success, size, status = fut.result()
                if success and status == "downloaded":
                    ok += 1
                    total_bytes += size
                elif success and status == "exists":
                    skipped += 1
                else:
                    failed.append((ref, status))
                if i % 50 == 0 or i == len(refs):
                    print(f"   {i}/{len(refs)}  ok={ok} skipped={skipped} failed={len(failed)}")

        print()
        print(f"Downloaded {ok} files ({_fmt_mb(total_bytes)})")
        print(f"Already existed: {skipped}")
        print(f"Failed: {len(failed)}")
        if failed:
            print("\nFailures (first 10):")
            for r, status in failed[:10]:
                print(f"  {status:>12}  {r['session_id']}/{r['file_name']}")

        if args.rewrite_urls and ok + skipped > 0:
            print(f"\n→ Rewriting public_url → '' in MySQL for downloaded files…")
            downloaded_keys = {
                (r["session_id"], r["file_name"])
                for r in refs
                if (OUTPUTS_DIR / r["session_id"] / r["file_name"]).exists()
            }

            updated_campaigns = 0
            with my.cursor() as mc:
                mc.execute("SELECT id, result_json FROM campaigns WHERE result_json IS NOT NULL")
                rows = mc.fetchall()

            for cid, result_raw in rows:
                try:
                    result = json.loads(result_raw) if isinstance(result_raw, (str, bytes)) else result_raw
                except Exception:
                    continue
                if not isinstance(result, dict):
                    continue
                session_id = result.get("session_id", "")
                changed = False
                for block_key in ("audio", "hook_previews"):
                    block = result.get(block_key) or {}
                    files = block.get("audio_files") if block_key == "audio" else block.get("hook_previews")
                    for af in (files or []):
                        if (session_id, af.get("file_name")) in downloaded_keys and af.get("public_url"):
                            af["public_url"] = ""
                            changed = True
                if changed:
                    with my.cursor() as mc:
                        mc.execute(
                            "UPDATE campaigns SET result_json = %s WHERE id = %s",
                            (json.dumps(result, ensure_ascii=False), cid),
                        )
                    updated_campaigns += 1
            my.commit()
            print(f"  Updated {updated_campaigns} campaigns")

        return 0

    finally:
        my.close()


if __name__ == "__main__":
    sys.exit(main())
