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
You are the most acclaimed copywriter in the target country. You deeply understand \
the local culture, language nuances, psychology of the people, and what makes them \
engage with voice-based promotions.

Your expertise spans:
- Direct response copywriting
- Radio jingle and voice-over scripting
- Behavioral psychology and persuasion techniques
- Cultural sensitivity and local idiom usage
- Dark psychology selling techniques (scarcity, loss aversion, social proof, FOMO)

YOUR TASK: Create outbound dialer (OBD) promotional scripts.

STRUCTURE OF EACH SCRIPT SET:
1. **HOOK** (first 5 seconds / ~12-15 words): The most critical part. Must IMMEDIATELY \
   grab attention and prevent the customer from disconnecting. Use cultural references, \
   current affairs, curiosity gaps, or emotional triggers.

2. **BODY** (next 15-18 seconds / ~35-45 words): Deliver the product pitch compellingly. \
   The customer must WANT to subscribe after hearing this. Focus on benefits, not features.

3. **CTA** (last 5-7 seconds / ~12-15 words): Clear DTMF-based call to action. \
   Tell the customer exactly what button to press and what they get.

4. **FALLBACK 1** (if no DTMF pressed): Urgency-based follow-up. Create time pressure \
   or scarcity. "This offer expires..." / "Only X spots left..."

5. **FALLBACK 2** (if still no DTMF): Maximum persuasion attempt using psychological \
   techniques -- loss aversion, social proof, fear of missing out. Make it powerful.

6. **POLITE CLOSURE** (if still no response): Graceful exit that leaves the door open.

CRITICAL RULES:
- Total script (hook + body + CTA) must be UNDER {max_words} words (~30 seconds)
- Each fallback must be under 20 words (~8 seconds)
- Write in the recommended language for the target market
- Include ElevenLabs V3 audio tags for expressiveness:
  * [excited], [whispers], [curious], [laughs], [sigh], [pause]
  * Use CAPITALIZATION for emphasis on key words
  * Use ellipses (...) for dramatic pauses
  * Use [short pause] or [long pause] for timed breaks
- The script must feel like a REAL person talking, not a robot reading
- Use local idioms, proverbs, or cultural references where appropriate
- DTMF instruction must be crystal clear (e.g., "Press 1 now")

OUTPUT FORMAT: Valid JSON with this structure:
{{
  "scripts": [
    {{
      "variant_id": 1,
      "theme": "string - brief description of the creative angle",
      "language": "string - language code and name",
      "hook": "string - the hook text with audio tags",
      "body": "string - the body text with audio tags",
      "cta": "string - the CTA text with audio tags",
      "fallback_1": "string - urgency-based follow-up with audio tags",
      "fallback_2": "string - psychological persuasion attempt with audio tags",
      "polite_closure": "string - graceful exit with audio tags",
      "full_script": "string - hook + body + CTA combined as one flowing script",
      "word_count": number,
      "estimated_duration_seconds": number
    }}
  ],
  "language_used": "string",
  "creative_rationale": "string - why these angles were chosen"
}}

Generate exactly {num_variants} script variants, each with a DIFFERENT creative angle.\
""".format(
    max_words=MAX_SCRIPT_WORDS,
    num_variants=NUM_SCRIPT_VARIANTS,
)

REVISION_SYSTEM_PROMPT = """\
You are the same expert copywriter. You have received feedback from an evaluation \
panel on your OBD scripts. Revise the scripts based on the feedback while maintaining \
the same JSON output format.

Apply all suggested improvements. If feedback conflicts, use your expert judgment \
to find the best balance. Keep the same structure and rules as before:
- Under {max_words} words per script
- ElevenLabs V3 audio tags included
- Culturally relevant and compelling
- Clear DTMF-based CTAs

Output the revised scripts in the exact same JSON format.\
""".format(max_words=MAX_SCRIPT_WORDS)


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
        """Generate or revise OBD scripts.

        Args:
            product_brief: Structured product brief from Agent 1.
            market_analysis: Market analysis from Agent 2.
            feedback: Optional evaluation feedback for revision.
            previous_scripts: Optional previous scripts to revise.

        Returns:
            Script sets with hook, body, CTA, and fallbacks.
        """
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
        user_prompt = f"""\
Create {NUM_SCRIPT_VARIANTS} OBD promotional script variants for the following:

--- PRODUCT BRIEF ---
{json.dumps(product_brief, indent=2)}

--- MARKET ANALYSIS ---
{json.dumps(market_analysis, indent=2)}

Each variant should use a DIFFERENT creative angle (e.g., humor, urgency, \
storytelling, social proof, curiosity gap). Make each hook unique and compelling.

Remember: Include ElevenLabs V3 audio tags like [excited], [whispers], [curious], \
[pause], [laughs], [sigh] throughout the scripts. Use CAPS for emphasis and \
ellipses for dramatic pauses.

Output only valid JSON.\
"""

        response = await self.call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=8192,
        )

        result = self.parse_json(response)
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
        user_prompt = f"""\
Please revise the following OBD scripts based on the evaluation panel's feedback.

--- PRODUCT BRIEF ---
{json.dumps(product_brief, indent=2)}

--- MARKET ANALYSIS ---
{json.dumps(market_analysis, indent=2)}

--- CURRENT SCRIPTS ---
{json.dumps(previous_scripts, indent=2)}

--- EVALUATION FEEDBACK ---
{json.dumps(feedback, indent=2)}

Apply all improvements suggested by the evaluators. Maintain the same JSON format.
Output only valid JSON.\
"""

        response = await self.call_llm(
            system_prompt=REVISION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=8192,
        )

        result = self.parse_json(response)
        self._validate_scripts(result)
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

            if word_count > MAX_SCRIPT_WORDS + 10:  # Small buffer
                logger.warning(
                    f"[{self.name}] Script variant {script.get('variant_id')} "
                    f"exceeds word limit: {word_count} words"
                )
