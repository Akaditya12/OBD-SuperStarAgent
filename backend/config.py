"""Configuration management for OBD SuperStar Agent."""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

def _env(key: str, default: str = "") -> str:
    """Read env var and strip surrounding whitespace/newlines."""
    return os.getenv(key, default).strip()


# --- Azure OpenAI Configuration ---
AZURE_OPENAI_API_KEY = _env("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = _env("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = _env("AZURE_OPENAI_DEPLOYMENT", "gpt-5.1-chat")
AZURE_OPENAI_API_VERSION = _env("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

# --- Default Provider ---
DEFAULT_LLM_PROVIDER = _env("DEFAULT_LLM_PROVIDER", "azure_openai")

# --- ElevenLabs Configuration ---
def _env_elevenlabs(key: str) -> str:
    """Load ELEVENLABS_API_KEY: strip quotes, newlines, and invisible chars so it matches the key used in curl."""
    v = _env(key)
    if not v:
        return ""
    # Remove surrounding quotes (single or double)
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        v = v[1:-1]
    # Strip all whitespace (including Unicode) from ends
    v = v.strip()
    # Remove newlines, carriage returns, tabs (paste from terminal can add these)
    v = v.replace("\n", "").replace("\r", "").replace("\t", "")
    # Keep only ASCII printable (API keys are ASCII; copy-paste can add Unicode lookalikes)
    v = "".join(c for c in v if ord(c) >= 32 and ord(c) <= 126)
    return v.strip()


ELEVENLABS_API_KEY = _env_elevenlabs("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"
ELEVENLABS_TTS_MODEL = "eleven_v3"
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_192"


def get_elevenlabs_headers() -> dict[str, str]:
    """Headers for ElevenLabs API. Use a browser-like User-Agent: httpx is often rejected with 401 otherwise."""
    return {
        "xi-api-key": ELEVENLABS_API_KEY,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }


def elevenlabs_401_is_tts_only(response_text: str) -> bool:
    """True if 401 is due to missing voices_read (key is valid for TTS only; we use curated voice list)."""
    if not response_text:
        return False
    try:
        data = json.loads(response_text)
        detail = data.get("detail") or {}
        status = detail.get("status", "")
        msg = (detail.get("message") or "").lower()
        return status == "missing_permissions" or "voices_read" in msg
    except Exception:
        return False


# --- App Configuration ---
OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

MAX_SCRIPT_WORDS = 75  # ~30 seconds at normal speaking pace
EVAL_FEEDBACK_ROUNDS = 1  # Number of revision cycles between Writer and Eval Panel
NUM_SCRIPT_VARIANTS = 5  # Number of script sets to generate
NUM_FALLBACKS_PER_SCRIPT = 2  # Fallback CTA variants per script


def get_live_config() -> dict:
    """Return pipeline config merged from DB overrides + code defaults.

    Lazy-imports database to avoid circular dependencies.
    """
    from backend.database import get_pipeline_config
    return get_pipeline_config()

# --- Cloudflare R2 (audio storage) ---
# Audio files are written locally under backend/outputs AND uploaded to R2
# (when configured). Frontend prefers public_url; falls back to local serve
# if R2 upload is disabled or failed.
R2_ACCOUNT_ID = _env("R2_ACCOUNT_ID")
R2_ACCESS_KEY = _env("R2_ACCESS_KEY")
R2_SECRET_KEY = _env("R2_SECRET_KEY")
R2_BUCKET = _env("R2_BUCKET")
R2_PUBLIC_BASE_URL = _env("R2_PUBLIC_BASE_URL").rstrip("/")

R2_ENABLED = all([R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET, R2_PUBLIC_BASE_URL])


# --- Database Configuration ---
# Primary: MySQL (local). Fallback: SQLite when MYSQL_URL is blank.
MYSQL_URL = _env("MYSQL_URL")

# Legacy Supabase env vars are still read but the app no longer uses them
# for DB or storage. Kept as empty strings so old imports don't crash.
SUPABASE_URL = _env("SUPABASE_URL")
SUPABASE_SERVICE_KEY = _env("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = _env("SUPABASE_ANON_KEY")
