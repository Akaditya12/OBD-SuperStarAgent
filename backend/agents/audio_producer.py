"""Agent 6: Audio Producer -- generates broadcast-quality OBD audio.

Produces professional audio with:
- edge-tts (free) or ElevenLabs (premium) for voice
- Upbeat synthesized background music
- Stereo 320kbps output matching industry standards
- Natural speech patterns from audio tag conversion
"""

from __future__ import annotations

import asyncio
import io
import logging
import math
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
)

from .base import BaseAgent

logger = logging.getLogger(__name__)

_AUDIO_TAGS = re.compile(
    r"\[(excited|curious|whispers|laughs|cheerfully|mischievously|playfully|"
    r"sigh|gasps|lightlaugh|friendly|warm|serious|dramatic|softly|"
    r"short\s*pause|pause)\]",
    re.IGNORECASE,
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

# Prosody per section type -- clear and crisp, not rushed
SECTION_PROSODY: dict[str, dict[str, str]] = {
    "main":      {"rate": "+0%",   "pitch": "+1Hz"},
    "fallback1": {"rate": "+3%",   "pitch": "+2Hz"},
    "fallback2": {"rate": "+0%",   "pitch": "+0Hz"},
    "closure":   {"rate": "-5%",   "pitch": "-1Hz"},
}


def _clean_text_for_tts(text: str) -> str:
    """Convert audio tags to natural speech sounds for TTS."""
    text = re.sub(r"\[laughs?\]", "ha ha! ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[lightlaugh\]", "heh, ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[sigh\]", "hmm... ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[gasps?\]", "oh! ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[whispers?\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[short\s*pause\]", "... ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[pause\]", "...... ", text, flags=re.IGNORECASE)
    text = _AUDIO_TAGS.sub("", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def _pick_edge_voice(country: str, language: str | None) -> str:
    if language:
        lang_lower = language.lower()
        for locale, voice in EDGE_VOICE_MAP.items():
            if lang_lower in locale.lower() or locale.lower().startswith(lang_lower[:2]):
                return voice
    locale = COUNTRY_LOCALE.get(country, "en-US")
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


def _mix_voice_with_music(voice_path: Path, output_path: Path) -> None:
    """Mix voice with upbeat background music, matching reference quality."""
    try:
        from pydub import AudioSegment

        voice = AudioSegment.from_mp3(str(voice_path))

        # Music: 1s intro before voice, continues through, 0.5s outro
        music_duration = len(voice) + 2500
        music_wav = _generate_upbeat_music(music_duration)
        music = AudioSegment.from_wav(io.BytesIO(music_wav))

        # Music level: -18dB below voice (subtle, professional background)
        music = music - 18

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
    ) -> dict[str, Any]:
        """Generate audio using edge-tts with prosody and background music."""
        clean_text = _clean_text_for_tts(text)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        prosody = SECTION_PROSODY.get(section_type, {"rate": "+0%", "pitch": "+0Hz"})

        # Generate voice-only first
        voice_only_path = output_path.with_suffix(".voice.mp3")
        communicate = edge_tts.Communicate(
            clean_text, voice, rate=prosody["rate"], pitch=prosody["pitch"]
        )
        await communicate.save(str(voice_only_path))

        # Mix with background music for all sections
        _mix_voice_with_music(voice_only_path, output_path)
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
            "has_background_music": True,
        }

    async def _generate_elevenlabs(
        self,
        text: str,
        voice_id: str,
        voice_settings: dict[str, Any],
        output_path: Path,
        model_id: str | None = None,
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
            output_path.write_bytes(response.content)

        file_size = output_path.stat().st_size
        return {
            "file_path": str(output_path),
            "file_name": output_path.name,
            "file_size_bytes": file_size,
            "voice_id": voice_id,
            "model": effective_model,
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

    async def run(
        self,
        scripts: dict[str, Any],
        voice_selection: dict[str, Any],
        session_id: str | None = None,
        country: str = "",
        language: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate broadcast-quality audio for all script variants."""
        voice_settings = voice_selection.get("voice_settings", {})
        voice_name = voice_selection.get("selected_voice", {}).get("name", "Unknown")

        session_id = session_id or str(uuid.uuid4())[:8]
        session_dir = OUTPUTS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Decide TTS engine
        use_elevenlabs = False
        el_voice_id = ""
        el_model_id = ELEVENLABS_TTS_MODEL
        edge_voice = ""

        if self._has_elevenlabs_credits():
            has_quota = await self._check_elevenlabs_quota()
            if has_quota:
                use_elevenlabs = True
                el_voice_id = voice_selection["selected_voice"]["voice_id"]
                api_params = voice_selection.get("elevenlabs_api_params", {})
                el_model_id = api_params.get("model_id", ELEVENLABS_TTS_MODEL)
                if el_model_id == "eleven_v3":
                    el_model_id = ELEVENLABS_TTS_MODEL
                el_voice_id = await self._validate_voice_id(el_voice_id)
                logger.info(f"[{self.name}] Using ElevenLabs: voice={voice_name}, model={el_model_id}")

        if not use_elevenlabs:
            edge_voice = _pick_edge_voice(country, language)
            logger.info(f"[{self.name}] Using edge-tts (FREE): voice={edge_voice}")

        script_list = scripts.get("scripts", [])

        jobs: list[dict[str, Any]] = []
        for script in script_list:
            variant_id = script.get("variant_id", 0)
            theme = script.get("theme", "unknown")

            sections = [
                ("full_script", "main"),
                ("fallback_1", "fallback1"),
                ("fallback_2", "fallback2"),
                ("polite_closure", "closure"),
            ]
            for field, audio_type in sections:
                text = script.get(field, "")
                if text and text.strip():
                    jobs.append({
                        "text": text,
                        "path": session_dir / f"variant_{variant_id}_{audio_type}.mp3",
                        "variant_id": variant_id,
                        "type": audio_type,
                        "theme": theme,
                    })

        engine_label = f"ElevenLabs ({el_model_id})" if use_elevenlabs else "edge-tts"
        logger.info(f"[{self.name}] Generating {len(jobs)} audio files via {engine_label}")

        async def _tts_job(job: dict[str, Any]) -> dict[str, Any]:
            try:
                if use_elevenlabs:
                    result = await self._generate_elevenlabs(
                        text=job["text"],
                        voice_id=el_voice_id,
                        voice_settings=voice_settings,
                        output_path=job["path"],
                        model_id=el_model_id,
                    )
                else:
                    result = await self._generate_edge_tts(
                        text=job["text"],
                        voice=edge_voice,
                        output_path=job["path"],
                        section_type=job["type"],
                    )
                result["variant_id"] = job["variant_id"]
                result["type"] = job["type"]
                result["theme"] = job.get("theme", "")
                return result
            except Exception as e:
                logger.error(f"[{self.name}] Failed {job['type']} v{job['variant_id']}: {e}")
                return {
                    "variant_id": job["variant_id"],
                    "type": job["type"],
                    "theme": job.get("theme", ""),
                    "error": str(e),
                }

        semaphore = asyncio.Semaphore(3)

        async def _limited_tts(job: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                return await _tts_job(job)

        audio_results = list(await asyncio.gather(*[_limited_tts(j) for j in jobs]))

        successful = [r for r in audio_results if "error" not in r]
        failed = [r for r in audio_results if "error" in r]

        logger.info(
            f"[{self.name}] Audio complete: {len(successful)} generated, "
            f"{len(failed)} failed via {engine_label}"
        )

        return {
            "session_id": session_id,
            "session_dir": str(session_dir),
            "tts_engine": "elevenlabs" if use_elevenlabs else "edge-tts",
            "voice_used": {
                "voice_id": el_voice_id if use_elevenlabs else edge_voice,
                "name": voice_name if use_elevenlabs else edge_voice,
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
