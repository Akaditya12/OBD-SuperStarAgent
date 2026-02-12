"""Agent 3: Script Writer -- creates Hook + Body + CTA scripts with ElevenLabs V3 audio tags."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from backend.config import MAX_SCRIPT_WORDS, NUM_SCRIPT_VARIANTS

from .base import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert OBD (Outbound Dialer) copywriter who creates promotional voice scripts \
for telecom markets. You understand local culture, psychology, and persuasion.

Create OBD scripts with ElevenLabs V3 audio tags embedded in the text.

SCRIPT STRUCTURE (each variant):
- hook: First 5 seconds, grab attention immediately. Use [excited], [curious], cultural refs.
- body: Next 15-18 seconds, deliver the product pitch compellingly. Benefits, not features.
- cta: Last 5-7 seconds, clear DTMF call to action (e.g. "Press 1 now").
- fallback_1: If no DTMF pressed, urgency follow-up (~15 words).
- fallback_2: If still no DTMF, psychological persuasion (~15 words).
- polite_closure: Graceful exit (~10 words).
- full_script: hook + body + cta combined into one string.

AUDIO TAGS (use 3-5 per script): [excited], [curious], [whispers], [laughs], [pause], \
[short pause], [cheerfully], [mischievously], [playfully], [sigh], [gasps]. \
Also use CAPITALIZATION for emphasis and ellipses (...) for dramatic pauses.

RULES:
- Total script (hook+body+cta) MUST be under {max_words} words (~30 seconds)
- Use the local language mixed with English where appropriate
- DTMF instruction must be crystal clear
- Each variant must have a DIFFERENT creative angle

OUTPUT: Valid JSON:
{{"scripts": [{{"variant_id": 1, "theme": "string", "language": "string", \
"hook": "string", "body": "string", "cta": "string", "fallback_1": "string", \
"fallback_2": "string", "polite_closure": "string", "full_script": "string", \
"word_count": 0, "estimated_duration_seconds": 0, \
"audio_tags_used": ["list"]}}], \
"language_used": "string", "creative_rationale": "string"}}

Generate exactly {num_variants} variants.\
""".format(max_words=MAX_SCRIPT_WORDS, num_variants=NUM_SCRIPT_VARIANTS)


REVISION_SYSTEM_PROMPT = """\
You are an expert OBD copywriter revising scripts based on evaluation feedback. \
Apply improvements while keeping the same JSON output format. \
Rules: under {max_words} words per script, include ElevenLabs V3 audio tags, \
culturally relevant, clear DTMF CTAs.\
""".format(max_words=MAX_SCRIPT_WORDS)


def _summarize_brief(product_brief: dict[str, Any]) -> str:
    """Create a concise text summary of the product brief for the prompt."""
    parts = []
    parts.append(f"Product: {product_brief.get('product_name', 'Unknown')}")
    parts.append(f"Type: {product_brief.get('product_type', 'VAS')}")
    desc = product_brief.get("description", "")
    if desc:
        parts.append(f"Description: {desc}")
    features = product_brief.get("key_features", [])
    if features:
        parts.append(f"Key features: {', '.join(features[:5])}")
    pricing = product_brief.get("pricing", {})
    if pricing:
        points = pricing.get("price_points", [])
        if points:
            parts.append(f"Pricing: {'; '.join(str(p) for p in points[:3])}")
        elif pricing.get("model"):
            parts.append(f"Pricing model: {pricing['model']}")
    usps = product_brief.get("unique_selling_points", [])
    if usps:
        parts.append(f"USPs: {', '.join(usps[:4])}")
    sub = product_brief.get("subscription_mechanism", "")
    if sub:
        parts.append(f"Subscribe via: {sub}")
    return "\n".join(parts)


def _summarize_market(market_analysis: dict[str, Any]) -> str:
    """Create a concise text summary of market analysis for the prompt."""
    parts = []
    parts.append(f"Country: {market_analysis.get('country', '?')}")
    parts.append(f"Telco: {market_analysis.get('telco', '?')}")
    overview = market_analysis.get("market_overview", {})
    if overview:
        lang = overview.get("dominant_language_for_promotions", "")
        if lang:
            parts.append(f"Language for promotions: {lang}")
        langs = overview.get("primary_languages", [])
        if langs:
            parts.append(f"Languages spoken: {', '.join(langs[:3])}")
    culture = market_analysis.get("cultural_insights", {})
    if culture:
        style = culture.get("communication_style", "")
        if style:
            parts.append(f"Communication style: {style}")
        humor = culture.get("humor_style", "")
        if humor:
            parts.append(f"Humor style: {humor}")
        refs = culture.get("local_references_to_use", [])
        if not refs:
            refs = market_analysis.get("promotion_recommendations", {}).get("local_references_to_use", [])
        if refs:
            parts.append(f"Local references: {', '.join(refs[:3])}")
    promo = market_analysis.get("promotion_recommendations", {})
    if promo:
        tone = promo.get("recommended_tone", "")
        if tone:
            parts.append(f"Recommended tone: {tone}")
        triggers = promo.get("key_emotional_triggers", [])
        if triggers:
            parts.append(f"Emotional triggers: {', '.join(triggers[:4])}")
        urgency = promo.get("urgency_tactics", [])
        if urgency:
            parts.append(f"Urgency tactics: {', '.join(urgency[:3])}")
    audience = market_analysis.get("target_audience_psyche", {})
    if audience:
        segment = audience.get("primary_segment", "")
        if segment:
            parts.append(f"Target segment: {segment}")
        pains = audience.get("pain_points", [])
        if pains:
            parts.append(f"Pain points: {', '.join(pains[:3])}")
    return "\n".join(parts)


class ScriptWriterAgent(BaseAgent):
    """Creates OBD promotional scripts with hook, body, CTA, and fallbacks."""

    name = "ScriptWriter"
    description = "Creates compelling OBD scripts with cultural relevance and audio tags"

    async def run(
        self,
        product_brief: dict[str, Any],
        market_analysis: dict[str, Any],
        feedback: dict[str, Any] | None = None,
        previous_scripts: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        is_revision = feedback is not None and previous_scripts is not None
        if is_revision:
            logger.info(f"[{self.name}] Revising scripts based on evaluation feedback")
            return await self._revise(product_brief, market_analysis, feedback, previous_scripts)
        else:
            logger.info(f"[{self.name}] Generating {NUM_SCRIPT_VARIANTS} new script variants")
            return await self._generate(product_brief, market_analysis)

    async def _generate(
        self,
        product_brief: dict[str, Any],
        market_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate fresh scripts."""
        brief_summary = _summarize_brief(product_brief)
        market_summary = _summarize_market(market_analysis)

        user_prompt = f"""\
Create {NUM_SCRIPT_VARIANTS} OBD promotional script variants.

PRODUCT:
{brief_summary}

MARKET:
{market_summary}

Each variant needs a DIFFERENT creative angle (e.g., curiosity gap, humor, urgency, \
storytelling, social proof). Embed ElevenLabs V3 audio tags in every field. \
Under {MAX_SCRIPT_WORDS} words per script. Output valid JSON with "scripts" array.\
"""

        response = await self.call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=32768,
        )

        logger.info(f"[{self.name}] Raw response (first 500 chars): {response[:500]}")
        result = self._normalize_result(response)
        self._validate_scripts(result)
        return result

    async def _revise(
        self,
        product_brief: dict[str, Any],
        market_analysis: dict[str, Any],
        feedback: dict[str, Any],
        previous_scripts: dict[str, Any],
    ) -> dict[str, Any]:
        """Revise scripts based on evaluation feedback."""
        # Extract just the consensus feedback, not the full evaluation
        consensus = feedback.get("consensus", {})
        improvements = consensus.get("critical_improvements", [])
        instructions = consensus.get("revision_instructions", "")

        feedback_text = ""
        if improvements:
            feedback_text += "Critical improvements needed:\n" + "\n".join(f"- {imp}" for imp in improvements)
        if instructions:
            feedback_text += f"\n\nRevision instructions: {instructions}"
        if not feedback_text:
            feedback_text = json.dumps(feedback, indent=2)[:2000]

        user_prompt = f"""\
Revise these OBD scripts based on evaluation feedback.

CURRENT SCRIPTS:
{json.dumps(previous_scripts, indent=2)}

FEEDBACK:
{feedback_text}

Apply improvements. Keep same JSON format with "scripts" array. \
Embed ElevenLabs V3 audio tags. Under {MAX_SCRIPT_WORDS} words per script. Output valid JSON.\
"""

        response = await self.call_llm(
            system_prompt=REVISION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=32768,
        )

        logger.info(f"[{self.name}] Raw revision response (first 500 chars): {response[:500]}")
        result = self._normalize_result(response)
        self._validate_scripts(result)
        return result

    def _normalize_result(self, response: str) -> dict[str, Any]:
        """Parse and normalize the LLM response into expected format."""
        result = self.parse_json(response)

        # Handle alternative key names
        if "scripts" not in result and "variants" in result:
            result["scripts"] = result.pop("variants")

        # Handle single script returned as top-level object
        if "scripts" not in result and "hook" in result and "body" in result:
            result = {
                "scripts": [result],
                "language_used": result.get("language", ""),
                "creative_rationale": "Single variant returned",
            }

        if "scripts" not in result:
            logger.warning(f"[{self.name}] Unexpected response structure. Keys: {list(result.keys())}")
            result["scripts"] = []

        # Ensure each script has required fields
        for i, script in enumerate(result.get("scripts", [])):
            if "variant_id" not in script:
                script["variant_id"] = i + 1
            if "full_script" not in script and "hook" in script:
                script["full_script"] = f"{script.get('hook', '')} {script.get('body', '')} {script.get('cta', '')}"

        return result

    def _validate_scripts(self, result: dict[str, Any]) -> None:
        """Validate script word counts and structure."""
        scripts = result.get("scripts", [])
        for script in scripts:
            full_text = script.get("full_script", "")
            # Strip audio tags for word count
            clean_text = re.sub(r"\[.*?\]", "", full_text)
            word_count = len(clean_text.split())
            script["word_count"] = word_count
            script["estimated_duration_seconds"] = round(word_count / 2.5, 1)

            if word_count > MAX_SCRIPT_WORDS + 10:
                logger.warning(
                    f"[{self.name}] Script variant {script.get('variant_id')} "
                    f"exceeds word limit: {word_count} words"
                )
