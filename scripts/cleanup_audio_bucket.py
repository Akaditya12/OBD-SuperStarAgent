"""Cleanup orphaned audio files from the Supabase `audio-files` bucket.

An "orphan" is any object in the bucket whose `{session_id}/{file_name}` path
is NOT referenced by a saved campaign's result payload
(`audio.audio_files[]` or `hook_previews.hook_previews[]`).

Usage:
  python scripts/cleanup_audio_bucket.py                   # dry-run, prints plan
  python scripts/cleanup_audio_bucket.py --confirm         # actually delete
  python scripts/cleanup_audio_bucket.py --confirm --batch 100
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
BUCKET = "audio-files"


def _fmt_mb(bytes_: int) -> str:
    return f"{bytes_ / 1_000_000:.1f} MB"


def _collect_referenced_paths(supabase) -> set[str]:
    """Pull every campaign's result_json and extract referenced storage paths."""
    referenced: set[str] = set()
    page_size = 1000
    offset = 0
    while True:
        resp = (
            supabase.table("campaigns")
            .select("result_json")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            break
        for row in rows:
            result = row.get("result_json") or {}
            session_id = result.get("session_id", "")
            audio = (result.get("audio") or {}).get("audio_files") or []
            for af in audio:
                name = af.get("file_name")
                if name and session_id:
                    referenced.add(f"{session_id}/{name}")
            preview_block = (result.get("hook_previews") or {}).get("hook_previews") or []
            for pv in preview_block:
                name = pv.get("file_name")
                if name and session_id:
                    referenced.add(f"{session_id}/{name}")
        if len(rows) < page_size:
            break
        offset += page_size
    return referenced


def _list_all_objects(supabase) -> list[dict[str, Any]]:
    """List every object in the bucket as a flat list of {path, size, updated_at}."""
    storage = supabase.storage.from_(BUCKET)
    results: list[dict[str, Any]] = []

    # List top-level entries (each is a "session_id" folder)
    top = storage.list("", {"limit": 1000, "offset": 0})
    session_dirs = [e["name"] for e in (top or []) if e.get("name") and not e["name"].startswith(".")]

    for session_id in session_dirs:
        offset = 0
        while True:
            page = storage.list(session_id, {"limit": 1000, "offset": offset})
            if not page:
                break
            for entry in page:
                name = entry.get("name") or ""
                if not name or name.startswith("."):
                    continue
                meta = entry.get("metadata") or {}
                size = int(meta.get("size") or entry.get("size") or 0)
                updated = entry.get("updated_at") or entry.get("created_at") or ""
                results.append({
                    "path": f"{session_id}/{name}",
                    "size": size,
                    "updated_at": updated,
                })
            if len(page) < 1000:
                break
            offset += 1000
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", action="store_true", help="Actually delete (otherwise dry-run)")
    parser.add_argument("--batch", type=int, default=100, help="Objects per delete call (default 100)")
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY not set in .env", file=sys.stderr)
        return 2

    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: supabase package not installed. `pip install supabase`", file=sys.stderr)
        return 2

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    print(f"→ Fetching referenced paths from campaigns table…")
    referenced = _collect_referenced_paths(supabase)
    print(f"  {len(referenced)} storage paths referenced by saved campaigns")

    print(f"→ Listing objects in bucket `{BUCKET}`…")
    objects = _list_all_objects(supabase)
    total_size = sum(o["size"] for o in objects)
    print(f"  {len(objects)} objects, total {_fmt_mb(total_size)}")

    orphans = [o for o in objects if o["path"] not in referenced]
    kept = [o for o in objects if o["path"] in referenced]
    orphan_size = sum(o["size"] for o in orphans)
    kept_size = sum(o["size"] for o in kept)

    print()
    print("── Cleanup plan ──")
    print(f"  Keep (referenced)   : {len(kept):>5} files  {_fmt_mb(kept_size):>12}")
    print(f"  Delete (orphans)    : {len(orphans):>5} files  {_fmt_mb(orphan_size):>12}")
    print(f"  After cleanup       : {_fmt_mb(total_size - orphan_size)}")
    print()

    if not orphans:
        print("Nothing to delete. Exiting.")
        return 0

    # Show a few example orphans by size (largest first)
    orphans_sorted = sorted(orphans, key=lambda o: -o["size"])
    print("Largest orphans (top 10):")
    for o in orphans_sorted[:10]:
        print(f"  {_fmt_mb(o['size']):>10}  {o['updated_at'][:10] or '?':>10}  {o['path']}")
    print()

    if not args.confirm:
        print("DRY-RUN — pass --confirm to actually delete.")
        return 0

    print(f"Deleting {len(orphans)} orphaned files in batches of {args.batch}…")
    deleted = 0
    errors = 0
    for i in range(0, len(orphans), args.batch):
        batch_paths = [o["path"] for o in orphans[i:i + args.batch]]
        try:
            supabase.storage.from_(BUCKET).remove(batch_paths)
            deleted += len(batch_paths)
            print(f"  {deleted}/{len(orphans)} deleted")
        except Exception as e:
            errors += 1
            print(f"  batch {i}-{i+len(batch_paths)} failed: {e}")

    print()
    print(f"Done. Deleted {deleted} files (~{_fmt_mb(orphan_size)} freed). Errors: {errors}")
    print(f"Estimated new bucket size: {_fmt_mb(total_size - orphan_size)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
