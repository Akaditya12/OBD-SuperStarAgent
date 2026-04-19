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
    # Female voices (7)
    {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah", "description": "Confident and warm, mature quality with a reassuring, professional tone.", "labels": {"accent": "american", "gender": "female", "age": "young"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/EXAVITQu4vr4xnSDxMaL/01a3e33c-6e99-4ee7-8543-ff2216a32186.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "FGY2WhTYpPnrIDTdsKH5", "name": "Laura", "description": "Sunny enthusiasm with a quirky attitude. Great for trendy, energetic content.", "labels": {"accent": "american", "gender": "female", "age": "young"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/FGY2WhTYpPnrIDTdsKH5/67341759-ad08-41a5-be6e-de12fe448618.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "Xb7hH8MSUJpSbSDYk0k2", "name": "Alice", "description": "Clear and engaging British voice. Friendly and approachable for e-learning and promos.", "labels": {"accent": "british", "gender": "female", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/Xb7hH8MSUJpSbSDYk0k2/d10f7534-11f6-41fe-a012-2de1e482d336.mp3", "best_for_regions": ["east_africa", "south_asia", "general"]},
    {"voice_id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily", "description": "Velvety British female. Delivers news and narrations with warmth and clarity.", "labels": {"accent": "british", "gender": "female", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/pFZP5JQG7iQjIQuC4Bku/89b68b35-b3dd-4348-a84a-a3c13a3c2b30.mp3", "best_for_regions": ["east_africa", "south_asia", "general"]},
    {"voice_id": "cgSgspJ2msm6clMCkdW9", "name": "Jessica", "description": "Playful, bright, and warm. Perfect for trendy telecom promotions.", "labels": {"accent": "american", "gender": "female", "age": "young"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/cgSgspJ2msm6clMCkdW9/56a97bf8-b69b-448f-846c-c3a11683d45a.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "XrExE9yKIg1WjnnlVkGX", "name": "Matilda", "description": "Professional woman with a pleasing alto pitch. Suitable for many use cases.", "labels": {"accent": "american", "gender": "female", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/XrExE9yKIg1WjnnlVkGX/b930e18d-6b4d-466e-bab2-0ae97c6d8535.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "hpp4J3VqNfWAUOO0d1Us", "name": "Bella", "description": "Warm, bright, and professional. Standard American accent with pleasant delivery.", "labels": {"accent": "american", "gender": "female", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/hpp4J3VqNfWAUOO0d1Us/dab0f5ba-3aa4-48a8-9fad-f138fea1126d.mp3", "best_for_regions": ["americas", "general"]},
    # Male voices (13)
    {"voice_id": "CwhRBWXzGAHq8TQ4Fs17", "name": "Roger", "description": "Laid-back and casual with a resonant quality. Perfect for casual conversations.", "labels": {"accent": "american", "gender": "male", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/CwhRBWXzGAHq8TQ4Fs17/58ee3ff5-f6f2-4628-93b8-e38eb31806b0.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie", "description": "Australian-accented male. Confident, energetic, and trustworthy.", "labels": {"accent": "australian", "gender": "male", "age": "young"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/IKne3meq5aSn9XLyUdCD/102de6f2-22ed-43e0-a1f1-111fa75c5481.mp3", "best_for_regions": ["apac", "general"]},
    {"voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "description": "Warm, captivating British storyteller. Authoritative narration quality.", "labels": {"accent": "british", "gender": "male", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/JBFqnCBsd6RMkjVDRZzb/e6206d1a-0721-4787-aafb-06a6e705cac5.mp3", "best_for_regions": ["east_africa", "south_asia", "general"]},
    {"voice_id": "N2lVS1w4EtoT3dr4eOWO", "name": "Callum", "description": "Gravelly, husky quality with character. Versatile across regions.", "labels": {"accent": "american", "gender": "male", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/N2lVS1w4EtoT3dr4eOWO/ac833bd8-ffda-4938-9ebc-b0f99ca25481.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "SAz9YHcvj6GT2YYXdXww", "name": "River", "description": "Relaxed, neutral, and informative. Great for narrations and conversational projects.", "labels": {"accent": "american", "gender": "neutral", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/SAz9YHcvj6GT2YYXdXww/e6c95f0b-2227-491a-b3d7-2249240decb7.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "SOYHLrjzK2X1ezoPC6cr", "name": "Harry", "description": "Animated and fierce. High energy for dynamic content.", "labels": {"accent": "american", "gender": "male", "age": "young"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/SOYHLrjzK2X1ezoPC6cr/86d178f6-f4b6-4e0e-85be-3de19f490794.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "TX3LPaxmHKxFdv7VOQHJ", "name": "Liam", "description": "Energetic and warm young adult. Suitable for reels, shorts, and promos.", "labels": {"accent": "american", "gender": "male", "age": "young"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/TX3LPaxmHKxFdv7VOQHJ/63148076-6363-42db-aea8-31424308b92c.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "bIHbv24MWmeRgasZH58o", "name": "Will", "description": "Conversational and laid back. Relaxed optimist tone.", "labels": {"accent": "american", "gender": "male", "age": "young"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/bIHbv24MWmeRgasZH58o/8caf8f3d-ad29-4980-af41-53f20c72d7a4.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "cjVigY5qzO86Huf0OWal", "name": "Eric", "description": "Smooth, trustworthy tenor. Perfect for agentic and professional use cases.", "labels": {"accent": "american", "gender": "male", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/cjVigY5qzO86Huf0OWal/d098fda0-6456-4030-b3d8-63aa048c9070.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "iP95p4xoKVk53GoZ742B", "name": "Chris", "description": "Natural and down-to-earth. Charming voice great across many use cases.", "labels": {"accent": "american", "gender": "male", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/iP95p4xoKVk53GoZ742B/3f4bde72-cc48-40dd-829f-57fbf906f4d7.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "nPczCjzI2devNBz1zQrb", "name": "Brian", "description": "Deep, resonant and comforting. Great for narrations and advertisements.", "labels": {"accent": "american", "gender": "male", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/nPczCjzI2devNBz1zQrb/2dd3e72c-4fd3-42f1-93ea-abc5d4e5aa1d.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel", "description": "Steady British broadcaster. Professional and trustworthy for campaigns.", "labels": {"accent": "british", "gender": "male", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/onwK4e9ZLuTAKqWW03F9/7eee0236-1a72-4b86-b303-5dcadc007ba9.mp3", "best_for_regions": ["east_africa", "south_asia", "general"]},
    {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "description": "Bright, dominant tenor. Brash and openly confident delivery.", "labels": {"accent": "american", "gender": "male", "age": "middle_aged"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/pNInz6obpgDQGcFmaJgB/d6905d7a-dd26-4187-bfff-1bd3a5ea7cac.mp3", "best_for_regions": ["americas", "general"]},
    {"voice_id": "pqHfZKP75CvOlQylNhV4", "name": "Bill", "description": "Wise, mature, and balanced. Friendly and comforting for storytelling.", "labels": {"accent": "american", "gender": "male", "age": "old"}, "category": "premade", "preview_url": "https://storage.googleapis.com/eleven-public-prod/premade/voices/pqHfZKP75CvOlQylNhV4/d782b3ff-84ba-4029-848c-acf01285524d.mp3", "best_for_regions": ["americas", "general"]},
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
