"""Serial LLM workflow orchestration: KW → RKW → SCN → ALT → MAP."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from ..config import NodeConfig, Settings
from ..llm_client import BaseLLMClient
from ..prompts import load_prompt

logger = logging.getLogger(__name__)


@dataclass
class StepDef:
    """Definition of a single workflow step."""

    name: str  # e.g. "kw"
    system_prompt: str  # template name for system (without .txt)
    user_prompt: str  # template name for user (without .txt)
    node_config: NodeConfig = field(default_factory=NodeConfig)


@dataclass
class WorkflowResult:
    mindmap_markdown: str
    step_outputs: dict[str, str] = field(default_factory=dict)


async def _call_with_retry(
    client: BaseLLMClient,
    system: str,
    user: str,
    *,
    model: Optional[str],
    temperature: Optional[float],
    timeout: Optional[int],
    step_name: str,
    request_id: str,
) -> str:
    """Call LLM with a single retry on failure."""
    for attempt in (1, 2):
        try:
            t0 = time.monotonic()
            result = await client.chat(
                system,
                user,
                model=model,
                temperature=temperature,
                timeout=timeout,
            )
            elapsed = time.monotonic() - t0
            logger.info(
                "step=%s attempt=%d elapsed=%.2fs ok",
                step_name,
                attempt,
                elapsed,
                extra={"request_id": request_id},
            )
            return result
        except Exception:
            if attempt == 2:
                logger.exception(
                    "step=%s attempt=%d failed, giving up",
                    step_name,
                    attempt,
                    extra={"request_id": request_id},
                )
                raise
            logger.warning(
                "step=%s attempt=%d failed, retrying",
                step_name,
                attempt,
                extra={"request_id": request_id},
            )
    # unreachable
    raise RuntimeError("retry logic error")


async def run_workflow(
    settings: Settings,
    client: BaseLLMClient,
    reqcons: str,
    qchar: str,
    ppc: str,
    request_id: str,
) -> WorkflowResult:
    """Execute the full KW→RKW→SCN→ALT→MAP pipeline."""

    steps: list[StepDef] = [
        StepDef("kw", "kw_system", "kw_user", settings.node_kw),
        StepDef("rkw", "rkw_system", "rkw_user", settings.node_rkw),
        StepDef("scn", "scn_system", "scn_user", settings.node_scn),
        StepDef("alt", "alt_system", "alt_user", settings.node_alt),
        StepDef("map", "map_system", "map_user", settings.node_map),
    ]

    outputs: dict[str, str] = {}
    render_vars: dict[str, str] = {"reqcons": reqcons, "qchar": qchar, "ppc": ppc}

    for step in steps:
        # Render prompts with all accumulated outputs
        system_text = load_prompt(settings.prompts_dir, step.system_prompt, **render_vars)
        user_text = load_prompt(settings.prompts_dir, step.user_prompt, **render_vars)

        result = await _call_with_retry(
            client,
            system_text,
            user_text,
            model=step.node_config.model,
            temperature=step.node_config.temperature,
            timeout=settings.llm_timeout_seconds,
            step_name=step.name,
            request_id=request_id,
        )

        outputs[step.name] = result
        render_vars[f"{step.name}_output"] = result

    mindmap = outputs.get("map", "")

    # Validation: if final output empty, retry MAP once more
    if not mindmap.strip():
        logger.warning(
            "MAP output empty, retrying MAP step",
            extra={"request_id": request_id},
        )
        map_step = steps[-1]
        system_text = load_prompt(settings.prompts_dir, map_step.system_prompt, **render_vars)
        user_text = load_prompt(settings.prompts_dir, map_step.user_prompt, **render_vars)
        mindmap = await _call_with_retry(
            client,
            system_text,
            user_text,
            model=map_step.node_config.model,
            temperature=map_step.node_config.temperature,
            timeout=settings.llm_timeout_seconds,
            step_name="map_retry",
            request_id=request_id,
        )
        if not mindmap.strip():
            raise RuntimeError("MAP step returned empty output after retry")

    return WorkflowResult(mindmap_markdown=mindmap, step_outputs=outputs)
