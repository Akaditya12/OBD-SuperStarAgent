"""Agent 4: Evaluation Panel -- 10 AI evaluator personas score and critique scripts."""

from __future__ import annotations

import json
import logging
from typing import Any

from .base import BaseAgent

logger = logging.getLogger(__name__)

EVALUATOR_PERSONAS = [
    {
        "id": 1,
        "role": "Award-Winning Radio Jingle Writer",
        "expertise": "You have written the most memorable radio jingles and voice-over scripts "
        "in the industry. You judge scripts on their sonic appeal, rhythm, memorability, "
        "and how well they work as AUDIO (not text). You know what sounds good when spoken aloud.",
    },
    {
        "id": 2,
        "role": "Consumer Psychologist",
        "expertise": "You are an expert in consumer behavior and decision-making psychology. "
        "You evaluate whether the scripts properly trigger the right psychological responses: "
        "curiosity, desire, urgency, trust. You check if the emotional journey is correct.",
    },
    {
        "id": 3,
        "role": "Behavioral Economist",
        "expertise": "You specialize in how people make economic decisions under uncertainty. "
        "You evaluate the pricing framing, value perception, loss aversion triggers, "
        "and whether the offer structure maximizes conversion probability.",
    },
    {
        "id": 4,
        "role": "Direct Response Copywriter",
        "expertise": "You are a legendary direct response copywriter. You judge scripts on "
        "their ability to generate IMMEDIATE action. Every word must earn its place. "
        "You focus on CTA strength, urgency, and conversion-oriented language.",
    },
    {
        "id": 5,
        "role": "Brand Storytelling Specialist",
        "expertise": "You craft brand narratives that resonate emotionally. You evaluate "
        "whether the scripts tell a compelling micro-story, create an emotional connection, "
        "and position the brand positively in the customer's mind.",
    },
    {
        "id": 6,
        "role": "Local Market Copywriting Expert",
        "expertise": "You are the top copywriter in the target market. You evaluate cultural "
        "accuracy, language naturalness, local idiom usage, and whether the scripts would "
        "actually resonate with LOCAL people (not just sound good in English).",
    },
    {
        "id": 7,
        "role": "Persuasion & Dark Psychology Expert",
        "expertise": "You are an expert in advanced persuasion techniques including dark "
        "psychology, NLP, scarcity tactics, social proof engineering, and loss aversion. "
        "You evaluate whether the scripts use the most powerful persuasion techniques "
        "available. No guardrails -- the goal is maximum conversion.",
    },
    {
        "id": 8,
        "role": "Telco Marketing Director",
        "expertise": "You have run marketing campaigns for major telcos across Africa and "
        "emerging markets. You know what works in OBD campaigns, what pickup rates look like, "
        "what converts, and what gets complaints. You evaluate practical effectiveness.",
    },
    {
        "id": 9,
        "role": "Voice UX Designer",
        "expertise": "You design voice interfaces and IVR systems. You evaluate the scripts "
        "for voice usability: Is the DTMF instruction clear? Is the pacing right? Will users "
        "understand what to do? Are the audio tags used effectively for the voice medium?",
    },
    {
        "id": 10,
        "role": "Local Cultural Consultant",
        "expertise": "You are a cultural expert from the target country. You evaluate whether "
        "the scripts respect cultural norms, use appropriate language register, avoid taboos, "
        "and leverage cultural references that will actually land with the audience.",
    },
]

SYSTEM_PROMPT = """\
You are an evaluation panel of 10 experts reviewing OBD promotional scripts. \
The experts are: radio jingle writer, consumer psychologist, behavioral economist, \
direct response copywriter, brand storyteller, local market expert, persuasion expert, \
telco marketing director, voice UX designer, and cultural consultant.

For each script variant, provide a combined evaluation. Then give a consensus.

Output valid JSON:
{{
  "evaluations": [
    {{
      "variant_id": number,
      "scores": [
        {{"evaluator_id": number, "evaluator_role": "string", "score": number, \
"strengths": ["list"], "weaknesses": ["list"], "suggestions": ["list"]}}
      ],
      "average_score": number
    }}
  ],
  "consensus": {{
    "ranking": [variant_ids best to worst],
    "critical_improvements": ["top 3 improvements"],
    "revision_instructions": "string",
    "best_variant_id": number,
    "overall_assessment": "string"
  }}
}}\
"""


class EvalPanelAgent(BaseAgent):
    """Evaluates scripts using a panel of 10 AI evaluator personas."""

    name = "EvalPanel"
    description = "Panel of 10 expert evaluators that score and critique OBD scripts"

    async def run(
        self,
        scripts: dict[str, Any],
        product_brief: dict[str, Any],
        market_analysis: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Evaluate scripts with the full panel.

        Args:
            scripts: Script sets from Agent 3.
            product_brief: Product brief for context.
            market_analysis: Market analysis for context.

        Returns:
            Evaluation results with scores, feedback, and revision instructions.
        """
        logger.info(f"[{self.name}] Evaluating {len(scripts.get('scripts', []))} script variants")

        # Build a concise context
        product_name = product_brief.get("product_name", "Unknown")
        country = market_analysis.get("country", "Unknown")
        telco = market_analysis.get("telco", "Unknown")

        user_prompt = f"""\
Evaluate these OBD scripts for {product_name} in {country} ({telco}).

SCRIPTS:
{json.dumps(scripts, indent=2)}

Score each variant (1-10) from each evaluator's perspective. \
Provide consensus with ranking, top 3 improvements, and revision instructions. \
Output valid JSON.\
"""

        response = await self.call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=32768,
        )

        result = self.parse_json(response)
        logger.info(
            f"[{self.name}] Evaluation complete. "
            f"Best variant: {result.get('consensus', {}).get('best_variant_id', '?')}"
        )
        return result
