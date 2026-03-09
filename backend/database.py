"""Database persistence for OBD SuperStar Agent (Supabase + SQLite fallback)."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from backend.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

logger = logging.getLogger(__name__)

# --- Supabase Setup ---
supabase: Optional[Any] = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        from supabase import Client, create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized successfully.")
    except ImportError:
        logger.warning("supabase package not installed; falling back to SQLite.")
        supabase = None
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", e)
        supabase = None

# --- SQLite Fallback Setup ---
DB_PATH = Path(__file__).parent / "campaigns.db"

def _get_sqlite_conn() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialize database tables (SQLite fallback only)."""
    if supabase:
        logger.info("Using Supabase. Skipping local SQLite init.")
        return

    conn = _get_sqlite_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_by TEXT NOT NULL DEFAULT 'local',
                team TEXT NOT NULL DEFAULT 'default',
                created_at TEXT NOT NULL,
                country TEXT NOT NULL DEFAULT '',
                telco TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT '',
                result_json TEXT NOT NULL DEFAULT '{}',
                script_count INTEGER NOT NULL DEFAULT 0,
                has_audio INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS campaign_comments (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                username TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        logger.info("Local SQLite database initialized at %s", DB_PATH)
    finally:
        conn.close()

# ── Campaigns ─────────────────────────────────────────────────────────────────

def save_campaign(
    campaign_id: str,
    name: str,
    created_by: str,
    country: str,
    telco: str,
    language: str,
    result: dict[str, Any],
    team: str = "default",
) -> dict[str, Any]:
    """Save a campaign to the database. Returns the saved campaign summary."""
    is_stv = result.get("campaign_type") == "script_to_voice"
    if is_stv:
        script_count = 1
        audio_files = result.get("audio", {}).get("audio_files", [])
    else:
        final_scripts = result.get("final_scripts", result.get("revised_scripts_round_1", result.get("initial_scripts", {})))
        scripts = final_scripts.get("scripts", [])
        script_count = len(scripts)
        audio_files = result.get("audio", {}).get("audio_files", [])
    has_audio = 1 if any(not f.get("error") for f in audio_files) else 0

    now = datetime.now(timezone.utc).isoformat()
    result_json = result

    campaign_data = {
        "id": campaign_id,
        "name": name,
        "created_by": created_by,
        "team": team,
        "created_at": now,
        "country": country,
        "telco": telco,
        "language": language,
        "result_json": result_json,
        "script_count": script_count,
        "has_audio": bool(has_audio),
    }

    if supabase:
        try:
            supabase.table("campaigns").upsert(campaign_data).execute()
            logger.info("Saved campaign '%s' to Supabase", name)
        except Exception as e:
            logger.error("Failed to save campaign to Supabase: %s", e)
            raise e
    else:
        conn = _get_sqlite_conn()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO campaigns
                    (id, name, created_by, team, created_at, country, telco, language, result_json, script_count, has_audio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (campaign_id, name, created_by, team, now, country, telco, language, json.dumps(result_json, default=str), script_count, has_audio),
            )
            conn.commit()
            logger.info("Saved campaign '%s' to SQLite", name)
        finally:
            conn.close()

    # Drop result_json from returned summary
    summary = campaign_data.copy()
    summary.pop("result_json")
    return summary


def list_campaigns(limit: int = 50) -> list[dict[str, Any]]:
    """List all campaigns (without full result JSON)."""
    if supabase:
        try:
            response = supabase.table("campaigns").select(
                "id, name, created_by, team, created_at, country, telco, language, script_count, has_audio"
            ).order("created_at", desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error("Failed to list campaigns from Supabase: %s", e)
            return []

    conn = _get_sqlite_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, name, created_by, team, created_at, country, telco, language, script_count, has_audio
            FROM campaigns
            ORDER BY created_at DESC LIMIT ?
            """, (limit,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_campaign(campaign_id: str) -> Optional[dict[str, Any]]:
    """Get a single campaign with full result JSON.

    Returns dict with ``result`` key (not ``result_json``) for consistency.
    """
    if supabase:
        try:
            response = supabase.table("campaigns").select("*").eq("id", campaign_id).maybe_single().execute()
            data = response.data
            if not data:
                return None
            data["result"] = data.pop("result_json", {})
            return data
        except Exception as e:
            logger.error("Failed to get campaign from Supabase: %s", e)
            return None

    conn = _get_sqlite_conn()
    try:
        row = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["result"] = json.loads(data.pop("result_json"))
        return data
    finally:
        conn.close()


def delete_campaign(campaign_id: str) -> bool:
    """Delete a campaign and its comments. Returns True if a row was deleted."""
    if supabase:
        try:
            response = supabase.table("campaigns").delete().eq("id", campaign_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error("Failed to delete campaign from Supabase: %s", e)
            return False

    conn = _get_sqlite_conn()
    try:
        conn.execute("DELETE FROM campaign_comments WHERE campaign_id = ?", (campaign_id,))
        cursor = conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ── Campaign Comments ─────────────────────────────────────────────────────────

def save_comment(
    comment_id: str,
    campaign_id: str,
    username: str,
    text: str,
) -> dict[str, Any]:
    """Save a comment on a campaign."""
    now = datetime.now(timezone.utc).isoformat()
    comment_data = {
        "id": comment_id,
        "campaign_id": campaign_id,
        "username": username,
        "text": text,
        "created_at": now,
    }

    if supabase:
        try:
            supabase.table("campaign_comments").insert(comment_data).execute()
        except Exception as e:
            logger.error("Failed to save comment to Supabase: %s", e)
            raise e
    else:
        conn = _get_sqlite_conn()
        try:
            conn.execute(
                "INSERT INTO campaign_comments (id, campaign_id, username, text, created_at) VALUES (?, ?, ?, ?, ?)",
                (comment_id, campaign_id, username, text, now),
            )
            conn.commit()
        finally:
            conn.close()

    return comment_data


def list_comments(campaign_id: str) -> list[dict[str, Any]]:
    """List all comments for a campaign, newest first."""
    if supabase:
        try:
            response = supabase.table("campaign_comments").select("*").eq("campaign_id", campaign_id).order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error("Failed to list comments from Supabase: %s", e)
            return []

    conn = _get_sqlite_conn()
    try:
        rows = conn.execute(
            "SELECT id, campaign_id, username, text, created_at FROM campaign_comments WHERE campaign_id = ? ORDER BY created_at DESC",
            (campaign_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_comment(comment_id: str) -> bool:
    """Delete a comment."""
    if supabase:
        try:
            response = supabase.table("campaign_comments").delete().eq("id", comment_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error("Failed to delete comment from Supabase: %s", e)
            return False

    conn = _get_sqlite_conn()
    try:
        cursor = conn.execute("DELETE FROM campaign_comments WHERE id = ?", (comment_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ── Analysis Cache ────────────────────────────────────────────────────────────

def _analysis_cache_key(product_text: str, country: str, telco: str, language: str | None) -> str:
    """Generate a stable hash key for an analysis input combination."""
    import hashlib
    raw = f"{product_text[:5000]}|{country}|{telco}|{language or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_cached_analysis(product_text: str, country: str, telco: str, language: str | None) -> Optional[dict[str, Any]]:
    """Look up cached product_brief + market_analysis.

    Tries exact match first (same product+country+telco). If no exact match,
    falls back to partial match (same country+telco) to reuse market_analysis
    while returning None for product_brief so the pipeline re-runs only step 1.
    """
    cache_key = _analysis_cache_key(product_text, country, telco, language)

    if not supabase:
        return None

    # 1) Exact match
    try:
        resp = (
            supabase.table("analysis_cache")
            .select("product_brief, market_analysis")
            .eq("cache_key", cache_key)
            .limit(1)
            .execute()
        )
        if resp and resp.data and len(resp.data) > 0:
            row = resp.data[0]
            logger.info("Analysis cache EXACT HIT for key %s", cache_key)
            return {
                "product_brief": row.get("product_brief"),
                "market_analysis": row.get("market_analysis"),
                "match_type": "exact",
            }
    except Exception as e:
        logger.warning("Exact cache lookup failed: %s", e)

    # 2) Partial match: same country + telco (reuse market_analysis only)
    try:
        resp = (
            supabase.table("analysis_cache")
            .select("market_analysis")
            .eq("country", country)
            .eq("telco", telco)
            .order("cache_key", desc=True)
            .limit(1)
            .execute()
        )
        if resp and resp.data and len(resp.data) > 0:
            row = resp.data[0]
            logger.info("Analysis cache PARTIAL HIT (country+telco) for %s/%s", country, telco)
            return {
                "product_brief": None,
                "market_analysis": row.get("market_analysis"),
                "match_type": "partial",
            }
    except Exception as e:
        logger.warning("Partial cache lookup failed: %s", e)

    return None


def check_cache_exists(product_text: str, country: str, telco: str, language: str | None) -> dict[str, Any]:
    """Check for cached analysis -- exact match and partial (same country+telco).

    Returns:
        {
            "exact": true/false,
            "exact_cached_at": "...",
            "partial": true/false,
            "partial_cached_at": "...",
        }
    """
    result: dict[str, Any] = {"exact": False, "partial": False}
    if not supabase:
        return result

    # Exact match only possible when product_text is provided
    if product_text:
        cache_key = _analysis_cache_key(product_text, country, telco, language)
        try:
            resp = (
                supabase.table("analysis_cache")
                .select("cache_key")
                .eq("cache_key", cache_key)
                .limit(1)
                .execute()
            )
            if resp and resp.data and len(resp.data) > 0:
                result["exact"] = True
                result["exact_cached_at"] = resp.data[0].get("cached_at", "")
                return result
        except Exception as e:
            logger.warning("Exact cache check failed: %s", e)

    # Partial match: same country + telco, any product
    try:
        resp = (
            supabase.table("analysis_cache")
            .select("cache_key, country, telco")
            .eq("country", country)
            .eq("telco", telco)
            .limit(1)
            .execute()
        )
        if resp and resp.data and len(resp.data) > 0:
            result["partial"] = True
            result["partial_cached_at"] = resp.data[0].get("cached_at", "")
    except Exception as e:
        logger.warning("Partial cache check failed: %s", e)

    return result


def save_analysis_cache(
    product_text: str,
    country: str,
    telco: str,
    language: str | None,
    product_brief: dict[str, Any],
    market_analysis: dict[str, Any],
) -> None:
    """Store analysis results so they can be reused."""
    from datetime import datetime, timezone
    cache_key = _analysis_cache_key(product_text, country, telco, language)

    if supabase:
        row: dict[str, Any] = {
            "cache_key": cache_key,
            "country": country,
            "telco": telco,
            "language": language or "",
            "product_brief": product_brief,
            "market_analysis": market_analysis,
        }
        try:
            row["cached_at"] = datetime.now(timezone.utc).isoformat()
            supabase.table("analysis_cache").upsert(row).execute()
            logger.info("Saved analysis cache for key %s", cache_key)
        except Exception as e:
            if "cached_at" in str(e):
                row.pop("cached_at", None)
                try:
                    supabase.table("analysis_cache").upsert(row).execute()
                    logger.info("Saved analysis cache for key %s (without cached_at)", cache_key)
                except Exception as e2:
                    logger.warning("Failed to save analysis cache: %s", e2)
            else:
                logger.warning("Failed to save analysis cache: %s", e)


# ── App Config (Pipeline Settings) ────────────────────────────────────────────

_PIPELINE_DEFAULTS: dict[str, Any] = {
    "max_script_words": 75,
    "num_script_variants": 5,
    "eval_feedback_rounds": 1,
    "num_hook_voices": 3,
    "elevenlabs_tts_model": "eleven_multilingual_v2",
    "elevenlabs_output_format": "mp3_44100_192",
    "voice_stability": 0.35,
    "voice_similarity_boost": 0.80,
    "voice_style": 0.45,
    "bgm_volume_db": -26,
    "bgm_default_style": "upbeat",
    "default_tts_engine": "elevenlabs",
}


def get_pipeline_config() -> dict[str, Any]:
    """Return full pipeline config, merging DB overrides over defaults."""
    config = dict(_PIPELINE_DEFAULTS)
    if supabase:
        try:
            resp = supabase.table("app_config").select("*").execute()
            for row in resp.data or []:
                config[row["key"]] = row["value"]
        except Exception as e:
            logger.warning("Failed to load pipeline config: %s", e)
    return config


def save_pipeline_config(updates: dict[str, Any], updated_by: str = "admin") -> dict[str, Any]:
    """Upsert one or more pipeline config keys. Raises on failure."""
    if not supabase:
        raise RuntimeError("Supabase not configured")
    errors: list[str] = []
    for key, value in updates.items():
        try:
            supabase.table("app_config").upsert({
                "key": key,
                "value": value,
                "updated_by": updated_by,
            }).execute()
        except Exception as e:
            logger.error("Failed to save config key '%s': %s", key, e)
            errors.append(f"{key}: {e}")
    if errors:
        raise RuntimeError("; ".join(errors))
    return get_pipeline_config()
