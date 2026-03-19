"""Agent 5: Voice Selector -- queries ElevenLabs for optimal voice matching."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from backend.config import ELEVENLABS_API_KEY, ELEVENLABS_BASE_URL, get_elevenlabs_headers, elevenlabs_401_is_tts_only

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
target region or accent. The eleven_multilingual_v2 model makes ANY voice speak naturally
in the target language, so accent/region fit matters more than language capability.

SOUTH ASIAN MARKET GUIDANCE (India, Bangladesh, Sri Lanka, Nepal, Pakistan):
- For India, prefer British-accented or Neutral-accented voices over American --
  Indian English is closer to British English. Voices with neutral/British accents
  sound more natural when speaking Hindi, Tamil, Bengali, Telugu via multilingual_v2.
- Select voices described as "warm", "approachable", or "natural" -- avoid overly
  deep/dramatic Western voices that sound out of place for Indian telecom promos.
- Recommended voices: Charlotte (Neutral), Lily (British), Dorothy (British),
  Daniel (British), George (British), Alice (British).
- For regional languages (Hindi, Tamil, Telugu, Bengali, Kannada, Malayalam,
  Marathi, Gujarati), eleven_multilingual_v2 is MANDATORY.

AFRICAN MARKET GUIDANCE (critical -- majority of our client base):
- When the campaign language is ENGLISH and the country is in Africa, prefer voices whose
  labels/accent are African, Nigerian, Kenyan, Ethiopian, Ghanaian, or Neutral -- NOT default
  American. British can work for some East African markets but if the brief asks for
  "African accent" or the audience expects local colour, pick library voices tagged African.
  Ethiopia + English: prefer East African / African-accented voices; avoid flat American unless
  the brief requires neutral international English.
- For East/Southern African countries (Kenya, Tanzania, Uganda, Rwanda, Zambia, Zimbabwe,
  Botswana, South Africa) where British is historically common on air, British-accented voices
  remain acceptable -- but still prefer African-tagged voices when available from the voice list.
- For West African countries (Nigeria, Ghana), British or Neutral accents work well.
  Nigerian Pidgin English content works best with warm, expressive voices.
- For Francophone Africa (Cameroon, Senegal, Congo DRC/Republic), select French-capable
  voices when the script is French. The eleven_v3 / multilingual_v2 models handle French with any suitable voice.
- CAMEROON SPECIFIC: Cameroon is bilingual (French + English + Pidgin). If the campaign language is
  English, do NOT default to UK British — Cameroonian English is closer to West African / neutral
  African English. Prefer warm, clear voices with Neutral or African character; British is optional
  only if the brief explicitly asks for British English. If the language is French, use French-capable
  voices (fr-FR or multilingual) and French-appropriate pacing.
- For Swahili-speaking markets, British-accented voices + multilingual_v2 model produce
  excellent Swahili pronunciation.
- For any local African language (Yoruba, Igbo, Hausa, Twi, Zulu, Xhosa, Shona, Luganda,
  Kinyarwanda, Wolof, Lingala, etc.), the eleven_multilingual_v2 model is MANDATORY --
  it handles these languages far better than other models.

ElevenLabs Voice Settings for eleven_v3 (PREMIUM tuning for OBD clarity):
- stability: 0.45 to 0.55 (clear pronunciation, especially for local languages -- avoid too low which causes mumbling)
- similarity_boost: 0.75 to 0.85 (high fidelity to voice character)
- style: 0.25 to 0.40 (moderate expressiveness -- too high causes distortion in local languages)
- speed: 0.95 to 1.05 (natural OBD pace -- customers need to understand every word on a phone call)

ElevenLabs Model IDs (MUST use one of these):
- "eleven_v3" -- PREFERRED. Most advanced model, 70+ languages, highest emotional range and expressiveness.
  Supports ALL African languages (Swahili, Yoruba, Hausa, Somali, Lingala, etc.),
  ALL South Asian languages (Hindi, Tamil, Telugu, Bengali, Kannada, Malayalam, Marathi, Gujarati, Punjabi, etc.),
  Arabic, Portuguese, Spanish, French, Indonesian, Filipino, Malay, and more.
- "eleven_multilingual_v2" -- Fallback. 29 languages, 10K char limit, very stable.

IMPORTANT: Always recommend "eleven_v3" as the model_id for maximum language coverage.

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
      "gender": "string - male or female",
      "accent": "string - accent of this voice (British, American, Neutral, etc.)",
      "reason": "string - SPECIFIC reason: why this voice works for this market, language, and demographic. Include accent match, gender fit, pronunciation quality for the target language. Do NOT give generic reasons."
    }
  ],
  "audio_production_notes": "string - specific tips for this market: pronunciation pitfalls, pacing for this language, emotional tone that resonates locally"
}

CRITICAL RULES FOR ALTERNATIVES:
- Select alternatives that are DIFFERENT from the primary voice: different name, different accent, different character.
- Do NOT always pick the same voices (Lily, Aria, Daniel, Eric). ElevenLabs has hundreds of voices -- explore the full list provided.
- Prefer voices you have NOT used in recent sessions. If you see professional/high_quality/cloned voices in the list, prioritize those.
- Each alternative MUST have a specific, market-relevant reason -- NOT generic "good quality" text.
- One alternative MUST be male if the primary is female (and vice versa) for gender diversity.
- For local languages, explain WHY this voice handles pronunciation well for the specific language.\
"""


_CURATED_ELEVENLABS_VOICES: list[dict[str, Any]] = [
    # Female voices -- diverse accents for regional targeting
    {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah", "description": "Soft, warm, friendly. Clear enunciation, natural for Western markets.", "labels": {"accent": "American", "gender": "female", "age": "young"}, "category": "premade", "best_for_regions": ["americas", "europe", "general"]},
    {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "description": "Calm, confident. Ideal for narration and promotions.", "labels": {"accent": "American", "gender": "female", "age": "young"}, "category": "premade", "best_for_regions": ["americas", "general"]},
    {"voice_id": "XB0fDUnXU5powFXDhCwa", "name": "Charlotte", "description": "Warm, neutral accent. Adapts naturally to Indian English, African English, and local languages.", "labels": {"accent": "Neutral", "gender": "female", "age": "young"}, "category": "premade", "best_for_regions": ["south_asia", "middle_east", "general"]},
    {"voice_id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily", "description": "Gentle, refined British accent. Natural for East/Southern African and South Asian markets.", "labels": {"accent": "British", "gender": "female", "age": "young"}, "category": "premade", "best_for_regions": ["east_africa", "southern_africa", "south_asia"]},
    {"voice_id": "9BWtsMINqrJLrRacOk9x", "name": "Aria", "description": "Versatile, expressive. Adapts well to Hindi, Swahili, Yoruba via eleven_v3.", "labels": {"accent": "American", "gender": "female", "age": "young"}, "category": "premade", "best_for_regions": ["general", "south_asia", "west_africa"]},
    {"voice_id": "ThT5KcBeYPX3keUQqHPh", "name": "Dorothy", "description": "Clear, pleasant British accent. Warm tone for African and South Asian markets.", "labels": {"accent": "British", "gender": "female", "age": "young"}, "category": "premade", "best_for_regions": ["east_africa", "west_africa", "south_asia"]},
    {"voice_id": "Xb7hH8MSUJpSbSDYk0k2", "name": "Alice", "description": "Natural, approachable British voice. Great for Swahili, Hindi, Tamil, Bengali, Arabic.", "labels": {"accent": "British", "gender": "female", "age": "middle-aged"}, "category": "premade", "best_for_regions": ["east_africa", "south_asia", "middle_east"]},
    {"voice_id": "jsCqWAovK2LkecY7zXl4", "name": "Freya", "description": "Expressive, lively with personality. Good for energetic promos.", "labels": {"accent": "American", "gender": "female", "age": "young"}, "category": "premade", "best_for_regions": ["americas", "europe"]},
    {"voice_id": "cgSgspJ2msm6clMCkdW9", "name": "Jessica", "description": "Smooth, professional female voice. Clear and engaging for business promos.", "labels": {"accent": "American", "gender": "female", "age": "young"}, "category": "premade", "best_for_regions": ["americas", "latam", "general"]},
    {"voice_id": "jBpfuIE2acCO8z3wKNLl", "name": "Gigi", "description": "Bright, youthful female voice. Cheerful tone for mobile/telecom promotions.", "labels": {"accent": "American", "gender": "female", "age": "young"}, "category": "premade", "best_for_regions": ["apac", "latam", "general"]},
    # Male voices -- diverse accents for regional targeting
    {"voice_id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel", "description": "Smooth, trustworthy British accent. Excellent for East/Southern African and South Asian campaigns.", "labels": {"accent": "British", "gender": "male", "age": "middle-aged"}, "category": "premade", "best_for_regions": ["east_africa", "southern_africa", "south_asia"]},
    {"voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "description": "Warm, authoritative British male. Professional narration quality for African and Indian English.", "labels": {"accent": "British", "gender": "male", "age": "middle-aged"}, "category": "premade", "best_for_regions": ["east_africa", "west_africa", "south_asia"]},
    {"voice_id": "cjVigY5qzO86Huf0OWal", "name": "Eric", "description": "Friendly, approachable. Natural delivery for telecom promotions across emerging markets.", "labels": {"accent": "American", "gender": "male", "age": "middle-aged"}, "category": "premade", "best_for_regions": ["general", "south_asia", "west_africa"]},
    {"voice_id": "TX3LPaxmHKxFdv7VOQHJ", "name": "Liam", "description": "Confident, clear articulation. Works well for Hindi, Swahili, Arabic, Portuguese, Spanish.", "labels": {"accent": "American", "gender": "male", "age": "young"}, "category": "premade", "best_for_regions": ["general", "middle_east", "latam"]},
    {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "description": "Deep, clear, authoritative presence. Professional telecom voice.", "labels": {"accent": "American", "gender": "male", "age": "middle-aged"}, "category": "premade", "best_for_regions": ["americas", "europe"]},
    {"voice_id": "nPczCjzI2devNBz1zQrb", "name": "Brian", "description": "Deep, resonant warmth. Good for promotional content across markets.", "labels": {"accent": "American", "gender": "male", "age": "middle-aged"}, "category": "premade", "best_for_regions": ["americas", "general"]},
    {"voice_id": "N2lVS1w4EtoT3dr4eOWO", "name": "Callum", "description": "Transatlantic accent, calm and authoritative. Versatile across regions.", "labels": {"accent": "Transatlantic", "gender": "male", "age": "middle-aged"}, "category": "premade", "best_for_regions": ["general", "apac", "middle_east"]},
    {"voice_id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie", "description": "Australian-accented male. Relaxed, trustworthy tone for APAC markets.", "labels": {"accent": "Australian", "gender": "male", "age": "young"}, "category": "premade", "best_for_regions": ["apac", "general"]},
]


class VoiceSelectorAgent(BaseAgent):
    """Selects the optimal ElevenLabs voice for the OBD campaign."""

    name = "VoiceSelector"
    description = "Selects and configures the best ElevenLabs voice for the campaign"

    async def _fetch_available_voices(self) -> list[dict[str, Any]]:
        """Fetch all available voices from ElevenLabs. On 401 (invalid key) return curated list and do not raise."""
        if not ELEVENLABS_API_KEY or len(ELEVENLABS_API_KEY) < 10:
            logger.info(
                "[%s] No valid ElevenLabs API key — using curated voice list (audio will use Edge TTS if ElevenLabs selected)",
                self.name,
            )
            return list(_CURATED_ELEVENLABS_VOICES)

        logger.info("[%s] Fetching available voices from ElevenLabs", self.name)
        all_voices: list[dict[str, Any]] = []
        try:
            async with httpx.AsyncClient() as client:
                params: dict[str, Any] = {"page_size": 100}
                response = await client.get(
                    f"{ELEVENLABS_BASE_URL}/v2/voices",
                    headers=get_elevenlabs_headers(),
                    params=params,
                    timeout=30.0,
                )
                if response.status_code == 401:
                    if elevenlabs_401_is_tts_only(response.text):
                        logger.info(
                            "[%s] ElevenLabs key is TTS-only (no voices_read). Using curated default voices.",
                            self.name,
                        )
                    else:
                        logger.info(
                            "[%s] ElevenLabs API key rejected (401). Using curated voice list — Edge TTS fallback if needed.",
                            self.name,
                        )
                    return list(_CURATED_ELEVENLABS_VOICES)
                response.raise_for_status()
                data = response.json()
                all_voices.extend(data.get("voices", []))
                next_cursor = data.get("next_cursor") or None
                while next_cursor and len(all_voices) < 300:
                    params = {"page_size": 100, "next_cursor": next_cursor}
                    response = await client.get(
                        f"{ELEVENLABS_BASE_URL}/v2/voices",
                        headers=get_elevenlabs_headers(),
                        params=params,
                        timeout=30.0,
                    )
                    if response.status_code == 401:
                        break
                    response.raise_for_status()
                    data = response.json()
                    all_voices.extend(data.get("voices", []))
                    next_cursor = data.get("next_cursor") or None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                if elevenlabs_401_is_tts_only(e.response.text):
                    logger.info(
                        "[%s] ElevenLabs key is TTS-only (no voices_read). Using curated default voices.",
                        self.name,
                    )
                else:
                    logger.info(
                        "[%s] ElevenLabs API key invalid (401). Using curated voice list — Edge TTS fallback if needed.",
                        self.name,
                    )
                return list(_CURATED_ELEVENLABS_VOICES)
            raise
        except Exception as e:
            logger.warning("[%s] Could not fetch ElevenLabs voices: %s — using curated list", self.name, e)
            return list(_CURATED_ELEVENLABS_VOICES)

        if not all_voices:
            return list(_CURATED_ELEVENLABS_VOICES)

        logger.info("[%s] Found %s available voices from API", self.name, len(all_voices))
        simplified = []
        for v in all_voices:
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

        # Fetch available voices (or curated list on 401 / no key)
        try:
            available_voices = await self._fetch_available_voices()
        except Exception as e:
            logger.warning("[%s] Could not fetch voices: %s — using curated list", self.name, e)
            available_voices = list(_CURATED_ELEVENLABS_VOICES)

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
            system_prompt=self._resolve_prompt(SYSTEM_PROMPT),
            user_prompt=user_prompt,
            max_tokens=4096,
        )

        result = self.parse_json(response)
        logger.info(
            f"[{self.name}] Selected voice: "
            f"{result.get('selected_voice', {}).get('name', 'Unknown')}"
        )
        return result
