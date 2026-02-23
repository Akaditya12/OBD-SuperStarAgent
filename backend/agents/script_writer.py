"""Agent 3: Script Writer -- creates Hook + Body + CTA scripts with ElevenLabs V3 audio tags.

Generates scripts in parallel batches to avoid LLM output-length limits.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from backend.config import MAX_SCRIPT_WORDS, NUM_SCRIPT_VARIANTS

from .base import BaseAgent

logger = logging.getLogger(__name__)

CREATIVE_ANGLES = [
    "Curiosity Gap",
    "Humor + Social Proof",
    "Storytelling (Relatable Scenario)",
    "Urgency + Fear of Missing Out",
    "Emotional / Aspirational",
]

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
"language_used": "string", "creative_rationale": "string"}}\
""".format(max_words=MAX_SCRIPT_WORDS)


REVISION_SYSTEM_PROMPT = """\
You are an expert OBD copywriter revising scripts based on evaluation feedback.

Apply the feedback improvements while keeping the same JSON output format.
Each variant must be under {max_words} words, include ElevenLabs V3 audio tags, \
be culturally relevant, and have clear DTMF CTAs.
Keep each variant's unique creative angle (theme) while incorporating feedback.

OUTPUT: Valid JSON with "scripts" array.\
""".format(max_words=MAX_SCRIPT_WORDS)


def _summarize_brief(product_brief: dict[str, Any]) -> str:
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
        language_override: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        is_revision = feedback is not None and previous_scripts is not None
        if is_revision:
            logger.info(f"[{self.name}] Revising scripts based on evaluation feedback")
            return await self._revise(product_brief, market_analysis, feedback, previous_scripts, language_override)
        else:
            logger.info(f"[{self.name}] Generating {NUM_SCRIPT_VARIANTS} new script variants (lang={language_override})")
            return await self._generate(product_brief, market_analysis, language_override)

    async def _generate_batch(
        self,
        brief_summary: str,
        market_summary: str,
        angles: list[str],
        start_id: int,
        language_override: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate a small batch of script variants (2-3 at a time)."""
        angle_list = ", ".join(angles)
        count = len(angles)
        ids = ", ".join(str(start_id + i) for i in range(count))

        lang_instruction = ""
        if language_override:
            lang_instruction = (
                f"\n\nCRITICAL LANGUAGE REQUIREMENT: ALL scripts MUST be written in {language_override}. "
                f"Use {language_override} as the primary language for hook, body, cta, fallbacks, "
                f"closure, and full_script. Mix with English only for brand names and technical terms."
            )

        user_prompt = f"""\
Create exactly {count} OBD promotional script variant(s) with these creative angles: {angle_list}.
Use variant_id values: {ids}.

PRODUCT:
{brief_summary}

MARKET:
{market_summary}{lang_instruction}

Each variant needs its specified creative angle. Embed ElevenLabs V3 audio tags in every field. \
Under {MAX_SCRIPT_WORDS} words per script. Output valid JSON with "scripts" array of {count} objects.\
"""

        response = await self.call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=8192,
        )

        logger.info(f"[{self.name}] Batch response ({count} scripts): {len(response)} chars")
        result = self._normalize_result(response)
        return result.get("scripts", [])

    async def _generate(
        self,
        product_brief: dict[str, Any],
        market_analysis: dict[str, Any],
        language_override: str | None = None,
    ) -> dict[str, Any]:
        """Generate scripts in parallel batches to avoid LLM output-length limits."""
        brief_summary = _summarize_brief(product_brief)
        market_summary = _summarize_market(market_analysis)

        angles = CREATIVE_ANGLES[:NUM_SCRIPT_VARIANTS]

        # Split into batches of 2
        batches: list[tuple[list[str], int]] = []
        for i in range(0, len(angles), 2):
            batch_angles = angles[i:i + 2]
            batches.append((batch_angles, i + 1))

        logger.info(
            f"[{self.name}] Generating {len(angles)} variants in {len(batches)} "
            f"parallel batches of 2 (lang={language_override})"
        )

        tasks = [
            self._generate_batch(brief_summary, market_summary, batch_angles, start_id, language_override)
            for batch_angles, start_id in batches
        ]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_scripts: list[dict[str, Any]] = []
        for i, res in enumerate(batch_results):
            if isinstance(res, Exception):
                logger.warning(f"[{self.name}] Batch {i+1} failed: {res} -- retrying once")
                try:
                    retry = await self._generate_batch(
                        brief_summary, market_summary, batches[i][0], batches[i][1], language_override
                    )
                    all_scripts.extend(retry)
                except Exception as retry_err:
                    logger.error(f"[{self.name}] Batch {i+1} retry also failed: {retry_err}")
            else:
                all_scripts.extend(res)

        # Re-number variant IDs sequentially (always 1-based)
        for idx, script in enumerate(all_scripts):
            script["variant_id"] = idx + 1

        logger.info(f"[{self.name}] Total scripts generated: {len(all_scripts)}")

        if len(all_scripts) < NUM_SCRIPT_VARIANTS:
            logger.warning(
                f"[{self.name}] Only {len(all_scripts)}/{NUM_SCRIPT_VARIANTS} variants generated. "
                f"Some batches may have failed."
            )

        result: dict[str, Any] = {
            "scripts": all_scripts,
            "language_used": all_scripts[0].get("language", "") if all_scripts else "",
            "creative_rationale": f"Generated {len(all_scripts)} variants across {len(batches)} parallel batches",
        }

        self._validate_scripts(result)
        return result

    async def _revise(
        self,
        product_brief: dict[str, Any],
        market_analysis: dict[str, Any],
        feedback: dict[str, Any],
        previous_scripts: dict[str, Any],
        language_override: str | None = None,
    ) -> dict[str, Any]:
        """Revise scripts in parallel batches based on evaluation feedback."""
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

        lang_instruction = ""
        if language_override:
            lang_instruction = (
                f"\n\nCRITICAL: ALL scripts MUST remain in {language_override}. "
                f"Do not switch to any other language."
            )

        scripts = previous_scripts.get("scripts", [])
        if not scripts:
            return previous_scripts

        # Revise in batches of 2
        async def _revise_batch(batch_scripts: list[dict[str, Any]]) -> list[dict[str, Any]]:
            count = len(batch_scripts)
            user_prompt = f"""\
Revise these {count} OBD script(s) based on evaluation feedback.

CURRENT SCRIPTS:
{json.dumps({"scripts": batch_scripts}, indent=2)}

FEEDBACK:
{feedback_text}{lang_instruction}

Return ALL {count} revised variants. Keep each variant's unique theme. \
Embed ElevenLabs V3 audio tags. Under {MAX_SCRIPT_WORDS} words per script. \
Output valid JSON with "scripts" array of {count} objects.\
"""
            response = await self.call_llm(
                system_prompt=REVISION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=8192,
            )
            result = self._normalize_result(response)
            revised = result.get("scripts", [])

            # If revision returned fewer, merge originals back
            if len(revised) < count:
                revised_ids = {s.get("variant_id") for s in revised}
                for orig in batch_scripts:
                    if orig.get("variant_id") not in revised_ids:
                        revised.append(orig)

            return revised

        batches = [scripts[i:i + 2] for i in range(0, len(scripts), 2)]
        logger.info(f"[{self.name}] Revising {len(scripts)} scripts in {len(batches)} parallel batches")

        tasks = [_revise_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_revised: list[dict[str, Any]] = []
        for i, res in enumerate(batch_results):
            if isinstance(res, Exception):
                logger.warning(f"[{self.name}] Revision batch {i+1} failed: {res} -- keeping originals")
                all_revised.extend(batches[i])
            else:
                all_revised.extend(res)

        # Re-number sequentially to guarantee 1-based IDs
        all_revised.sort(key=lambda s: s.get("variant_id", 0))
        for idx, script in enumerate(all_revised):
            script["variant_id"] = idx + 1

        result: dict[str, Any] = {
            "scripts": all_revised,
            "language_used": previous_scripts.get("language_used", ""),
            "creative_rationale": f"Revised {len(all_revised)} variants based on evaluation feedback",
        }

        self._validate_scripts(result)
        return result

    def _normalize_result(self, response: str) -> dict[str, Any]:
        """Parse and normalize the LLM response into expected format."""
        result = self.parse_json(response)

        if "scripts" not in result and "variants" in result:
            result["scripts"] = result.pop("variants")

        if "scripts" not in result and "hook" in result and "body" in result:
            result = {
                "scripts": [result],
                "language_used": result.get("language", ""),
                "creative_rationale": "Single variant returned",
            }

        if "scripts" not in result:
            if "error" in result:
                logger.error(f"[{self.name}] LLM returned error: {result['error']}")
            else:
                logger.warning(f"[{self.name}] Unexpected response structure. Keys: {list(result.keys())}")
            result["scripts"] = []

        for i, script in enumerate(result.get("scripts", [])):
            if "variant_id" not in script:
                script["variant_id"] = i + 1
            if "full_script" not in script and "hook" in script:
                script["full_script"] = f"{script.get('hook', '')} {script.get('body', '')} {script.get('cta', '')}"
            if not script.get("fallback_1"):
                script["fallback_1"] = (
                    "Don't miss out! This exclusive offer won't last long. Press 1 now to grab it before it's gone!"
                )
            if not script.get("fallback_2"):
                script["fallback_2"] = (
                    "Last chance! Thousands are already enjoying this. Press 1 now or you may miss this opportunity."
                )
            if not script.get("polite_closure"):
                script["polite_closure"] = (
                    "Thank you for your time. Have a wonderful day!"
                )

        return result

    def _validate_scripts(self, result: dict[str, Any]) -> None:
        """Validate script word counts and structure."""
        scripts = result.get("scripts", [])
        for script in scripts:
            full_text = script.get("full_script", "")
            clean_text = re.sub(r"\[.*?\]", "", full_text)
            word_count = len(clean_text.split())
            script["word_count"] = word_count
            script["estimated_duration_seconds"] = round(word_count / 2.5, 1)

            if word_count > MAX_SCRIPT_WORDS + 10:
                logger.warning(
                    f"[{self.name}] Script variant {script.get('variant_id')} "
                    f"exceeds word limit: {word_count} words"
                )
