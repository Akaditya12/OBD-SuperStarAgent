"""FastAPI application -- REST API + WebSocket for the OBD SuperStar Agent."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import OUTPUTS_DIR
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated audio files
OUTPUTS_DIR.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# ── In-memory session store ──
sessions: dict[str, dict[str, Any]] = {}


# ── REST Endpoints ──


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "OBD SuperStar Agent"}


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


# ── WebSocket Endpoint ──


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
