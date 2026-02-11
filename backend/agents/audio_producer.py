"""Agent 6: Audio Producer -- generates audio files via ElevenLabs TTS API."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

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


class AudioProducerAgent(BaseAgent):
    """Generates audio files from scripts using ElevenLabs TTS API."""

    name = "AudioProducer"
    description = "Produces final audio recordings via ElevenLabs V3 TTS"

    async def _generate_audio(
        self,
        text: str,
        voice_id: str,
        voice_settings: dict[str, Any],
        output_path: Path,
    ) -> dict[str, Any]:
        """Call ElevenLabs TTS API to generate a single audio file.

        Args:
            text: Script text with V3 audio tags.
            voice_id: ElevenLabs voice ID.
            voice_settings: Voice configuration parameters.
            output_path: Where to save the MP3 file.

        Returns:
            Metadata about the generated audio.
        """
        url = f"{ELEVENLABS_BASE_URL}/v1/text-to-speech/{voice_id}"

        payload = {
            "text": text,
            "model_id": ELEVENLABS_TTS_MODEL,
            "voice_settings": {
                "stability": voice_settings.get("stability", 0.4),
                "similarity_boost": voice_settings.get("similarity_boost", 0.75),
                "style": voice_settings.get("style", 0.6),
                "use_speaker_boost": True,
            },
        }

        # Add speed if specified and supported
        speed = voice_settings.get("speed")
        if speed and speed != 1.0:
            payload["voice_settings"]["speed"] = speed

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        params = {"output_format": ELEVENLABS_OUTPUT_FORMAT}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()

            # Save the audio file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.content)

        file_size = output_path.stat().st_size
        logger.info(
            f"[{self.name}] Generated audio: {output_path.name} "
            f"({file_size / 1024:.1f} KB)"
        )

        return {
            "file_path": str(output_path),
            "file_name": output_path.name,
            "file_size_bytes": file_size,
            "voice_id": voice_id,
            "model": ELEVENLABS_TTS_MODEL,
        }

    async def run(
        self,
        scripts: dict[str, Any],
        voice_selection: dict[str, Any],
        session_id: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate audio files for all script variants.

        Args:
            scripts: Final approved scripts with V3 audio tags.
            voice_selection: Voice selection from Agent 5.
            session_id: Optional session ID for organizing output files.

        Returns:
            Audio generation results with file paths and metadata.
        """
        voice_id = voice_selection["selected_voice"]["voice_id"]
        voice_settings = voice_selection["voice_settings"]
        voice_name = voice_selection["selected_voice"].get("name", "Unknown")

        session_id = session_id or str(uuid.uuid4())[:8]
        session_dir = OUTPUTS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"[{self.name}] Generating audio for {len(scripts.get('scripts', []))} "
            f"variants using voice '{voice_name}' ({voice_id})"
        )

        audio_results = []
        script_list = scripts.get("scripts", [])

        for script in script_list:
            variant_id = script.get("variant_id", 0)
            theme = script.get("theme", "unknown")

            # Generate main script audio
            main_text = script.get("full_script", "")
            if main_text:
                main_path = session_dir / f"variant_{variant_id}_main.mp3"
                try:
                    main_result = await self._generate_audio(
                        text=main_text,
                        voice_id=voice_id,
                        voice_settings=voice_settings,
                        output_path=main_path,
                    )
                    main_result["variant_id"] = variant_id
                    main_result["type"] = "main"
                    main_result["theme"] = theme
                    audio_results.append(main_result)
                except Exception as e:
                    logger.error(
                        f"[{self.name}] Failed to generate main audio for "
                        f"variant {variant_id}: {e}"
                    )
                    audio_results.append({
                        "variant_id": variant_id,
                        "type": "main",
                        "theme": theme,
                        "error": str(e),
                    })

            # Generate fallback 1 audio
            fb1_text = script.get("fallback_1", "")
            if fb1_text:
                fb1_path = session_dir / f"variant_{variant_id}_fallback1.mp3"
                try:
                    fb1_result = await self._generate_audio(
                        text=fb1_text,
                        voice_id=voice_id,
                        voice_settings=voice_settings,
                        output_path=fb1_path,
                    )
                    fb1_result["variant_id"] = variant_id
                    fb1_result["type"] = "fallback_1"
                    audio_results.append(fb1_result)
                except Exception as e:
                    logger.error(f"[{self.name}] Failed fallback_1 variant {variant_id}: {e}")

            # Generate fallback 2 audio
            fb2_text = script.get("fallback_2", "")
            if fb2_text:
                fb2_path = session_dir / f"variant_{variant_id}_fallback2.mp3"
                try:
                    fb2_result = await self._generate_audio(
                        text=fb2_text,
                        voice_id=voice_id,
                        voice_settings=voice_settings,
                        output_path=fb2_path,
                    )
                    fb2_result["variant_id"] = variant_id
                    fb2_result["type"] = "fallback_2"
                    audio_results.append(fb2_result)
                except Exception as e:
                    logger.error(f"[{self.name}] Failed fallback_2 variant {variant_id}: {e}")

            # Generate polite closure audio
            closure_text = script.get("polite_closure", "")
            if closure_text:
                closure_path = session_dir / f"variant_{variant_id}_closure.mp3"
                try:
                    closure_result = await self._generate_audio(
                        text=closure_text,
                        voice_id=voice_id,
                        voice_settings=voice_settings,
                        output_path=closure_path,
                    )
                    closure_result["variant_id"] = variant_id
                    closure_result["type"] = "polite_closure"
                    audio_results.append(closure_result)
                except Exception as e:
                    logger.error(f"[{self.name}] Failed closure variant {variant_id}: {e}")

        successful = [r for r in audio_results if "error" not in r]
        failed = [r for r in audio_results if "error" in r]

        logger.info(
            f"[{self.name}] Audio generation complete: "
            f"{len(successful)} successful, {len(failed)} failed"
        )

        return {
            "session_id": session_id,
            "session_dir": str(session_dir),
            "voice_used": {
                "voice_id": voice_id,
                "name": voice_name,
                "settings": voice_settings,
            },
            "audio_files": audio_results,
            "summary": {
                "total_generated": len(successful),
                "total_failed": len(failed),
                "variants_count": len(script_list),
            },
        }
