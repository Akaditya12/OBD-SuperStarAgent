"""Configuration management for OBD SuperStar Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _get_secret(key: str, default: str = "") -> str:
    """Read from env vars first, then Streamlit secrets as fallback."""
    val = os.getenv(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


# --- Azure OpenAI Configuration ---
AZURE_OPENAI_API_KEY = _get_secret("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = _get_secret("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = _get_secret("AZURE_OPENAI_DEPLOYMENT", "gpt-5.1-chat")
AZURE_OPENAI_API_VERSION = _get_secret("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

# --- Default Provider ---
DEFAULT_LLM_PROVIDER = _get_secret("DEFAULT_LLM_PROVIDER", "azure_openai")

# --- ElevenLabs Configuration ---
ELEVENLABS_API_KEY = _get_secret("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"
ELEVENLABS_TTS_MODEL = "eleven_multilingual_v2"
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128"

# --- Murf AI Configuration ---
MURF_API_KEY = _get_secret("MURF_API_KEY")

# --- App Configuration ---
OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

MAX_SCRIPT_WORDS = 75  # ~30 seconds at normal speaking pace
EVAL_FEEDBACK_ROUNDS = 1  # Number of revision cycles between Writer and Eval Panel
NUM_SCRIPT_VARIANTS = 5  # Number of script sets to generate
NUM_FALLBACKS_PER_SCRIPT = 2  # Fallback CTA variants per script
