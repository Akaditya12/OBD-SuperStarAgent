"""Agent 3: Script Writer -- creates Hook + Body + CTA scripts with emotion tags.

Generates scripts in parallel batches to avoid LLM output-length limits.
Emotion tags like [excited], [warm] guide voice tone; they are stripped before TTS.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from backend.config import MAX_SCRIPT_WORDS, NUM_SCRIPT_VARIANTS, get_live_config

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

Create OBD scripts with emotion tags embedded in the text. These tags guide the voice \
actor's tone and delivery. Use ONLY square-bracket tags from the approved list below.

SCRIPT STRUCTURE (each variant):
- hook: First 5 seconds, grab attention immediately. Use [excited], [curious], cultural refs.
- body: Next 15-18 seconds, deliver the product pitch compellingly. Benefits, not features. When the brief includes "Pricing (mention in script body)", incorporate that pricing or value in the body (e.g. cost, offer).
- cta: Last 5-7 seconds, clear DTMF call to action. When the brief provides a Shortcode/CTA, use that EXACT text (e.g. "Press 1 now", "Dial *123#").
- fallback_1: If no DTMF pressed, urgency follow-up (~15 words).
- fallback_2: If still no DTMF, psychological persuasion (~15 words).
- polite_closure: Graceful exit (~10 words).
- full_script: hook + body + cta combined into one string.

EMOTION TAGS (use 3-5 per script, ONLY these square-bracket tags): \
[excited], [curious], [warm], [gentle], [whispers], [laughs], [pause], \
[short pause], [cheerfully], [mischievously], [playfully], [sigh], [gasps], \
[soft], [energetic], [sincere], [urgent].
Also use CAPITALIZATION for emphasis and ellipses (...) for dramatic pauses.

RULES:
- Total script (hook+body+cta) MUST be under {max_words} words (~30 seconds)
- Write scripts STRICTLY in the language specified by the LANGUAGE REQUIREMENT below. \
If no language requirement is given, default to English.
- When writing in a non-English language, ALWAYS use LATIN/ROMAN script (English letters). \
NEVER use native scripts like Amharic (ገ), Arabic (ع), Hindi (ह), Thai (ก), etc. \
Transliterate all local language words into English characters. \
Example: write "Selam" not "ሰላም", write "Namaste" not "नमस्ते", write "Marhaba" not "مرحبا".
- When the product brief includes "Shortcode/CTA (MUST use this EXACTLY...)", the cta, fallback_1, and fallback_2 MUST repeat that exact instruction (same words, same numbers/codes). Do not invent a different CTA.
- When the product brief includes "Pricing (mention in script body)", mention that pricing or value in the script body (e.g. "Only 50 cents a month", "Free for the first month").
- DTMF instruction must be crystal clear
- Each variant must have a DIFFERENT creative angle
- Never use a slash between words—TTS will say "slash" aloud; write "A or B" not "A/B" when you need alternatives.

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
Each variant must be under {max_words} words, include emotion tags from the approved list, \
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
    pricing_text = (product_brief.get("pricing_text") or "").strip()
    pricing = product_brief.get("pricing", {})
    if pricing_text:
        parts.append(f"Pricing (mention in script body): {pricing_text}")
    elif pricing:
        points = pricing.get("price_points", [])
        if points:
            parts.append(f"Pricing (mention in script body): {'; '.join(str(p) for p in points[:3])}")
        elif pricing.get("model"):
            parts.append(f"Pricing (mention in script body): {pricing['model']}")
    usps = product_brief.get("unique_selling_points", [])
    if usps:
        parts.append(f"USPs: {', '.join(usps[:4])}")
    shortcode_cta = (product_brief.get("shortcode_or_cta") or "").strip()
    if shortcode_cta:
        parts.append(f"Shortcode/CTA (MUST use this EXACTLY in cta and fallbacks): {shortcode_cta}")
    sub = product_brief.get("subscription_mechanism", "")
    if sub and not shortcode_cta:
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
    description = "Creates compelling OBD scripts with cultural relevance and emotion tags"

    async def run(
        self,
        product_brief: dict[str, Any],
        market_analysis: dict[str, Any],
        feedback: dict[str, Any] | None = None,
        previous_scripts: dict[str, Any] | None = None,
        language_override: str | None = None,
        flow_config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        cfg = get_live_config()
        max_words = cfg.get("max_script_words", MAX_SCRIPT_WORDS)
        num_variants = cfg.get("num_script_variants", NUM_SCRIPT_VARIANTS)

        is_revision = feedback is not None and previous_scripts is not None
        steps = (flow_config or {}).get("steps") if isinstance(flow_config, dict) else []
        use_flow = isinstance(steps, list) and len(steps) > 0
        scripts_list = (previous_scripts or {}).get("scripts", [])
        has_segments = scripts_list and (scripts_list[0].get("segments") if scripts_list else [])

        if is_revision:
            if use_flow and has_segments:
                logger.info(f"[{self.name}] Revising flow scripts (segment-aware) based on evaluation feedback")
                return await self._revise_flow(product_brief, market_analysis, feedback, previous_scripts, language_override, steps=steps, max_words=max_words)
            logger.info(f"[{self.name}] Revising scripts based on evaluation feedback")
            return await self._revise(product_brief, market_analysis, feedback, previous_scripts, language_override, max_words=max_words, num_variants=num_variants)
        elif use_flow:
            logger.info(f"[{self.name}] Generating flow-based scripts ({len(steps)} steps, {num_variants} variants, lang={language_override})")
            return await self._generate_flow(product_brief, market_analysis, language_override, steps=steps, max_words=max_words, num_variants=num_variants)
        else:
            logger.info(f"[{self.name}] Generating {num_variants} new script variants (lang={language_override})")
            return await self._generate(product_brief, market_analysis, language_override, max_words=max_words, num_variants=num_variants)

    async def _generate_batch(
        self,
        brief_summary: str,
        market_summary: str,
        angles: list[str],
        start_id: int,
        language_override: str | None = None,
        max_words: int = MAX_SCRIPT_WORDS,
    ) -> list[dict[str, Any]]:
        """Generate a small batch of script variants (2-3 at a time)."""
        angle_list = ", ".join(angles)
        count = len(angles)
        ids = ", ".join(str(start_id + i) for i in range(count))

        lang_instruction = ""
        if language_override and language_override.lower().startswith("english"):
            lang_instruction = (
                "\n\nCRITICAL LANGUAGE REQUIREMENT: ALL scripts MUST be written entirely in ENGLISH."
            )
        elif language_override:
            lang_instruction = (
                f"\n\nCRITICAL LANGUAGE REQUIREMENT: Write the ENTIRE script (hook, body, CTA, fallbacks, closure) "
                f"in {language_override}. The script must be PRIMARILY or WHOLLY in {language_override} — not in English. "
                f"ALWAYS write using LATIN/ROMAN letters (transliterate); do NOT use native script characters. "
                f"Example: if {language_override} is Amharic write 'Selam' not 'ሰላም'. "
                f"Use English only for brand names, shortcodes, and numbers (e.g. 'Press 1', 'Dial 1195')."
            )
        else:
            lang_instruction = (
                "\n\nLANGUAGE REQUIREMENT: Write all scripts in ENGLISH by default."
            )

        user_prompt = f"""\
Create exactly {count} OBD promotional script variant(s) with these creative angles: {angle_list}.
Use variant_id values: {ids}.

PRODUCT:
{brief_summary}

MARKET:
{market_summary}{lang_instruction}

Each variant needs its specified creative angle. Include emotion tags from the approved list. \
Under {max_words} words per script. If the PRODUCT section includes "Shortcode/CTA (MUST use this EXACTLY...)", \
your cta, fallback_1, and fallback_2 MUST use that exact shortcode/CTA wording. If it includes "Pricing (mention in script body)", \
mention that pricing in the script body. Output valid JSON with "scripts" array of {count} objects.\
"""

        response = await self.call_llm(
            system_prompt=self._resolve_prompt(SYSTEM_PROMPT),
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
        max_words: int = MAX_SCRIPT_WORDS,
        num_variants: int = NUM_SCRIPT_VARIANTS,
    ) -> dict[str, Any]:
        """Generate scripts in parallel batches to avoid LLM output-length limits."""
        brief_summary = _summarize_brief(product_brief)
        market_summary = _summarize_market(market_analysis)

        angles = CREATIVE_ANGLES[:num_variants]

        batches: list[tuple[list[str], int]] = []
        for i in range(0, len(angles), 2):
            batch_angles = angles[i:i + 2]
            batches.append((batch_angles, i + 1))

        logger.info(
            f"[{self.name}] Generating {len(angles)} variants in {len(batches)} "
            f"parallel batches of 2 (lang={language_override})"
        )

        tasks = [
            self._generate_batch(brief_summary, market_summary, batch_angles, start_id, language_override, max_words=max_words)
            for batch_angles, start_id in batches
        ]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_scripts: list[dict[str, Any]] = []
        for i, res in enumerate(batch_results):
            if isinstance(res, Exception):
                logger.warning(f"[{self.name}] Batch {i+1} failed: {res} -- retrying once")
                try:
                    retry = await self._generate_batch(
                        brief_summary, market_summary, batches[i][0], batches[i][1], language_override, max_words=max_words
                    )
                    all_scripts.extend(retry)
                except Exception as retry_err:
                    logger.error(f"[{self.name}] Batch {i+1} retry also failed: {retry_err}")
            else:
                all_scripts.extend(res)

        for idx, script in enumerate(all_scripts):
            script["variant_id"] = idx + 1
            if (language_override or "").strip():
                script["language"] = (language_override or "").strip()

        logger.info(f"[{self.name}] Total scripts generated: {len(all_scripts)}")

        if len(all_scripts) < num_variants:
            logger.warning(
                f"[{self.name}] Only {len(all_scripts)}/{num_variants} variants generated. "
                f"Some batches may have failed."
            )

        result: dict[str, Any] = {
            "scripts": all_scripts,
            "language_used": (language_override or "").strip() or (all_scripts[0].get("language", "") if all_scripts else ""),
            "creative_rationale": f"Generated {len(all_scripts)} variants across {len(batches)} parallel batches",
        }

        self._validate_scripts(result)
        return result

    def _flow_script_from_segments(
        self,
        segment_list: list[dict[str, Any]],
        variant_id: int,
        theme: str,
        language_override: str | None,
    ) -> dict[str, Any]:
        """Build one script dict from segments (hook, full_script, segments, etc.)."""
        full_parts = [s["text"] for s in segment_list]
        hook_text = full_parts[0] if full_parts else ""
        full_script = " ".join(full_parts)
        n = len(segment_list)
        body_text = full_parts[1] if n > 1 else ""
        cta_text = full_parts[2] if n > 2 else (full_parts[-1] if n > 1 else "")
        closure_text = full_parts[-1] if n > 0 else "Thank you for your time. Have a wonderful day!"
        return {
            "variant_id": variant_id,
            "theme": theme,
            "language": language_override or "English",
            "hook": hook_text,
            "body": body_text,
            "cta": cta_text,
            "polite_closure": closure_text,
            "full_script": full_script,
            "segments": segment_list,
            "fallback_1": "Don't miss out! Press 1 now to activate.",
            "fallback_2": "Last chance! Press 1 now or you may miss this opportunity.",
            "word_count": len(re.sub(r"\[.*?\]", "", full_script).split()),
            "estimated_duration_seconds": round(len(full_script.split()) / 2.5, 1),
        }

    async def _generate_flow_batch(
        self,
        brief_summary: str,
        market_summary: str,
        steps: list[dict[str, Any]],
        angles: list[str],
        start_id: int,
        language_override: str | None,
        steps_desc: str,
        lang_instruction: str,
        max_words: int,
    ) -> list[dict[str, Any]]:
        """Generate a batch of flow script variants (each with segments). Returns list of script dicts."""
        count = len(angles)
        angle_list = ", ".join(angles)
        ids = ", ".join(str(start_id + i) for i in range(count))

        user_prompt = f"""\
Generate exactly {count} OBD script VARIANT(s) that follow this exact flow. Each variant has the SAME flow steps but DIFFERENT creative angle/tone. Write one prompt per step per variant. Output valid JSON only.

PRODUCT:
{brief_summary}

MARKET:
{market_summary}{lang_instruction}

CREATIVE ANGLES for each variant (use this tone/style for that variant):
{angle_list}

Variant IDs: {ids}.

FLOW STEPS (each variant must have exactly these steps, in order):
{steps_desc}

If the PRODUCT section includes "Shortcode/CTA (MUST use this EXACTLY...)", use that exact wording in the relevant step(s). If it includes "Pricing (mention in script body)", include that pricing in the step that describes the offer. For alternatives (e.g. "rra or mma"), write " or " not "/" so TTS pronounces correctly.

OUTPUT: A JSON object with key "scripts" — an array of {count} objects. Each object has "variant_id" (number, one of {ids}) and "segments" — array of objects with "step_id" (string, match step id above) and "text" (string). Example:
{{"scripts": [{{"variant_id": 1, "segments": [{{"step_id": "welcome", "text": "..."}}, ...]}}, {{"variant_id": 2, "segments": [{{"step_id": "welcome", "text": "..."}}, ...]}}]}}
"""

        response = await self.call_llm(
            system_prompt=self._resolve_prompt(SYSTEM_PROMPT),
            user_prompt=user_prompt,
            max_tokens=8192,
        )

        result = self.parse_json(response)
        scripts_raw = result.get("scripts", [])
        step_ids = [s.get("id", f"step_{i+1}") for i, s in enumerate(steps)]

        out_scripts: list[dict[str, Any]] = []
        for idx, raw in enumerate(scripts_raw[:count]):
            variant_id = start_id + idx
            theme = angles[idx] if idx < len(angles) else "flow"
            segs_raw = raw.get("segments", []) if isinstance(raw, dict) else []
            segment_list: list[dict[str, Any]] = []
            for i, step_id in enumerate(step_ids):
                text = ""
                for seg in segs_raw:
                    if isinstance(seg, dict) and seg.get("step_id") == step_id:
                        text = (seg.get("text") or "").strip()
                        break
                if not text and i < len(segs_raw) and isinstance(segs_raw[i], dict):
                    text = (segs_raw[i].get("text") or "").strip()
                segment_list.append({"step_id": step_id, "text": text or f"[Prompt for {step_id}]"})
            out_scripts.append(self._flow_script_from_segments(segment_list, variant_id, theme, language_override))
        return out_scripts

    async def _generate_flow(
        self,
        product_brief: dict[str, Any],
        market_analysis: dict[str, Any],
        language_override: str | None = None,
        steps: list[dict[str, Any]] | None = None,
        max_words: int = MAX_SCRIPT_WORDS,
        num_variants: int = NUM_SCRIPT_VARIANTS,
    ) -> dict[str, Any]:
        """Generate num_variants script variants, each with one prompt per flow step (segments). Same philosophy as non-flow: 5 variants, each with segments."""
        steps = steps or []
        if not steps:
            return await self._generate(product_brief, market_analysis, language_override, max_words=max_words, num_variants=num_variants)

        brief_summary = _summarize_brief(product_brief)
        market_summary = _summarize_market(market_analysis)

        lang_instruction = ""
        if language_override and language_override.lower().startswith("english"):
            lang_instruction = (
                "\n\nCRITICAL LANGUAGE REQUIREMENT: ALL step text MUST be written entirely in ENGLISH."
            )
        elif language_override:
            lang_instruction = (
                f"\n\nCRITICAL LANGUAGE REQUIREMENT: Write EVERY step's text in {language_override}. "
                f"The script must be PRIMARILY or WHOLLY in {language_override} — not in English. "
                f"Use LATIN/ROMAN letters (transliterate); do NOT use native script characters. "
                f"Use English only for brand names, shortcodes, and numbers."
            )
        else:
            lang_instruction = "\n\nLANGUAGE: Write all prompts in ENGLISH."

        steps_desc = "\n".join(
            f"- Step id=\"{s.get('id', 'step')}\": {s.get('purpose', '')} (max ~{s.get('max_words', 30)} words)"
            for s in steps
        )

        angles = CREATIVE_ANGLES[:num_variants]
        batches: list[tuple[list[str], int]] = []
        for i in range(0, len(angles), 2):
            batch_angles = angles[i : i + 2]
            batches.append((batch_angles, i + 1))

        logger.info(
            f"[{self.name}] Generating {num_variants} flow variants in {len(batches)} batches (lang={language_override})"
        )

        tasks = [
            self._generate_flow_batch(
                brief_summary,
                market_summary,
                steps,
                batch_angles,
                start_id,
                language_override,
                steps_desc,
                lang_instruction,
                max_words,
            )
            for batch_angles, start_id in batches
        ]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_scripts: list[dict[str, Any]] = []
        for i, res in enumerate(batch_results):
            if isinstance(res, Exception):
                logger.warning(f"[{self.name}] Flow batch {i+1} failed: {res} -- retrying once")
                try:
                    retry = await self._generate_flow_batch(
                        brief_summary,
                        market_summary,
                        steps,
                        batches[i][0],
                        batches[i][1],
                        language_override,
                        steps_desc,
                        lang_instruction,
                        max_words,
                    )
                    all_scripts.extend(retry)
                except Exception as retry_err:
                    logger.error(f"[{self.name}] Flow batch {i+1} retry failed: {retry_err}")
            else:
                all_scripts.extend(res)

        for idx, script in enumerate(all_scripts):
            script["variant_id"] = idx + 1

        out: dict[str, Any] = {
            "scripts": all_scripts,
            "language_used": language_override or "English",
            "creative_rationale": f"Flow-based {len(all_scripts)} variants, {len(steps)} steps each",
        }
        self._validate_scripts(out)
        return out

    async def _revise(
        self,
        product_brief: dict[str, Any],
        market_analysis: dict[str, Any],
        feedback: dict[str, Any],
        previous_scripts: dict[str, Any],
        language_override: str | None = None,
        max_words: int = MAX_SCRIPT_WORDS,
        num_variants: int = NUM_SCRIPT_VARIANTS,
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
        if language_override and language_override.lower().startswith("english"):
            lang_instruction = "\n\nCRITICAL: ALL scripts MUST remain in ENGLISH."
        elif language_override:
            lang_instruction = (
                f"\n\nCRITICAL: ALL scripts MUST remain in {language_override} words, "
                f"but written in LATIN/ROMAN letters (transliterated). "
                f"Do NOT use native script characters."
            )
        else:
            lang_instruction = "\n\nCRITICAL: ALL scripts MUST remain in ENGLISH."

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
Keep the exact CTA/shortcode wording from the current scripts (e.g. "Press 1", "Dial *123#") — do not change it. \
Include emotion tags. Under {max_words} words per script. \
Output valid JSON with "scripts" array of {count} objects.\
"""
            response = await self.call_llm(
                system_prompt=self._resolve_prompt(REVISION_SYSTEM_PROMPT, "agent_prompt_ScriptWriter_Revision"),
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

    async def _revise_flow(
        self,
        product_brief: dict[str, Any],
        market_analysis: dict[str, Any],
        feedback: dict[str, Any],
        previous_scripts: dict[str, Any],
        language_override: str | None = None,
        steps: list[dict[str, Any]] | None = None,
        max_words: int = MAX_SCRIPT_WORDS,
    ) -> dict[str, Any]:
        """Revise flow scripts: apply feedback to each segment's text while preserving step_ids and structure."""
        consensus = feedback.get("consensus", {})
        improvements = consensus.get("critical_improvements", [])
        instructions = consensus.get("revision_instructions", "")

        feedback_text = ""
        if improvements:
            feedback_text += "Critical improvements:\n" + "\n".join(f"- {imp}" for imp in improvements)
        if instructions:
            feedback_text += f"\n\nRevision instructions: {instructions}"
        if not feedback_text:
            feedback_text = json.dumps(feedback, indent=2)[:2000]

        lang_instruction = ""
        if language_override and language_override.lower().startswith("english"):
            lang_instruction = "\n\nCRITICAL: Keep ALL segment text in ENGLISH."
        elif language_override:
            lang_instruction = f"\n\nCRITICAL: Keep ALL segment text in {language_override}, LATIN/ROMAN letters."
        else:
            lang_instruction = "\n\nCRITICAL: Keep ALL segment text in ENGLISH."

        scripts = previous_scripts.get("scripts", [])
        if not scripts or not (steps or []):
            return previous_scripts

        step_ids = [s.get("id", f"step_{i+1}") for i, s in enumerate(steps)]

        async def _revise_flow_batch(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
            count = len(batch)
            user_prompt = f"""\
Revise these {count} flow-based OBD script(s) based on evaluation feedback. Each script has "segments" (step_id + text). Apply the feedback to improve the TEXT of each segment. Keep the EXACT same step_id order and structure. Do NOT add or remove segments. Do NOT change CTA/shortcode wording if it was correct.

CURRENT SCRIPTS (with segments):
{json.dumps({"scripts": batch}, indent=2)}

FEEDBACK:
{feedback_text}{lang_instruction}

Return valid JSON with "scripts" array of {count} objects. Each object MUST have "variant_id" and "segments" (array of {{"step_id": "...", "text": "..."}} in the same order). Preserve exact step_id values.
"""

            response = await self.call_llm(
                system_prompt=self._resolve_prompt(REVISION_SYSTEM_PROMPT, "agent_prompt_ScriptWriter_Revision"),
                user_prompt=user_prompt,
                max_tokens=8192,
            )
            result = self.parse_json(response)
            revised = result.get("scripts", [])

            out: list[dict[str, Any]] = []
            for i, orig in enumerate(batch):
                vid = orig.get("variant_id", i + 1)
                theme = orig.get("theme", "flow")
                segs = orig.get("segments", [])
                if i < len(revised) and revised[i].get("segments"):
                    segs = revised[i]["segments"]
                segment_list = []
                for j, step_id in enumerate(step_ids):
                    text = ""
                    for seg in segs:
                        if isinstance(seg, dict) and seg.get("step_id") == step_id:
                            text = (seg.get("text") or "").strip()
                            break
                    if not text and j < len(segs) and isinstance(segs[j], dict):
                        text = (segs[j].get("text") or "").strip()
                    segment_list.append({"step_id": step_id, "text": text or f"[Prompt for {step_id}]"})
                out.append(self._flow_script_from_segments(segment_list, vid, theme, language_override))
            return out

        batches = [scripts[i : i + 2] for i in range(0, len(scripts), 2)]
        tasks = [_revise_flow_batch(b) for b in batches]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_revised: list[dict[str, Any]] = []
        for i, res in enumerate(batch_results):
            if isinstance(res, Exception):
                logger.warning(f"[{self.name}] Flow revision batch {i+1} failed: {res} -- keeping originals")
                all_revised.extend(batches[i])
            else:
                all_revised.extend(res)

        all_revised.sort(key=lambda s: s.get("variant_id", 0))
        for idx, script in enumerate(all_revised):
            script["variant_id"] = idx + 1

        result = {
            "scripts": all_revised,
            "language_used": previous_scripts.get("language_used", ""),
            "creative_rationale": f"Revised {len(all_revised)} flow variants (segment-aware)",
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
