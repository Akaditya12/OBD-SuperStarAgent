"""Real-time collaboration: WebSocket rooms, presence tracking, and live events."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


# ── Presence ──────────────────────────────────────────────────────────────────

@dataclass
class PresenceUser:
    """Represents an online user."""
    username: str
    connected_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    viewing_campaign: Optional[str] = None  # campaign_id they're currently viewing
    color: str = ""  # assigned avatar color

    def to_dict(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "connected_at": self.connected_at,
            "last_active": self.last_active,
            "viewing_campaign": self.viewing_campaign,
            "color": self.color,
        }


# Predefined avatar colors for presence dots
AVATAR_COLORS = [
    "#5c7cfa", "#ff6b6b", "#51cf66", "#fcc419", "#cc5de8",
    "#22b8cf", "#ff922b", "#f06595", "#20c997", "#845ef7",
]

# Global presence store: ws_id -> PresenceUser
_presence: dict[str, PresenceUser] = {}
# Map ws_id -> WebSocket for broadcasting
_presence_sockets: dict[str, WebSocket] = {}
_color_index = 0


def _next_color() -> str:
    global _color_index
    color = AVATAR_COLORS[_color_index % len(AVATAR_COLORS)]
    _color_index += 1
    return color


def register_user(ws_id: str, username: str, ws: WebSocket) -> PresenceUser:
    """Register a user as online."""
    user = PresenceUser(username=username, color=_next_color())
    _presence[ws_id] = user
    _presence_sockets[ws_id] = ws
    logger.info(f"[Presence] {username} connected (ws_id={ws_id})")
    return user


def unregister_user(ws_id: str) -> Optional[PresenceUser]:
    """Remove a user from online presence."""
    user = _presence.pop(ws_id, None)
    _presence_sockets.pop(ws_id, None)
    if user:
        logger.info(f"[Presence] {user.username} disconnected")
    return user


def update_user_activity(ws_id: str, campaign_id: Optional[str] = None) -> None:
    """Update a user's last active time and optionally which campaign they're viewing."""
    user = _presence.get(ws_id)
    if user:
        user.last_active = time.time()
        if campaign_id is not None:
            user.viewing_campaign = campaign_id


def get_online_users() -> list[dict[str, Any]]:
    """Get all currently online users."""
    return [u.to_dict() for u in _presence.values()]


def get_users_viewing_campaign(campaign_id: str) -> list[dict[str, Any]]:
    """Get users currently viewing a specific campaign."""
    return [
        u.to_dict()
        for u in _presence.values()
        if u.viewing_campaign == campaign_id
    ]


# ── Collaboration Rooms ──────────────────────────────────────────────────────

@dataclass
class CollaborationRoom:
    """A WebSocket room for a specific campaign."""
    campaign_id: str
    subscribers: dict[str, WebSocket] = field(default_factory=dict)  # ws_id -> WebSocket

    async def broadcast(self, event: dict[str, Any], exclude_ws_id: Optional[str] = None) -> None:
        """Send an event to all subscribers in this room."""
        message = event
        dead_ids = []
        for ws_id, ws in self.subscribers.items():
            if ws_id == exclude_ws_id:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead_ids.append(ws_id)
        for ws_id in dead_ids:
            self.subscribers.pop(ws_id, None)

    def add(self, ws_id: str, ws: WebSocket) -> None:
        self.subscribers[ws_id] = ws

    def remove(self, ws_id: str) -> None:
        self.subscribers.pop(ws_id, None)

    @property
    def member_count(self) -> int:
        return len(self.subscribers)


# Global rooms: campaign_id -> CollaborationRoom
_rooms: dict[str, CollaborationRoom] = {}


def get_or_create_room(campaign_id: str) -> CollaborationRoom:
    """Get or create a collaboration room for a campaign."""
    if campaign_id not in _rooms:
        _rooms[campaign_id] = CollaborationRoom(campaign_id=campaign_id)
    return _rooms[campaign_id]


def cleanup_room(campaign_id: str) -> None:
    """Remove a room if it has no subscribers."""
    room = _rooms.get(campaign_id)
    if room and room.member_count == 0:
        del _rooms[campaign_id]
        logger.info(f"[Room] Cleaned up empty room for campaign {campaign_id}")


# ── Activity Events ──────────────────────────────────────────────────────────

# In-memory activity feed (last N events)
_activity_feed: list[dict[str, Any]] = []
MAX_ACTIVITY_ITEMS = 50


def record_activity(
    event_type: str,
    username: str,
    campaign_id: Optional[str] = None,
    campaign_name: Optional[str] = None,
    detail: Optional[str] = None,
) -> dict[str, Any]:
    """Record an activity event and broadcast to all online users."""
    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,  # "campaign_created", "comment_added", "user_joined", "user_left"
        "username": username,
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "detail": detail,
        "timestamp": time.time(),
    }
    _activity_feed.insert(0, event)
    if len(_activity_feed) > MAX_ACTIVITY_ITEMS:
        _activity_feed.pop()
    return event


def get_recent_activity(limit: int = 20) -> list[dict[str, Any]]:
    """Get the most recent activity events."""
    return _activity_feed[:limit]


async def broadcast_to_all(event: dict[str, Any]) -> None:
    """Broadcast an event to ALL connected presence sockets."""
    dead_ids = []
    for ws_id, ws in _presence_sockets.items():
        try:
            await ws.send_json(event)
        except Exception:
            dead_ids.append(ws_id)
    for ws_id in dead_ids:
        _presence_sockets.pop(ws_id, None)
        _presence.pop(ws_id, None)
