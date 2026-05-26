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

CRITICAL — HOOK STYLE:
- ABSOLUTELY NEVER start any script with a greeting, honorific, or address to the listener. \
This includes ALL languages: "Madam", "Sir", "Madam/Sir", "Dear subscriber", "Dear listener", \
"Welcome sir", "Karibu bwana", "Habari", "Shikamoo", "Jambo", "Namaste ji", "Duh kaka", \
"Big brother", "Bhai sahab", "Cher abonne", "Bonjour monsieur", or ANY similar formal address. \
This is a HARD requirement — violations will be rejected.
- Every hook MUST start DIRECTLY with a SCENARIO, QUESTION, SOUND EFFECT, or PRODUCT TEASER. \
NO greeting before it. The very first word should pull the listener into a story or question. \
Examples of GOOD hooks: "[curious] Sochiye...", "Kya hoga agar...", "[laughs] Watu wanabadili sauti...", \
"[excited] Imagina ukipiga simu na sauti ya cartoon..."
- Write like a young radio copywriter — punchy, street-smart, current generation lingo. \
NOT like a corporate letter, customer service call, or IVR greeting.

CRITICAL — VARIANT UNIQUENESS:
- Each of the 5 variants MUST use a COMPLETELY DIFFERENT scenario, setting, and context. \
NEVER reuse the same situation (e.g., traffic, driving, meeting, office) across multiple variants. \
If variant 1 mentions "driving", NO other variant can mention driving, traffic, or commuting.
- Use diverse real-life contexts that match the TARGET COUNTRY and PRODUCT. Examples of DISTINCT contexts: \
morning routine, family dinner, weekend outing, exam preparation, festival shopping, gym workout, \
cooking at home, traveling by train, airport queue, kids playing, doctor visit, late night work.
- Each variant's BODY must pitch the product from a DIFFERENT angle tied to its unique scenario. \
Don't just change the hook and keep the same pitch — the entire story should be different.
- Use insights from the MARKET RESEARCH (cultural values, audience psyche, local references) \
to make each variant feel authentic to the country and operator.

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

EMOTION TAGS — placement and discipline (these tags drive ElevenLabs v3 voice delivery; treat them with the same care as the words themselves):

Approved tags ONLY — never invent new ones, never use tags outside this list:
- Energy / excitement: [excited], [energetic], [cheerfully], [playfully]
- Curiosity / intrigue: [curious], [mischievously], [whispers]
- Warmth / connection: [warm], [gentle], [sincere], [soft]
- Reactions: [laughs], [sigh], [gasps]
- Urgency: [urgent]
- Pacing (breath, NOT emotion): [pause], [short pause]

PLACEMENT — these are HARD requirements (violations break voice delivery):
- A tag goes IMMEDIATELY BEFORE the words it should color. Never after the sentence, never as a paragraph header divorced from text.
  GOOD: "[excited] Imagine winning a thousand kwacha today!"
  BAD:  "Imagine winning a thousand kwacha today! [excited]"
- NEVER stack tags ("[excited][playfully] ..."). Pick ONE — stacked tags get ignored by the TTS engine.
- Tags shape ~1-2 sentences of tone. Don't sprinkle them mid-clause as decoration.
- One tag per emotional beat, not per sentence.

MULTILINGUAL — tags work IDENTICALLY across all languages (English, Tamil, Hindi, Swahili, Yoruba, Hausa, Amharic, Arabic, French, Tagalog, Bengali, Telugu, Kinyarwanda, etc.):
- Tag names stay in ENGLISH square brackets regardless of the script's language. The transliteration rule applies to local-language words only — it does NOT apply to emotion tags.
  GOOD (Tamil):    "[curious] Theriyumaa, ungal voicelaye paadalaam!"
  GOOD (Swahili):  "[excited] Hebu fikiria, sauti yako inabadilika sasa!"
  GOOD (Hindi):    "[playfully] Arre, kya aap sapne dekh rahe hain?"
  GOOD (Amharic):  "[urgent] Ahun yitebiku, idilachehu ke 5 daqiqa beful yiqeral!"
  BAD:             "[ம் ஆர்வம்] ..." (do NOT translate the tag itself)
  BAD:             "[curiosus] ..." (do NOT invent localized variants)
- The same approved tag list applies to every language. Don't add new tags for cultural concepts — choose the closest fit from the list ([warm] / [sincere] for respect, [playfully] for teasing, [urgent] for now-or-never, etc.).
- The PER-SECTION and EMOTIONAL ARC rules are universal — they hold in every language.

PER-SECTION USAGE (target placement, not rigid):
- hook       — 1 tag at the very start. Choose a high-engagement opener: [curious], [excited], [playfully], [whispers], [laughs].
- body       — 1 tag mid-section, matching the beat: [sincere] for trust, [warm] for empathy, [energetic] for benefit reveal.
- cta        — 1 tag, MUST be activating: [urgent], [excited], or [energetic]. NEVER [soft] or [gentle] in a CTA — they kill momentum.
- fallback_1 — [urgent] or [energetic] (this is the "you might be missing out" beat).
- fallback_2 — [sincere] (social proof / reassurance) or [warm] (gentle persuasion). Pick one.
- polite_closure — [warm], [gentle], or [sincere]. Soft landing only.

EMOTIONAL ARC across the script:
- HOOK pulls attention (curious / excited / intrigue).
- BODY builds trust + shows value (warm / sincere / energetic).
- CTA drives action (urgent / excited).
- FALLBACKS escalate urgency then reassure.
- CLOSURE leaves a positive feeling (warm / gentle).

PACING DISCIPLINE:
- [pause] adds ~0.8s of silence — use AT MOST ONCE per full script, on a single dramatic beat (e.g. right before the price reveal). Never inside a CTA.
- [short pause] adds ~0.3s — max twice per script. Prefer "..." ellipses for shorter rhetorical pauses.
- Do not place pacing tags inside the CTA — every fraction of a second matters there.

VARIETY:
- Aim for 3-5 DISTINCT tags across the full script (hook + body + cta). More than 5 dilutes effect.
- Don't repeat the same tag in adjacent sections — if hook is [excited], body should NOT also be [excited]; pick a different shade ([warm], [sincere], [energetic]).
- Across the 5 variants, vary the overall tag palette so no two variants sound emotionally identical.

ADDITIONAL TYPOGRAPHY (not tags, but supported):
- CAPITALIZATION on a key word for emphasis (e.g. "ONLY today", "FREE first month"). Use 1-2 per script max.
- Ellipses (...) for short mid-sentence rhetorical pauses — better than [short pause] for in-line beats.

CRITICAL — PRODUCT ACCURACY:
- ONLY mention features, voices, effects, pricing, and capabilities that are EXPLICITLY stated in the product brief. \
NEVER invent, hallucinate, or embellish features that are not in the brief. \
If the brief says voice avatars are "Female, Cartoon" — ONLY mention Female and Cartoon. \
Do NOT add "celebrity voice", "presenter voice", "hero voice" or any other voice type not listed.
- ONLY use the EXACT pricing from the brief. Do not round, convert, or guess pricing.
- ONLY use the EXACT shortcode/CTA from the product brief. Do not invent ANY DTMF options. \
If the brief says "dial 901767777" — use ONLY "dial 901767777". Do NOT add "Press 1", "Press 2", \
"press 2 to hear again", "press 9 to repeat" or ANY press/dial instruction not in the brief. \
If the brief says "Press 1" — use ONLY "Press 1". Never add Press 2, Press 3, etc. \
The CTA must contain EXACTLY what the product brief specifies — nothing invented.
- When describing the product, use the EXACT feature names from the brief. \
If the brief says "Background ambience: Concert, Airport, Traffic, James Bond" — use those exact names.
- NEVER describe the product in ways that imply capabilities not stated. \
Stick to what the brief says — nothing more, nothing less.

RULES:
- Total script (hook+body+cta) MUST be under {max_words} words (~30 seconds)
- Write scripts STRICTLY in the language specified by the LANGUAGE REQUIREMENT below. \
If no language requirement is given, default to English.
- When writing in ENGLISH for a non-English market: the script must be in English, but you MAY \
sprinkle in 1-2 SHORT, widely-understood local greetings or exclamations for warmth \
(e.g. "Asante", "Namaste", "Merci"). Do NOT insert full local phrases, sentences, or \
uncommon words — the listener must understand the entire script in English.
- When writing in a non-English language, ALWAYS use LATIN/ROMAN script (English letters). \
NEVER use native scripts like Amharic (ገ), Arabic (ع), Hindi (ह), Thai (ก), etc. \
Transliterate all local language words into English characters. \
Example: write "Selam" not "ሰላም", write "Namaste" not "नमस्ते", write "Marhaba" not "مرحبا".
- ALL sections (hook, body, cta, fallback_1, fallback_2, polite_closure) MUST be in the SAME language as the main script. \
Never write fallbacks or closure in English when the script is in Hindi or another local language.
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


# Language-aware fallback defaults so non-English scripts don't get English fallbacks
_FALLBACK_BY_LANG: dict[str, tuple[str, str, str]] = {
    # (fallback_1, fallback_2, polite_closure)
    "hindi":    ("[urgent] Yeh mauka mat chhodiye... abhi Press 1 karein.", "[gentle] Hazaaron log already enjoy kar rahe hain... aap bhi Press 1 karein.", "[warm] Dhanyavaad, aapka din shubh ho."),
    "hinglish": ("[urgent] Yeh mauka mat chhodiye... abhi Press 1 karein.", "[gentle] Hazaaron log already enjoy kar rahe hain... aap bhi Press 1 karein.", "[warm] Dhanyavaad, aapka din shubh ho."),
    "swahili":  ("[urgent] Usikose fursa hii... bonyeza 1 sasa.", "[gentle] Maelfu tayari wanafurahia... bonyeza 1 sasa.", "[warm] Asante, siku njema."),
    "kiswahili":("[urgent] Usikose fursa hii... bonyeza 1 sasa.", "[gentle] Maelfu tayari wanafurahia... bonyeza 1 sasa.", "[warm] Asante, siku njema."),
    "amharic":  ("[urgent] Yihen idil aderagachew... 1 yitebiku.", "[gentle] Beziwochu iyetedsetut new... 1 yitebiku.", "[warm] Ameseginalehu, melikami ken."),
    "french":   ("[urgent] Ne manquez pas cette offre... appuyez sur 1 maintenant.", "[gentle] Des milliers en profitent deja... appuyez sur 1.", "[warm] Merci, bonne journee."),
    "portuguese":("[urgent] Nao perca esta oportunidade... pressione 1 agora.", "[gentle] Milhares ja estao aproveitando... pressione 1.", "[warm] Obrigado, tenha um bom dia."),
    "arabic":   ("[urgent] La tafawwit hadhihi al-fursa... idghat 1 al-aan.", "[gentle] Al-alaaf yastamti'oon bi-hadha... idghat 1.", "[warm] Shukran, yawm sa'eed."),
    "tamil":    ("[urgent] Idha thavara vidaatheenga... ippo 1 press pannunga.", "[gentle] Aayirakkanakkaanor idha enjoy panraanga... 1 press pannunga.", "[warm] Nandri, nallanal vazhthukkal."),
    "bengali":  ("[urgent] Ei sujog chharben na... ekhuni 1 press korun.", "[gentle] Hajar hajar lok eita enjoy korche... 1 press korun.", "[warm] Dhonnobad, shubho din."),
    "telugu":   ("[urgent] Ee avakasham vadulukokandi... ippudu 1 press cheyandi.", "[gentle] Vellamandi idhi enjoy chesthunnaru... 1 press cheyandi.", "[warm] Dhanyavaadalu, subha dinam."),
}

def _get_language_fallbacks(lang: str | None) -> tuple[str, str]:
    """Return (fallback_1, fallback_2) in the appropriate language."""
    if not lang:
        return (
            "Don't miss out! Press 1 now to grab this offer!",
            "Thousands are already enjoying this. Press 1 now!",
        )
    lang_lower = lang.lower().strip()
    for key, (fb1, fb2, _closure) in _FALLBACK_BY_LANG.items():
        if key in lang_lower or lang_lower in key:
            return (fb1, fb2)
    return (
        "Don't miss out! Press 1 now to grab this offer!",
        "Thousands are already enjoying this. Press 1 now!",
    )

def _get_language_closure(lang: str | None) -> str:
    """Return polite_closure in the appropriate language."""
    if not lang:
        return "Thank you for your time. Have a wonderful day!"
    lang_lower = lang.lower().strip()
    for key, (_fb1, _fb2, closure) in _FALLBACK_BY_LANG.items():
        if key in lang_lower or lang_lower in key:
            return closure
    return "Thank you for your time. Have a wonderful day!"


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
        fb1, fb2 = _get_language_fallbacks(language_override)
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
            "fallback_1": fb1,
            "fallback_2": fb2,
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

        lang_used = result.get("language_used") or ""

        for i, script in enumerate(result.get("scripts", [])):
            if "variant_id" not in script:
                script["variant_id"] = i + 1
            if "full_script" not in script and "hook" in script:
                script["full_script"] = f"{script.get('hook', '')} {script.get('body', '')} {script.get('cta', '')}"
            # Fallback defaults in the same language as the script
            script_lang = script.get("language") or lang_used
            fb1, fb2 = _get_language_fallbacks(script_lang)
            if not script.get("fallback_1"):
                script["fallback_1"] = fb1
            if not script.get("fallback_2"):
                script["fallback_2"] = fb2
            if not script.get("polite_closure"):
                script["polite_closure"] = _get_language_closure(script_lang)
            # Ensure word_count is always present
            if not script.get("word_count"):
                full_text = script.get("full_script", "")
                clean_text = re.sub(r"\[.*?\]", "", full_text)
                wc = len(clean_text.split())
                script["word_count"] = wc
                script["estimated_duration_seconds"] = round(wc / 2.5, 1)

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

        self._clean_scripts(result)

    @staticmethod
    def _clean_scripts(result: dict[str, Any]) -> None:
        """Post-process scripts to remove formal greetings, honorifics, and fix issues.

        The LLM stubbornly inserts formal greetings in multiple languages despite
        prompt instructions. This method enforces clean hooks at the code level.
        """
        # Formal AND casual greeting words/phrases to strip from the START of hooks/full_script
        _GREETING_PATTERN = re.compile(
            r"^(\s*(?:\[[^\]]*\]\s*)*)"  # Capture leading emotion tags
            r"(?:"
            # English formal greetings
            r"(?:Dear\s+)?(?:Madam|Sir|Madam\s*/?\s*Sir|Sir\s*/?\s*Madam|Madam\s+or\s+Sir|Sir\s+or\s+Madam)"
            r"|(?:Dear\s+(?:subscriber|listener|user|customer|friend))"
            r"|Welcome\s+(?:sir|madam|bwana|mama|dada)"
            # English casual greetings
            r"|(?:Hey\s+(?:there|friend|buddy|folks|everyone))"
            r"|(?:Hello\s+(?:there|friend|everyone|folks))"
            r"|(?:Hi\s+(?:there|friend|everyone|folks))"
            # Hindi/Urdu greetings
            r"|(?:Namaste|Namaskar|Pranam)\s*(?:ji)?"
            r"|(?:Arre\s+(?:bhai|dost|yaar))"
            # Swahili greetings and honorifics
            r"|(?:Mambo\s+(?:rafiki|ndugu|vipi))"
            r"|(?:Karibu\s+)?(?:bwana|mama|dada|ndugu|kaka|rafiki)"
            r"|(?:Habari\s+(?:yako|zako|za\s+asubuhi|za\s+jioni))"
            r"|(?:Shikamoo|Hujambo|Jambo)"
            r"|(?:Duh|Eeh|Eh)\s+(?:kaka|bwana|mama|dada|ndugu)\s*(?:mkubwa|yangu)?"
            r"|(?:Sasa|Niaje|Vipi)"
            # French greetings
            r"|(?:Cher|Chere)\s+(?:abonne|client|ami)"
            r"|Bonjour\s+(?:monsieur|madame|cher)"
            r"|(?:Salut\s+(?:ami|mon\s+ami))"
            # General patterns
            r"|(?:Big\s+brother|Big\s+sister|Brother|Sister|Bhai|Didi|Bhaiya)"
            r"|(?:Good\s+(?:morning|afternoon|evening)\s*(?:friend|sir|madam)?)"
            r")"
            r"(?:\s*[,!.…\s])*",
            re.IGNORECASE,
        )
        # Inline formal references anywhere in text
        _INLINE_FORMAL = re.compile(
            r"\b(?:"
            r"Sir\s*/?\s*Madam|Madam\s*/?\s*Sir|Sir\s+or\s+Madam|Madam\s+or\s+Sir"
            r"|Dear\s+(?:Sir|Madam|subscriber|listener|user|customer)"
            r"|(?:kaka|bwana|mama|dada)\s+mkubwa"
            r")\b[,\s]*",
            re.IGNORECASE,
        )

        text_fields = ["hook", "body", "cta", "full_script", "fallback_1", "fallback_2", "polite_closure"]

        for script in result.get("scripts", []):
            for field in text_fields:
                text = script.get(field, "")
                if not text or not isinstance(text, str):
                    continue

                # Strip greeting from start of hook and full_script
                if field in ("hook", "full_script"):
                    text = _GREETING_PATTERN.sub(r"\1", text)

                # Strip inline formal references from all fields
                text = _INLINE_FORMAL.sub("", text)

                # Clean up double spaces and leading punctuation
                text = re.sub(r"\s{2,}", " ", text).strip()
                text = re.sub(r"^[,.\s…]+", "", text).strip()

                script[field] = text

            # Rebuild full_script if hook/body/cta were cleaned
            if script.get("hook") and script.get("body") and script.get("cta"):
                script["full_script"] = f"{script['hook']} {script['body']} {script['cta']}"

            # Recalculate word count after cleaning
            full_text = script.get("full_script", "")
            clean_text = re.sub(r"\[.*?\]", "", full_text)
            script["word_count"] = len(clean_text.split())
            script["estimated_duration_seconds"] = round(script["word_count"] / 2.5, 1)
