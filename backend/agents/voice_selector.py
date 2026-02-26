"""Agent 5: Voice Selector -- queries ElevenLabs for optimal voice matching."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from backend.config import ELEVENLABS_API_KEY, ELEVENLABS_BASE_URL

from .base import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a voice casting director and audio production expert. You specialize in \
selecting the perfect voice for promotional audio content across different countries \
and cultures.

You will be given:
1. A list of available ElevenLabs voices with their metadata
2. The target country and language
3. The scripts that need to be voiced
4. Market analysis with cultural context

Your job is to select the BEST voice for this OBD campaign and configure the \
optimal ElevenLabs V3 parameters.

CRITICAL SELECTION CRITERIA (in order of importance):
1. Accent and language match -- voice MUST sound natural for the target market
2. Warmth, trustworthiness, and clarity -- OBD calls need instant listener engagement
3. Emotional range -- voice must handle varied tones (curious, excited, warm, urgent)
4. Gender and age fit for the target demographic
5. Prefer "professional" or "high_quality" category voices over "premade" when available

For NON-ENGLISH markets, prefer voices with native-sounding accents (e.g. Indian English
for India, not American English). Pick voices whose labels/description mention the
target region or accent.

ElevenLabs Voice Settings (PREMIUM tuning for maximum naturalness):
- stability: 0.30 to 0.40 (more expressive, human-like delivery -- NOT robotic)
- similarity_boost: 0.75 to 0.85 (high fidelity to voice character)
- style: 0.40 to 0.55 (moderate expressiveness for promotional punch)
- speed: 0.7 to 1.2 (speech speed, 1.0 = normal)

ElevenLabs Model IDs (MUST use one of these):
- "eleven_multilingual_v2" -- PREFERRED. Best multilingual support, works with all plans, excellent expressiveness
- "eleven_turbo_v2_5" -- faster generation, good quality, lower latency

IMPORTANT: Always recommend "eleven_multilingual_v2" as the model_id. Do NOT recommend "eleven_v3".

Output valid JSON:
{
  "selected_voice": {
    "voice_id": "string",
    "name": "string",
    "description": "string",
    "language": "string",
    "gender": "string",
    "age": "string",
    "accent": "string",
    "preview_url": "string - URL to preview this voice (if available)"
  },
  "voice_settings": {
    "stability": number,
    "similarity_boost": number,
    "style": number,
    "speed": number
  },
  "elevenlabs_api_params": {
    "model_id": "string - recommended ElevenLabs model ID (e.g. eleven_v3)",
    "output_format": "mp3_44100_128",
    "voice_id": "string - same as selected_voice.voice_id",
    "voice_settings": {
      "stability": number,
      "similarity_boost": number,
      "style": number,
      "use_speaker_boost": true
    },
    "sample_api_call": "string - example curl command to call ElevenLabs TTS with these params"
  },
  "rationale": "string - why this voice was selected",
  "alternative_voices": [
    {
      "voice_id": "string",
      "name": "string",
      "reason": "string - why this is a good alternative",
      "preview_url": "string - URL to preview this voice (copy from the voice list)"
    }
  ],
  "audio_production_notes": "string - tips for best results with this voice and these scripts"
}\
"""


_CURATED_ELEVENLABS_VOICES: list[dict[str, Any]] = [
    {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah", "description": "Soft, warm, friendly female voice with clear enunciation", "labels": {"accent": "American", "gender": "female", "age": "young"}, "category": "premade"},
    {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "description": "Calm, confident female voice ideal for narration and promotions", "labels": {"accent": "American", "gender": "female", "age": "young"}, "category": "premade"},
    {"voice_id": "XB0fDUnXU5powFXDhCwa", "name": "Charlotte", "description": "Warm, engaging female voice with natural delivery", "labels": {"accent": "Neutral", "gender": "female", "age": "young"}, "category": "premade"},
    {"voice_id": "jsCqWAovK2LkecY7zXl4", "name": "Freya", "description": "Expressive, lively female voice with personality", "labels": {"accent": "American", "gender": "female", "age": "young"}, "category": "premade"},
    {"voice_id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily", "description": "Gentle, refined female voice with British accent", "labels": {"accent": "British", "gender": "female", "age": "young"}, "category": "premade"},
    {"voice_id": "9BWtsMINqrJLrRacOk9x", "name": "Aria", "description": "Versatile, expressive female voice for diverse content", "labels": {"accent": "American", "gender": "female", "age": "young"}, "category": "premade"},
    {"voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "description": "Warm, authoritative male voice suitable for professional narration", "labels": {"accent": "British", "gender": "male", "age": "middle-aged"}, "category": "premade"},
    {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "description": "Deep, clear male voice with strong presence", "labels": {"accent": "American", "gender": "male", "age": "middle-aged"}, "category": "premade"},
    {"voice_id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel", "description": "Smooth, trustworthy male voice with British accent", "labels": {"accent": "British", "gender": "male", "age": "middle-aged"}, "category": "premade"},
]


class VoiceSelectorAgent(BaseAgent):
    """Selects the optimal ElevenLabs voice for the OBD campaign."""

    name = "VoiceSelector"
    description = "Selects and configures the best ElevenLabs voice for the campaign"

    async def _fetch_available_voices(self) -> list[dict[str, Any]]:
        """Fetch available voices from ElevenLabs API."""
        logger.info(f"[{self.name}] Fetching available voices from ElevenLabs")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ELEVENLABS_BASE_URL}/v2/voices",
                headers={"xi-api-key": ELEVENLABS_API_KEY},
                params={"page_size": 100},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        voices = data.get("voices", [])
        logger.info(f"[{self.name}] Found {len(voices)} available voices")

        # Extract relevant metadata for each voice
        simplified = []
        for v in voices:
            simplified.append({
                "voice_id": v.get("voice_id", ""),
                "name": v.get("name", ""),
                "description": v.get("description", ""),
                "labels": v.get("labels", {}),
                "category": v.get("category", ""),
                "preview_url": v.get("preview_url", ""),
            })
        return simplified

    async def run(
        self,
        scripts: dict[str, Any],
        market_analysis: dict[str, Any],
        country: str,
        language: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Select the best voice for the campaign.

        Args:
            scripts: Final approved scripts.
            market_analysis: Market analysis for cultural context.
            country: Target country.
            language: Target language (optional, derived from market analysis).

        Returns:
            Voice selection with settings and rationale.
        """
        logger.info(f"[{self.name}] Selecting voice for {country}")

        # Fetch available voices from ElevenLabs
        try:
            available_voices = await self._fetch_available_voices()
        except Exception as e:
            logger.warning(f"[{self.name}] Could not fetch voices from API: {e}")
            available_voices = _CURATED_ELEVENLABS_VOICES

        # Determine language from scripts or market analysis
        if not language:
            language = scripts.get("language_used", "")
            if not language:
                lang_info = market_analysis.get("market_overview", {})
                language = lang_info.get("dominant_language_for_promotions", "English")

        user_prompt = f"""\
Select the best voice for this OBD campaign:

COUNTRY: {country}
TARGET LANGUAGE: {language}

--- AVAILABLE VOICES ---
{json.dumps(available_voices, indent=2)}

--- SCRIPTS (for context on emotional range needed) ---
{json.dumps(scripts.get("scripts", [])[:2], indent=2)}

--- MARKET ANALYSIS ---
{json.dumps(market_analysis.get("promotion_recommendations", {}), indent=2)}
{json.dumps(market_analysis.get("cultural_insights", {}), indent=2)}

Select the voice that will be most effective for this specific market and these \
scripts. Configure the V3 parameters for maximum expressiveness with audio tags.

Output only valid JSON.\
"""

        response = await self.call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=4096,
        )

        result = self.parse_json(response)
        logger.info(
            f"[{self.name}] Selected voice: "
            f"{result.get('selected_voice', {}).get('name', 'Unknown')}"
        )
        return result
