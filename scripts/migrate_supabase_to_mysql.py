"""One-shot migration: Supabase Postgres → local MySQL.

Reads every row from the public schema in Supabase and writes to the
matching MySQL tables in order that respects FK constraints.

Env vars (from .env):
  SUPABASE_DB_URL   postgres://postgres.<ref>:<pw>@<pooler>:5432/postgres
  MYSQL_URL         mysql://obd_app:pw@localhost:3306/obd_superstar

Usage:
  python scripts/migrate_supabase_to_mysql.py           # dry-run (counts only)
  python scripts/migrate_supabase_to_mysql.py --write   # actually insert
  python scripts/migrate_supabase_to_mysql.py --write --truncate   # wipe MySQL tables first
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "").strip()
MYSQL_URL = os.getenv("MYSQL_URL", "").strip()

# Tables in FK-safe insertion order
TABLE_ORDER = [
    "users",
    "market_countries",
    "market_languages",
    "market_telcos",
    "product_presets",
    "flow_configs",
    "app_config",
    "audit_log",
    "analysis_cache",
    "campaigns",
    "campaign_comments",
]

# Column lists — use explicit lists so PG and MySQL see the same order
COLUMNS: dict[str, list[str]] = {
    "users": ["id", "username", "email", "password_hash", "role", "team", "is_active", "created_at"],
    "market_countries": ["id", "name", "currency_code", "display_order", "created_at", "updated_at"],
    "market_languages": ["id", "country_id", "name", "display_order", "created_at"],
    "market_telcos": ["id", "country_id", "name", "display_order", "created_at"],
    "product_presets": ["id", "name", "icon", "short_desc", "full_description", "category", "display_order", "created_at", "updated_at"],
    "flow_configs": ["id", "account_key", "service_key", "display_name", "steps", "is_default", "created_at", "updated_at"],
    "app_config": ["key", "value", "updated_by", "updated_at"],
    "audit_log": ["id", "admin_username", "action", "target_user", "details", "created_at"],
    "analysis_cache": ["cache_key", "country", "telco", "language", "product_brief", "market_analysis", "created_at", "updated_at"],
    "campaigns": ["id", "name", "created_by", "team", "created_at", "country", "telco", "language", "result_json", "script_count", "has_audio"],
    "campaign_comments": ["id", "campaign_id", "username", "text", "created_at"],
}

# Columns that store JSON (need json.dumps when inserting into MySQL)
JSON_COLUMNS: dict[str, set[str]] = {
    "flow_configs": {"steps"},
    "app_config": {"value"},
    "audit_log": {"details"},
    "analysis_cache": {"product_brief", "market_analysis"},
    "campaigns": {"result_json"},
}


def _parse_mysql_url(url: str) -> dict:
    p = urlparse(url)
    return {
        "host": p.hostname,
        "port": p.port or 3306,
        "user": unquote(p.username or ""),
        "password": unquote(p.password or ""),
        "db": (p.path or "/").lstrip("/"),
    }


def _convert_value(table: str, col: str, val):
    """Convert a Postgres value to something MySQL / PyMySQL accepts."""
    if val is None:
        return None

    if col in JSON_COLUMNS.get(table, set()):
        # psycopg2 auto-decodes JSONB to Python natives (dict/list/str/int/bool).
        # MySQL JSON column needs valid JSON text — always re-encode.
        return json.dumps(val, ensure_ascii=False, default=str)

    if isinstance(val, uuid.UUID):
        return str(val)

    if isinstance(val, datetime):
        # MySQL DATETIME has no tz — strip tzinfo after converting to UTC.
        if val.tzinfo is not None:
            val = val.astimezone(timezone.utc).replace(tzinfo=None)
        return val

    if isinstance(val, bool):
        return 1 if val else 0

    return val


def _quote_col_mysql(col: str) -> str:
    """Backtick a MySQL identifier (e.g. `key`, `value` are reserved)."""
    return f"`{col}`"


def _quote_col_pg(col: str) -> str:
    """Double-quote a Postgres identifier."""
    return f'"{col}"'


def _build_select(table: str) -> str:
    cols = ", ".join(_quote_col_pg(c) for c in COLUMNS[table])
    return f'SELECT {cols} FROM public."{table}"'


def _build_insert(table: str) -> str:
    cols = COLUMNS[table]
    col_list = ", ".join(_quote_col_mysql(c) for c in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    return f"INSERT INTO `{table}` ({col_list}) VALUES ({placeholders})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Actually insert into MySQL (default: dry-run counts only)")
    parser.add_argument("--truncate", action="store_true", help="TRUNCATE MySQL tables before insert (use with --write)")
    args = parser.parse_args()

    if not SUPABASE_DB_URL or not MYSQL_URL:
        print("ERROR: SUPABASE_DB_URL or MYSQL_URL missing from .env", file=sys.stderr)
        return 2

    import psycopg2
    import pymysql

    print(f"→ Connecting to Supabase Postgres…")
    pg = psycopg2.connect(SUPABASE_DB_URL)
    pg.set_session(readonly=True)

    print(f"→ Connecting to local MySQL…")
    my = pymysql.connect(**_parse_mysql_url(MYSQL_URL), charset="utf8mb4", autocommit=False)

    try:
        if args.write and args.truncate:
            print(f"→ TRUNCATE all MySQL tables first…")
            with my.cursor() as mc:
                mc.execute("SET FOREIGN_KEY_CHECKS = 0")
                for t in reversed(TABLE_ORDER):
                    mc.execute(f"TRUNCATE TABLE `{t}`")
                    print(f"   truncated {t}")
                mc.execute("SET FOREIGN_KEY_CHECKS = 1")
            my.commit()

        total_copied = 0
        summary: list[tuple[str, int, int]] = []  # (table, pg_count, inserted)

        # Temporarily disable FK checks during insert (safer if insertion order is off)
        if args.write:
            with my.cursor() as mc:
                mc.execute("SET FOREIGN_KEY_CHECKS = 0")
            my.commit()

        for table in TABLE_ORDER:
            print(f"\n── {table} ──")
            with pg.cursor() as pc:
                pc.execute(_build_select(table))
                rows = pc.fetchall()
            pg_count = len(rows)
            print(f"  Postgres rows: {pg_count}")

            if not args.write:
                summary.append((table, pg_count, 0))
                continue

            if pg_count == 0:
                summary.append((table, 0, 0))
                continue

            insert_sql = _build_insert(table)
            converted = [
                tuple(_convert_value(table, col, row[i]) for i, col in enumerate(COLUMNS[table]))
                for row in rows
            ]

            with my.cursor() as mc:
                try:
                    mc.executemany(insert_sql, converted)
                    inserted = mc.rowcount
                except Exception as e:
                    my.rollback()
                    print(f"  ERROR inserting {table}: {e}")
                    print(f"  Sample row: {converted[0] if converted else 'none'}")
                    raise
            my.commit()
            total_copied += inserted
            summary.append((table, pg_count, inserted))
            print(f"  Inserted into MySQL: {inserted}")

        # Re-enable FK checks
        if args.write:
            with my.cursor() as mc:
                mc.execute("SET FOREIGN_KEY_CHECKS = 1")
            my.commit()

        print("\n── Summary ──")
        print(f"  {'Table':<22}{'Postgres':>12}{'MySQL':>12}")
        for t, pc_, mc_ in summary:
            match = "✓" if (not args.write) or pc_ == mc_ else "✗"
            print(f"  {t:<22}{pc_:>12}{mc_:>12}  {match}")
        print(f"\n  Total rows copied: {total_copied}")

        if not args.write:
            print("\n  DRY-RUN — pass --write to actually insert.")

        return 0

    finally:
        pg.close()
        my.close()


if __name__ == "__main__":
    sys.exit(main())
