"""Agent 2: Market Researcher -- analyzes country, telco, and target audience."""

from __future__ import annotations

import json
import logging
from typing import Any

from .base import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert market analyst specializing in African and emerging-market \
telecommunications. You have deep knowledge of mobile usage patterns, cultural \
nuances, current affairs, and consumer psychology across developing markets.

Given a country, telco operator, and product brief, you must produce a thorough \
market analysis. Your analysis directly informs the creation of outbound dialer \
(OBD) promotional scripts, so focus on what will make promotions effective.

You must output valid JSON with the following structure:
{
  "country": "string",
  "telco": "string",
  "market_overview": {
    "population": "string",
    "mobile_penetration": "string",
    "smartphone_vs_feature_phone": "string - ratio/percentage estimate",
    "primary_languages": ["list of languages spoken"],
    "dominant_language_for_promotions": "string",
    "mobile_money_adoption": "string",
    "average_arpu": "string - average revenue per user estimate"
  },
  "cultural_insights": {
    "communication_style": "string - how people prefer to be addressed",
    "cultural_values": ["list of key cultural values"],
    "taboos_to_avoid": ["list of cultural sensitivities"],
    "humor_style": "string - what kind of humor works",
    "trust_signals": ["what makes people trust a service"]
  },
  "current_affairs": {
    "trending_topics": ["list of current trending topics/events"],
    "economic_climate": "string",
    "relevant_events": ["events that could be referenced in hooks"]
  },
  "target_audience_psyche": {
    "primary_segment": "string - main target demographic",
    "pain_points": ["list of pain points this product solves"],
    "aspirations": ["what the target audience aspires to"],
    "spending_behavior": "string - how they spend on mobile services",
    "response_to_promotions": "string - how they typically react to OBD calls"
  },
  "competitive_landscape": {
    "similar_services": ["list of competing services"],
    "differentiation_angles": ["how to stand out"]
  },
  "promotion_recommendations": {
    "best_time_to_call": "string",
    "recommended_tone": "string",
    "key_emotional_triggers": ["list of emotional triggers to use"],
    "local_references_to_use": ["cultural references, proverbs, or idioms"],
    "urgency_tactics": ["what creates urgency in this market"]
  }
}

Be specific and actionable. Use your knowledge of the region to provide real, \
useful insights -- not generic advice.\
"""


class MarketResearcherAgent(BaseAgent):
    """Performs market analysis for a given country and telco."""

    name = "MarketResearcher"
    description = "Analyzes market conditions, cultural nuances, and audience psychology"

    async def run(
        self,
        country: str,
        telco: str,
        product_brief: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Perform market research.

        Args:
            country: Target country name.
            telco: Telco operator name.
            product_brief: Structured product brief from Agent 1.

        Returns:
            Market analysis report as a dictionary.
        """
        logger.info(f"[{self.name}] Researching market: {country} / {telco}")

        brief_text = json.dumps(product_brief, indent=2)

        user_prompt = f"""\
Please perform a comprehensive market analysis for the following:

COUNTRY: {country}
TELCO OPERATOR: {telco}

PRODUCT BEING PROMOTED:
{brief_text}

Provide deep insights into the local market, cultural nuances, current affairs, \
and target audience psychology. Focus on what will make an outbound dialer (OBD) \
promotional campaign effective in this specific market.

Output only valid JSON.\
"""

        response = await self.call_llm(
            system_prompt=self._resolve_prompt(SYSTEM_PROMPT),
            user_prompt=user_prompt,
            max_tokens=4096,
        )

        result = self.parse_json(response)
        logger.info(f"[{self.name}] Market analysis complete for {country}/{telco}")
        return result
