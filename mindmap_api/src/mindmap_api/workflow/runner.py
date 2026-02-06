"""Serial LLM workflow orchestration: KW → RKW → SCN → ALT → MAP."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from ..config import NodeConfig, Settings
from ..llm.base import BaseLLMClient, LLMResponse
from .validators import check_keywords_count, check_min_items, check_not_empty

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    mindmap_markdown: str
    step_outputs: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------------------------

async def _call_with_retry(
    fn: Callable[..., Awaitable[LLMResponse]],
    *args: Any,
    step_name: str,
    request_id: str,
    **kwargs: Any,
) -> LLMResponse:
    """Call *fn* with a single retry on failure. Logs elapsed time and token usage."""
    for attempt in (1, 2):
        try:
            t0 = time.monotonic()
            resp = await fn(*args, **kwargs)
            elapsed = time.monotonic() - t0
            token_info = ""
            if resp.total_tokens is not None:
                token_info = f" tokens={resp.total_tokens}(p={resp.prompt_tokens},c={resp.completion_tokens})"
            logger.info(
                "step=%s attempt=%d elapsed=%.2fs ok%s",
                step_name,
                attempt,
                elapsed,
                token_info,
                extra={"request_id": request_id},
            )
            return resp
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
    raise RuntimeError("retry logic error")  # unreachable


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

async def run_workflow(
    settings: Settings,
    client: BaseLLMClient,
    reqcons: str,
    qchar: str,
    ppc: str,
    request_id: str,
) -> WorkflowResult:
    """Execute the full KW→RKW→SCN→ALT→MAP pipeline using step functions."""
    from .steps import (
        extract_keywords,
        derive_factors,
        generate_alternatives,
        generate_mindmap,
        generate_scenarios,
    )

    def _node_kwargs(nc: NodeConfig) -> dict:
        return dict(model=nc.model, temperature=nc.temperature, timeout=settings.llm_timeout_seconds)

    outputs: dict[str, str] = {}

    # --- KW ---
    resp = await _call_with_retry(
        extract_keywords, client, settings.prompts_dir, reqcons,
        step_name="kw", request_id=request_id,
        **_node_kwargs(settings.node_kw),
    )
    outputs["kw"] = resp.content
    check_keywords_count(resp.content, request_id=request_id)

    # --- RKW ---
    resp = await _call_with_retry(
        derive_factors, client, settings.prompts_dir, reqcons, outputs["kw"],
        step_name="rkw", request_id=request_id,
        **_node_kwargs(settings.node_rkw),
    )
    outputs["rkw"] = resp.content
    check_min_items(resp.content, min_expected=20, step_name="RKW", request_id=request_id)

    # --- SCN ---
    resp = await _call_with_retry(
        generate_scenarios, client, settings.prompts_dir, reqcons, outputs["rkw"],
        step_name="scn", request_id=request_id,
        **_node_kwargs(settings.node_scn),
    )
    outputs["scn"] = resp.content
    check_min_items(resp.content, min_expected=15, step_name="SCN", request_id=request_id)

    # --- ALT ---
    resp = await _call_with_retry(
        generate_alternatives, client, settings.prompts_dir, reqcons, outputs["rkw"], outputs["scn"],
        step_name="alt", request_id=request_id,
        **_node_kwargs(settings.node_alt),
    )
    outputs["alt"] = resp.content

    # --- MAP ---
    resp = await _call_with_retry(
        generate_mindmap, client, settings.prompts_dir,
        reqcons, qchar, ppc, outputs["kw"], outputs["rkw"], outputs["scn"], outputs["alt"],
        step_name="map", request_id=request_id,
        **_node_kwargs(settings.node_map),
    )
    outputs["map"] = resp.content

    # Validation: if final output empty, retry MAP once more
    if not check_not_empty(outputs["map"], step_name="MAP", request_id=request_id):
        logger.warning("MAP output empty, retrying MAP step", extra={"request_id": request_id})
        resp = await _call_with_retry(
            generate_mindmap, client, settings.prompts_dir,
            reqcons, qchar, ppc, outputs["kw"], outputs["rkw"], outputs["scn"], outputs["alt"],
            step_name="map_retry", request_id=request_id,
            **_node_kwargs(settings.node_map),
        )
        outputs["map"] = resp.content
        if not outputs["map"].strip():
            raise RuntimeError("MAP step returned empty output after retry")

    return WorkflowResult(mindmap_markdown=outputs["map"], step_outputs=outputs)
