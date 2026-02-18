"""FastAPI application -- REST API + WebSocket for the OBD SuperStar Agent."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from backend.auth import (
    auth_enabled,
    auth_middleware,
    create_token,
    get_token_from_websocket,
    verify_token,
    LOGIN_USERNAME,
    LOGIN_PASSWORD,
)
from backend.config import OUTPUTS_DIR
from backend.database import (
    init_db,
    save_campaign,
    list_campaigns,
    get_campaign,
    delete_campaign,
    save_comment,
    list_comments,
    delete_comment,
)
from backend.collaboration import (
    register_user,
    unregister_user,
    update_user_activity,
    get_online_users,
    get_users_viewing_campaign,
    get_or_create_room,
    cleanup_room,
    record_activity,
    get_recent_activity,
    broadcast_to_all,
)
from backend.orchestrator import PipelineOrchestrator

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ──
app = FastAPI(
    title="OBD SuperStar Agent",
    description="Multi-agent AI system for generating OBD promotional scripts and audio",
    version="1.0.0",
)

# CORS -- use ALLOWED_ORIGINS env var in production, default to * for local dev
import os
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware -- only active when LOGIN_USERNAME + LOGIN_PASSWORD are set
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

# Serve generated audio files
OUTPUTS_DIR.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# Initialize campaign database
init_db()

# ── In-memory session store ──
sessions: dict[str, dict[str, Any]] = {}


# ── Background pipeline tracker ──

@dataclass
class PipelineState:
    """Tracks a running or completed pipeline."""
    session_id: str
    status: str = "running"  # running | done | error
    progress_log: list[dict[str, Any]] = field(default_factory=list)
    result: Optional[dict[str, Any]] = None
    error_message: str = ""
    task: Optional[asyncio.Task] = None  # type: ignore[type-arg]
    subscribers: list[WebSocket] = field(default_factory=list)

pipelines: dict[str, PipelineState] = {}


async def _run_pipeline_bg(
    state: PipelineState,
    product_text: str,
    country: str,
    telco: str,
    language: Optional[str],
    provider: Optional[str],
) -> None:
    """Run the pipeline as a background task, storing progress in state."""

    async def on_progress(agent: str, status: str, data: dict[str, Any]) -> None:
        msg = {
            "agent": agent,
            "status": status,
            "message": data.get("message", ""),
            "data": {
                k: v for k, v in data.items()
                if k != "message" and _is_json_serializable(v)
            },
        }
        state.progress_log.append(msg)
        # Broadcast to any connected WebSocket subscribers
        dead: list[WebSocket] = []
        for ws in state.subscribers:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            state.subscribers.remove(ws)

    try:
        orchestrator = PipelineOrchestrator(
            provider=provider,
            on_progress=on_progress,
        )
        result = await orchestrator.run(
            product_text=product_text,
            country=country,
            telco=telco,
            language=language,
        )
        session_id = result.get("session_id", state.session_id)
        result["country"] = country
        result["telco"] = telco
        result["language"] = language or ""
        sessions[session_id] = result
        # Also store under the pipeline's session_id so the frontend can find it
        if state.session_id != session_id:
            sessions[state.session_id] = result
        state.result = _make_serializable(result)
        state.status = "error" if "error" in result else "done"

        # Notify subscribers of completion
        done_msg = {
            "agent": "Pipeline",
            "status": state.status,
            "message": result.get("error", "Pipeline complete"),
            "session_id": session_id,
            "result": state.result,
        }
        state.progress_log.append(done_msg)
        dead = []
        for ws in state.subscribers:
            try:
                await ws.send_json(done_msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            state.subscribers.remove(ws)

    except Exception as e:
        logger.exception(f"Background pipeline error: {e}")
        state.status = "error"
        state.error_message = str(e)
        err_msg = {
            "agent": "Pipeline",
            "status": "error",
            "message": str(e),
        }
        state.progress_log.append(err_msg)
        for ws in list(state.subscribers):
            try:
                await ws.send_json(err_msg)
            except Exception:
                pass


# ── REST Endpoints ──


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "OBD SuperStar Agent"}


# ── Auth Endpoints ──


@app.post("/api/auth/login")
async def login(request: Request):
    """Authenticate with username/password and receive a JWT cookie."""
    if not auth_enabled():
        return {"message": "Auth not enabled", "authenticated": True}

    body = await request.json()
    username = body.get("username", "")
    password = body.get("password", "")

    if username == LOGIN_USERNAME and password == LOGIN_PASSWORD:
        token = create_token(username)
        response = JSONResponse(content={
            "message": "Login successful",
            "authenticated": True,
            "username": username,
        })
        response.set_cookie(
            key="obd_token",
            value=token,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
            max_age=72 * 3600,  # 3 days
        )
        return response
    else:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid username or password"},
        )


@app.get("/api/auth/me")
async def auth_me(request: Request):
    """Check if the current user is authenticated."""
    if not auth_enabled():
        return {"authenticated": True, "auth_enabled": False, "username": "local"}

    from backend.auth import get_token_from_request
    token = get_token_from_request(request)
    if token:
        username = verify_token(token)
        if username:
            return {"authenticated": True, "auth_enabled": True, "username": username}

    return JSONResponse(
        status_code=401,
        content={"authenticated": False, "auth_enabled": True},
    )


@app.post("/api/auth/logout")
async def logout():
    """Clear the auth cookie."""
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("obd_token")
    return response


# ── File Upload / Text Extraction ──


@app.post("/api/upload/extract-text")
async def extract_text_from_file(file: UploadFile = File(...)):
    """Extract text content from uploaded documents (PDF, DOCX, PPTX, TXT, MD)."""
    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No file provided"})

    ext = Path(file.filename).suffix.lower()
    content = await file.read()

    try:
        if ext == ".pdf":
            import pdfplumber
            import io
            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            text = "\n\n".join(text_parts)

        elif ext in (".doc", ".docx"):
            import docx
            import io
            doc = docx.Document(io.BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

        elif ext == ".pptx":
            from pptx import Presentation
            import io
            prs = Presentation(io.BytesIO(content))
            text_parts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        text_parts.append(shape.text)
            text = "\n\n".join(text_parts)

        elif ext in (".txt", ".md"):
            text = content.decode("utf-8", errors="replace")

        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unsupported file type: {ext}"},
            )

        if not text.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Could not extract any text from the file"},
            )

        logger.info(f"Extracted {len(text)} chars from {file.filename} ({ext})")
        return {"text": text, "filename": file.filename, "chars": len(text)}

    except Exception as e:
        logger.error(f"File extraction failed for {file.filename}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to extract text: {str(e)}"},
        )


# ── Background Pipeline Endpoints ──


@app.post("/api/generate/start")
async def start_pipeline(request: Request):
    """Start the pipeline as a background task. Returns session_id immediately."""
    body = await request.json()
    product_text = body.get("product_text", "")
    country = body.get("country", "")
    telco = body.get("telco", "")
    language = body.get("language")
    provider = body.get("provider")

    if not product_text or not country or not telco:
        return JSONResponse(
            status_code=400,
            content={"error": "product_text, country, and telco are required"},
        )

    session_id = uuid.uuid4().hex[:8]
    state = PipelineState(session_id=session_id)
    pipelines[session_id] = state

    task = asyncio.create_task(
        _run_pipeline_bg(state, product_text, country, telco, language, provider)
    )
    state.task = task

    logger.info(f"Pipeline started in background: session_id={session_id}")
    return {"session_id": session_id, "status": "running"}


@app.get("/api/generate/{session_id}/status")
async def pipeline_status(session_id: str):
    """Get current pipeline status, progress log, and result if done."""
    state = pipelines.get(session_id)
    if not state:
        # Check if it's a completed session from the old flow
        if session_id in sessions:
            return {
                "session_id": session_id,
                "status": "done",
                "progress": [],
                "result": _make_serializable(sessions[session_id]),
            }
        return JSONResponse(status_code=404, content={"error": "Pipeline not found"})

    resp: dict[str, Any] = {
        "session_id": session_id,
        "status": state.status,
        "progress": state.progress_log,
    }
    if state.result:
        resp["result"] = state.result
    if state.error_message:
        resp["error"] = state.error_message
    return resp


@app.post("/api/generate")
async def generate_scripts(
    product_file: Optional[UploadFile] = File(None),
    product_text: str = Form(""),
    country: str = Form(...),
    telco: str = Form(...),
    language: str = Form(""),
    provider: str = Form(""),
):
    """Start the OBD script generation pipeline (non-WebSocket version).

    Accepts product documentation as either a file upload or text input.
    Returns the full pipeline result synchronously.
    """
    # Get product text from file or form field
    if product_file:
        content = await product_file.read()
        doc_text = content.decode("utf-8", errors="replace")
    elif product_text:
        doc_text = product_text
    else:
        return JSONResponse(
            status_code=400,
            content={"error": "Either product_file or product_text is required"},
        )

    orchestrator = PipelineOrchestrator(provider=provider or None)

    result = await orchestrator.run(
        product_text=doc_text,
        country=country,
        telco=telco,
        language=language or None,
    )

    session_id = result.get("session_id", "unknown")
    result["country"] = country
    result["telco"] = telco
    result["language"] = language or ""
    sessions[session_id] = result

    return result


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Retrieve results for a completed session."""
    if session_id in sessions:
        return sessions[session_id]
    return JSONResponse(status_code=404, content={"error": "Session not found"})


@app.get("/api/sessions/{session_id}/audio")
async def list_audio_files(session_id: str):
    """List all generated audio files for a session."""
    session_dir = OUTPUTS_DIR / session_id
    if not session_dir.exists():
        return JSONResponse(status_code=404, content={"error": "Session not found"})

    files = []
    for f in sorted(session_dir.glob("*.mp3")):
        files.append({
            "name": f.name,
            "size_bytes": f.stat().st_size,
            "url": f"/outputs/{session_id}/{f.name}",
        })
    return {"session_id": session_id, "files": files}


@app.get("/api/audio/{session_id}/{filename}")
async def download_audio(session_id: str, filename: str):
    """Download a specific audio file."""
    file_path = OUTPUTS_DIR / session_id / filename
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        filename=filename,
    )


@app.get("/api/sessions/{session_id}/scripts")
async def download_scripts(session_id: str, fmt: str = "json"):
    """Download scripts for a session as JSON or plain text."""
    if session_id not in sessions:
        return JSONResponse(status_code=404, content={"error": "Session not found"})

    result = sessions[session_id]
    final_scripts = result.get("final_scripts", result.get("revised_scripts_round_1", result.get("initial_scripts", {})))
    scripts = final_scripts.get("scripts", [])

    if not scripts:
        return JSONResponse(status_code=404, content={"error": "No scripts found in session"})

    if fmt == "text":
        # Plain text format for easy reading / copy-paste
        lines = []
        for s in scripts:
            lines.append(f"{'='*60}")
            lines.append(f"VARIANT {s.get('variant_id', '?')}: {s.get('theme', '')}")
            lines.append(f"Language: {s.get('language', 'N/A')}  |  Words: {s.get('word_count', '?')}  |  ~{s.get('estimated_duration_seconds', '?')}s")
            lines.append(f"{'='*60}")
            lines.append(f"\n--- HOOK (0-5s) ---\n{s.get('hook', '')}")
            lines.append(f"\n--- BODY (5-23s) ---\n{s.get('body', '')}")
            lines.append(f"\n--- CTA (23-30s) ---\n{s.get('cta', '')}")
            lines.append(f"\n--- FULL SCRIPT ---\n{s.get('full_script', '')}")
            lines.append(f"\n--- FALLBACK 1 (Urgency) ---\n{s.get('fallback_1', '')}")
            lines.append(f"\n--- FALLBACK 2 (Psychology) ---\n{s.get('fallback_2', '')}")
            lines.append(f"\n--- POLITE CLOSURE ---\n{s.get('polite_closure', '')}")
            lines.append("")
        text_content = "\n".join(lines)
        return JSONResponse(
            content={"filename": f"scripts_{session_id}.txt", "content": text_content},
        )

    # Default: JSON
    return JSONResponse(
        content={
            "filename": f"scripts_{session_id}.json",
            "content": json.dumps(final_scripts, indent=2),
        },
    )


# ── Campaign Endpoints ──


@app.post("/api/campaigns")
async def create_campaign(request: Request):
    """Save a pipeline result as a named campaign."""
    body = await request.json()
    session_id = body.get("session_id", "")
    name = body.get("name", "").strip()

    if not session_id or not name:
        return JSONResponse(
            status_code=400,
            content={"error": "session_id and name are required"},
        )

    if session_id not in sessions:
        return JSONResponse(
            status_code=404,
            content={"error": "Session not found. Generate a campaign first."},
        )

    result = sessions[session_id]

    # Get username from auth
    username = getattr(request.state, "username", "local")

    # Extract country/telco/language from the result or session
    country = result.get("country", "")
    telco = result.get("telco", "")
    language = result.get("language", "")

    campaign = save_campaign(
        campaign_id=session_id,
        name=name,
        created_by=username,
        country=country,
        telco=telco,
        language=language,
        result=result,
    )

    return campaign


@app.get("/api/campaigns")
async def get_campaigns():
    """List all saved campaigns."""
    campaigns = list_campaigns()
    return {"campaigns": campaigns}


@app.get("/api/campaigns/{campaign_id}")
async def get_campaign_detail(campaign_id: str):
    """Get full details of a saved campaign."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        return JSONResponse(status_code=404, content={"error": "Campaign not found"})
    return campaign


@app.delete("/api/campaigns/{campaign_id}")
async def remove_campaign(campaign_id: str):
    """Delete a saved campaign."""
    deleted = delete_campaign(campaign_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"error": "Campaign not found"})
    return {"message": "Campaign deleted"}


# ── Collaboration Endpoints ──


@app.get("/api/presence")
async def get_presence():
    """Get all currently online users."""
    return {"users": get_online_users()}


@app.get("/api/presence/{campaign_id}")
async def get_campaign_presence(campaign_id: str):
    """Get users currently viewing a specific campaign."""
    return {"users": get_users_viewing_campaign(campaign_id)}


@app.get("/api/activity")
async def get_activity(limit: int = 20):
    """Get recent activity feed."""
    return {"events": get_recent_activity(limit)}


@app.get("/api/campaigns/{campaign_id}/comments")
async def get_comments(campaign_id: str):
    """List all comments for a campaign."""
    comments = list_comments(campaign_id)
    return {"comments": comments}


@app.post("/api/campaigns/{campaign_id}/comments")
async def add_comment(campaign_id: str, request: Request):
    """Add a comment to a campaign."""
    body = await request.json()
    text = body.get("text", "").strip()
    username = getattr(request.state, "username", body.get("username", "anonymous"))
    if not text:
        return JSONResponse(status_code=400, content={"error": "Comment text is required"})

    comment_id = str(uuid.uuid4())
    comment = save_comment(comment_id, campaign_id, username, text)

    # Record activity and broadcast to collaboration room
    campaign = get_campaign(campaign_id)
    campaign_name = campaign["name"] if campaign else "Unknown"
    event = record_activity(
        "comment_added", username, campaign_id, campaign_name, text[:100]
    )

    room = get_or_create_room(campaign_id)
    await room.broadcast({"type": "comment_added", "comment": comment})
    await broadcast_to_all({"type": "activity", "event": event})

    return comment


@app.delete("/api/campaigns/{campaign_id}/comments/{comment_id}")
async def remove_comment(campaign_id: str, comment_id: str):
    """Delete a comment."""
    deleted = delete_comment(comment_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"error": "Comment not found"})

    room = get_or_create_room(campaign_id)
    await room.broadcast({"type": "comment_deleted", "comment_id": comment_id})

    return {"deleted": True}


@app.websocket("/ws/collaborate/{campaign_id}")
async def websocket_collaborate(ws: WebSocket, campaign_id: str):
    """WebSocket for real-time collaboration on a campaign.

    On connect: sends current presence for the campaign.
    Receives: heartbeats and user actions.
    Broadcasts: user joined/left, comments, presence updates.
    """
    await ws.accept()
    ws_id = str(uuid.uuid4())

    # Determine username
    from backend.auth import get_token_from_websocket, verify_token, auth_enabled
    username = "anonymous"
    if auth_enabled():
        token = get_token_from_websocket(ws)
        if token:
            username = verify_token(token) or "anonymous"

    user = register_user(ws_id, username, ws)
    update_user_activity(ws_id, campaign_id)
    room = get_or_create_room(campaign_id)
    room.add(ws_id, ws)

    # Record and broadcast join
    event = record_activity("user_joined", username, campaign_id)
    await room.broadcast(
        {"type": "user_joined", "user": user.to_dict()}, exclude_ws_id=ws_id
    )
    await broadcast_to_all({"type": "activity", "event": event})

    # Send current state to the connecting user
    await ws.send_json({
        "type": "init",
        "users": get_users_viewing_campaign(campaign_id),
        "comments": list_comments(campaign_id),
    })

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "heartbeat":
                update_user_activity(ws_id, campaign_id)

            elif msg_type == "typing":
                await room.broadcast(
                    {"type": "typing", "username": username},
                    exclude_ws_id=ws_id,
                )
    except Exception:
        pass
    finally:
        room.remove(ws_id)
        left_user = unregister_user(ws_id)
        cleanup_room(campaign_id)
        if left_user:
            event = record_activity("user_left", left_user.username, campaign_id)
            await room.broadcast({"type": "user_left", "username": left_user.username})
            await broadcast_to_all({"type": "activity", "event": event})


# ── WebSocket Endpoints ──


@app.websocket("/ws/progress/{session_id}")
async def websocket_progress(ws: WebSocket, session_id: str):
    """Read-only WebSocket that streams progress for a background pipeline.

    On connect: sends all buffered progress messages (catch-up).
    Then streams new messages as they arrive.
    Disconnect does NOT stop the pipeline.
    """
    if auth_enabled():
        token = get_token_from_websocket(ws)
        if not token or not verify_token(token):
            await ws.close(code=4001, reason="Authentication required")
            return

    state = pipelines.get(session_id)
    if not state:
        await ws.close(code=4004, reason="Pipeline not found")
        return

    await ws.accept()
    logger.info(f"Progress WS connected for session {session_id}")

    # Send all buffered progress (catch-up)
    for msg in list(state.progress_log):
        try:
            await ws.send_json(msg)
        except Exception:
            return

    # If already finished, close after catch-up
    if state.status in ("done", "error"):
        try:
            await ws.close()
        except Exception:
            pass
        return

    # Subscribe for live updates
    state.subscribers.append(ws)
    try:
        # Keep connection alive until client disconnects or pipeline finishes
        while True:
            # We just wait for the client to disconnect; all sending is done
            # from _run_pipeline_bg via the subscribers list
            try:
                await ws.receive_text()
            except WebSocketDisconnect:
                break
    finally:
        if ws in state.subscribers:
            state.subscribers.remove(ws)
        logger.info(f"Progress WS disconnected for session {session_id}")


@app.websocket("/ws/generate")
async def websocket_generate(ws: WebSocket):
    """WebSocket endpoint for real-time pipeline execution with progress updates.

    Client sends a JSON message to start:
    {
        "product_text": "...",
        "country": "...",
        "telco": "...",
        "language": "..." (optional),
        "provider": "..." (optional)
    }

    Server streams progress updates:
    {
        "agent": "AgentName",
        "status": "started|completed|error",
        "message": "...",
        "data": {...} (optional)
    }

    Final message includes the complete result.
    """
    # WebSocket auth check
    if auth_enabled():
        token = get_token_from_websocket(ws)
        if not token or not verify_token(token):
            await ws.close(code=4001, reason="Authentication required")
            return

    await ws.accept()
    logger.info("WebSocket client connected")

    try:
        # Wait for the initial configuration message
        raw = await ws.receive_text()
        config = json.loads(raw)

        product_text = config.get("product_text", "")
        country = config.get("country", "")
        telco = config.get("telco", "")
        language = config.get("language")
        provider = config.get("provider")

        if not product_text or not country or not telco:
            await ws.send_json({
                "agent": "Pipeline",
                "status": "error",
                "message": "product_text, country, and telco are required",
            })
            await ws.close()
            return

        # Progress callback that sends updates via WebSocket
        async def on_progress(agent: str, status: str, data: dict[str, Any]) -> None:
            try:
                await ws.send_json({
                    "agent": agent,
                    "status": status,
                    "message": data.get("message", ""),
                    "data": {
                        k: v for k, v in data.items()
                        if k != "message" and _is_json_serializable(v)
                    },
                })
            except Exception as e:
                logger.warning(f"Failed to send progress update: {e}")

        orchestrator = PipelineOrchestrator(
            provider=provider,
            on_progress=on_progress,
        )

        result = await orchestrator.run(
            product_text=product_text,
            country=country,
            telco=telco,
            language=language,
        )

        session_id = result.get("session_id", "unknown")
        # Store input params alongside result for campaign saving
        result["country"] = country
        result["telco"] = telco
        result["language"] = language or ""
        sessions[session_id] = result

        # Send the final result -- distinguish success vs failure
        has_error = "error" in result
        await ws.send_json({
            "agent": "Pipeline",
            "status": "error" if has_error else "done",
            "message": result.get("error", "Pipeline complete"),
            "session_id": session_id,
            "result": _make_serializable(result),
        })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except json.JSONDecodeError:
        await ws.send_json({
            "agent": "Pipeline",
            "status": "error",
            "message": "Invalid JSON received",
        })
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        try:
            await ws.send_json({
                "agent": "Pipeline",
                "status": "error",
                "message": str(e),
            })
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


def _is_json_serializable(value: Any) -> bool:
    """Check if a value is JSON serializable."""
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


def _make_serializable(obj: Any) -> Any:
    """Recursively make an object JSON serializable."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    elif isinstance(obj, Path):
        return str(obj)
    elif _is_json_serializable(obj):
        return obj
    else:
        return str(obj)
