"""SQLite-based campaign persistence for OBD SuperStar Agent."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "campaigns.db"


def _get_conn() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the campaigns and comments tables if they don't exist."""
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_by TEXT NOT NULL DEFAULT 'local',
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
        logger.info("Campaign database initialized at %s", DB_PATH)
    finally:
        conn.close()


def save_campaign(
    campaign_id: str,
    name: str,
    created_by: str,
    country: str,
    telco: str,
    language: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Save a campaign to the database. Returns the saved campaign summary."""
    # Extract quick-display fields
    final_scripts = result.get("final_scripts", result.get("revised_scripts_round_1", result.get("initial_scripts", {})))
    scripts = final_scripts.get("scripts", [])
    script_count = len(scripts)
    audio_files = result.get("audio", {}).get("audio_files", [])
    has_audio = 1 if any(not f.get("error") for f in audio_files) else 0

    now = datetime.now(timezone.utc).isoformat()
    result_json = json.dumps(result, default=str)

    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO campaigns
                (id, name, created_by, created_at, country, telco, language, result_json, script_count, has_audio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (campaign_id, name, created_by, now, country, telco, language, result_json, script_count, has_audio),
        )
        conn.commit()
        logger.info("Saved campaign '%s' (id=%s, scripts=%d)", name, campaign_id, script_count)
    finally:
        conn.close()

    return {
        "id": campaign_id,
        "name": name,
        "created_by": created_by,
        "created_at": now,
        "country": country,
        "telco": telco,
        "language": language,
        "script_count": script_count,
        "has_audio": bool(has_audio),
    }


def list_campaigns() -> list[dict[str, Any]]:
    """List all campaigns (without full result JSON)."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, name, created_by, created_at, country, telco, language, script_count, has_audio
            FROM campaigns
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "created_by": row["created_by"],
                "created_at": row["created_at"],
                "country": row["country"],
                "telco": row["telco"],
                "language": row["language"],
                "script_count": row["script_count"],
                "has_audio": bool(row["has_audio"]),
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_campaign(campaign_id: str) -> Optional[dict[str, Any]]:
    """Get a single campaign with full result JSON."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "country": row["country"],
            "telco": row["telco"],
            "language": row["language"],
            "script_count": row["script_count"],
            "has_audio": bool(row["has_audio"]),
            "result": json.loads(row["result_json"]),
        }
    finally:
        conn.close()


def delete_campaign(campaign_id: str) -> bool:
    """Delete a campaign and its comments. Returns True if a row was deleted."""
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM campaign_comments WHERE campaign_id = ?", (campaign_id,))
        cursor = conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Deleted campaign id=%s", campaign_id)
        return deleted
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
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO campaign_comments (id, campaign_id, username, text, created_at) VALUES (?, ?, ?, ?, ?)",
            (comment_id, campaign_id, username, text, now),
        )
        conn.commit()
        logger.info("Saved comment %s on campaign %s", comment_id, campaign_id)
    finally:
        conn.close()
    return {
        "id": comment_id,
        "campaign_id": campaign_id,
        "username": username,
        "text": text,
        "created_at": now,
    }


def list_comments(campaign_id: str) -> list[dict[str, Any]]:
    """List all comments for a campaign, newest first."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, campaign_id, username, text, created_at FROM campaign_comments WHERE campaign_id = ? ORDER BY created_at DESC",
            (campaign_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "campaign_id": row["campaign_id"],
                "username": row["username"],
                "text": row["text"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def delete_comment(comment_id: str) -> bool:
    """Delete a comment. Returns True if a row was deleted."""
    conn = _get_conn()
    try:
        cursor = conn.execute("DELETE FROM campaign_comments WHERE id = ?", (comment_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
