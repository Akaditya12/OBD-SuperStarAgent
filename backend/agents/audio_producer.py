"""Agent 6: Audio Producer -- generates broadcast-quality OBD audio.

Produces professional audio with:
- Murf AI (primary, 100k free chars) for studio-quality voice
- edge-tts (unlimited free fallback) for voice
- ElevenLabs (premium) for voice
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
    MURF_API_KEY,
    OUTPUTS_DIR,
)
from backend.database import supabase

from .base import BaseAgent

logger = logging.getLogger(__name__)

# Matches ANY [tag] -- catches all LLM-invented tags like [neutral], [friendly], etc.
_ANY_BRACKET_TAG = re.compile(r"\[[^\]]{1,30}\]")
# Matches XML-style tags like <voice emotion='curious'>, </voice>, <break time="1s"/>, etc.
_ANY_XML_TAG = re.compile(r"</?[a-zA-Z][^>]{0,80}>")

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
    "so-SO": "so-SO-UbaxNeural",
}

COUNTRY_LOCALE: dict[str, str] = {
    "India": "en-IN", "Nigeria": "en-NG", "Kenya": "en-KE",
    "Tanzania": "en-TZ", "South Africa": "en-ZA", "Ghana": "en-GH",
    "Cameroon": "fr-CM", "Senegal": "fr-SN", "Congo (DRC)": "fr-CD",
    "Congo (Republic)": "fr-CD", "Ethiopia": "am-ET",
    "Mozambique": "pt-BR", "Rwanda": "en-KE", "Uganda": "en-KE",
    "Zambia": "en-ZA", "Zimbabwe": "en-ZA", "Botswana": "en-ZA",
    "Somalia": "so-SO", "Bangladesh": "bn-IN", "Pakistan": "ur-PK",
    "Indonesia": "id-ID", "Philippines": "fil-PH",
}

# Prosody per section type -- warm and clear with slight variation
SECTION_PROSODY: dict[str, dict[str, str]] = {
    "main":      {"rate": "-3%",   "pitch": "+2Hz"},   # slightly slower = warmer
    "fallback1": {"rate": "+0%",   "pitch": "+3Hz"},   # a touch brighter for urgency
    "fallback2": {"rate": "-2%",   "pitch": "+1Hz"},   # calm, reassuring
    "closure":   {"rate": "-5%",   "pitch": "-1Hz"},   # gentle close
}


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
    """Strip ALL bracket tags and prepare text for TTS.

    Args:
        apply_pronunciation_hacks: If True, replace acronyms with spaced letters
            (for edge-tts/elevenlabs). Set False for Murf which uses its own
            pronunciationDictionary.
    """
    # Step 1: Convert known tags to natural speech sounds
    text = re.sub(r"\[laughs?\]", "ha ha, ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[lightlaugh\]", "heh, ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[sigh\]", "hmm, ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[gasps?\]", "oh! ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[short\s*pause\]", ", ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[pause\]", "... ", text, flags=re.IGNORECASE)

    # Step 2: Strip ALL remaining [anything] tags
    text = _ANY_BRACKET_TAG.sub("", text)

    # Step 3: Strip XML-style tags (<voice emotion='...'>, </voice>, etc.)
    text = _ANY_XML_TAG.sub("", text)

    # Step 4: Remove markdown bold/italic markers
    text = text.replace("**", "").replace("*", "")

    # Step 5: Convert ALL-CAPS common words back to normal case so TTS
    # doesn't spell them out (e.g. "YOU" -> "you", "NOW" -> "now").
    _KNOWN_ACRONYMS = {"IVR", "OBD", "CLI", "BNG", "DTMF", "USSD", "SMS", "CTA", "AI", "EVA", "INR"}
    def _fix_caps(m: re.Match) -> str:
        word = m.group(0)
        return word if word in _KNOWN_ACRONYMS else word.capitalize()
    text = re.sub(r"\b[A-Z]{2,}\b", _fix_caps, text)

    # Step 6: Fix acronym/brand pronunciation (only for non-Murf engines)
    if apply_pronunciation_hacks:
        for pattern, replacement in _PRONUNCIATION_FIXES:
            text = pattern.sub(replacement, text)

    # Step 7: Clean up artifacts
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
    "somali": "so-SO", "zulu": "zu-ZA", "afrikaans": "en-ZA",
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
}

MURF_VOICE_POOL: dict[str, list[tuple[str, str, str, str]]] = {
    # language -> [(voice_id, locale, style, label), ...]
    "hindi": [
        ("hi-IN-ayushi", "hi-IN", "Conversational", "Ayushi (Female)"),
        ("hi-IN-kabir", "hi-IN", "Conversational", "Kabir (Male)"),
        ("en-IN-arohi", "en-IN", "Promo", "Arohi (Female)"),
    ],
    "hinglish": [
        ("hi-IN-ayushi", "hi-IN", "Conversational", "Ayushi (Female)"),
        ("hi-IN-kabir", "hi-IN", "Conversational", "Kabir (Male)"),
        ("en-IN-arohi", "en-IN", "Promo", "Arohi (Female)"),
    ],
    "english": [
        ("en-IN-arohi", "en-IN", "Promo", "Arohi (Female)"),
        ("en-US-zion", "en-US", "Conversational", "Zion (Male)"),
        ("en-US-samantha", "en-US", "Promo", "Samantha (Female)"),
    ],
    "tamil": [
        ("ta-IN-iniya", "ta-IN", "Conversational", "Iniya (Female)"),
        ("en-IN-arohi", "en-IN", "Promo", "Arohi (Female)"),
        ("en-US-zion", "en-US", "Conversational", "Zion (Male)"),
    ],
    "telugu": [
        ("en-IN-arohi", "en-IN", "Promo", "Arohi (Female)"),
        ("en-US-zion", "en-US", "Conversational", "Zion (Male)"),
        ("en-US-samantha", "en-US", "Promo", "Samantha (Female)"),
    ],
    "bengali": [
        ("bn-IN-anwesha", "bn-IN", "Conversational", "Anwesha (Female)"),
        ("en-IN-arohi", "en-IN", "Promo", "Arohi (Female)"),
        ("en-US-zion", "en-US", "Conversational", "Zion (Male)"),
    ],
    "french": [
        ("fr-FR-adélie", "fr-FR", "Narration", "Adélie (Female)"),
        ("fr-FR-axel", "fr-FR", "Narration", "Axel (Male)"),
        ("fr-FR-louise", "fr-FR", "Narration", "Louise (Female)"),
    ],
    "portuguese": [
        ("pt-BR-isadora", "pt-BR", "Conversational", "Isadora (Female)"),
        ("en-US-zion", "en-US", "Conversational", "Zion (Male)"),
        ("en-US-samantha", "en-US", "Promo", "Samantha (Female)"),
    ],
}


def _get_edge_voice_pool(country: str, language: str | None) -> list[tuple[str, str]]:
    """Get 3 edge-tts voices for the given country/language."""
    locale = None
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
        locale = COUNTRY_LOCALE.get(country, "en-US")

    if locale in EDGE_VOICE_POOL:
        return EDGE_VOICE_POOL[locale]

    # Fallback: fr-CM -> fr-FR, pt-MZ -> pt-BR, etc.
    lang_prefix = locale.split("-")[0] if locale else ""
    for pool_locale in EDGE_VOICE_POOL:
        if pool_locale.startswith(lang_prefix + "-"):
            return EDGE_VOICE_POOL[pool_locale]

    primary = EDGE_VOICE_MAP.get(locale, "en-US-AriaNeural")
    return [(primary, "Voice 1"), (primary, "Voice 2"), (primary, "Voice 3")]


def _get_murf_voice_pool(country: str, language: str | None) -> list[tuple[str, str, str, str]]:
    """Get 3 Murf voices for the given country/language."""
    if language:
        lang_lower = language.lower().strip()
        if lang_lower in MURF_VOICE_POOL:
            return MURF_VOICE_POOL[lang_lower]
        for lang_key, pool in MURF_VOICE_POOL.items():
            if lang_key in lang_lower:
                return pool

    # Country fallback
    lang_for_country = {
        "India": "english", "Nigeria": "english", "Kenya": "english",
        "Cameroon": "french", "Senegal": "french", "Mozambique": "portuguese",
        "Bangladesh": "bengali",
    }
    mapped = lang_for_country.get(country, "english")
    if mapped in MURF_VOICE_POOL:
        return MURF_VOICE_POOL[mapped]

    return MURF_VOICE_POOL["english"]


def _pick_edge_voice(country: str, language: str | None) -> str:
    """Pick the best edge-tts voice for the given country and language."""
    if language:
        lang_lower = language.lower().strip()
        # Direct language name match (Hindi, Hinglish, Tamil, etc.)
        if lang_lower in LANGUAGE_TO_LOCALE:
            locale = LANGUAGE_TO_LOCALE[lang_lower]
            if locale in EDGE_VOICE_MAP:
                return EDGE_VOICE_MAP[locale]
        # Try partial match (e.g. "Hindi/English mix" -> "hindi")
        for lang_key, locale in LANGUAGE_TO_LOCALE.items():
            if lang_key in lang_lower:
                if locale in EDGE_VOICE_MAP:
                    return EDGE_VOICE_MAP[locale]

    locale = COUNTRY_LOCALE.get(country, "en-US")
    return EDGE_VOICE_MAP.get(locale, "en-US-AriaNeural")


# ── Murf AI voice mapping ──
# (voice_id, locale, style) -- voice IDs are in locale-name format
MURF_VOICE_MAP: dict[str, tuple[str, str, str]] = {
    "hindi":      ("hi-IN-ayushi",   "hi-IN",  "Conversational"),
    "hinglish":   ("hi-IN-ayushi",   "hi-IN",  "Conversational"),
    "tamil":      ("ta-IN-iniya",    "ta-IN",  "Conversational"),
    "telugu":     ("en-IN-arohi",    "te-IN",  "Promo"),
    "bengali":    ("bn-IN-anwesha",  "bn-IN",  "Conversational"),
    "kannada":    ("en-UK-hazel",    "kn-IN",  "Conversational"),
    "malayalam":  ("en-IN-arohi",    "en-IN",  "Promo"),
    "marathi":    ("en-IN-arohi",    "en-IN",  "Promo"),
    "punjabi":    ("en-IN-arohi",    "en-IN",  "Promo"),
    "gujarati":   ("bn-IN-anwesha",  "gu-IN",  "Conversational"),
    "english":    ("en-IN-arohi",    "en-IN",  "Promo"),
    "french":     ("fr-FR-adélie",   "fr-FR",  "Narration"),
    "portuguese": ("pt-BR-isadora",  "pt-BR",  "Conversational"),
    "indonesian": ("en-US-zion",     "id-ID",  "Conversational"),
    "filipino":   ("en-IN-arohi",    "en-IN",  "Promo"),
    "german":     ("de-DE-josephine","de-DE",  "Promo"),
    "spanish":    ("en-US-samantha", "es-ES",  "Promo"),
}

MURF_COUNTRY_VOICE: dict[str, tuple[str, str, str]] = {
    "India":       ("en-IN-arohi",    "en-IN",  "Promo"),
    "Nigeria":     ("en-US-samantha", "en-US",  "Promo"),
    "Kenya":       ("en-US-samantha", "en-US",  "Promo"),
    "Tanzania":    ("en-US-samantha", "en-US",  "Promo"),
    "South Africa":("en-US-samantha", "en-US",  "Promo"),
    "Ghana":       ("en-US-samantha", "en-US",  "Promo"),
    "Ethiopia":    ("en-US-samantha", "en-US",  "Promo"),
    "Cameroon":    ("fr-FR-adélie",   "fr-FR",  "Narration"),
    "Senegal":     ("fr-FR-adélie",   "fr-FR",  "Narration"),
    "Congo (DRC)": ("fr-FR-adélie",   "fr-FR",  "Narration"),
    "Mozambique":  ("pt-BR-isadora",  "pt-BR",  "Conversational"),
    "Bangladesh":  ("bn-IN-anwesha",  "bn-IN",  "Conversational"),
    "Pakistan":    ("en-US-samantha", "en-US",  "Promo"),
    "Indonesia":   ("en-US-zion",     "id-ID",  "Conversational"),
    "Philippines": ("en-IN-arohi",    "en-IN",  "Promo"),
}

# Pronunciation dictionary for Murf -- only technical acronyms
MURF_PRONUNCIATION: dict[str, dict[str, str]] = {
    "IVR":  {"type": "SAY_AS", "pronunciation": "I V R"},
    "OBD":  {"type": "SAY_AS", "pronunciation": "O B D"},
    "CLI":  {"type": "SAY_AS", "pronunciation": "C L I"},
    "BNG":  {"type": "SAY_AS", "pronunciation": "B N G"},
    "DTMF": {"type": "SAY_AS", "pronunciation": "D T M F"},
    "USSD": {"type": "SAY_AS", "pronunciation": "U S S D"},
    "SMS":  {"type": "SAY_AS", "pronunciation": "S M S"},
    "CTA":  {"type": "SAY_AS", "pronunciation": "C T A"},
}


def _pick_murf_voice(country: str, language: str | None) -> tuple[str, str, str]:
    """Pick the best Murf voice_id, locale, and style.

    Returns (voice_id, multiNativeLocale, style).
    """
    if language:
        lang_lower = language.lower().strip()
        if lang_lower in MURF_VOICE_MAP:
            return MURF_VOICE_MAP[lang_lower]
        for lang_key, voice_info in MURF_VOICE_MAP.items():
            if lang_key in lang_lower:
                return voice_info

    if country in MURF_COUNTRY_VOICE:
        return MURF_COUNTRY_VOICE[country]

    return ("en-IN-arohi", "en-IN", "Promo")


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


def _mix_voice_with_music(voice_path: Path, output_path: Path, bgm_style: str = "upbeat") -> None:
    """Mix voice with background music, matching reference quality."""
    try:
        from pydub import AudioSegment

        voice = AudioSegment.from_mp3(str(voice_path))

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
        logger.info(f"Mixed with music: {output_path.name} ({output_path.stat().st_size / 1024:.1f} KB)")
    except Exception as e:
        logger.warning(f"Music mixing failed ({e}), using voice-only")
        if voice_path != output_path:
            import shutil
            shutil.copy2(voice_path, output_path)


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
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{ELEVENLABS_BASE_URL}/v1/user/subscription",
                    headers={"xi-api-key": ELEVENLABS_API_KEY},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    remaining = data.get("character_count", 0)
                    limit = data.get("character_limit", 0)
                    available = limit - remaining
                    logger.info(f"[{self.name}] ElevenLabs quota: {available} chars remaining")
                    return available > 500
        except Exception as e:
            logger.warning(f"[{self.name}] Could not check ElevenLabs quota: {e}")
        return False

    async def _generate_edge_tts(
        self,
        text: str,
        voice: str,
        output_path: Path,
        section_type: str = "main",
        skip_bgm: bool = False,
        bgm_style: str = "upbeat",
    ) -> dict[str, Any]:
        """Generate audio using edge-tts with prosody and optional background music."""
        clean_text = _clean_text_for_tts(text)
        logger.info(f"[{self.name}] TTS input (first 120 chars): {clean_text[:120]!r}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        prosody = SECTION_PROSODY.get(section_type, {"rate": "+0%", "pitch": "+0Hz"})

        if skip_bgm:
            communicate = edge_tts.Communicate(
                clean_text, voice, rate=prosody["rate"], pitch=prosody["pitch"]
            )
            await communicate.save(str(output_path))
        else:
            voice_only_path = output_path.with_suffix(".voice.mp3")
            communicate = edge_tts.Communicate(
                clean_text, voice, rate=prosody["rate"], pitch=prosody["pitch"]
            )
            await communicate.save(str(voice_only_path))
            _mix_voice_with_music(voice_only_path, output_path, bgm_style=bgm_style)
            voice_only_path.unlink(missing_ok=True)

        file_size = output_path.stat().st_size
        logger.info(
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

    async def _generate_murf_tts(
        self,
        text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        style: str = "Conversational",
        skip_bgm: bool = False,
        bgm_style: str = "upbeat",
    ) -> dict[str, Any]:
        """Generate audio using Murf AI API with pronunciation dictionary."""
        clean_text = _clean_text_for_tts(text, apply_pronunciation_hacks=False)

        logger.info(f"[{self.name}] Murf TTS input (first 150 chars): {clean_text[:150]!r}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Murf supports inline pause tags: [pause 1s]
        clean_text = re.sub(r"\.{3,}", " [pause 0.5s] ", clean_text)

        payload: dict[str, Any] = {
            "text": clean_text,
            "voiceId": voice_id,
            "modelVersion": "GEN2",
            "format": "MP3",
            "sampleRate": 44100,
            "channelType": "STEREO",
            "variation": 2,
            "pronunciationDictionary": MURF_PRONUNCIATION,
        }
        if locale:
            payload["multiNativeLocale"] = locale
        if style:
            payload["style"] = style

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.murf.ai/v1/speech/generate",
                json=payload,
                headers={
                    "api-key": MURF_API_KEY,
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
            if response.status_code != 200:
                logger.error(f"[{self.name}] Murf error {response.status_code}: {response.text[:300]}")
                response.raise_for_status()

            data = response.json()
            audio_url = data.get("audioFile", "")
            audio_length = data.get("audioLengthInSeconds", 0)
            remaining = data.get("remainingCharacterCount", -1)

            logger.info(
                f"[{self.name}] Murf response: {audio_length:.1f}s, "
                f"remaining chars: {remaining}"
            )

            if not audio_url:
                raise ValueError("Murf returned no audioFile URL")

            # Download the audio file
            audio_response = await client.get(audio_url, timeout=30.0)
            audio_response.raise_for_status()

            if skip_bgm:
                output_path.write_bytes(audio_response.content)
            else:
                voice_only_path = output_path.with_suffix(".voice.mp3")
                voice_only_path.write_bytes(audio_response.content)
                _mix_voice_with_music(voice_only_path, output_path, bgm_style=bgm_style)
                voice_only_path.unlink(missing_ok=True)

        file_size = output_path.stat().st_size
        logger.info(
            f"[{self.name}] Murf: {output_path.name} "
            f"({file_size / 1024:.1f} KB, voice={voice_id}, locale={locale})"
        )

        return {
            "file_path": str(output_path),
            "file_name": output_path.name,
            "file_size_bytes": file_size,
            "voice_id": voice_id,
            "model": "murf-gen2",
            "has_background_music": not skip_bgm,
        }

    async def _generate_elevenlabs(
        self,
        text: str,
        voice_id: str,
        voice_settings: dict[str, Any],
        output_path: Path,
        model_id: str | None = None,
        skip_bgm: bool = False,
        bgm_style: str = "upbeat",
    ) -> dict[str, Any]:
        effective_model = model_id or ELEVENLABS_TTS_MODEL
        url = f"{ELEVENLABS_BASE_URL}/v1/text-to-speech/{voice_id}"
        clean_text = _clean_text_for_tts(text)

        payload: dict[str, Any] = {
            "text": clean_text,
            "model_id": effective_model,
            "voice_settings": {
                "stability": voice_settings.get("stability", 0.5),
                "similarity_boost": voice_settings.get("similarity_boost", 0.75),
                "use_speaker_boost": True,
            },
        }
        style_val = voice_settings.get("style")
        if style_val is not None:
            payload["voice_settings"]["style"] = float(style_val)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                params={"output_format": ELEVENLABS_OUTPUT_FORMAT},
                timeout=60.0,
            )
            if response.status_code != 200:
                logger.error(f"[{self.name}] ElevenLabs error {response.status_code}: {response.text[:300]}")
                response.raise_for_status()

            output_path.parent.mkdir(parents=True, exist_ok=True)

            if skip_bgm:
                output_path.write_bytes(response.content)
            else:
                voice_only_path = output_path.with_suffix(".voice.mp3")
                voice_only_path.write_bytes(response.content)
                _mix_voice_with_music(voice_only_path, output_path, bgm_style=bgm_style)
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
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{ELEVENLABS_BASE_URL}/v2/voices",
                    headers={"xi-api-key": ELEVENLABS_API_KEY},
                    params={"page_size": 100},
                    timeout=15.0,
                )
                response.raise_for_status()
                voices = response.json().get("voices", [])
                valid_ids = {v["voice_id"] for v in voices}

                if voice_id in valid_ids:
                    return voice_id

                logger.warning(f"[{self.name}] Voice '{voice_id}' not found, falling back")
                if voices:
                    return voices[0]["voice_id"]
        except Exception as e:
            logger.error(f"[{self.name}] Voice validation failed: {e}")
        return voice_id

    async def _resolve_engine(
        self,
        voice_selection: dict[str, Any],
        country: str,
        language: str | None,
        tts_engine_override: str | None,
    ) -> dict[str, Any]:
        """Resolve TTS engine, voice pools, and per-engine config.

        Returns a dict with keys: tts_engine, voice_settings, voice_name,
        el_voice_id, el_model_id, edge_voice, murf_voice_id, murf_locale,
        murf_style, voice_pool (list of 3 voice descriptors).
        """
        voice_settings = voice_selection.get("voice_settings", {})
        voice_name = voice_selection.get("selected_voice", {}).get("name", "Unknown")

        tts_engine = "edge-tts"
        el_voice_id = ""
        el_model_id = ELEVENLABS_TTS_MODEL
        edge_voice = ""
        murf_voice_id = ""
        murf_locale = ""
        murf_style = ""

        if tts_engine_override in ("murf", "elevenlabs", "edge-tts"):
            tts_engine = tts_engine_override
        elif MURF_API_KEY:
            tts_engine = "murf"
        elif self._has_elevenlabs_credits():
            has_quota = await self._check_elevenlabs_quota()
            if has_quota:
                tts_engine = "elevenlabs"

        if tts_engine == "murf":
            if not MURF_API_KEY:
                logger.warning(f"[{self.name}] Murf requested but no API key; falling back")
                tts_engine = "edge-tts"
            else:
                murf_voice_id, murf_locale, murf_style = _pick_murf_voice(country, language)
                logger.info(
                    f"[{self.name}] Using Murf AI: voice={murf_voice_id}, "
                    f"locale={murf_locale}, style={murf_style}"
                )

        if tts_engine == "elevenlabs":
            if not self._has_elevenlabs_credits():
                logger.warning(f"[{self.name}] ElevenLabs requested but no key; falling back")
                tts_engine = "edge-tts"
            else:
                el_voice_id = voice_selection["selected_voice"]["voice_id"]
                api_params = voice_selection.get("elevenlabs_api_params", {})
                el_model_id = api_params.get("model_id", ELEVENLABS_TTS_MODEL)
                if el_model_id == "eleven_v3":
                    el_model_id = ELEVENLABS_TTS_MODEL
                el_voice_id = await self._validate_voice_id(el_voice_id)
                logger.info(f"[{self.name}] Using ElevenLabs: voice={voice_name}, model={el_model_id}")

        if tts_engine == "edge-tts":
            edge_voice = _pick_edge_voice(country, language)
            logger.info(f"[{self.name}] Using edge-tts (FREE): voice={edge_voice}")

        # Build voice pool (3 voices)
        voice_pool: list[dict[str, str]] = []
        if tts_engine == "murf":
            for vid, loc, sty, lbl in _get_murf_voice_pool(country, language):
                voice_pool.append({"murf_voice_id": vid, "murf_locale": loc, "murf_style": sty, "voice_label": lbl})
        elif tts_engine == "edge-tts":
            for eid, lbl in _get_edge_voice_pool(country, language):
                voice_pool.append({"edge_voice": eid, "voice_label": lbl})
        else:
            alt_voices = voice_selection.get("alternative_voices", [])
            el_pool = [(el_voice_id, voice_name)]
            for av in alt_voices[:2]:
                el_pool.append((av.get("voice_id", el_voice_id), av.get("name", "Alt")))
            while len(el_pool) < 3:
                el_pool.append(el_pool[0])
            for eid, lbl in el_pool:
                voice_pool.append({"el_voice_id": eid, "voice_label": lbl})

        return {
            "tts_engine": tts_engine,
            "voice_settings": voice_settings,
            "voice_name": voice_name,
            "el_voice_id": el_voice_id,
            "el_model_id": el_model_id,
            "edge_voice": edge_voice,
            "murf_voice_id": murf_voice_id,
            "murf_locale": murf_locale,
            "murf_style": murf_style,
            "voice_pool": voice_pool,
        }

    async def _run_tts_jobs(
        self,
        jobs: list[dict[str, Any]],
        engine_ctx: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute a list of TTS jobs with concurrency limiting."""
        tts_engine = engine_ctx["tts_engine"]
        voice_settings = engine_ctx["voice_settings"]
        el_voice_id = engine_ctx["el_voice_id"]
        el_model_id = engine_ctx["el_model_id"]
        edge_voice = engine_ctx["edge_voice"]

        async def _tts_job(job: dict[str, Any]) -> dict[str, Any]:
            skip_bgm = job.get("skip_bgm", False)
            bgm_style = job.get("bgm_style", "upbeat")
            try:
                if tts_engine == "murf":
                    result = await self._generate_murf_tts(
                        text=job["text"],
                        voice_id=job["murf_voice_id"],
                        locale=job["murf_locale"],
                        output_path=job["path"],
                        style=job["murf_style"],
                        skip_bgm=skip_bgm,
                        bgm_style=bgm_style,
                    )
                elif tts_engine == "elevenlabs":
                    result = await self._generate_elevenlabs(
                        text=job["text"],
                        voice_id=job.get("el_voice_id", el_voice_id),
                        voice_settings=voice_settings,
                        output_path=job["path"],
                        model_id=el_model_id,
                        skip_bgm=skip_bgm,
                        bgm_style=bgm_style,
                    )
                else:
                    result = await self._generate_edge_tts(
                        text=job["text"],
                        voice=job.get("edge_voice", edge_voice),
                        output_path=job["path"],
                        section_type=job["type"],
                        skip_bgm=skip_bgm,
                        bgm_style=bgm_style,
                    )
                result["variant_id"] = job["variant_id"]
                result["type"] = job["type"]
                result["theme"] = job.get("theme", "")
                result["voice_index"] = job.get("voice_index", 1)
                result["voice_label"] = job.get("voice_label", "Voice 1")
                
                # UPLOAD TO SUPABASE If Available
                if supabase:
                    try:
                        file_path = Path(result["file_path"])
                        bucket_name = "audio-files"
                        # Create unique path in bucket like session_id/filename
                        session_id = str(job["path"].parent.name)
                        storage_path = f"{session_id}/{file_path.name}"
                        
                        # Upload file
                        with open(file_path, "rb") as f:
                            supabase.storage.from_(bucket_name).upload(
                                path=storage_path,
                                file=f,
                                file_options={"content-type": "audio/mpeg"}
                            )
                        
                        # Get public url
                        public_url = supabase.storage.from_(bucket_name).get_public_url(storage_path)
                        result["public_url"] = public_url
                        logger.info(f"[{self.name}] Uploaded {file_path.name} to Supabase: {public_url}")
                    except Exception as upload_err:
                        logger.error(f"[{self.name}] Supabase upload failed for {job['path'].name}: {upload_err}")
                        
                return result
            except Exception as e:
                logger.error(f"[{self.name}] Failed {job['type']} v{job['variant_id']} voice{job.get('voice_index', 1)}: {e}")
                return {
                    "variant_id": job["variant_id"],
                    "type": job["type"],
                    "theme": job.get("theme", ""),
                    "voice_index": job.get("voice_index", 1),
                    "voice_label": job.get("voice_label", "Voice 1"),
                    "error": str(e),
                }

        semaphore = asyncio.Semaphore(5)

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
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate hook-only audio previews with 3 voices per variant (no BGM)."""
        session_id = session_id or str(uuid.uuid4())[:8]
        session_dir = OUTPUTS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        engine_ctx = await self._resolve_engine(voice_selection, country, language, tts_engine_override)
        tts_engine = engine_ctx["tts_engine"]
        voice_pool = engine_ctx["voice_pool"]
        script_list = scripts.get("scripts", [])

        jobs: list[dict[str, Any]] = []
        for script in script_list:
            variant_id = script.get("variant_id", 0)
            theme = script.get("theme", "unknown")
            hook_text = script.get("hook", "")
            if not hook_text or not hook_text.strip():
                hook_text = script.get("full_script", "")
                if hook_text:
                    hook_text = hook_text[:200]

            if not hook_text or not hook_text.strip():
                continue

            for voice_idx in range(3):
                job: dict[str, Any] = {
                    "text": hook_text,
                    "path": session_dir / f"variant_{variant_id}_voice{voice_idx + 1}_hook_preview.mp3",
                    "variant_id": variant_id,
                    "type": "hook_preview",
                    "theme": theme,
                    "voice_index": voice_idx + 1,
                    "skip_bgm": False,
                }
                job.update(voice_pool[voice_idx])
                jobs.append(job)

        logger.info(f"[{self.name}] Generating {len(jobs)} hook previews via {tts_engine}")
        results = await self._run_tts_jobs(jobs, engine_ctx)

        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]

        # Auto-fallback: if ALL jobs failed, retry with next available engine
        if len(successful) == 0 and len(failed) > 0:
            fallback_order = ["murf", "edge-tts"]
            for fb_engine in fallback_order:
                if fb_engine == tts_engine:
                    continue
                if fb_engine == "murf" and not MURF_API_KEY:
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
                        hook_text = (script.get("full_script", "") or "")[:200]
                    if not hook_text.strip():
                        continue
                    for vi in range(min(3, len(voice_pool))):
                        rj: dict[str, Any] = {
                            "text": hook_text,
                            "path": session_dir / f"variant_{variant_id}_voice{vi + 1}_hook_preview.mp3",
                            "variant_id": variant_id,
                            "type": "hook_preview",
                            "theme": theme,
                            "voice_index": vi + 1,
                            "skip_bgm": False,
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
                {"voice_index": i + 1, "voice_label": v.get("voice_label", f"Voice {i + 1}")}
                for i, v in enumerate(voice_pool)
            ],
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
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate full audio for all sections using the user-chosen voice per variant.

        Args:
            voice_choices: mapping of variant_id -> voice_index (1-based).
            bgm_style: one of "upbeat", "calm", "corporate".
        """
        session_dir = OUTPUTS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        engine_ctx = await self._resolve_engine(voice_selection, country, language, tts_engine_override)
        tts_engine = engine_ctx["tts_engine"]
        voice_pool = engine_ctx["voice_pool"]
        script_list = scripts.get("scripts", [])

        ALL_SECTIONS = [
            ("full_script", "main"),
            ("fallback_1", "fallback1"),
            ("fallback_2", "fallback2"),
            ("polite_closure", "closure"),
        ]

        jobs: list[dict[str, Any]] = []
        for script in script_list:
            variant_id = script.get("variant_id", 0)
            theme = script.get("theme", "unknown")
            chosen_idx = voice_choices.get(variant_id, 1) - 1
            chosen_idx = max(0, min(chosen_idx, len(voice_pool) - 1))

            for field, audio_type in ALL_SECTIONS:
                text = script.get(field, "")
                if not text or not text.strip():
                    continue
                job: dict[str, Any] = {
                    "text": text,
                    "path": session_dir / f"variant_{variant_id}_voice{chosen_idx + 1}_{audio_type}.mp3",
                    "variant_id": variant_id,
                    "type": audio_type,
                    "theme": theme,
                    "voice_index": chosen_idx + 1,
                    "skip_bgm": False,
                    "bgm_style": bgm_style,
                }
                job.update(voice_pool[chosen_idx])
                jobs.append(job)

        logger.info(
            f"[{self.name}] Generating {len(jobs)} final audio files via {tts_engine} "
            f"(bgm={bgm_style})"
        )
        results = await self._run_tts_jobs(jobs, engine_ctx)

        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]

        # Auto-fallback: if ALL jobs failed, retry with next available engine
        if len(successful) == 0 and len(failed) > 0:
            for fb_engine in ["murf", "edge-tts"]:
                if fb_engine == tts_engine:
                    continue
                if fb_engine == "murf" and not MURF_API_KEY:
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
                retry_jobs: list[dict[str, Any]] = []
                for script in script_list:
                    variant_id = script.get("variant_id", 0)
                    theme = script.get("theme", "unknown")
                    chosen_idx = max(0, min(voice_choices.get(variant_id, 1) - 1, len(voice_pool) - 1))
                    for field, audio_type in ALL_SECTIONS:
                        text = script.get(field, "")
                        if not text or not text.strip():
                            continue
                        rj: dict[str, Any] = {
                            "text": text,
                            "path": session_dir / f"variant_{variant_id}_voice{chosen_idx + 1}_{audio_type}.mp3",
                            "variant_id": variant_id,
                            "type": audio_type,
                            "theme": theme,
                            "voice_index": chosen_idx + 1,
                            "skip_bgm": False,
                            "bgm_style": bgm_style,
                        }
                        rj.update(voice_pool[chosen_idx])
                        retry_jobs.append(rj)
                results = await self._run_tts_jobs(retry_jobs, engine_ctx)
                successful = [r for r in results if "error" not in r]
                failed = [r for r in results if "error" in r]
                if len(successful) > 0:
                    break

        voice_settings = engine_ctx["voice_settings"]
        voice_id_used = (
            engine_ctx["murf_voice_id"] if tts_engine == "murf"
            else engine_ctx["el_voice_id"] if tts_engine == "elevenlabs"
            else engine_ctx["edge_voice"]
        )
        voice_name_used = (
            f"{engine_ctx['murf_voice_id']} ({engine_ctx['murf_locale']})" if tts_engine == "murf"
            else engine_ctx["voice_name"] if tts_engine == "elevenlabs"
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
            engine_ctx["murf_voice_id"] if tts_engine == "murf"
            else engine_ctx["el_voice_id"] if tts_engine == "elevenlabs"
            else engine_ctx["edge_voice"]
        )
        voice_name_used = (
            f"{engine_ctx['murf_voice_id']} ({engine_ctx['murf_locale']})" if tts_engine == "murf"
            else voice_name if tts_engine == "elevenlabs"
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
