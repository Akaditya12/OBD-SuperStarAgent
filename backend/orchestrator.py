"""Pipeline orchestrator -- chains all 6 agents with feedback loop."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Awaitable

from backend.agents import (
    AudioProducerAgent,
    EvalPanelAgent,
    MarketResearcherAgent,
    ProductAnalyzerAgent,
    ScriptWriterAgent,
    VoiceSelectorAgent,
)
from backend.config import ELEVENLABS_API_KEY, EVAL_FEEDBACK_ROUNDS

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

        # Initialize agents
        self.product_analyzer = ProductAnalyzerAgent(provider=provider)
        self.market_researcher = MarketResearcherAgent(provider=provider)
        self.script_writer = ScriptWriterAgent(provider=provider)
        self.eval_panel = EvalPanelAgent(provider=provider)
        self.voice_selector = VoiceSelectorAgent(provider=provider)
        self.audio_producer = AudioProducerAgent(provider=provider)

    async def run(
        self,
        product_text: str,
        country: str,
        telco: str,
        language: str | None = None,
        tts_engine: str | None = None,
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
            pipeline_start = time.monotonic()

            # ── Steps 1 & 2: Product Analysis + Market Research (PARALLEL) ──
            await self.on_progress("ProductAnalyzer", "started", {
                "message": "Analyzing product documentation..."
            })
            await self.on_progress("MarketResearcher", "started", {
                "message": f"Researching market: {country} / {telco}..."
            })

            async def _run_product_analysis() -> dict[str, Any]:
                t0 = time.monotonic()
                brief = await self.product_analyzer.run(product_text=product_text)
                elapsed = time.monotonic() - t0
                logger.info(f"[ProductAnalyzer] completed in {elapsed:.1f}s")
                return brief

            async def _run_market_research() -> dict[str, Any]:
                t0 = time.monotonic()
                # Market research doesn't need product_brief -- it uses country/telco
                # We pass a minimal brief so it has product context
                analysis = await self.market_researcher.run(
                    country=country,
                    telco=telco,
                    product_brief={"product_name": "pending", "description": product_text[:500]},
                )
                elapsed = time.monotonic() - t0
                logger.info(f"[MarketResearcher] completed in {elapsed:.1f}s")
                return analysis

            product_brief, market_analysis = await asyncio.gather(
                _run_product_analysis(),
                _run_market_research(),
            )

            results["product_brief"] = product_brief
            await self.on_progress("ProductAnalyzer", "completed", {
                "message": f"Product analyzed: {product_brief.get('product_name', 'Unknown')}",
                "data": product_brief,
                "system_prompt": self.product_analyzer.last_system_prompt,
                "user_prompt": self.product_analyzer.last_user_prompt,
            })

            results["market_analysis"] = market_analysis
            await self.on_progress("MarketResearcher", "completed", {
                "message": "Market analysis complete",
                "data": market_analysis,
                "system_prompt": self.market_researcher.last_system_prompt,
                "user_prompt": self.market_researcher.last_user_prompt,
            })

            # ── Step 3: Script Generation ──
            await self.on_progress("ScriptWriter", "started", {
                "message": "Generating OBD script variants..."
            })
            scripts = await self.script_writer.run(
                product_brief=product_brief,
                market_analysis=market_analysis,
                language_override=language,
            )
            results["initial_scripts"] = scripts
            await self.on_progress("ScriptWriter", "completed", {
                "message": f"Generated {len(scripts.get('scripts', []))} script variants",
                "data": scripts,
                "system_prompt": self.script_writer.last_system_prompt,
                "user_prompt": self.script_writer.last_user_prompt,
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
                    "system_prompt": self.eval_panel.last_system_prompt,
                    "user_prompt": self.eval_panel.last_user_prompt,
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
                    language_override=language,
                )
                results[f"revised_scripts_round_{round_num + 1}"] = final_scripts
                await self.on_progress("ScriptWriter", "completed", {
                    "message": f"Scripts revised {round_label}",
                    "data": final_scripts,
                    "system_prompt": self.script_writer.last_system_prompt,
                    "user_prompt": self.script_writer.last_user_prompt,
                })

            results["final_scripts"] = final_scripts

            # ── Step 6: Voice Selection ──
            await self.on_progress("VoiceSelector", "started", {
                "message": "Selecting optimal ElevenLabs voice and parameters..."
            })
            voice_selection = await self.voice_selector.run(
                scripts=final_scripts,
                market_analysis=market_analysis,
                country=country,
                language=language,
            )
            results["voice_selection"] = voice_selection
            await self.on_progress("VoiceSelector", "completed", {
                "message": f"Voice selected: {voice_selection.get('selected_voice', {}).get('name', 'Unknown')}",
                "data": voice_selection,
                "system_prompt": self.voice_selector.last_system_prompt,
                "user_prompt": self.voice_selector.last_user_prompt,
            })

            # ── Step 7: Audio Production ──
            await self.on_progress("AudioProducer", "started", {
                "message": "Generating audio recordings..."
            })
            try:
                audio_result = await self.audio_producer.run(
                    scripts=final_scripts,
                    voice_selection=voice_selection,
                    session_id=session_id,
                    country=country,
                    language=language,
                    tts_engine_override=tts_engine,
                )
                results["audio"] = audio_result
                successful = audio_result.get("summary", {}).get("total_generated", 0)
                engine = audio_result.get("tts_engine", "unknown")
                await self.on_progress("AudioProducer", "completed", {
                    "message": f"Generated {successful} audio files via {engine}",
                    "data": {"summary": audio_result.get("summary", {})},
                })
            except Exception as audio_err:
                logger.error(f"Audio production failed: {audio_err}")
                await self.on_progress("AudioProducer", "completed", {
                    "message": f"Audio generation failed: {str(audio_err)}. Scripts are still available.",
                })

            # ── Pipeline Complete ──
            total_time = time.monotonic() - pipeline_start
            logger.info(f"Pipeline completed in {total_time:.1f}s")
            await self.on_progress("Pipeline", "completed", {
                "message": f"Pipeline complete in {total_time:.0f}s! Scripts and voice recommendation are ready.",
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
