"""Agent 6: Audio Producer -- generates broadcast-quality OBD audio.

Produces professional audio with:
- ElevenLabs (primary) for premium multilingual voice
- edge-tts (unlimited free fallback) for voice
- Upbeat synthesized background music
- Stereo 320kbps output matching industry standards
- Pronunciation dictionary for brand names (EVA, IVR, OBD, etc.)
"""

from __future__ import annotations

import asyncio
import io
import logging
import math
import os
import re
import struct
import uuid
import wave
from pathlib import Path
from typing import Any

import edge_tts
import httpx

from backend.config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_BASE_URL,
    ELEVENLABS_OUTPUT_FORMAT,
    ELEVENLABS_TTS_MODEL,
    OUTPUTS_DIR,
    get_elevenlabs_headers,
    elevenlabs_401_is_tts_only,
)

from .base import BaseAgent

logger = logging.getLogger(__name__)

# Languages not supported by eleven_v3; use eleven_multilingual_v2 so ElevenLabs still works
ELEVENLABS_V3_UNSUPPORTED_LANGUAGES = ("amharic",)

# eleven_multilingual_v2 supports ~29 languages; others (e.g. sw, am) must not be sent as language_code
ELEVENLABS_V2_SUPPORTED_LANG_CODES = frozenset({
    "en", "de", "fr", "es", "it", "pt", "pl", "hi", "ja", "ko", "zh", "ar", "id", "nl", "tr",
    "fil", "sv", "bg", "ro", "cs", "el", "fi", "hr", "ms", "sk", "da", "ta", "uk", "ru",
})

# Matches ANY [tag] with no length limit
_ANY_BRACKET_TAG = re.compile(r"\[[^\]]+\]")
# Matches fullwidth brackets 【tag】 (LLMs occasionally use these)
_FULLWIDTH_BRACKET_TAG = re.compile(r"【[^】]+】")
# Matches (tag) when the content looks like a voice/emotion direction, not real speech
_PAREN_DIRECTION_TAG = re.compile(
    r"\(\s*(?:warm|gentle|soft|excited|curious|cheerful(?:ly)?|neutral|friendly|"
    r"mischievous(?:ly)?|playful(?:ly)?|energetic(?:ally)?|calm(?:ly)?|sincere(?:ly)?|"
    r"enthusiastic(?:ally)?|serious(?:ly)?|whisper(?:s|ing)?|dramatic(?:ally)?|"
    r"urgent(?:ly)?|compassionate(?:ly)?|empathetic(?:ally)?|sad(?:ly)?|happy|"
    r"joyful(?:ly)?|confident(?:ly)?|soothing(?:ly)?|reassuring(?:ly)?|"
    r"encouraging(?:ly)?|inspiring|motivating|conversational(?:ly)?|"
    r"pause|short\s*pause|long\s*pause|beat|breath|sigh|gasp|laugh|chuckle|"
    r"voice\s*direction|tone|emotion|with\s+emotion|with\s+warmth|"
    r"in\s+a\s+\w+\s+tone|in\s+a\s+\w+\s+voice)\s*\)",
    re.IGNORECASE,
)
# Matches {tag} curly-brace directions
_CURLY_DIRECTION_TAG = re.compile(r"\{[^}]{1,50}\}", re.IGNORECASE)
# Matches XML-style tags like <voice emotion='curious'>, </voice>, <break time="1s"/>, etc.
_ANY_XML_TAG = re.compile(r"</?[a-zA-Z][^>]{0,120}>")
# Standalone emotion/direction words at the very start of a line or after punctuation
_STANDALONE_DIRECTION = re.compile(
    r"(?:^|(?<=\.\s)|(?<=!\s)|(?<=\?\s))\s*"
    r"(?:warm(?:ly)?|gentle|gently|soft(?:ly)?|excited(?:ly)?|curious(?:ly)?|"
    r"cheerful(?:ly)?|neutral|friendly|mischievous(?:ly)?|playful(?:ly)?|"
    r"energetic(?:ally)?|calm(?:ly)?|sincere(?:ly)?|enthusiastic(?:ally)?|"
    r"serious(?:ly)?|dramatic(?:ally)?|urgent(?:ly)?|compassionate(?:ly)?|"
    r"soothing(?:ly)?|reassuring(?:ly)?|encouraging(?:ly)?|conversational(?:ly)?)"
    r"\s*[,:]?\s*(?=\S)",
    re.IGNORECASE | re.MULTILINE,
)

EDGE_VOICE_MAP: dict[str, str] = {
    "en-IN": "en-IN-NeerjaNeural",
    "en-NG": "en-NG-EzinneNeural",
    "en-KE": "en-KE-AsiliaNeural",
    "en-TZ": "en-TZ-ImaniNeural",
    "en-ZA": "en-ZA-LeahNeural",
    "en-GH": "en-GH-EsiNeural",
    "en-US": "en-US-AriaNeural",
    "en-GB": "en-GB-SoniaNeural",
    "fr-FR": "fr-FR-DeniseNeural",
    "fr-CM": "fr-FR-DeniseNeural",
    "fr-SN": "fr-FR-DeniseNeural",
    "fr-CD": "fr-FR-DeniseNeural",
    "sw-KE": "sw-KE-ZuriNeural",
    "sw-TZ": "sw-TZ-RehemaNeural",
    "am-ET": "am-ET-MekdesNeural",
    "hi-IN": "hi-IN-SwaraNeural",
    "bn-IN": "bn-IN-TanishaaNeural",
    "ta-IN": "ta-IN-PallaviNeural",
    "te-IN": "te-IN-ShrutiNeural",
    "ur-PK": "ur-PK-UzmaNeural",
    "id-ID": "id-ID-GadisNeural",
    "fil-PH": "fil-PH-BlessicaNeural",
    "pt-BR": "pt-BR-FranciscaNeural",
    "ar-SA": "ar-SA-ZariyahNeural",
    "zu-ZA": "zu-ZA-ThandoNeural",
    "af-ZA": "af-ZA-AdriNeural",
    "so-SO": "so-SO-UbaxNeural",
}

COUNTRY_LOCALE: dict[str, str] = {
    # Africa
    "Nigeria": "en-NG", "Kenya": "en-KE", "Tanzania": "sw-KE",
    "South Africa": "en-ZA", "Ghana": "en-GH",
    "Cameroon": "fr-FR", "Senegal": "fr-FR",
    "Congo (DRC)": "fr-FR", "Congo (Republic)": "fr-FR",
    "Ethiopia": "am-ET", "Mozambique": "pt-BR",
    "Rwanda": "en-KE", "Uganda": "en-KE",
    "Zambia": "en-ZA", "Zimbabwe": "en-ZA", "Botswana": "en-ZA",
    "Somalia": "so-SO", "Mali": "fr-FR", "Ivory Coast": "fr-FR",
    "Burkina Faso": "fr-FR", "Niger": "fr-FR", "Guinea": "fr-FR",
    "Benin": "fr-FR", "Togo": "fr-FR", "Madagascar": "fr-FR",
    "Chad": "fr-FR", "Sierra Leone": "en-KE", "Liberia": "en-US",
    "Malawi": "en-KE", "Namibia": "en-ZA", "Lesotho": "en-ZA",
    "Eswatini": "en-ZA", "Gabon": "fr-FR",
    # South Asia
    "India": "en-IN", "Bangladesh": "bn-IN", "Pakistan": "ur-PK",
    # Southeast Asia
    "Indonesia": "id-ID", "Philippines": "fil-PH",
    # Caribbean / Latin America
    "Guyana": "en-US", "Haiti": "fr-FR",
    "Jamaica": "en-US", "Trinidad and Tobago": "en-US",
}

# Prosody per section type -- warm and clear with slight variation (emotions/expression by section)
SECTION_PROSODY: dict[str, dict[str, str]] = {
    "main":      {"rate": "-3%",   "pitch": "+2Hz"},   # slightly slower = warmer
    "fallback1": {"rate": "+0%",   "pitch": "+3Hz"},   # a touch brighter for urgency
    "fallback2": {"rate": "-2%",   "pitch": "+1Hz"},   # calm, reassuring
    "closure":   {"rate": "-5%",   "pitch": "-1Hz"},   # gentle close
}


def _edge_rate_with_speed(section_type: str, speed: float) -> str:
    """Combine section prosody rate with user speed for edge-tts (format +X% or -X%)."""
    prosody = SECTION_PROSODY.get(section_type, {"rate": "+0%", "pitch": "+0Hz"})
    rate_s = prosody["rate"].strip().rstrip("%").lstrip("+")
    try:
        base = int(rate_s)
    except ValueError:
        base = 0
    delta = int((speed - 1.0) * 100)
    pct = max(-50, min(50, base + delta))
    return f"{pct:+d}%"


# Technical acronyms that TTS should spell out letter by letter.
# EVA is a product NAME (pronounced "Eva") -- NOT an acronym, so it's excluded.
_PRONUNCIATION_FIXES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bIVR\b"), "I V R"),
    (re.compile(r"\bOBD\b"), "O B D"),
    (re.compile(r"\bCLI\b"), "C L I"),
    (re.compile(r"\bBNG\b"), "B N G"),
    (re.compile(r"\bDTMF\b"), "D T M F"),
    (re.compile(r"\bUSSD\b"), "U S S D"),
    (re.compile(r"\bSMS\b"), "S M S"),
    (re.compile(r"\bCTA\b"), "C T A"),
]


def _clean_text_for_tts(text: str, apply_pronunciation_hacks: bool = True) -> str:
    """Strip ALL bracket/direction tags and prepare text for TTS.

    Converts action/emotion tags that can be spoken ([laughs], [sigh], [gasps],
    [pause]) to natural speech or pacing; strips the rest. Section-based
    prosody (rate/pitch per hook, body, fallback, closure) and engine-specific style
    carry expression so the final audio reflects warmth, urgency, or calm by section.
    Also removes [square], 【fullwidth】, (direction), {curly}, <xml>, and fixes
    pronunciation (IVR, OBD, etc.) for brand names and acronyms.
    """
    # Step 1: Convert known emotion/action tags to natural speech or pacing (so they show in the voice)
    text = re.sub(r"\[laughs?\]", "ha ha, ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[lightlaugh\]", "heh, ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[sigh\]", "hmm, ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[gasps?\]", "oh! ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[short\s*pause\]", ", ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[pause\]", "... ", text, flags=re.IGNORECASE)

    # Step 2: Strip ALL [anything] tags (no length limit)
    text = _ANY_BRACKET_TAG.sub("", text)

    # Step 3: Strip fullwidth bracket tags 【anything】
    text = _FULLWIDTH_BRACKET_TAG.sub("", text)

    # Step 4: Strip (direction) parenthetical tags like (warm), (cheerfully)
    text = _PAREN_DIRECTION_TAG.sub("", text)

    # Step 5: Strip {direction} curly-brace tags
    text = _CURLY_DIRECTION_TAG.sub("", text)

    # Step 6: Strip XML-style tags (<voice emotion='...'>, </voice>, etc.)
    text = _ANY_XML_TAG.sub("", text)

    # Step 7: Strip standalone emotion/direction words at sentence start
    text = _STANDALONE_DIRECTION.sub("", text)

    # Step 8: Remove markdown bold/italic markers
    text = text.replace("**", "").replace("*", "")

    # Step 8.5: Remove ALL slashes so TTS never says "slash"
    # Leading/trailing slashes: "/Hello" -> "Hello"
    text = re.sub(r"(?<!\w)/|/(?!\w)", "", text)
    # Word/Word alternatives: "Madam/Sir" -> "Madam or Sir"
    text = re.sub(r"(\w+)/(\w+)", r"\1 or \2", text)

    # Step 9: Convert ALL-CAPS common words back to normal case so TTS
    # doesn't spell them out (e.g. "YOU" -> "you", "NOW" -> "now").
    _KNOWN_ACRONYMS = {"IVR", "OBD", "CLI", "BNG", "DTMF", "USSD", "SMS", "CTA", "AI", "INR"}
    def _fix_caps(m: re.Match) -> str:
        word = m.group(0)
        return word if word in _KNOWN_ACRONYMS else word.capitalize()
    text = re.sub(r"\b[A-Z]{2,}\b", _fix_caps, text)

    # Step 10: Fix acronym/brand pronunciation
    if apply_pronunciation_hacks:
        for pattern, replacement in _PRONUNCIATION_FIXES:
            text = pattern.sub(replacement, text)

    # Step 11: Clean up artifacts
    text = re.sub(r"\s{2,}", " ", text).strip()
    text = re.sub(r"\s+([,.])", r"\1", text)  # fix " ," or " ."
    text = re.sub(r"^[,.\s]+", "", text)       # fix leading comma/period
    return text


# Language name -> edge-tts locale for proper matching
LANGUAGE_TO_LOCALE: dict[str, str] = {
    "hindi": "hi-IN", "hinglish": "hi-IN", "english": "en-US",
    "tamil": "ta-IN", "telugu": "te-IN", "bengali": "bn-IN",
    "urdu": "ur-PK", "swahili": "sw-KE", "kiswahili": "sw-KE",
    "amharic": "am-ET", "french": "fr-FR", "arabic": "ar-SA",
    "portuguese": "pt-BR", "indonesian": "id-ID", "filipino": "fil-PH",
    "somali": "so-SO",     "zulu": "zu-ZA", "isizulu": "zu-ZA",
    "afrikaans": "af-ZA",
    "setswana": "en-ZA", "tswana": "en-ZA",
    "sesotho": "en-ZA", "sotho": "en-ZA",
    "isixhosa": "en-ZA",
    "haitian creole": "fr-FR", "creolese": "en-US",
    "pidgin english": "en-NG", "pidgin": "en-NG",
    "kinyarwanda": "en-KE", "wolof": "fr-FR",
    "lingala": "fr-FR", "luganda": "en-KE",
    "shona": "en-ZA", "ndebele": "en-ZA",
    "yoruba": "en-NG", "igbo": "en-NG", "hausa": "en-NG",
    "twi": "en-GH", "bemba": "en-ZA", "nyanja": "en-ZA",
    "xhosa": "en-ZA", "tagalog": "fil-PH",
    "kannada": "kn-IN", "malayalam": "ml-IN",
    "punjabi": "pa-IN", "gujarati": "gu-IN",
    "oromo": "en-KE",
}


# Voice pools: 3 voices per locale for multi-voice generation
# Each entry: (voice_id, label) -- label shown in UI
EDGE_VOICE_POOL: dict[str, list[tuple[str, str]]] = {
    "en-IN": [
        ("en-IN-NeerjaNeural", "Neerja (Female)"),
        ("en-IN-PrabhatNeural", "Prabhat (Male)"),
        ("en-IN-NeerjaExpressiveNeural", "Neerja Expressive (Female)"),
    ],
    "hi-IN": [
        ("hi-IN-SwaraNeural", "Swara (Female)"),
        ("hi-IN-MadhurNeural", "Madhur (Male)"),
        ("hi-IN-SwaraNeural", "Swara Alt (Female)"),
    ],
    "ta-IN": [
        ("ta-IN-PallaviNeural", "Pallavi (Female)"),
        ("ta-IN-ValluvarNeural", "Valluvar (Male)"),
        ("ta-IN-PallaviNeural", "Pallavi Alt (Female)"),
    ],
    "te-IN": [
        ("te-IN-ShrutiNeural", "Shruti (Female)"),
        ("te-IN-MohanNeural", "Mohan (Male)"),
        ("te-IN-ShrutiNeural", "Shruti Alt (Female)"),
    ],
    "bn-IN": [
        ("bn-IN-TanishaaNeural", "Tanishaa (Female)"),
        ("bn-IN-BashkarNeural", "Bashkar (Male)"),
        ("bn-IN-TanishaaNeural", "Tanishaa Alt (Female)"),
    ],
    "en-NG": [
        ("en-NG-EzinneNeural", "Ezinne (Female)"),
        ("en-NG-AbeoNeural", "Abeo (Male)"),
        ("en-NG-EzinneNeural", "Ezinne Alt (Female)"),
    ],
    "en-KE": [
        ("en-KE-AsiliaNeural", "Asilia (Female)"),
        ("en-KE-ChilembaNeural", "Chilemba (Male)"),
        ("en-KE-AsiliaNeural", "Asilia Alt (Female)"),
    ],
    "en-US": [
        ("en-US-AriaNeural", "Aria (Female)"),
        ("en-US-GuyNeural", "Guy (Male)"),
        ("en-US-JennyNeural", "Jenny (Female)"),
    ],
    "en-GB": [
        ("en-GB-SoniaNeural", "Sonia (Female)"),
        ("en-GB-RyanNeural", "Ryan (Male)"),
        ("en-GB-LibbyNeural", "Libby (Female)"),
    ],
    "fr-FR": [
        ("fr-FR-DeniseNeural", "Denise (Female)"),
        ("fr-FR-HenriNeural", "Henri (Male)"),
        ("fr-FR-EloiseNeural", "Eloise (Female)"),
    ],
    "pt-BR": [
        ("pt-BR-FranciscaNeural", "Francisca (Female)"),
        ("pt-BR-AntonioNeural", "Antonio (Male)"),
        ("pt-BR-FranciscaNeural", "Francisca Alt (Female)"),
    ],
    "ur-PK": [
        ("ur-PK-UzmaNeural", "Uzma (Female)"),
        ("ur-PK-AsadNeural", "Asad (Male)"),
        ("ur-PK-UzmaNeural", "Uzma Alt (Female)"),
    ],
    "id-ID": [
        ("id-ID-GadisNeural", "Gadis (Female)"),
        ("id-ID-ArdiNeural", "Ardi (Male)"),
        ("id-ID-GadisNeural", "Gadis Alt (Female)"),
    ],
    "sw-KE": [
        ("sw-KE-ZuriNeural", "Zuri (Female)"),
        ("sw-KE-RafikiNeural", "Rafiki (Male)"),
        ("sw-KE-ZuriNeural", "Zuri Alt (Female)"),
    ],
    "en-ZA": [
        ("en-ZA-LeahNeural", "Leah (Female)"),
        ("en-ZA-LukeNeural", "Luke (Male)"),
        ("en-ZA-LeahNeural", "Leah Alt (Female)"),
    ],
    "en-GH": [
        ("en-GH-EsiNeural", "Esi (Female)"),
        ("en-GH-EkuaNeural", "Ekua (Male)"),
        ("en-GH-EsiNeural", "Esi Alt (Female)"),
    ],
    "en-TZ": [
        ("en-TZ-ImaniNeural", "Imani (Female)"),
        ("en-TZ-ElimuNeural", "Elimu (Male)"),
        ("en-TZ-ImaniNeural", "Imani Alt (Female)"),
    ],
    "zu-ZA": [
        ("zu-ZA-ThandoNeural", "Thando (Female)"),
        ("zu-ZA-ThembaNeural", "Themba (Male)"),
        ("zu-ZA-ThandoNeural", "Thando Alt (Female)"),
    ],
    "af-ZA": [
        ("af-ZA-AdriNeural", "Adri (Female)"),
        ("af-ZA-WillemNeural", "Willem (Male)"),
        ("af-ZA-AdriNeural", "Adri Alt (Female)"),
    ],
    "am-ET": [
        ("am-ET-MekdesNeural", "Mekdes (Female)"),
        ("am-ET-AmehaNeural", "Ameha (Male)"),
        ("am-ET-MekdesNeural", "Mekdes Alt (Female)"),
    ],
    "so-SO": [
        ("so-SO-UbaxNeural", "Ubax (Female)"),
        ("so-SO-MuuseNeural", "Muuse (Male)"),
        ("so-SO-UbaxNeural", "Ubax Alt (Female)"),
    ],
    "fil-PH": [
        ("fil-PH-BlessicaNeural", "Blessica (Female)"),
        ("fil-PH-AngeloNeural", "Angelo (Male)"),
        ("fil-PH-BlessicaNeural", "Blessica Alt (Female)"),
    ],
    "ar-SA": [
        ("ar-SA-ZariyahNeural", "Zariyah (Female)"),
        ("ar-SA-HamedNeural", "Hamed (Male)"),
        ("ar-EG-SalmaNeural", "Salma (Female)"),
    ],
    "ar-EG": [
        ("ar-EG-SalmaNeural", "Salma (Female)"),
        ("ar-EG-ShakirNeural", "Shakir (Male)"),
        ("ar-SA-ZariyahNeural", "Zariyah (Female)"),
    ],
}

def _get_edge_voice_pool(country: str, language: str | None) -> list[tuple[str, str]]:
    """Get 3 edge-tts voices for the given country/language."""
    locale = None
    country_locale = COUNTRY_LOCALE.get(country)
    if language:
        lang_lower = language.lower().strip()
        if lang_lower in LANGUAGE_TO_LOCALE:
            locale = LANGUAGE_TO_LOCALE[lang_lower]
        else:
            for lang_key, loc in LANGUAGE_TO_LOCALE.items():
                if lang_key in lang_lower:
                    locale = loc
                    break
    if not locale:
        locale = country_locale or "en-US"

    if locale in EDGE_VOICE_POOL:
        return EDGE_VOICE_POOL[locale]

    # Fallback: fr-CM -> fr-FR, pt-MZ -> pt-BR, etc.
    lang_prefix = locale.split("-")[0] if locale else ""
    for pool_locale in EDGE_VOICE_POOL:
        if pool_locale.startswith(lang_prefix + "-"):
            return EDGE_VOICE_POOL[pool_locale]

    primary = EDGE_VOICE_MAP.get(locale, "en-US-AriaNeural")
    return [(primary, "Voice 1"), (primary, "Voice 2"), (primary, "Voice 3")]


def _country_to_elevenlabs_lang_code(country: str, language: str | None) -> str | None:
    """Map country/language to ElevenLabs eleven_v3 language_code (BCP-47).

    Returns None if no specific mapping is needed (defaults to model auto-detect).
    """
    c = country.lower().strip()

    if language:
        lang_lower = language.lower().strip()
        lang_map = {
            "english": "en", "french": "fr", "spanish": "es",
            "portuguese": "pt", "arabic": "ar", "swahili": "sw",
            "hindi": "hi", "amharic": "am", "setswana": "tn",
            "zulu": "zu", "yoruba": "yo", "hausa": "ha",
            "igbo": "ig", "shona": "sn", "afrikaans": "af",
            "malay": "ms", "indonesian": "id", "tagalog": "tl",
            "thai": "th", "vietnamese": "vi", "turkish": "tr",
            "urdu": "ur", "bengali": "bn", "tamil": "ta",
            "telugu": "te", "chinese": "zh", "japanese": "ja",
            "korean": "ko", "german": "de", "italian": "it",
            "russian": "ru", "polish": "pl", "dutch": "nl",
        }
        for key, code in lang_map.items():
            if key in lang_lower:
                return code

    country_map = {
        "zambia": "en", "botswana": "en", "kenya": "en", "nigeria": "en",
        "ghana": "en", "south africa": "en", "tanzania": "sw",
        "ethiopia": "am", "cameroon": "fr", "senegal": "fr",
        "congo (drc)": "fr", "mozambique": "pt", "rwanda": "fr",
        "uganda": "en", "zimbabwe": "en", "malawi": "en",
        "namibia": "en", "madagascar": "fr",
        "india": "hi", "bangladesh": "bn", "sri lanka": "en",
        "nepal": "hi", "pakistan": "ur",
        "saudi arabia": "ar", "uae": "ar", "qatar": "ar",
        "oman": "ar", "bahrain": "ar", "kuwait": "ar",
        "egypt": "ar", "jordan": "ar", "iraq": "ar",
        "lebanon": "ar", "morocco": "ar", "tunisia": "ar",
        "brazil": "pt", "mexico": "es", "colombia": "es",
        "argentina": "es", "chile": "es", "peru": "es",
        "indonesia": "id", "philippines": "tl", "malaysia": "ms",
        "thailand": "th", "vietnam": "vi", "singapore": "en",
        "south korea": "ko", "japan": "ja", "china": "zh",
    }
    return country_map.get(c)


def _pick_edge_voice(country: str, language: str | None) -> str:
    """Pick the best edge-tts voice for the given country and language."""
    locale = None
    country_locale = COUNTRY_LOCALE.get(country)
    if language:
        lang_lower = language.lower().strip()
        if lang_lower in LANGUAGE_TO_LOCALE:
            locale = LANGUAGE_TO_LOCALE[lang_lower]
        else:
            for lang_key, loc in LANGUAGE_TO_LOCALE.items():
                if lang_key in lang_lower:
                    locale = loc
                    break
    if not locale:
        locale = country_locale or "en-US"
    return EDGE_VOICE_MAP.get(locale, "en-US-AriaNeural")


def _generate_upbeat_music(duration_ms: int, sample_rate: int = 44100) -> bytes:
    """Generate an upbeat, groovy background music track.

    Creates a layered composition:
    - Warm bass pad (low chord)
    - Bright melodic shimmer (high arpeggiated notes)
    - Gentle rhythmic pulse (kick-like thump)
    - Soft hi-hat pattern
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    bpm = 110
    beat_samples = int(sample_rate * 60 / bpm)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(2)  # Stereo
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            beat_pos = (i % beat_samples) / beat_samples

            # Fade in/out envelope
            fade_in = min(1.0, t / 1.0)
            fade_out = min(1.0, (duration_ms / 1000 - t) / 1.5)
            master_env = fade_in * fade_out

            # Layer 1: Warm bass pad (C3 major chord, slow)
            bass_freqs = [130.81, 164.81, 196.0]
            bass = sum(math.sin(2 * math.pi * f * t) for f in bass_freqs) / len(bass_freqs)
            bass_lfo = 0.7 + 0.3 * math.sin(2 * math.pi * 0.2 * t)
            bass *= bass_lfo * 0.35

            # Layer 2: Bright shimmer (arpeggiated C5 major, faster)
            arp_freqs = [523.25, 659.25, 783.99, 659.25]
            arp_idx = int(t * 4) % len(arp_freqs)
            arp_freq = arp_freqs[arp_idx]
            arp_env = max(0, 1.0 - ((t * 4) % 1.0) * 2.5)
            shimmer = math.sin(2 * math.pi * arp_freq * t) * arp_env * 0.12

            # Layer 3: Gentle kick on beats 1 and 3
            kick = 0.0
            if beat_pos < 0.08 or (0.5 <= beat_pos < 0.58):
                kick_env = max(0, 1.0 - beat_pos * 12 if beat_pos < 0.5 else 1.0 - (beat_pos - 0.5) * 12)
                kick = math.sin(2 * math.pi * 60 * t * (1 + kick_env * 2)) * kick_env * 0.25

            # Layer 4: Soft hi-hat on every 8th note
            hihat = 0.0
            eighth_pos = (i % (beat_samples // 2)) / (beat_samples // 2)
            if eighth_pos < 0.03:
                import random
                hihat = (random.random() * 2 - 1) * 0.06 * (1 - eighth_pos / 0.03)

            # Mix all layers
            sample = (bass + shimmer + kick + hihat) * master_env

            # Stereo: slight panning for width
            left = sample + shimmer * 0.05
            right = sample - shimmer * 0.05

            left_val = max(-32768, min(32767, int(left * 28000)))
            right_val = max(-32768, min(32767, int(right * 28000)))
            frames.extend(struct.pack("<hh", left_val, right_val))

        wf.writeframes(bytes(frames))

    return buf.getvalue()


def _generate_calm_music(duration_ms: int, sample_rate: int = 44100) -> bytes:
    """Soft piano-like arpeggios, no percussion, 80 BPM -- distinctly mellow."""
    num_samples = int(sample_rate * duration_ms / 1000)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            fade_in = min(1.0, t / 2.0)
            fade_out = min(1.0, (duration_ms / 1000 - t) / 2.5)
            master_env = fade_in * fade_out

            # Slow, dreamy arpeggio -- Am7 chord tones, very slow (1.5 notes/sec)
            arp_freqs = [220.0, 261.63, 329.63, 392.0, 329.63, 261.63]
            arp_idx = int(t * 1.5) % len(arp_freqs)
            arp_freq = arp_freqs[arp_idx]
            arp_env = max(0, 1.0 - ((t * 1.5) % 1.0) * 1.2)
            # Use triangle wave for softer "piano" tone
            phase = (arp_freq * t) % 1.0
            tri = 2.0 * abs(2.0 * phase - 1.0) - 1.0
            note = tri * arp_env * 0.30

            # Deep warm pad (A2 + C3) -- very low, slow LFO
            pad = (math.sin(2 * math.pi * 110.0 * t) + math.sin(2 * math.pi * 130.81 * t)) * 0.10
            pad *= 0.6 + 0.4 * math.sin(2 * math.pi * 0.08 * t)

            sample = (note + pad) * master_env
            left = sample + note * 0.06
            right = sample - note * 0.06
            left_val = max(-32768, min(32767, int(left * 28000)))
            right_val = max(-32768, min(32767, int(right * 28000)))
            frames.extend(struct.pack("<hh", left_val, right_val))

        wf.writeframes(bytes(frames))
    return buf.getvalue()


def _generate_corporate_music(duration_ms: int, sample_rate: int = 44100) -> bytes:
    """Clean, confident corporate track -- steady pulse + bright pad, 100 BPM."""
    num_samples = int(sample_rate * duration_ms / 1000)
    bpm = 100
    beat_samples = int(sample_rate * 60 / bpm)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            beat_pos = (i % beat_samples) / beat_samples
            fade_in = min(1.0, t / 1.0)
            fade_out = min(1.0, (duration_ms / 1000 - t) / 1.5)
            master_env = fade_in * fade_out

            # Bright major pad (D4 + F#4 + A4) -- D major, distinctly different key
            pad_freqs = [293.66, 369.99, 440.0]
            pad = sum(math.sin(2 * math.pi * f * t) for f in pad_freqs) / len(pad_freqs)
            pad *= (0.8 + 0.2 * math.sin(2 * math.pi * 0.3 * t)) * 0.30

            # Steady rhythmic click on every beat (like a metronome tick)
            click = 0.0
            if beat_pos < 0.015:
                click_env = 1.0 - beat_pos / 0.015
                click = math.sin(2 * math.pi * 1200 * t) * click_env * 0.15

            # Sub-bass pulse on beats 1 and 3
            sub = 0.0
            if beat_pos < 0.08 or (0.5 <= beat_pos < 0.58):
                sub_env = max(0, 1.0 - beat_pos * 10 if beat_pos < 0.5 else 1.0 - (beat_pos - 0.5) * 10)
                sub = math.sin(2 * math.pi * 55 * t) * sub_env * 0.18

            # Rising tone every 4 beats
            four_beat = (i % (beat_samples * 4)) / (beat_samples * 4)
            rise = math.sin(2 * math.pi * (600 + 200 * four_beat) * t) * 0.03 * (1 - four_beat)

            sample = (pad + click + sub + rise) * master_env
            left = sample + rise * 0.04
            right = sample - rise * 0.04
            left_val = max(-32768, min(32767, int(left * 28000)))
            right_val = max(-32768, min(32767, int(right * 28000)))
            frames.extend(struct.pack("<hh", left_val, right_val))

        wf.writeframes(bytes(frames))
    return buf.getvalue()


BGM_GENERATORS = {
    "upbeat": _generate_upbeat_music,
    "calm": _generate_calm_music,
    "corporate": _generate_corporate_music,
}


def _mix_voice_with_music(
    voice_path: Path,
    output_path: Path,
    bgm_style: str = "upbeat",
    custom_bgm_path: Path | None = None,
) -> None:
    """Mix voice with background music, matching reference quality."""
    try:
        from pydub import AudioSegment

        voice = AudioSegment.from_mp3(str(voice_path))

        if custom_bgm_path and custom_bgm_path.exists():
            ext = custom_bgm_path.suffix.lower()
            if ext == ".wav":
                music = AudioSegment.from_wav(str(custom_bgm_path))
            elif ext in (".mp3",):
                music = AudioSegment.from_mp3(str(custom_bgm_path))
            else:
                music = AudioSegment.from_file(str(custom_bgm_path))
            music_duration = len(voice) + 2500
            if len(music) < music_duration:
                loops = (music_duration // len(music)) + 1
                music = music * loops
            music = music[:music_duration]
        else:
            music_gen = BGM_GENERATORS.get(bgm_style, _generate_upbeat_music)
            music_duration = len(voice) + 2500
            music_wav = music_gen(music_duration)
            music = AudioSegment.from_wav(io.BytesIO(music_wav))

        # Music level: -26dB below voice (subtle but audible)
        music = music - 26

        # Add 1s silence before voice (music plays alone as intro)
        silence = AudioSegment.silent(duration=1000)
        voice_padded = silence + voice + AudioSegment.silent(duration=500)

        # Match lengths
        if len(music) < len(voice_padded):
            music = music + AudioSegment.silent(duration=len(voice_padded) - len(music))
        else:
            music = music[:len(voice_padded)]

        # Overlay
        mixed = voice_padded.overlay(music)

        # Normalize to -16 dBFS (matches reference loudness)
        change_db = -16.0 - mixed.dBFS
        mixed = mixed.apply_gain(change_db)

        # Export as stereo 320kbps (matching reference quality)
        mixed.export(
            str(output_path),
            format="mp3",
            bitrate="320k",
            parameters=["-ac", "2", "-ar", "44100"],
        )
        logger.debug(f"Mixed with music: {output_path.name} ({output_path.stat().st_size / 1024:.1f} KB)")
    except Exception as e:
        logger.warning(f"Music mixing failed ({e}), using voice-only")
        if voice_path != output_path:
            import shutil
            shutil.copy2(voice_path, output_path)


async def _mix_voice_with_music_async(
    voice_path: Path,
    output_path: Path,
    bgm_style: str = "upbeat",
    custom_bgm_path: Path | None = None,
) -> None:
    """Run BGM mixing in a thread so it doesn't block the event loop (avoids pipeline stuck)."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: _mix_voice_with_music(voice_path, output_path, bgm_style=bgm_style, custom_bgm_path=custom_bgm_path),
    )


class AudioProducerAgent(BaseAgent):
    """Generates broadcast-quality OBD audio files."""

    name = "AudioProducer"
    description = "Produces professional audio recordings with background music"

    def _has_elevenlabs_credits(self) -> bool:
        return bool(
            ELEVENLABS_API_KEY
            and not ELEVENLABS_API_KEY.startswith("sk-dummy")
            and len(ELEVENLABS_API_KEY) > 10
        )

    async def _check_elevenlabs_quota(self) -> bool:
        """Return True if we can use ElevenLabs (quota OK or key may be TTS-only with no subscription read)."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{ELEVENLABS_BASE_URL}/v1/user/subscription",
                    headers=get_elevenlabs_headers(),
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    remaining = data.get("character_count", 0)
                    limit = data.get("character_limit", 0)
                    available = limit - remaining
                    logger.info(f"[{self.name}] ElevenLabs quota: {available} chars remaining")
                    return available > 500
                # 401 or other: key may have TTS but not subscription read — assume OK and let TTS call decide
                if resp.status_code == 401:
                    logger.info(f"[{self.name}] ElevenLabs subscription endpoint 401 (key may be TTS-only) — assuming OK")
                return True
        except Exception as e:
            logger.warning(f"[{self.name}] Could not check ElevenLabs quota: {e}")
        return False

    async def _elevenlabs_key_valid(self) -> bool:
        """True if key works for TTS. 200 = full access; 401 with missing voices_read = TTS-only (use curated voices)."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{ELEVENLABS_BASE_URL}/v2/voices",
                    headers=get_elevenlabs_headers(),
                    params={"page_size": 1},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return True
                if resp.status_code == 401 and elevenlabs_401_is_tts_only(resp.text):
                    logger.info(
                        "[%s] ElevenLabs key is TTS-only (no voices_read); using curated voice list.",
                        self.name,
                    )
                    return True
                if resp.status_code == 401:
                    logger.warning(
                        "[%s] ElevenLabs 401 — API key invalid or expired. Falling back to Edge TTS.",
                        self.name,
                    )
                    return False
        except Exception as e:
            logger.warning(f"[{self.name}] ElevenLabs check failed: {e}")
        return False

    async def _generate_edge_tts(
        self,
        text: str,
        voice: str,
        output_path: Path,
        section_type: str = "main",
        voice_settings: dict[str, Any] | None = None,
        skip_bgm: bool = False,
        bgm_style: str = "upbeat",
        custom_bgm_path: Path | None = None,
    ) -> dict[str, Any]:
        """Generate audio using edge-tts with section prosody, user speed, and optional BGM."""
        clean_text = _clean_text_for_tts(text)
        logger.debug(f"[{self.name}] TTS input (first 120 chars): {clean_text[:120]!r}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        prosody = SECTION_PROSODY.get(section_type, {"rate": "+0%", "pitch": "+0Hz"})
        speed = float((voice_settings or {}).get("speed", 1.0))
        rate_str = _edge_rate_with_speed(section_type, speed)

        if skip_bgm:
            communicate = edge_tts.Communicate(
                clean_text, voice, rate=rate_str, pitch=prosody["pitch"]
            )
            await communicate.save(str(output_path))
        else:
            voice_only_path = output_path.with_suffix(".voice.mp3")
            communicate = edge_tts.Communicate(
                clean_text, voice, rate=rate_str, pitch=prosody["pitch"]
            )
            await communicate.save(str(voice_only_path))
            await _mix_voice_with_music_async(voice_only_path, output_path, bgm_style=bgm_style, custom_bgm_path=custom_bgm_path)
            voice_only_path.unlink(missing_ok=True)

        file_size = output_path.stat().st_size
        logger.debug(
            f"[{self.name}] edge-tts: {output_path.name} "
            f"({file_size / 1024:.1f} KB, voice={voice}, section={section_type})"
        )

        return {
            "file_path": str(output_path),
            "file_name": output_path.name,
            "file_size_bytes": file_size,
            "voice_id": voice,
            "model": "edge-tts",
            "has_background_music": not skip_bgm,
        }

    async def _generate_elevenlabs(
        self,
        text: str,
        voice_id: str,
        voice_settings: dict[str, Any],
        output_path: Path,
        model_id: str | None = None,
        section_type: str = "main",
        skip_bgm: bool = False,
        bgm_style: str = "upbeat",
        custom_bgm_path: Path | None = None,
        language_code: str | None = None,
    ) -> dict[str, Any]:
        effective_model = model_id or ELEVENLABS_TTS_MODEL
        url = f"{ELEVENLABS_BASE_URL}/v1/text-to-speech/{voice_id}"
        clean_text = _clean_text_for_tts(text)

        from backend.config import get_live_config
        live = get_live_config()

        is_v3 = "v3" in effective_model
        default_stability = 0.65 if is_v3 else 0.35
        default_similarity = 0.85
        default_style = 0.25 if is_v3 else 0.45
        style_val = float(voice_settings.get("style", live.get("voice_style", default_style)))

        # Speed applies to both v3 (top-level) and v2 (inside voice_settings per API)
        speed_val = float(voice_settings.get("speed", live.get("voice_speed", 1.0)))

        vs: dict[str, Any] = {
            "stability": voice_settings.get("stability", live.get("voice_stability", default_stability)),
            "similarity_boost": voice_settings.get("similarity_boost", live.get("voice_similarity_boost", default_similarity)),
            "style": style_val,
            "use_speaker_boost": True,
        }

        payload: dict[str, Any] = {
            "text": clean_text,
            "model_id": effective_model,
            "voice_settings": vs,
            "apply_text_normalization": "on",
        }

        def _apply_lang_accent(p: dict[str, Any], model: str) -> None:
            """Attach language_code for local language. v3 supports many languages; v2 only ~29 (no sw, am)."""
            if language_code:
                if "v3" in model or language_code in ELEVENLABS_V2_SUPPORTED_LANG_CODES:
                    p["language_code"] = language_code

        if is_v3:
            # v3: top-level speed; voice_settings.speed not used for v3 in our stack
            payload["speed"] = speed_val
            _apply_lang_accent(payload, effective_model)
        else:
            # Primary v2 (or any non-v3): speed only inside voice_settings; lang only if v2 supports it
            payload["voice_settings"] = {**vs, "speed": speed_val}
            _apply_lang_accent(payload, effective_model)

        headers = {
            **get_elevenlabs_headers(),
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        params = {"output_format": ELEVENLABS_OUTPUT_FORMAT}

        async with httpx.AsyncClient() as client:
            response = None
            for attempt in range(2):
                try:
                    response = await client.post(
                        url, json=payload, headers=headers, params=params, timeout=30.0,
                    )
                    break
                except httpx.ConnectError as e:
                    if attempt == 0:
                        logger.warning(
                            "[%s] ElevenLabs connection error, retrying in 1.5s: %s",
                            self.name, e,
                        )
                        await asyncio.sleep(1.5)
                    else:
                        raise

            # Auto-fallback: if v3 fails, retry with eleven_multilingual_v2 — keep speed; v2 supports only ~29 languages (no Swahili, Amharic, etc.)
            if response.status_code != 200 and is_v3:
                logger.warning(
                    f"[{self.name}] eleven_v3 returned {response.status_code}, "
                    f"falling back to eleven_multilingual_v2 (v2 has limited language set)"
                )
                payload["model_id"] = "eleven_multilingual_v2"
                payload.pop("speed", None)  # v3 top-level; v2 uses voice_settings.speed
                payload["voice_settings"] = {**vs, "speed": speed_val}
                # v2 does not support all v3 languages (e.g. no "sw" Swahili) — omit language_code so v2 doesn't 400
                payload.pop("language_code", None)
                payload.pop("previous_text", None)
                response = await client.post(
                    url, json=payload, headers=headers, params=params, timeout=30.0,
                )
                if response.status_code == 422:
                    payload.pop("previous_text", None)
                    response = await client.post(
                        url, json=payload, headers=headers, params=params, timeout=30.0,
                    )
                if response.status_code == 422:
                    payload.pop("language_code", None)
                    response = await client.post(
                        url, json=payload, headers=headers, params=params, timeout=30.0,
                    )
                effective_model = "eleven_multilingual_v2"

            if response.status_code != 200:
                logger.error(f"[{self.name}] ElevenLabs error {response.status_code}: {response.text[:300]}")
                response.raise_for_status()

            output_path.parent.mkdir(parents=True, exist_ok=True)

            if skip_bgm:
                output_path.write_bytes(response.content)
            else:
                voice_only_path = output_path.with_suffix(".voice.mp3")
                voice_only_path.write_bytes(response.content)
                await _mix_voice_with_music_async(voice_only_path, output_path, bgm_style=bgm_style, custom_bgm_path=custom_bgm_path)
                voice_only_path.unlink(missing_ok=True)

        file_size = output_path.stat().st_size
        return {
            "file_path": str(output_path),
            "file_name": output_path.name,
            "file_size_bytes": file_size,
            "voice_id": voice_id,
            "model": effective_model,
            "has_background_music": not skip_bgm,
        }

    async def _validate_voice_id(self, voice_id: str) -> str:
        """Validate a voice ID exists. With premium keys, trust the ID
        since it may be from the shared library not returned by /v2/voices."""
        try:
            async with httpx.AsyncClient() as client:
                # Quick check: try to get the specific voice directly
                response = await client.get(
                    f"{ELEVENLABS_BASE_URL}/v1/voices/{voice_id}",
                    headers=get_elevenlabs_headers(),
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return voice_id
                if response.status_code in (401, 403):
                    logger.info(f"[{self.name}] Voice API restricted — trusting voice_id {voice_id}")
                    return voice_id
                logger.warning(f"[{self.name}] Voice '{voice_id}' returned {response.status_code}, trusting anyway")
        except Exception as e:
            logger.error(f"[{self.name}] Voice validation failed: {e} — trusting voice_id")
        return voice_id

    async def _build_elevenlabs_voice_pool(
        self,
        primary_voice_id: str,
        primary_name: str,
        voice_selection: dict[str, Any],
        country: str,
        language: str | None,
    ) -> list[tuple[str, str]]:
        """Build a pool of 3 diverse ElevenLabs voices (2F + 1M).

        Priority: LLM-selected alternatives > API-fetched premium voices
        > region-aware curated fallbacks. Shuffled each session for variety.
        """
        import random

        fallback_gender = ""
        if not primary_voice_id or not primary_voice_id.strip():
            from backend.agents.voice_selector import _CURATED_ELEVENLABS_VOICES
            _country_tag = country.lower().strip()
            _region_tags: set[str] = set()
            if _country_tag in {"nigeria", "kenya", "tanzania", "south africa", "ghana",
                                "zambia", "botswana", "uganda", "zimbabwe", "ethiopia", "malawi"}:
                _region_tags = {"east_africa", "west_africa", "southern_africa"}
            elif _country_tag in {"india", "bangladesh", "sri lanka", "nepal", "pakistan"}:
                _region_tags = {"south_asia"}
            elif _country_tag in {"saudi arabia", "uae", "egypt", "jordan", "qatar"}:
                _region_tags = {"middle_east"}
            elif _country_tag in {"brazil", "mexico", "colombia", "argentina"}:
                _region_tags = {"latam", "americas"}
            elif _country_tag in {"indonesia", "philippines", "malaysia", "thailand", "vietnam"}:
                _region_tags = {"apac"}

            fallback = None
            if _region_tags and _CURATED_ELEVENLABS_VOICES:
                for v in _CURATED_ELEVENLABS_VOICES:
                    v_regions = set(v.get("best_for_regions", []))
                    if v_regions & _region_tags:
                        fallback = v
                        break
            if not fallback and _CURATED_ELEVENLABS_VOICES:
                fallback = _CURATED_ELEVENLABS_VOICES[0]

            if fallback:
                primary_voice_id = fallback["voice_id"]
                primary_name = f"{fallback['name']} (Auto)"
                fallback_gender = fallback.get("labels", {}).get("gender", "female")
                logger.info(f"[{self.name}] Empty primary voice_id; using region-aware fallback for '{country}': {primary_name} ({fallback_gender})")

        primary_gender = (
            voice_selection.get("selected_voice", {}).get("gender", "").lower()
            or fallback_gender
            or "female"
        )
        seen_ids = {primary_voice_id}
        pool: list[tuple[str, str]] = [(primary_voice_id, primary_name)]

        # Collect LLM-selected alternatives as high-priority candidates
        alt_candidates: list[tuple[str, str, str]] = []
        for alt in voice_selection.get("alternative_voices", []):
            alt_id = alt.get("voice_id", "")
            alt_name = alt.get("name", "Alt Voice")
            if alt_id and alt_id not in seen_ids:
                gender_hint = "female" if any(w in alt_name.lower() for w in ["female", "woman", "girl"]) else (
                    "male" if any(w in alt_name.lower() for w in ["male", "man", "boy"]) else ""
                )
                alt_candidates.append((alt_id, alt_name, gender_hint))
                seen_ids.add(alt_id)

        # ── Region detection (for curated fallback labels only) ──
        _country_lower = country.lower().strip()
        is_african = _country_lower in {
            "nigeria", "kenya", "tanzania", "south africa", "ghana",
            "cameroon", "senegal", "congo (drc)", "congo (republic)",
            "ethiopia", "mozambique", "rwanda", "uganda", "zambia",
            "zimbabwe", "botswana", "somalia", "malawi", "namibia",
            "madagascar", "burkina faso", "mali", "niger", "chad",
            "guinea", "benin", "togo", "sierra leone", "liberia",
        }
        is_south_asian = _country_lower in {
            "india", "bangladesh", "sri lanka", "nepal", "pakistan",
        }
        is_middle_east = _country_lower in {
            "saudi arabia", "uae", "qatar", "oman", "bahrain", "kuwait",
            "egypt", "jordan", "iraq", "lebanon", "morocco", "tunisia",
            "algeria", "libya",
        }
        is_latam = _country_lower in {
            "brazil", "mexico", "colombia", "argentina", "chile", "peru",
            "venezuela", "ecuador", "guatemala", "cuba", "bolivia",
            "dominican republic", "honduras", "paraguay", "el salvador",
            "nicaragua", "costa rica", "panama", "uruguay",
        }
        is_apac = _country_lower in {
            "indonesia", "philippines", "malaysia", "thailand", "vietnam",
            "myanmar", "cambodia", "singapore", "taiwan", "south korea",
            "japan", "china", "mongolia", "laos",
        }

        # ── Fetch user's voices from API (no accent filtering) ──
        api_female: list[tuple[str, str]] = []
        api_male: list[tuple[str, str]] = []
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{ELEVENLABS_BASE_URL}/v2/voices",
                    headers=get_elevenlabs_headers(),
                    params={"page_size": 100},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    voices = resp.json().get("voices", [])
                    for v in voices:
                        vid = v.get("voice_id", "")
                        if not vid or vid in seen_ids:
                            continue
                        name = v.get("name", "")
                        labels = v.get("labels", {})
                        gender = labels.get("gender", "").lower()
                        display_accent = labels.get("accent", "Neutral") or "Neutral"
                        label = f"{name} (Female, {display_accent})" if gender == "female" else f"{name} (Male, {display_accent})"
                        if gender == "female":
                            api_female.append((vid, label))
                        elif gender == "male":
                            api_male.append((vid, label))
                random.shuffle(api_female)
                random.shuffle(api_male)
                logger.info(f"[{self.name}] API voices: {len(api_female)}F + {len(api_male)}M")
        except Exception as e:
            logger.debug(f"[{self.name}] API voice fetch skipped: {e}")

        # ── Region-aware curated fallbacks ──
        # Determine display accent for the region
        if is_african:
            _accent_label = "African"
        elif is_south_asian:
            _accent_label = "South Asian"
        elif is_middle_east:
            _accent_label = "Middle Eastern"
        elif is_latam:
            _accent_label = "Latin"
        elif is_apac:
            _accent_label = "Asian"
        else:
            _accent_label = ""

        if is_south_asian:
            female_voices = [
                ("XB0fDUnXU5powFXDhCwa", f"Charlotte (Female, {_accent_label})"),
                ("9BWtsMINqrJLrRacOk9x", f"Aria (Female, {_accent_label})"),
                ("EXAVITQu4vr4xnSDxMaL", f"Sarah (Female, {_accent_label})"),
                ("cgSgspJ2msm6clMCkdW9", f"Jessica (Female, {_accent_label})"),
                ("jBpfuIE2acCO8z3wKNLl", f"Gigi (Female, {_accent_label})"),
                ("pFZP5JQG7iQjIQuC4Bku", f"Lily (Female, {_accent_label})"),
            ]
            male_voices = [
                ("N2lVS1w4EtoT3dr4eOWO", f"Callum (Male, {_accent_label})"),
                ("cjVigY5qzO86Huf0OWal", f"Eric (Male, {_accent_label})"),
                ("TX3LPaxmHKxFdv7VOQHJ", f"Liam (Male, {_accent_label})"),
                ("onwK4e9ZLuTAKqWW03F9", f"Daniel (Male, {_accent_label})"),
                ("IKne3meq5aSn9XLyUdCD", f"Charlie (Male, {_accent_label})"),
            ]
        elif is_african:
            female_voices = [
                ("XB0fDUnXU5powFXDhCwa", f"Charlotte (Female, {_accent_label})"),
                ("9BWtsMINqrJLrRacOk9x", f"Aria (Female, {_accent_label})"),
                ("EXAVITQu4vr4xnSDxMaL", f"Sarah (Female, {_accent_label})"),
                ("cgSgspJ2msm6clMCkdW9", f"Jessica (Female, {_accent_label})"),
                ("jBpfuIE2acCO8z3wKNLl", f"Gigi (Female, {_accent_label})"),
                ("pFZP5JQG7iQjIQuC4Bku", f"Lily (Female, {_accent_label})"),
            ]
            male_voices = [
                ("N2lVS1w4EtoT3dr4eOWO", f"Callum (Male, {_accent_label})"),
                ("cjVigY5qzO86Huf0OWal", f"Eric (Male, {_accent_label})"),
                ("TX3LPaxmHKxFdv7VOQHJ", f"Liam (Male, {_accent_label})"),
                ("nPczCjzI2devNBz1zQrb", f"Brian (Male, {_accent_label})"),
                ("onwK4e9ZLuTAKqWW03F9", f"Daniel (Male, {_accent_label})"),
            ]
        elif is_middle_east:
            female_voices = [
                ("XB0fDUnXU5powFXDhCwa", f"Charlotte (Female, {_accent_label})"),
                ("9BWtsMINqrJLrRacOk9x", f"Aria (Female, {_accent_label})"),
                ("cgSgspJ2msm6clMCkdW9", f"Jessica (Female, {_accent_label})"),
                ("jBpfuIE2acCO8z3wKNLl", f"Gigi (Female, {_accent_label})"),
                ("EXAVITQu4vr4xnSDxMaL", f"Sarah (Female, {_accent_label})"),
                ("pFZP5JQG7iQjIQuC4Bku", f"Lily (Female, {_accent_label})"),
            ]
            male_voices = [
                ("N2lVS1w4EtoT3dr4eOWO", f"Callum (Male, {_accent_label})"),
                ("TX3LPaxmHKxFdv7VOQHJ", f"Liam (Male, {_accent_label})"),
                ("cjVigY5qzO86Huf0OWal", f"Eric (Male, {_accent_label})"),
                ("onwK4e9ZLuTAKqWW03F9", f"Daniel (Male, {_accent_label})"),
            ]
        elif is_latam:
            female_voices = [
                ("XB0fDUnXU5powFXDhCwa", f"Charlotte (Female, {_accent_label})"),
                ("EXAVITQu4vr4xnSDxMaL", f"Sarah (Female, {_accent_label})"),
                ("9BWtsMINqrJLrRacOk9x", f"Aria (Female, {_accent_label})"),
                ("cgSgspJ2msm6clMCkdW9", f"Jessica (Female, {_accent_label})"),
                ("jBpfuIE2acCO8z3wKNLl", f"Gigi (Female, {_accent_label})"),
                ("21m00Tcm4TlvDq8ikWAM", f"Rachel (Female, {_accent_label})"),
            ]
            male_voices = [
                ("TX3LPaxmHKxFdv7VOQHJ", f"Liam (Male, {_accent_label})"),
                ("cjVigY5qzO86Huf0OWal", f"Eric (Male, {_accent_label})"),
                ("N2lVS1w4EtoT3dr4eOWO", f"Callum (Male, {_accent_label})"),
                ("pNInz6obpgDQGcFmaJgB", f"Adam (Male, {_accent_label})"),
                ("onwK4e9ZLuTAKqWW03F9", f"Daniel (Male, {_accent_label})"),
            ]
        elif is_apac:
            female_voices = [
                ("XB0fDUnXU5powFXDhCwa", f"Charlotte (Female, {_accent_label})"),
                ("9BWtsMINqrJLrRacOk9x", f"Aria (Female, {_accent_label})"),
                ("cgSgspJ2msm6clMCkdW9", f"Jessica (Female, {_accent_label})"),
                ("jBpfuIE2acCO8z3wKNLl", f"Gigi (Female, {_accent_label})"),
                ("EXAVITQu4vr4xnSDxMaL", f"Sarah (Female, {_accent_label})"),
                ("pFZP5JQG7iQjIQuC4Bku", f"Lily (Female, {_accent_label})"),
            ]
            male_voices = [
                ("N2lVS1w4EtoT3dr4eOWO", f"Callum (Male, {_accent_label})"),
                ("TX3LPaxmHKxFdv7VOQHJ", f"Liam (Male, {_accent_label})"),
                ("cjVigY5qzO86Huf0OWal", f"Eric (Male, {_accent_label})"),
                ("onwK4e9ZLuTAKqWW03F9", f"Daniel (Male, {_accent_label})"),
                ("IKne3meq5aSn9XLyUdCD", f"Charlie (Male, {_accent_label})"),
            ]
        else:
            female_voices = [
                ("EXAVITQu4vr4xnSDxMaL", "Sarah (Female, American)"),
                ("21m00Tcm4TlvDq8ikWAM", "Rachel (Female, American)"),
                ("XB0fDUnXU5powFXDhCwa", "Charlotte (Female, Neutral)"),
                ("jsCqWAovK2LkecY7zXl4", "Freya (Female, American)"),
                ("pFZP5JQG7iQjIQuC4Bku", "Lily (Female, British)"),
                ("9BWtsMINqrJLrRacOk9x", "Aria (Female, American)"),
                ("cgSgspJ2msm6clMCkdW9", "Jessica (Female, American)"),
                ("jBpfuIE2acCO8z3wKNLl", "Gigi (Female, American)"),
            ]
            male_voices = [
                ("JBFqnCBsd6RMkjVDRZzb", "George (Male, British)"),
                ("pNInz6obpgDQGcFmaJgB", "Adam (Male, American)"),
                ("onwK4e9ZLuTAKqWW03F9", "Daniel (Male, British)"),
                ("TX3LPaxmHKxFdv7VOQHJ", "Liam (Male, American)"),
                ("cjVigY5qzO86Huf0OWal", "Eric (Male, American)"),
                ("N2lVS1w4EtoT3dr4eOWO", "Callum (Male, Transatlantic)"),
                ("IKne3meq5aSn9XLyUdCD", "Charlie (Male, Australian)"),
            ]

        # Shuffle curated lists for variety across sessions
        random.shuffle(female_voices)
        random.shuffle(male_voices)

        # Merge sources: API premium voices first (most diverse), then curated fallbacks
        all_female = api_female + female_voices
        all_male = api_male + male_voices

        # Prepend LLM alt candidates (highest priority after primary)
        for alt_id, alt_name, g in alt_candidates:
            if g == "female" or (not g and "female" in alt_name.lower()):
                all_female.insert(0, (alt_id, alt_name))
            else:
                all_male.insert(0, (alt_id, alt_name))

        # Enforce 2 female + 1 male gender balance
        female_count = 1 if primary_gender == "female" else 0
        male_count = 1 if primary_gender == "male" else 0
        need_female = 2 - female_count
        need_male = 1 - male_count

        for vid, lbl in all_female:
            if len(pool) >= 3 or need_female <= 0:
                break
            if vid not in seen_ids:
                pool.append((vid, lbl))
                seen_ids.add(vid)
                need_female -= 1
        for vid, lbl in all_male:
            if len(pool) >= 3 or need_male <= 0:
                break
            if vid not in seen_ids:
                pool.append((vid, lbl))
                seen_ids.add(vid)
                need_male -= 1
        for vid, lbl in all_female + all_male:
            if len(pool) >= 3:
                break
            if vid not in seen_ids:
                pool.append((vid, lbl))
                seen_ids.add(vid)

        logger.info(f"[{self.name}] ElevenLabs voice pool: {[p[1] for p in pool]}")
        while len(pool) < 3:
            pool.append(pool[0])
        return pool[:3]

    async def _resolve_engine(
        self,
        voice_selection: dict[str, Any],
        country: str,
        language: str | None,
        tts_engine_override: str | None,
    ) -> dict[str, Any]:
        """Resolve TTS engine, voice pools, and per-engine config.

        Returns a dict with keys: tts_engine, voice_settings, voice_name,
        el_voice_id, el_model_id, edge_voice, voice_pool (list of 3 voice descriptors).
        """
        voice_settings = voice_selection.get("voice_settings", {})
        voice_name = voice_selection.get("selected_voice", {}).get("name", "Unknown")

        tts_engine = "edge-tts"
        el_voice_id = ""
        el_model_id = ELEVENLABS_TTS_MODEL
        edge_voice = ""

        if tts_engine_override in ("elevenlabs", "edge-tts"):
            tts_engine = tts_engine_override
            logger.info(f"[{self.name}] Using user-selected TTS engine: {tts_engine}")
        else:
            # Auto priority: ElevenLabs (best quality, multilingual) > edge-tts
            if self._has_elevenlabs_credits():
                has_quota = await self._check_elevenlabs_quota()
                if has_quota:
                    tts_engine = "elevenlabs"

        if tts_engine == "elevenlabs":
            if not self._has_elevenlabs_credits():
                logger.warning(f"[{self.name}] ElevenLabs requested but no key; falling back")
                tts_engine = "edge-tts"
            elif not await self._elevenlabs_key_valid():
                # Key present but 401 Unauthorized — use Edge TTS so audio still generates
                tts_engine = "edge-tts"
            else:
                el_voice_id = voice_selection["selected_voice"]["voice_id"]
                api_params = voice_selection.get("elevenlabs_api_params", {})
                el_model_id = api_params.get("model_id", ELEVENLABS_TTS_MODEL)
                _lang = (language or "").lower().strip()
                if _lang and any(unsupported in _lang for unsupported in ELEVENLABS_V3_UNSUPPORTED_LANGUAGES):
                    el_model_id = "eleven_multilingual_v2"
                    logger.info(
                        f"[{self.name}] Using eleven_multilingual_v2 for language (v3 unsupported)"
                    )
                el_voice_id = await self._validate_voice_id(el_voice_id)
                logger.info(f"[{self.name}] Using ElevenLabs: voice={voice_name}, model={el_model_id}")

        if tts_engine == "edge-tts":
            edge_voice = _pick_edge_voice(country, language)
            logger.info(f"[{self.name}] Using edge-tts (FREE): voice={edge_voice}")

        # Build voice pool (3 voices)
        voice_pool: list[dict[str, str]] = []
        if tts_engine == "edge-tts":
            for eid, lbl in _get_edge_voice_pool(country, language):
                voice_pool.append({"edge_voice": eid, "voice_label": lbl})
        else:
            el_pool = await self._build_elevenlabs_voice_pool(
                el_voice_id, voice_name, voice_selection, country, language,
            )
            for eid, lbl in el_pool:
                voice_pool.append({"el_voice_id": eid, "voice_label": lbl})

        el_language_code = _country_to_elevenlabs_lang_code(country, language)

        return {
            "tts_engine": tts_engine,
            "voice_settings": voice_settings,
            "voice_name": voice_name,
            "el_voice_id": el_voice_id,
            "el_model_id": el_model_id,
            "el_language_code": el_language_code,
            "edge_voice": edge_voice,
            "voice_pool": voice_pool,
        }

    async def _run_tts_jobs(
        self,
        jobs: list[dict[str, Any]],
        engine_ctx: dict[str, Any],
        audio_format: str = "mp3",
    ) -> list[dict[str, Any]]:
        """Execute a list of TTS jobs with concurrency limiting."""
        tts_engine = engine_ctx["tts_engine"]
        voice_settings = engine_ctx["voice_settings"]
        el_voice_id = engine_ctx["el_voice_id"]
        el_model_id = engine_ctx["el_model_id"]
        el_language_code = engine_ctx.get("el_language_code")
        edge_voice = engine_ctx["edge_voice"]

        async def _tts_job(job: dict[str, Any]) -> dict[str, Any]:
            job["text"] = _clean_text_for_tts(
                job["text"],
                apply_pronunciation_hacks=True,
            )
            if re.search(r"[\[\]【】<>{}]", job["text"]):
                logger.warning(
                    f"[{self.name}] Possible residual tags in TTS text: "
                    f"{job['text'][:150]!r}"
                )

            skip_bgm = job.get("skip_bgm", False)
            bgm_style = job.get("bgm_style", "upbeat")
            custom_bgm = job.get("custom_bgm_path")
            if custom_bgm and isinstance(custom_bgm, str):
                custom_bgm = Path(custom_bgm)
            try:
                if tts_engine == "elevenlabs":
                    result = await self._generate_elevenlabs(
                        text=job["text"],
                        voice_id=job.get("el_voice_id", el_voice_id),
                        voice_settings=voice_settings,
                        output_path=job["path"],
                        model_id=el_model_id,
                        section_type=job.get("type", "main"),
                        skip_bgm=skip_bgm,
                        bgm_style=bgm_style,
                        custom_bgm_path=custom_bgm,
                        language_code=el_language_code,
                    )
                else:
                    result = await self._generate_edge_tts(
                        text=job["text"],
                        voice=job.get("edge_voice", edge_voice),
                        output_path=job["path"],
                        section_type=job.get("type", "main"),
                        voice_settings=voice_settings,
                        skip_bgm=skip_bgm,
                        bgm_style=bgm_style,
                        custom_bgm_path=custom_bgm,
                    )
                result["variant_id"] = job["variant_id"]
                result["type"] = job["type"]
                result["theme"] = job.get("theme", "")
                result["voice_index"] = job.get("voice_index", 1)
                result["voice_label"] = job.get("voice_label", "Voice 1")

                if audio_format == "wav":
                    try:
                        from pydub import AudioSegment
                        mp3_path = Path(result["file_path"])
                        if mp3_path.suffix.lower() == ".mp3" and mp3_path.exists():
                            wav_path = mp3_path.with_suffix(".wav")
                            seg = AudioSegment.from_mp3(str(mp3_path))
                            seg.export(str(wav_path), format="wav")
                            mp3_path.unlink(missing_ok=True)
                            result["file_name"] = wav_path.name
                            result["file_path"] = str(wav_path)
                            result["file_size_bytes"] = wav_path.stat().st_size
                    except Exception as wav_err:
                        logger.warning(f"[{self.name}] WAV conversion failed: {wav_err}")

                # Persist the local file (kept as a safety copy) and try to upload
                # to Cloudflare R2 so the audio is reachable even when the backend
                # is offline. If R2 isn't configured or the upload fails, the local
                # file is still served via FastAPI's /api/audio/{sid}/{file}.
                try:
                    from backend.storage import upload_audio as _r2_upload
                    file_path = Path(result["file_path"])
                    session_id = file_path.parent.name
                    key = f"{session_id}/{file_path.name}"
                    public_url = _r2_upload(file_path, key)
                    if public_url:
                        result["public_url"] = public_url
                except Exception as _r2_err:
                    logger.debug(f"[{self.name}] R2 upload skipped: {_r2_err}")
                return result
            except Exception as e:
                err_detail = f"{type(e).__name__}: {e}" if str(e) else f"{type(e).__name__} (no message)"
                logger.error(f"[{self.name}] Failed {job['type']} v{job['variant_id']} voice{job.get('voice_index', 1)}: {err_detail}", exc_info=True)

                # Retry once on transient failures
                try:
                    logger.debug(f"[{self.name}] Retrying {job['type']} v{job['variant_id']} voice{job.get('voice_index', 1)}...")
                    if tts_engine == "elevenlabs":
                        result = await self._generate_elevenlabs(
                            text=job["text"],
                            voice_id=job.get("el_voice_id", el_voice_id),
                            voice_settings=voice_settings,
                            output_path=job["path"],
                            model_id=el_model_id,
                            section_type=job.get("type", "main"),
                            skip_bgm=True,
                            language_code=el_language_code,
                        )
                    else:
                        result = await self._generate_edge_tts(
                            text=job["text"], voice=job.get("edge_voice", edge_voice),
                            output_path=job["path"], section_type=job.get("type", "main"),
                            voice_settings=voice_settings, skip_bgm=True,
                        )
                    result["variant_id"] = job["variant_id"]
                    result["type"] = job["type"]
                    result["theme"] = job.get("theme", "")
                    result["voice_index"] = job.get("voice_index", 1)
                    result["voice_label"] = job.get("voice_label", "Voice 1")
                    logger.debug(f"[{self.name}] Retry succeeded for v{job['variant_id']} voice{job.get('voice_index', 1)}")
                    return result
                except Exception:
                    pass

                return {
                    "variant_id": job["variant_id"],
                    "type": job["type"],
                    "theme": job.get("theme", ""),
                    "voice_index": job.get("voice_index", 1),
                    "voice_label": job.get("voice_label", "Voice 1"),
                    "error": err_detail,
                }

        semaphore = asyncio.Semaphore(10)

        async def _limited(job: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                return await _tts_job(job)

        return list(await asyncio.gather(*[_limited(j) for j in jobs]))

    # ── Phase 1: Hook-only previews (3 voices, no BGM) ──────────────────

    async def run_hook_previews(
        self,
        scripts: dict[str, Any],
        voice_selection: dict[str, Any],
        session_id: str | None = None,
        country: str = "",
        language: str | None = None,
        tts_engine_override: str | None = None,
        num_voices: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate hook-only audio previews with N voices per variant (no BGM)."""
        from backend.database import get_pipeline_config
        config = get_pipeline_config()
        n_voices = num_voices or config.get("num_hook_voices", 3)
        if not isinstance(n_voices, int) or n_voices < 1:
            n_voices = 3

        session_id = session_id or str(uuid.uuid4())[:8]
        session_dir = OUTPUTS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        engine_ctx = await self._resolve_engine(voice_selection, country, language, tts_engine_override)
        tts_engine = engine_ctx["tts_engine"]
        voice_pool = engine_ctx["voice_pool"]
        while len(voice_pool) < n_voices:
            voice_pool.append(voice_pool[0])
        voice_pool = voice_pool[:n_voices]
        script_list = scripts.get("scripts", [])
        # Hook previews must stay short + voice-only — no BGM (avoids 15× ffmpeg hangs)
        _PREVIEW_MAX_CHARS = 500

        jobs: list[dict[str, Any]] = []
        for script in script_list:
            variant_id = script.get("variant_id", 0)
            theme = script.get("theme", "unknown")
            hook_text = script.get("hook", "")
            if not hook_text or not hook_text.strip():
                hook_text = script.get("full_script", "") or ""
            if hook_text and len(hook_text) > _PREVIEW_MAX_CHARS:
                hook_text = hook_text[:_PREVIEW_MAX_CHARS].rsplit(" ", 1)[0] + "..."

            if not hook_text or not hook_text.strip():
                continue

            for voice_idx in range(n_voices):
                job: dict[str, Any] = {
                    "text": hook_text,
                    "path": session_dir / f"variant_{variant_id}_voice{voice_idx + 1}_hook_preview.mp3",
                    "variant_id": variant_id,
                    "type": "hook_preview",
                    "theme": theme,
                    "voice_index": voice_idx + 1,
                    "skip_bgm": True,
                }
                job.update(voice_pool[voice_idx])
                jobs.append(job)

        logger.info(f"[{self.name}] Generating {len(jobs)} hook previews via {tts_engine}")
        results = await self._run_tts_jobs(jobs, engine_ctx)

        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]

        # Auto-fallback only when engine was Auto; never override user's choice
        if len(successful) == 0 and len(failed) > 0 and not tts_engine_override:
            for fb_engine in ["edge-tts"]:
                if fb_engine == tts_engine:
                    continue

                logger.warning(
                    f"[{self.name}] All {len(failed)} previews failed via {tts_engine}; "
                    f"retrying with {fb_engine}"
                )
                engine_ctx = await self._resolve_engine(
                    voice_selection, country, language, fb_engine
                )
                tts_engine = engine_ctx["tts_engine"]
                voice_pool = engine_ctx["voice_pool"]

                retry_jobs: list[dict[str, Any]] = []
                for script in script_list:
                    variant_id = script.get("variant_id", 0)
                    theme = script.get("theme", "unknown")
                    hook_text = script.get("hook", "") or ""
                    if not hook_text.strip():
                        hook_text = (script.get("full_script", "") or "")[:_PREVIEW_MAX_CHARS]
                    if len(hook_text) > _PREVIEW_MAX_CHARS:
                        hook_text = hook_text[:_PREVIEW_MAX_CHARS].rsplit(" ", 1)[0] + "..."
                    if not hook_text.strip():
                        continue
                    for vi in range(min(n_voices, len(voice_pool))):
                        rj: dict[str, Any] = {
                            "text": hook_text,
                            "path": session_dir / f"variant_{variant_id}_voice{vi + 1}_hook_preview.mp3",
                            "variant_id": variant_id,
                            "type": "hook_preview",
                            "theme": theme,
                            "voice_index": vi + 1,
                            "skip_bgm": True,
                        }
                        rj.update(voice_pool[vi])
                        retry_jobs.append(rj)

                results = await self._run_tts_jobs(retry_jobs, engine_ctx)
                successful = [r for r in results if "error" not in r]
                failed = [r for r in results if "error" in r]
                if len(successful) > 0:
                    break

        logger.info(
            f"[{self.name}] Hook previews done: {len(successful)} ok, {len(failed)} failed"
        )

        return {
            "session_id": session_id,
            "session_dir": str(session_dir),
            "tts_engine": tts_engine,
            "voice_pool": [
                {
                    "voice_index": i + 1,
                    "voice_label": v.get("voice_label", f"Voice {i + 1}"),
                    **({"el_voice_id": v["el_voice_id"]} if "el_voice_id" in v else {}),
                    **({"edge_voice": v["edge_voice"]} if "edge_voice" in v else {}),
                }
                for i, v in enumerate(voice_pool)
            ],
            "engine_ctx": engine_ctx,
            "hook_previews": successful,
            "failed_previews": failed,
            "summary": {
                "total_generated": len(successful),
                "total_failed": len(failed),
                "variants_count": len(script_list),
            },
        }

    # ── Phase 2: Full audio with chosen voice + BGM ──────────────────────

    async def run_final_audio(
        self,
        scripts: dict[str, Any],
        voice_selection: dict[str, Any],
        voice_choices: dict[int, int],
        session_id: str,
        country: str = "",
        language: str | None = None,
        tts_engine_override: str | None = None,
        bgm_style: str = "upbeat",
        audio_format: str = "mp3",
        custom_bgm_path: str | Path | None = None,
        prebuilt_engine_ctx: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate full audio for all sections using the user-chosen voice per variant.

        Args:
            voice_choices: mapping of variant_id -> voice_index (1-based).
            bgm_style: one of "upbeat", "calm", "corporate".
            audio_format: "mp3" or "wav" -- if wav, files are converted before upload.
            prebuilt_engine_ctx: reuse engine context from preview phase to keep voice pool consistent.
        """
        session_dir = OUTPUTS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        if prebuilt_engine_ctx and isinstance(prebuilt_engine_ctx, dict) and (prebuilt_engine_ctx.get("voice_pool") or []):
            engine_ctx = prebuilt_engine_ctx
        else:
            engine_ctx = await self._resolve_engine(voice_selection, country, language, tts_engine_override)
        tts_engine = engine_ctx["tts_engine"]
        voice_pool = engine_ctx.get("voice_pool") or []
        if not voice_pool:
            # Final fallback: force edge-tts so we always have a voice pool
            logger.warning(f"[{self.name}] run_final_audio: voice_pool was empty; resolving edge-tts fallback")
            engine_ctx = await self._resolve_engine(voice_selection, country, language, "edge-tts")
            voice_pool = engine_ctx.get("voice_pool") or []
            tts_engine = engine_ctx["tts_engine"]
        if not voice_pool:
            logger.error(f"[{self.name}] run_final_audio: voice_pool still empty after edge-tts fallback")
            return {
                "session_id": session_id,
                "session_dir": str(session_dir),
                "tts_engine": tts_engine,
                "voice_used": {},
                "audio_files": [],
                "failed_files": [],
                "summary": {"total_generated": 0, "total_failed": 0, "variants_count": 0, "has_background_music": False, "bgm_style": bgm_style, "output_quality": ""},
                "error": "No voice pool available for TTS",
            }
        script_list = scripts.get("scripts", [])

        ALL_SECTIONS = [
            ("full_script", "main"),
            ("fallback_1", "fallback1"),
            ("fallback_2", "fallback2"),
            ("polite_closure", "closure"),
        ]

        def make_job(
            text: str,
            audio_type: str,
            variant_id: int,
            theme: str,
            chosen_idx: int,
            no_bgm: bool,
            resolved_bgm_path: Path | None,
        ) -> dict[str, Any]:
            j: dict[str, Any] = {
                "text": text,
                "path": session_dir / f"variant_{variant_id}_voice{chosen_idx + 1}_{audio_type}.mp3",
                "variant_id": variant_id,
                "type": audio_type,
                "theme": theme,
                "voice_index": chosen_idx + 1,
                "skip_bgm": no_bgm,
                "bgm_style": bgm_style if not no_bgm else "upbeat",
                "custom_bgm_path": str(resolved_bgm_path) if resolved_bgm_path else None,
            }
            j.update(voice_pool[chosen_idx])
            return j

        jobs: list[dict[str, Any]] = []
        no_bgm = bgm_style == "none"
        resolved_bgm_path = Path(custom_bgm_path) if custom_bgm_path else None

        for script in script_list:
            variant_id = script.get("variant_id", 0)
            theme = script.get("theme", "unknown")
            chosen_idx = voice_choices.get(variant_id, 1) - 1
            chosen_idx = max(0, min(chosen_idx, len(voice_pool) - 1))

            segments = script.get("segments")
            full_script_text = (script.get("full_script") or "").strip()
            is_flow_script = isinstance(segments, list) and len(segments) > 0
            segment_texts = [(seg.get("text") or "").strip() for seg in segments] if is_flow_script else []
            has_segment_text = bool(segment_texts and any(segment_texts))
            if has_segment_text:
                # Flow-based: always prefer individual segments when they have text.
                # This ensures edited segments still produce separate audio files
                # even if full_script has minor whitespace differences.
                for seg in segments:
                    step_id = seg.get("step_id", "step")
                    text = (seg.get("text") or "").strip()
                    if not text:
                        continue
                    audio_type = f"step_{step_id}"
                    jobs.append(make_job(text, audio_type, variant_id, theme, chosen_idx, no_bgm, resolved_bgm_path))
            elif is_flow_script and full_script_text:
                # Flow campaign but segments empty/stale; user edited full_script only (e.g. added "BTC")
                jobs.append(
                    make_job(
                        full_script_text,
                        "main",
                        variant_id,
                        theme,
                        chosen_idx,
                        no_bgm,
                        resolved_bgm_path,
                    )
                )
            else:
                # Non-flow (default): main + fallback1 + fallback2 + closure
                for field, audio_type in ALL_SECTIONS:
                    text = script.get(field, "")
                    if not text or not str(text).strip():
                        continue
                    jobs.append(make_job(str(text).strip(), audio_type, variant_id, theme, chosen_idx, no_bgm, resolved_bgm_path))

        if not jobs:
            logger.warning(
                f"[{self.name}] run_final_audio: no TTS jobs built (scripts={len(script_list)}, "
                "check script structure: full_script/segments and section text)"
            )
            return {
                "session_id": session_id,
                "session_dir": str(session_dir),
                "tts_engine": tts_engine,
                "voice_used": {},
                "audio_files": [],
                "failed_files": [],
                "summary": {"total_generated": 0, "total_failed": 0, "variants_count": len(script_list), "has_background_music": False, "bgm_style": bgm_style, "output_quality": ""},
                "error": "No audio segments to generate (script sections may be empty)",
            }

        logger.info(
            f"[{self.name}] Generating {len(jobs)} final audio files via {tts_engine} "
            f"(bgm={bgm_style}, fmt={audio_format})"
        )
        results = await self._run_tts_jobs(jobs, engine_ctx, audio_format=audio_format)

        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]
        logger.info(
            f"[{self.name}] Final audio TTS phase done: {len(successful)} ok, {len(failed)} failed"
        )

        # Auto-fallback only when engine was Auto; never override user's choice
        if len(successful) == 0 and len(failed) > 0 and not tts_engine_override:
            for fb_engine in ["edge-tts"]:
                if fb_engine == tts_engine:
                    continue

                logger.warning(
                    f"[{self.name}] All {len(failed)} final audio failed via {tts_engine}; "
                    f"retrying with {fb_engine}"
                )
                engine_ctx = await self._resolve_engine(
                    voice_selection, country, language, fb_engine
                )
                tts_engine = engine_ctx["tts_engine"]
                voice_pool = engine_ctx["voice_pool"]
                retry_jobs = []
                for script in script_list:
                    vid = script.get("variant_id", 0)
                    th = script.get("theme", "unknown")
                    cidx = max(0, min(voice_choices.get(vid, 1) - 1, len(voice_pool) - 1))
                    segs = script.get("segments")
                    is_flow = isinstance(segs, list) and len(segs) > 0
                    fst = (script.get("full_script") or "").strip()
                    seg_txts = [(s.get("text") or "").strip() for s in segs] if is_flow else []
                    segs_match = fst and seg_txts and fst == " ".join(seg_txts)
                    has_stext = bool(seg_txts and any(seg_txts))
                    if has_stext and (not fst or segs_match):
                        for seg in segs:
                            step_id = seg.get("step_id", "step")
                            t = (seg.get("text") or "").strip()
                            if not t:
                                continue
                            at = f"step_{step_id}"
                            retry_jobs.append(make_job(t, at, vid, th, cidx, False, resolved_bgm_path))
                    elif is_flow and fst:
                        retry_jobs.append(make_job(fst, "main", vid, th, cidx, False, resolved_bgm_path))
                    else:
                        for field, audio_type in ALL_SECTIONS:
                            text = script.get(field, "")
                            if not text or not str(text).strip():
                                continue
                            retry_jobs.append(make_job(str(text).strip(), audio_type, vid, th, cidx, False, resolved_bgm_path))
                results = await self._run_tts_jobs(retry_jobs, engine_ctx, audio_format=audio_format)
                successful = [r for r in results if "error" not in r]
                failed = [r for r in results if "error" in r]
                if len(successful) > 0:
                    break

        voice_settings = engine_ctx["voice_settings"]
        voice_id_used = (
            engine_ctx["el_voice_id"] if tts_engine == "elevenlabs"
            else engine_ctx["edge_voice"]
        )
        voice_name_used = (
            engine_ctx["voice_name"] if tts_engine == "elevenlabs"
            else engine_ctx["edge_voice"]
        )

        logger.info(
            f"[{self.name}] Final audio complete: {len(successful)} generated, "
            f"{len(failed)} failed via {tts_engine}"
        )

        return {
            "session_id": session_id,
            "session_dir": str(session_dir),
            "tts_engine": tts_engine,
            "voice_used": {
                "voice_id": voice_id_used,
                "name": voice_name_used,
                "settings": voice_settings,
            },
            "audio_files": successful,
            "failed_files": failed,
            "summary": {
                "total_generated": len(successful),
                "total_failed": len(failed),
                "variants_count": len(script_list),
                "has_background_music": True,
                "bgm_style": bgm_style,
                "output_quality": "stereo 320kbps 44.1kHz",
            },
        }

    # ── Legacy: single-step full generation (kept for backward compat) ───

    async def run(
        self,
        scripts: dict[str, Any],
        voice_selection: dict[str, Any],
        session_id: str | None = None,
        country: str = "",
        language: str | None = None,
        tts_engine_override: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate broadcast-quality audio for all script variants (legacy single-step)."""
        session_id = session_id or str(uuid.uuid4())[:8]
        session_dir = OUTPUTS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        engine_ctx = await self._resolve_engine(voice_selection, country, language, tts_engine_override)
        tts_engine = engine_ctx["tts_engine"]
        voice_pool = engine_ctx["voice_pool"]
        voice_settings = engine_ctx["voice_settings"]
        voice_name = engine_ctx["voice_name"]
        script_list = scripts.get("scripts", [])

        MULTI_VOICE_SECTIONS = [("full_script", "main")]
        SINGLE_VOICE_SECTIONS = [("fallback_1", "fallback1"), ("fallback_2", "fallback2"), ("polite_closure", "closure")]

        jobs: list[dict[str, Any]] = []
        for script in script_list:
            variant_id = script.get("variant_id", 0)
            theme = script.get("theme", "unknown")

            for voice_idx in range(3):
                for field, audio_type in MULTI_VOICE_SECTIONS:
                    text = script.get(field, "")
                    if not text or not text.strip():
                        continue
                    job: dict[str, Any] = {
                        "text": text,
                        "path": session_dir / f"variant_{variant_id}_voice{voice_idx + 1}_{audio_type}.mp3",
                        "variant_id": variant_id,
                        "type": audio_type,
                        "theme": theme,
                        "voice_index": voice_idx + 1,
                    }
                    job.update(voice_pool[voice_idx])
                    jobs.append(job)

            for field, audio_type in SINGLE_VOICE_SECTIONS:
                text = script.get(field, "")
                if not text or not text.strip():
                    continue
                job = {
                    "text": text,
                    "path": session_dir / f"variant_{variant_id}_voice1_{audio_type}.mp3",
                    "variant_id": variant_id,
                    "type": audio_type,
                    "theme": theme,
                    "voice_index": 1,
                }
                job.update(voice_pool[0])
                jobs.append(job)

        logger.info(f"[{self.name}] Generating {len(jobs)} audio files via {tts_engine} (3 voices)")
        audio_results = await self._run_tts_jobs(jobs, engine_ctx)

        successful = [r for r in audio_results if "error" not in r]
        failed = [r for r in audio_results if "error" in r]

        logger.info(
            f"[{self.name}] Audio complete: {len(successful)} generated, "
            f"{len(failed)} failed via {tts_engine}"
        )

        voice_id_used = (
            engine_ctx["el_voice_id"] if tts_engine == "elevenlabs"
            else engine_ctx["edge_voice"]
        )
        voice_name_used = (
            voice_name if tts_engine == "elevenlabs"
            else engine_ctx["edge_voice"]
        )

        return {
            "session_id": session_id,
            "session_dir": str(session_dir),
            "tts_engine": tts_engine,
            "voice_used": {
                "voice_id": voice_id_used,
                "name": voice_name_used,
                "settings": voice_settings,
            },
            "audio_files": successful,
            "failed_files": failed,
            "summary": {
                "total_generated": len(successful),
                "total_failed": len(failed),
                "variants_count": len(script_list),
                "has_background_music": True,
                "output_quality": "stereo 320kbps 44.1kHz",
            },
        }
