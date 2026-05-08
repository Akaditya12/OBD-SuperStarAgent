"""Database persistence for OBD SuperStar Agent.

Primary: local MySQL (via pymysql). Fallback: SQLite for dev-only.

Function signatures are kept stable so callers don't change. Calling code
wraps sync calls in asyncio.to_thread where needed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, urlparse

from backend.config import MYSQL_URL

logger = logging.getLogger(__name__)

# Legacy symbol kept for backwards compatibility during migration — always None.
# Some modules still `from backend.database import supabase`; those paths are
# dead code post-migration but we keep the name so imports don't fail.
supabase = None

# ── MySQL Setup ─────────────────────────────────────────────────────────────
_USE_MYSQL = bool(MYSQL_URL)
_MYSQL_CONFIG: dict[str, Any] | None = None

if _USE_MYSQL:
    try:
        import pymysql  # noqa: F401
        p = urlparse(MYSQL_URL)
        _MYSQL_CONFIG = {
            "host": p.hostname or "localhost",
            "port": p.port or 3306,
            "user": unquote(p.username or ""),
            "password": unquote(p.password or ""),
            "db": (p.path or "/").lstrip("/"),
            "charset": "utf8mb4",
            "autocommit": False,
        }
        logger.info("MySQL configured: %s@%s:%s/%s",
                    _MYSQL_CONFIG["user"], _MYSQL_CONFIG["host"], _MYSQL_CONFIG["port"], _MYSQL_CONFIG["db"])
    except ImportError:
        logger.warning("pymysql not installed; falling back to SQLite.")
        _USE_MYSQL = False
    except Exception as e:
        logger.error("Failed to parse MYSQL_URL: %s", e)
        _USE_MYSQL = False


def _get_mysql_conn():
    """Open a new MySQL connection. Caller closes."""
    import pymysql
    return pymysql.connect(**_MYSQL_CONFIG)


# ── SQLite Fallback Setup ───────────────────────────────────────────────────
DB_PATH = Path(__file__).parent / "campaigns.db"

def _get_sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize local SQLite tables (MySQL schema is managed via migration/mysql_schema.sql)."""
    if _USE_MYSQL:
        logger.info("Using MySQL. Skipping SQLite init.")
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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_dt() -> datetime:
    """Timezone-naive UTC datetime for MySQL DATETIME columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_json_col(val: Any) -> Any:
    """Parse a JSON value returned from MySQL (may be dict already or a JSON string)."""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, (bytes, bytearray)):
        val = val.decode("utf-8", errors="replace")
    try:
        return json.loads(val)
    except Exception:
        return val


# ── Product Presets ─────────────────────────────────────────────────────────

def list_product_presets() -> list[dict[str, Any]]:
    if _USE_MYSQL:
        conn = _get_mysql_conn()
        try:
            with conn.cursor() as mc:
                mc.execute("""
                    SELECT id, name, icon, short_desc, full_description, category, display_order
                    FROM product_presets ORDER BY display_order, id
                """)
                cols = [c[0] for c in mc.description]
                return [dict(zip(cols, r)) for r in mc.fetchall()]
        except Exception as e:
            logger.error("Failed to list product presets: %s", e)
            return []
        finally:
            conn.close()
    return []


def get_market_options() -> list[dict[str, Any]]:
    if not _USE_MYSQL:
        return []
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute("SELECT id, name, currency_code, display_order FROM market_countries ORDER BY display_order, id")
            countries = [
                {"id": r[0], "name": r[1], "currency_code": r[2] or "", "display_order": r[3]}
                for r in mc.fetchall()
            ]
            if not countries:
                return []
            mc.execute("SELECT country_id, name FROM market_telcos ORDER BY display_order, name")
            telcos_by_country: dict[str, list[str]] = {}
            for cid, name in mc.fetchall():
                telcos_by_country.setdefault(cid, []).append(name)
            mc.execute("SELECT country_id, name FROM market_languages ORDER BY display_order, name")
            langs_by_country: dict[str, list[str]] = {}
            for cid, name in mc.fetchall():
                langs_by_country.setdefault(cid, []).append(name)
        return [
            {
                "id": c["id"],
                "name": c["name"],
                "currency_code": c["currency_code"],
                "telcos": telcos_by_country.get(c["id"], []),
                "languages": langs_by_country.get(c["id"], []),
            }
            for c in countries
        ]
    except Exception as e:
        logger.error("Failed to list market options: %s", e)
        return []
    finally:
        conn.close()


# ── Flow Configs ────────────────────────────────────────────────────────────

_FLOW_COLS = "id, account_key, service_key, display_name, steps, is_default, created_at, updated_at"


def _row_to_flow_config(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "account_key": row[1],
        "service_key": row[2],
        "display_name": row[3],
        "steps": _parse_json_col(row[4]),
        "is_default": bool(row[5]),
        "created_at": row[6].isoformat() if isinstance(row[6], datetime) else row[6],
        "updated_at": row[7].isoformat() if isinstance(row[7], datetime) else row[7],
    }


def list_flow_configs(account_key: str | None = None) -> list[dict[str, Any]]:
    if not _USE_MYSQL:
        return []
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            if account_key and str(account_key).strip():
                mc.execute(
                    f"SELECT {_FLOW_COLS} FROM flow_configs WHERE account_key = %s ORDER BY account_key, service_key",
                    (str(account_key).strip(),),
                )
            else:
                mc.execute(f"SELECT {_FLOW_COLS} FROM flow_configs ORDER BY account_key, service_key")
            return [_row_to_flow_config(r) for r in mc.fetchall()]
    except Exception as e:
        logger.error("Failed to list flow configs: %s", e)
        return []
    finally:
        conn.close()


def get_flow_config(flow_config_id: str | None = None, account_key: str | None = None, service_key: str | None = None) -> dict[str, Any] | None:
    if not _USE_MYSQL:
        return None
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            if flow_config_id:
                mc.execute(f"SELECT {_FLOW_COLS} FROM flow_configs WHERE id = %s LIMIT 1", (flow_config_id,))
            elif account_key is not None and service_key is not None:
                mc.execute(
                    f"SELECT {_FLOW_COLS} FROM flow_configs WHERE account_key = %s AND service_key = %s LIMIT 1",
                    (account_key, service_key),
                )
            else:
                return None
            row = mc.fetchone()
            return _row_to_flow_config(row) if row else None
    except Exception as e:
        logger.error("Failed to get flow config: %s", e)
        return None
    finally:
        conn.close()


def create_flow_config(account_key: str, service_key: str, display_name: str,
                        steps: list[dict[str, Any]], is_default: bool = False) -> dict[str, Any] | None:
    if not _USE_MYSQL:
        return None
    conn = _get_mysql_conn()
    new_id = str(uuid.uuid4())
    try:
        with conn.cursor() as mc:
            mc.execute(
                "INSERT INTO flow_configs (id, account_key, service_key, display_name, steps, is_default) VALUES (%s,%s,%s,%s,%s,%s)",
                (new_id, account_key.strip(), service_key.strip(), display_name.strip(),
                 json.dumps(steps, ensure_ascii=False), 1 if is_default else 0),
            )
        conn.commit()
        return get_flow_config(flow_config_id=new_id)
    except Exception as e:
        logger.error("Failed to create flow config: %s", e)
        conn.rollback()
        return None
    finally:
        conn.close()


def update_flow_config(flow_config_id: str, *, display_name: str | None = None,
                        steps: list[dict[str, Any]] | None = None,
                        is_default: bool | None = None) -> dict[str, Any] | None:
    if not _USE_MYSQL:
        return None
    sets: list[str] = []
    params: list[Any] = []
    if display_name is not None:
        sets.append("display_name = %s")
        params.append(display_name.strip())
    if steps is not None:
        sets.append("steps = %s")
        params.append(json.dumps(steps, ensure_ascii=False))
    if is_default is not None:
        sets.append("is_default = %s")
        params.append(1 if is_default else 0)
    if not sets:
        return get_flow_config(flow_config_id=flow_config_id)
    params.append(flow_config_id)
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute(f"UPDATE flow_configs SET {', '.join(sets)} WHERE id = %s", params)
        conn.commit()
        return get_flow_config(flow_config_id=flow_config_id)
    except Exception as e:
        logger.error("Failed to update flow config: %s", e)
        conn.rollback()
        return None
    finally:
        conn.close()


# ── Campaigns ───────────────────────────────────────────────────────────────

_CAMPAIGN_COLS = "id, name, created_by, team, created_at, country, telco, language, script_count, has_audio"


def _row_to_campaign_summary(row: tuple, cols: list[str]) -> dict[str, Any]:
    d = dict(zip(cols, row))
    if isinstance(d.get("created_at"), datetime):
        d["created_at"] = d["created_at"].isoformat()
    if "has_audio" in d:
        d["has_audio"] = bool(d["has_audio"])
    return d


def save_campaign(campaign_id: str, name: str, created_by: str, country: str, telco: str,
                   language: str, result: dict[str, Any], team: str = "default") -> dict[str, Any]:
    is_stv = result.get("campaign_type") == "script_to_voice"
    if is_stv:
        script_count = 1
        audio_files = result.get("audio", {}).get("audio_files", [])
    else:
        final_scripts = result.get("final_scripts", result.get("revised_scripts_round_1", result.get("initial_scripts", {})))
        script_count = len(final_scripts.get("scripts", []))
        audio_files = result.get("audio", {}).get("audio_files", [])
    has_audio = 1 if any(not f.get("error") for f in audio_files) else 0

    now_iso = _now_iso()
    campaign_summary = {
        "id": campaign_id,
        "name": name,
        "created_by": created_by,
        "team": team,
        "created_at": now_iso,
        "country": country,
        "telco": telco,
        "language": language,
        "script_count": script_count,
        "has_audio": bool(has_audio),
    }

    if _USE_MYSQL:
        conn = _get_mysql_conn()
        try:
            with conn.cursor() as mc:
                mc.execute(
                    """
                    INSERT INTO campaigns
                        (id, name, created_by, team, created_at, country, telco, language, result_json, script_count, has_audio)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                        name=VALUES(name), created_by=VALUES(created_by), team=VALUES(team),
                        created_at=VALUES(created_at), country=VALUES(country), telco=VALUES(telco),
                        language=VALUES(language), result_json=VALUES(result_json),
                        script_count=VALUES(script_count), has_audio=VALUES(has_audio)
                    """,
                    (campaign_id, name, created_by, team, _now_dt(), country, telco, language,
                     json.dumps(result, ensure_ascii=False, default=str), script_count, has_audio),
                )
            conn.commit()
            logger.info("Saved campaign '%s' to MySQL", name)
        except Exception as e:
            logger.error("Failed to save campaign to MySQL: %s", e)
            conn.rollback()
            raise
        finally:
            conn.close()
        return campaign_summary

    # SQLite fallback
    conn = _get_sqlite_conn()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO campaigns
                (id, name, created_by, team, created_at, country, telco, language, result_json, script_count, has_audio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (campaign_id, name, created_by, team, now_iso, country, telco, language,
             json.dumps(result, default=str), script_count, has_audio),
        )
        conn.commit()
        logger.info("Saved campaign '%s' to SQLite", name)
    finally:
        conn.close()
    return campaign_summary


def list_campaigns(limit: int = 50, created_by: Optional[str] = None) -> list[dict[str, Any]]:
    if _USE_MYSQL:
        conn = _get_mysql_conn()
        try:
            with conn.cursor() as mc:
                if created_by is not None:
                    mc.execute(
                        f"SELECT {_CAMPAIGN_COLS} FROM campaigns WHERE created_by = %s ORDER BY created_at DESC LIMIT %s",
                        (created_by, limit),
                    )
                else:
                    mc.execute(
                        f"SELECT {_CAMPAIGN_COLS} FROM campaigns ORDER BY created_at DESC LIMIT %s",
                        (limit,),
                    )
                cols = [c[0] for c in mc.description]
                return [_row_to_campaign_summary(r, cols) for r in mc.fetchall()]
        except Exception as e:
            logger.error("Failed to list campaigns from MySQL: %s", e)
            return []
        finally:
            conn.close()

    conn = _get_sqlite_conn()
    try:
        if created_by is not None:
            rows = conn.execute(
                f"SELECT {_CAMPAIGN_COLS} FROM campaigns WHERE created_by = ? ORDER BY created_at DESC LIMIT ?",
                (created_by, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT {_CAMPAIGN_COLS} FROM campaigns ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_campaign(campaign_id: str) -> Optional[dict[str, Any]]:
    if _USE_MYSQL:
        conn = _get_mysql_conn()
        try:
            with conn.cursor() as mc:
                mc.execute("SELECT * FROM campaigns WHERE id = %s LIMIT 1", (campaign_id,))
                row = mc.fetchone()
                if not row:
                    return None
                cols = [c[0] for c in mc.description]
                d = dict(zip(cols, row))
            if isinstance(d.get("created_at"), datetime):
                d["created_at"] = d["created_at"].isoformat()
            d["has_audio"] = bool(d.get("has_audio"))
            d["result"] = _parse_json_col(d.pop("result_json", None)) or {}
            return d
        except Exception as e:
            logger.error("Failed to get campaign from MySQL: %s", e)
            return None
        finally:
            conn.close()

    conn = _get_sqlite_conn()
    try:
        row = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["result"] = json.loads(d.pop("result_json"))
        return d
    finally:
        conn.close()


def delete_campaign(campaign_id: str) -> bool:
    if _USE_MYSQL:
        conn = _get_mysql_conn()
        try:
            with conn.cursor() as mc:
                mc.execute("DELETE FROM campaigns WHERE id = %s", (campaign_id,))
                deleted = mc.rowcount
            conn.commit()
            return deleted > 0
        except Exception as e:
            logger.error("Failed to delete campaign from MySQL: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    conn = _get_sqlite_conn()
    try:
        conn.execute("DELETE FROM campaign_comments WHERE campaign_id = ?", (campaign_id,))
        cur = conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Campaign Comments ───────────────────────────────────────────────────────

def save_comment(comment_id: str, campaign_id: str, username: str, text: str) -> dict[str, Any]:
    now_iso = _now_iso()
    comment_data = {
        "id": comment_id,
        "campaign_id": campaign_id,
        "username": username,
        "text": text,
        "created_at": now_iso,
    }
    if _USE_MYSQL:
        conn = _get_mysql_conn()
        try:
            with conn.cursor() as mc:
                mc.execute(
                    "INSERT INTO campaign_comments (id, campaign_id, username, text, created_at) VALUES (%s,%s,%s,%s,%s)",
                    (comment_id, campaign_id, username, text, _now_dt()),
                )
            conn.commit()
        except Exception as e:
            logger.error("Failed to save comment to MySQL: %s", e)
            conn.rollback()
            raise
        finally:
            conn.close()
        return comment_data

    conn = _get_sqlite_conn()
    try:
        conn.execute(
            "INSERT INTO campaign_comments (id, campaign_id, username, text, created_at) VALUES (?, ?, ?, ?, ?)",
            (comment_id, campaign_id, username, text, now_iso),
        )
        conn.commit()
    finally:
        conn.close()
    return comment_data


def list_comments(campaign_id: str) -> list[dict[str, Any]]:
    if _USE_MYSQL:
        conn = _get_mysql_conn()
        try:
            with conn.cursor() as mc:
                mc.execute(
                    "SELECT id, campaign_id, username, text, created_at FROM campaign_comments WHERE campaign_id = %s ORDER BY created_at DESC",
                    (campaign_id,),
                )
                rows = mc.fetchall()
            return [
                {
                    "id": r[0], "campaign_id": r[1], "username": r[2], "text": r[3],
                    "created_at": r[4].isoformat() if isinstance(r[4], datetime) else r[4],
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Failed to list comments from MySQL: %s", e)
            return []
        finally:
            conn.close()

    conn = _get_sqlite_conn()
    try:
        rows = conn.execute(
            "SELECT id, campaign_id, username, text, created_at FROM campaign_comments WHERE campaign_id = ? ORDER BY created_at DESC",
            (campaign_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_comment(comment_id: str) -> bool:
    if _USE_MYSQL:
        conn = _get_mysql_conn()
        try:
            with conn.cursor() as mc:
                mc.execute("DELETE FROM campaign_comments WHERE id = %s", (comment_id,))
                deleted = mc.rowcount
            conn.commit()
            return deleted > 0
        except Exception as e:
            logger.error("Failed to delete comment from MySQL: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    conn = _get_sqlite_conn()
    try:
        cur = conn.execute("DELETE FROM campaign_comments WHERE id = ?", (comment_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Analysis Cache ──────────────────────────────────────────────────────────

def _analysis_cache_key(product_text: str, country: str, telco: str, language: str | None) -> str:
    raw = f"{product_text[:5000]}|{country}|{telco}|{language or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_cached_analysis(product_text: str, country: str, telco: str, language: str | None) -> Optional[dict[str, Any]]:
    if not _USE_MYSQL:
        return None
    cache_key = _analysis_cache_key(product_text, country, telco, language)
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute(
                "SELECT product_brief, market_analysis FROM analysis_cache WHERE cache_key = %s LIMIT 1",
                (cache_key,),
            )
            row = mc.fetchone()
            if row:
                logger.info("Analysis cache EXACT HIT for key %s", cache_key)
                return {
                    "product_brief": _parse_json_col(row[0]),
                    "market_analysis": _parse_json_col(row[1]),
                    "match_type": "exact",
                }
            mc.execute(
                "SELECT market_analysis FROM analysis_cache WHERE country = %s AND telco = %s ORDER BY cache_key DESC LIMIT 1",
                (country, telco),
            )
            row = mc.fetchone()
            if row:
                logger.info("Analysis cache PARTIAL HIT for %s/%s", country, telco)
                return {
                    "product_brief": None,
                    "market_analysis": _parse_json_col(row[0]),
                    "match_type": "partial",
                }
    except Exception as e:
        logger.warning("Analysis cache lookup failed: %s", e)
    finally:
        conn.close()
    return None


def check_cache_exists(product_text: str, country: str, telco: str, language: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {"exact": False, "partial": False}
    if not _USE_MYSQL:
        return result
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            if product_text:
                cache_key = _analysis_cache_key(product_text, country, telco, language)
                mc.execute("SELECT created_at FROM analysis_cache WHERE cache_key = %s LIMIT 1", (cache_key,))
                row = mc.fetchone()
                if row:
                    result["exact"] = True
                    result["exact_cached_at"] = row[0].isoformat() if isinstance(row[0], datetime) else (row[0] or "")
                    return result
            mc.execute(
                "SELECT created_at FROM analysis_cache WHERE country = %s AND telco = %s LIMIT 1",
                (country, telco),
            )
            row = mc.fetchone()
            if row:
                result["partial"] = True
                result["partial_cached_at"] = row[0].isoformat() if isinstance(row[0], datetime) else (row[0] or "")
    except Exception as e:
        logger.warning("Cache check failed: %s", e)
    finally:
        conn.close()
    return result


def save_analysis_cache(product_text: str, country: str, telco: str, language: str | None,
                         product_brief: dict[str, Any], market_analysis: dict[str, Any]) -> None:
    if not _USE_MYSQL:
        return
    cache_key = _analysis_cache_key(product_text, country, telco, language)
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute(
                """
                INSERT INTO analysis_cache (cache_key, country, telco, language, product_brief, market_analysis)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    country=VALUES(country), telco=VALUES(telco), language=VALUES(language),
                    product_brief=VALUES(product_brief), market_analysis=VALUES(market_analysis)
                """,
                (cache_key, country, telco, language or "",
                 json.dumps(product_brief, ensure_ascii=False, default=str),
                 json.dumps(market_analysis, ensure_ascii=False, default=str)),
            )
        conn.commit()
        logger.info("Saved analysis cache for key %s", cache_key)
    except Exception as e:
        logger.warning("Failed to save analysis cache: %s", e)
        conn.rollback()
    finally:
        conn.close()


# ── App Config (Pipeline Settings) ──────────────────────────────────────────

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
    config = dict(_PIPELINE_DEFAULTS)
    if not _USE_MYSQL:
        return config
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute("SELECT `key`, `value` FROM app_config")
            for key, value in mc.fetchall():
                config[key] = _parse_json_col(value)
    except Exception as e:
        logger.warning("Failed to load pipeline config: %s", e)
    finally:
        conn.close()
    return config


def save_pipeline_config(updates: dict[str, Any], updated_by: str = "admin") -> dict[str, Any]:
    if not _USE_MYSQL:
        raise RuntimeError("MySQL not configured — cannot save pipeline config")
    conn = _get_mysql_conn()
    errors: list[str] = []
    try:
        with conn.cursor() as mc:
            for key, value in updates.items():
                try:
                    mc.execute(
                        """
                        INSERT INTO app_config (`key`, `value`, updated_by) VALUES (%s,%s,%s)
                        ON DUPLICATE KEY UPDATE `value`=VALUES(`value`), updated_by=VALUES(updated_by)
                        """,
                        (key, json.dumps(value, ensure_ascii=False, default=str), updated_by),
                    )
                except Exception as e:
                    logger.error("Failed to save config key '%s': %s", key, e)
                    errors.append(f"{key}: {e}")
        conn.commit()
    finally:
        conn.close()
    if errors:
        raise RuntimeError("; ".join(errors))
    return get_pipeline_config()


def delete_pipeline_config(key: str) -> bool:
    """Delete a single app_config row. Used for resetting agent prompts."""
    if not _USE_MYSQL:
        return False
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute("DELETE FROM app_config WHERE `key` = %s", (key,))
            deleted = mc.rowcount
        conn.commit()
        return deleted > 0
    except Exception as e:
        logger.error("Failed to delete config key '%s': %s", key, e)
        conn.rollback()
        return False
    finally:
        conn.close()


# ── Users & Audit ───────────────────────────────────────────────────────────

_USER_COLS = "id, username, email, password_hash, role, team, is_active, created_at"
_USER_PUBLIC_COLS = "id, username, email, role, team, is_active, created_at"


def _row_to_user(row: tuple, cols: list[str]) -> dict[str, Any]:
    d = dict(zip(cols, row))
    if isinstance(d.get("created_at"), datetime):
        d["created_at"] = d["created_at"].isoformat()
    if "is_active" in d:
        d["is_active"] = bool(d["is_active"])
    return d


def get_user_by_username(username: str) -> Optional[dict[str, Any]]:
    """Full user row including password_hash (for auth)."""
    if not _USE_MYSQL:
        return None
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute(f"SELECT {_USER_COLS} FROM users WHERE username = %s LIMIT 1", (username,))
            row = mc.fetchone()
            if not row:
                return None
            cols = [c[0] for c in mc.description]
            return _row_to_user(row, cols)
    except Exception as e:
        logger.error("Failed to get user by username: %s", e)
        return None
    finally:
        conn.close()


def list_users() -> list[dict[str, Any]]:
    """List users without password hashes."""
    if not _USE_MYSQL:
        return []
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute(f"SELECT {_USER_PUBLIC_COLS} FROM users ORDER BY created_at")
            cols = [c[0] for c in mc.description]
            return [_row_to_user(r, cols) for r in mc.fetchall()]
    except Exception as e:
        logger.error("Failed to list users: %s", e)
        return []
    finally:
        conn.close()


def create_user(username: str, email: str, password_hash: str, role: str,
                 team: str = "default", is_active: bool = True) -> Optional[dict[str, Any]]:
    if not _USE_MYSQL:
        return None
    new_id = str(uuid.uuid4())
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute(
                "INSERT INTO users (id, username, email, password_hash, role, team, is_active) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (new_id, username, email, password_hash, role, team, 1 if is_active else 0),
            )
        conn.commit()
        return get_user_by_id(new_id, public=True)
    except Exception as e:
        logger.error("Failed to create user: %s", e)
        conn.rollback()
        raise
    finally:
        conn.close()


def get_user_by_id(user_id: str, public: bool = True) -> Optional[dict[str, Any]]:
    if not _USE_MYSQL:
        return None
    cols_sql = _USER_PUBLIC_COLS if public else _USER_COLS
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute(f"SELECT {cols_sql} FROM users WHERE id = %s LIMIT 1", (user_id,))
            row = mc.fetchone()
            if not row:
                return None
            cols = [c[0] for c in mc.description]
            return _row_to_user(row, cols)
    except Exception as e:
        logger.error("Failed to get user by id: %s", e)
        return None
    finally:
        conn.close()


def update_user(user_id: str, *, role: str | None = None, team: str | None = None,
                 is_active: bool | None = None, password_hash: str | None = None) -> Optional[dict[str, Any]]:
    if not _USE_MYSQL:
        return None
    sets: list[str] = []
    params: list[Any] = []
    if role is not None:
        sets.append("role = %s"); params.append(role)
    if team is not None:
        sets.append("team = %s"); params.append(team)
    if is_active is not None:
        sets.append("is_active = %s"); params.append(1 if is_active else 0)
    if password_hash is not None:
        sets.append("password_hash = %s"); params.append(password_hash)
    if not sets:
        return get_user_by_id(user_id, public=True)
    params.append(user_id)
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = %s", params)
        conn.commit()
        return get_user_by_id(user_id, public=True)
    except Exception as e:
        logger.error("Failed to update user: %s", e)
        conn.rollback()
        return None
    finally:
        conn.close()


def deactivate_user(user_id: str) -> bool:
    return update_user(user_id, is_active=False) is not None


def log_audit(admin_username: str, action: str, target_user: str | None = None,
               details: dict[str, Any] | None = None) -> None:
    """Write an entry to audit_log. Best-effort: swallows errors."""
    if not _USE_MYSQL:
        return
    conn = _get_mysql_conn()
    try:
        with conn.cursor() as mc:
            mc.execute(
                "INSERT INTO audit_log (id, admin_username, action, target_user, details) VALUES (%s,%s,%s,%s,%s)",
                (str(uuid.uuid4()), admin_username, action, target_user,
                 json.dumps(details or {}, ensure_ascii=False, default=str)),
            )
        conn.commit()
    except Exception as e:
        logger.warning("Audit log write failed: %s", e)
    finally:
        conn.close()
