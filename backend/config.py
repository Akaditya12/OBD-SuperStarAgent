"""Configuration management for OBD SuperStar Agent."""

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
ELEVENLABS_API_KEY = _env("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"
ELEVENLABS_TTS_MODEL = "eleven_multilingual_v2"
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_192"

# --- Murf AI Configuration ---
MURF_API_KEY = _env("MURF_API_KEY")

# --- App Configuration ---
OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

MAX_SCRIPT_WORDS = 75  # ~30 seconds at normal speaking pace
EVAL_FEEDBACK_ROUNDS = 1  # Number of revision cycles between Writer and Eval Panel
NUM_SCRIPT_VARIANTS = 5  # Number of script sets to generate
NUM_FALLBACKS_PER_SCRIPT = 2  # Fallback CTA variants per script

# --- Supabase Configuration ---
SUPABASE_URL = _env("SUPABASE_URL")
SUPABASE_SERVICE_KEY = _env("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = _env("SUPABASE_ANON_KEY")
