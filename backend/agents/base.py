"""Base agent class with LLM abstraction supporting Azure OpenAI."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from openai import AsyncAzureOpenAI

from backend.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
    DEFAULT_LLM_PROVIDER,
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all pipeline agents.

    Provides a unified interface for calling Azure OpenAI,
    with structured JSON output parsing and progress callbacks.
    """

    name: str = "BaseAgent"
    description: str = ""

    def __init__(self, provider: str | None = None):
        self.provider = provider or DEFAULT_LLM_PROVIDER
        self._client: AsyncAzureOpenAI | None = None

    @property
    def client(self) -> AsyncAzureOpenAI:
        if self._client is None:
            self._client = AsyncAzureOpenAI(
                api_key=AZURE_OPENAI_API_KEY,
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_version=AZURE_OPENAI_API_VERSION,
            )
        return self._client

    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        json_output: bool = True,
    ) -> str:
        """Call Azure OpenAI and return the response text."""
        logger.info(f"[{self.name}] Calling Azure OpenAI ({AZURE_OPENAI_DEPLOYMENT})")

        kwargs: dict[str, Any] = {}
        if json_output:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            max_completion_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **kwargs,
        )
        text = response.choices[0].message.content or ""
        logger.info(f"[{self.name}] Azure OpenAI response: {len(text)} chars")
        return text

    def parse_json(self, text: str) -> dict[str, Any]:
        """Extract and parse JSON from LLM response text.

        Handles cases where the LLM wraps JSON in markdown code blocks.
        """
        cleaned = text.strip()
        # Strip markdown code fences if present
        if cleaned.startswith("```"):
            first_newline = cleaned.index("\n")
            cleaned = cleaned[first_newline + 1 :]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error(f"[{self.name}] Failed to parse JSON from LLM response")
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(cleaned[start:end])
            raise

    @abstractmethod
    async def run(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the agent's task. Must be implemented by subclasses."""
        ...
