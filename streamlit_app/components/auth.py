"""Admin-managed user authentication with SQLite + bcrypt."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

import bcrypt
import streamlit as st

DB_PATH = Path(__file__).parent.parent / "users.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_auth_db() -> None:
    """Create users table and seed admin from st.secrets if needed."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_by TEXT DEFAULT 'system',
            created_at REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()

    admin_user = st.secrets.get("ADMIN_USERNAME", "")
    admin_pass = st.secrets.get("ADMIN_PASSWORD", "")
    if admin_user and admin_pass:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (admin_user,)
        ).fetchone()
        if not existing:
            hashed = bcrypt.hashpw(admin_pass.encode(), bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_by, created_at) VALUES (?, ?, 'admin', 'system', ?)",
                (admin_user, hashed, time.time()),
            )
            conn.commit()
    conn.close()


def verify_user(username: str, password: str) -> dict[str, Any] | None:
    """Verify credentials. Returns user dict or None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
    ).fetchone()
    conn.close()
    if row and bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return dict(row)
    return None


def create_user(username: str, password: str, role: str = "user", created_by: str = "admin") -> bool:
    """Create a new user. Returns True on success."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, hashed, role, created_by, time.time()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def list_users() -> list[dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, username, role, created_by, created_at, is_active FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_user_active(user_id: int, active: bool) -> None:
    conn = _get_conn()
    conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if active else 0, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id: int) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def reset_password(user_id: int, new_password: str) -> None:
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    conn = _get_conn()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed, user_id))
    conn.commit()
    conn.close()


def require_auth() -> dict[str, Any] | None:
    """Check session state for auth. Returns user dict or shows login and returns None."""
    if "user" in st.session_state and st.session_state["user"]:
        return st.session_state["user"]
    return None


def show_login_form() -> bool:
    """Render login form. Returns True if user just logged in successfully."""
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem;">
            <h1 style="font-size:2rem; font-weight:700;">OBD SuperStar Agent</h1>
            <p style="color:#888; font-size:0.95rem;">Sign in to continue</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
            return False
        user = verify_user(username, password)
        if user:
            st.session_state["user"] = {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
            }
            st.rerun()
            return True
        else:
            st.error("Invalid username or password.")
    return False
