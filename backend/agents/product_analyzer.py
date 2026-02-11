"""Agent 1: Product Analyzer -- parses product documentation into a structured brief."""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert product analyst specializing in telecom VAS (Value Added Services) \
and mobile products. Your job is to read product documentation thoroughly and extract \
a comprehensive, structured product brief.

You must output valid JSON with the following structure:
{
  "product_name": "string",
  "product_type": "string (e.g., OBD, IVR, Smart Connect, AIPA, etc.)",
  "description": "string - concise 2-3 sentence description",
  "key_features": ["list of key features"],
  "pricing": {
    "model": "string (subscription/per-use/freemium/etc.)",
    "price_points": ["list of price points with details"],
    "currency": "string"
  },
  "target_audience": "string - who this product is for",
  "unique_selling_points": ["list of USPs that differentiate from competitors"],
  "value_propositions": ["list of value props from the customer's perspective"],
  "how_it_works": "string - brief explanation of how the product works for the end user",
  "subscription_mechanism": "string - how users subscribe (DTMF, SMS, USSD, etc.)",
  "technical_notes": "string - any technical details relevant for promotion"
}

Be thorough but concise. Focus on what matters for creating compelling outbound \
promotional content. Extract every pricing detail and subscription mechanism.\
"""


class ProductAnalyzerAgent(BaseAgent):
    """Reads product documentation and produces a structured product brief."""

    name = "ProductAnalyzer"
    description = "Analyzes product documentation to create a structured product brief"

    async def run(self, product_text: str, **kwargs: Any) -> dict[str, Any]:
        """Analyze product documentation.

        Args:
            product_text: The raw text content of the product documentation.

        Returns:
            Structured product brief as a dictionary.
        """
        logger.info(f"[{self.name}] Analyzing product documentation ({len(product_text)} chars)")

        user_prompt = f"""\
Please analyze the following product documentation and create a comprehensive \
product brief in JSON format.

--- PRODUCT DOCUMENTATION ---
{product_text}
--- END DOCUMENTATION ---

Extract all key information including features, pricing, USPs, subscription \
mechanisms, and value propositions. Output only valid JSON.\
"""

        response = await self.call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=4096,
        )

        result = self.parse_json(response)
        logger.info(f"[{self.name}] Product brief created: {result.get('product_name', 'Unknown')}")
        return result
