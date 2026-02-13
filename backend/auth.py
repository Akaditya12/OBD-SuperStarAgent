"""Simple JWT-based authentication for team access."""

from __future__ import annotations

import os
import time
import logging
from typing import Optional

import jwt
from fastapi import Request, WebSocket
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# ── Config ──
LOGIN_USERNAME = os.getenv("LOGIN_USERNAME", "")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "")
JWT_SECRET = os.getenv("JWT_SECRET", "obd-superstar-default-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72  # 3 days

# Routes that don't require authentication
PUBLIC_PATHS = {
    "/api/health",
    "/api/auth/login",
    "/api/auth/me",
}


def auth_enabled() -> bool:
    """Auth is only enforced when LOGIN_USERNAME and LOGIN_PASSWORD are set."""
    return bool(LOGIN_USERNAME and LOGIN_PASSWORD)


def create_token(username: str) -> str:
    """Create a signed JWT token."""
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + (JWT_EXPIRY_HOURS * 3600),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the username, or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
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

    Skips auth if LOGIN_USERNAME/LOGIN_PASSWORD are not configured (local dev).
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

    username = verify_token(token)
    if not username:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"},
        )

    # Attach username to request state
    request.state.username = username
    return await call_next(request)
