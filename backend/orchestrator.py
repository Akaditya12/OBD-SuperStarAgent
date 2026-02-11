"""Pipeline orchestrator -- chains all 6 agents with feedback loop."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Awaitable

from backend.agents import (
    EvalPanelAgent,
    MarketResearcherAgent,
    ProductAnalyzerAgent,
    ScriptWriterAgent,
)
from backend.config import EVAL_FEEDBACK_ROUNDS

logger = logging.getLogger(__name__)

# Type for progress callback: (agent_name, status, data)
ProgressCallback = Callable[[str, str, dict[str, Any]], Awaitable[None]]

# Maximum characters of product text to send to the LLM
MAX_PRODUCT_TEXT_CHARS = 50_000


async def _noop_callback(agent: str, status: str, data: dict[str, Any]) -> None:
    """Default no-op progress callback."""
    pass


class PipelineOrchestrator:
    """Orchestrates the OBD script generation pipeline.

    Pipeline flow:
    1. Product Analyzer -> product brief
    2. Market Researcher -> market analysis
    3. Script Writer -> initial scripts
    4. Eval Panel -> feedback
    5. Script Writer (revision) -> final scripts
    """

    def __init__(
        self,
        provider: str | None = None,
        on_progress: ProgressCallback | None = None,
    ):
        self.provider = provider
        self.on_progress = on_progress or _noop_callback

        # Initialize agents (scripts-only pipeline)
        self.product_analyzer = ProductAnalyzerAgent(provider=provider)
        self.market_researcher = MarketResearcherAgent(provider=provider)
        self.script_writer = ScriptWriterAgent(provider=provider)
        self.eval_panel = EvalPanelAgent(provider=provider)

    async def run(
        self,
        product_text: str,
        country: str,
        telco: str,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Execute the full pipeline.

        Args:
            product_text: Raw product documentation text.
            country: Target country name.
            telco: Telco operator name.
            language: Optional target language override.

        Returns:
            Complete pipeline results including all intermediate outputs.
        """
        session_id = str(uuid.uuid4())[:8]
        results: dict[str, Any] = {"session_id": session_id}

        # Truncate oversized product text to avoid token limits
        original_len = len(product_text)
        if original_len > MAX_PRODUCT_TEXT_CHARS:
            product_text = product_text[:MAX_PRODUCT_TEXT_CHARS]
            logger.warning(
                f"Product text truncated from {original_len} to "
                f"{MAX_PRODUCT_TEXT_CHARS} chars"
            )

        try:
            # ── Step 1: Product Analysis ──
            await self.on_progress("ProductAnalyzer", "started", {
                "message": "Analyzing product documentation..."
            })
            product_brief = await self.product_analyzer.run(product_text=product_text)
            results["product_brief"] = product_brief
            await self.on_progress("ProductAnalyzer", "completed", {
                "message": f"Product analyzed: {product_brief.get('product_name', 'Unknown')}",
                "data": product_brief,
            })

            # ── Step 2: Market Research ──
            await self.on_progress("MarketResearcher", "started", {
                "message": f"Researching market: {country} / {telco}..."
            })
            market_analysis = await self.market_researcher.run(
                country=country,
                telco=telco,
                product_brief=product_brief,
            )
            results["market_analysis"] = market_analysis
            await self.on_progress("MarketResearcher", "completed", {
                "message": "Market analysis complete",
                "data": market_analysis,
            })

            # ── Step 3: Script Generation ──
            await self.on_progress("ScriptWriter", "started", {
                "message": "Generating OBD script variants..."
            })
            scripts = await self.script_writer.run(
                product_brief=product_brief,
                market_analysis=market_analysis,
            )
            results["initial_scripts"] = scripts
            await self.on_progress("ScriptWriter", "completed", {
                "message": f"Generated {len(scripts.get('scripts', []))} script variants",
                "data": scripts,
            })

            # ── Step 4 & 5: Evaluation + Revision Loop ──
            final_scripts = scripts
            for round_num in range(EVAL_FEEDBACK_ROUNDS):
                round_label = f"(round {round_num + 1}/{EVAL_FEEDBACK_ROUNDS})"

                # Evaluate
                await self.on_progress("EvalPanel", "started", {
                    "message": f"Evaluation panel reviewing scripts {round_label}..."
                })
                evaluation = await self.eval_panel.run(
                    scripts=final_scripts,
                    product_brief=product_brief,
                    market_analysis=market_analysis,
                )
                results[f"evaluation_round_{round_num + 1}"] = evaluation
                await self.on_progress("EvalPanel", "completed", {
                    "message": f"Evaluation complete {round_label}",
                    "data": evaluation,
                })

                # Revise
                await self.on_progress("ScriptWriter", "started", {
                    "message": f"Revising scripts based on feedback {round_label}..."
                })
                final_scripts = await self.script_writer.run(
                    product_brief=product_brief,
                    market_analysis=market_analysis,
                    feedback=evaluation,
                    previous_scripts=final_scripts,
                )
                results[f"revised_scripts_round_{round_num + 1}"] = final_scripts
                await self.on_progress("ScriptWriter", "completed", {
                    "message": f"Scripts revised {round_label}",
                    "data": final_scripts,
                })

            results["final_scripts"] = final_scripts

            # ── Voice Selection & Audio skipped for now ──
            await self.on_progress("VoiceSelector", "completed", {
                "message": "Skipped (audio generation disabled)",
            })
            await self.on_progress("AudioProducer", "completed", {
                "message": "Skipped (audio generation disabled)",
            })

            # ── Pipeline Complete ──
            await self.on_progress("Pipeline", "completed", {
                "message": "Pipeline complete! Scripts are ready for review.",
                "session_id": session_id,
            })

        except Exception as e:
            logger.exception(f"Pipeline failed: {e}")
            await self.on_progress("Pipeline", "error", {
                "message": f"Pipeline failed: {str(e)}",
                "error": str(e),
            })
            results["error"] = str(e)

        return results
