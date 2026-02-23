"""JWT-based authentication for team access (Supabase DB-backed with local fallback)."""

from __future__ import annotations

import os
import time
import logging
from typing import Optional, Dict, Any

import jwt
from fastapi import Request, WebSocket
from fastapi.responses import JSONResponse

try:
    import bcrypt
except ImportError:
    bcrypt = None  # type: ignore[assignment]

from backend.database import supabase
from backend.config import SUPABASE_URL

logger = logging.getLogger(__name__)

# ── Config ──
JWT_SECRET = os.getenv("JWT_SECRET", "obd-superstar-default-secret-change-me").strip()
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72  # 3 days

# Optional env-var fallback for local dev (single-user, no Supabase)
_FALLBACK_USERNAME = os.getenv("LOGIN_USERNAME", "")
_FALLBACK_PASSWORD = os.getenv("LOGIN_PASSWORD", "")

PUBLIC_PATHS = {
    "/api/health",
    "/api/auth/login",
    "/api/auth/me",
}

def auth_enabled() -> bool:
    """Auth is enabled if Supabase is configured OR env-var fallback is set."""
    if SUPABASE_URL and supabase:
        return True
    return bool(_FALLBACK_USERNAME and _FALLBACK_PASSWORD)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    if not bcrypt:
        return False
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify credentials against the Supabase users table or env-var fallback."""
    if supabase:
        try:
            response = (
                supabase.table("users")
                .select("*")
                .eq("username", username)
                .maybe_single()
                .execute()
            )
            user_record = response.data
            if not user_record:
                return None
            if not user_record.get("is_active", True):
                logger.warning("Attempted login by deactivated user: %s", username)
                return None
            if verify_password(password, user_record["password_hash"]):
                return user_record
            return None
        except Exception as e:
            logger.error("Error authenticating user %s: %s", username, e)
            return None

    # Env-var fallback (local dev, no Supabase)
    if _FALLBACK_USERNAME and username == _FALLBACK_USERNAME and password == _FALLBACK_PASSWORD:
        return {
            "id": "local",
            "username": _FALLBACK_USERNAME,
            "role": "admin",
            "team": "local",
        }
    return None

def create_token(user: Dict[str, Any]) -> str:
    """Create a signed JWT token with user roles and team."""
    payload = {
        "sub": user.get("username", "unknown"),
        "id": str(user.get("id", "local")),
        "role": user.get("role", "member"),
        "team": user.get("team", "default"),
        "iat": int(time.time()),
        "exp": int(time.time()) + (JWT_EXPIRY_HOURS * 3600),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT token and return the payload, or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.debug("Invalid token")
        return None

def get_token_from_request(request: Request) -> Optional[str]:
    """Extract JWT token from cookie or Authorization header."""
    # Try cookie first
    token = request.cookies.get("obd_token")
    if token:
        return token
    # Try Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None

def get_token_from_websocket(ws: WebSocket) -> Optional[str]:
    """Extract JWT token from WebSocket cookie or query param."""
    # Try cookie
    token = ws.cookies.get("obd_token")
    if token:
        return token
    # Try query parameter
    token = ws.query_params.get("token")
    return token

async def auth_middleware(request: Request, call_next):
    """Middleware that protects API routes with JWT auth.

    Skips auth if Supabase is not configured (local dev fallback).
    """
    path = request.url.path

    # Skip auth if not enabled (local dev without credentials)
    if not auth_enabled():
        return await call_next(request)

    # Skip public paths
    if path in PUBLIC_PATHS:
        return await call_next(request)

    # Skip non-API paths (frontend static files, etc.)
    if not path.startswith("/api/") and not path.startswith("/ws/") and not path.startswith("/outputs/"):
        return await call_next(request)

    # Verify token
    token = get_token_from_request(request)
    if not token:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    payload = verify_token(token)
    if not payload:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"},
        )

    # Attach user info to request state
    request.state.user = payload
    request.state.username = payload.get("sub")
    
    # Admin route guard
    if path.startswith("/api/admin/") and payload.get("role") != "admin":
        return JSONResponse(
            status_code=403,
            content={"error": "Admin privileges required"},
        )
        
    return await call_next(request)
