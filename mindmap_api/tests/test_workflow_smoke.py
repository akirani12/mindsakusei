"""Smoke tests for the workflow runner (no HTTP layer)."""

from __future__ import annotations

import pytest

from mindmap_api.config import Settings
from mindmap_api.workflow.runner import run_workflow


@pytest.mark.asyncio
async def test_workflow_returns_nonempty_mindmap(mock_llm):
    settings = Settings()  # type: ignore[call-arg]
    result = await run_workflow(
        settings,
        mock_llm,
        reqcons="ECサイトの商品検索機能",
        qchar="一般消費者",
        ppc="",
        request_id="test-123",
    )
    assert result.mindmap_markdown != ""
    assert "mock-output" in result.mindmap_markdown


@pytest.mark.asyncio
async def test_workflow_runs_all_five_steps(mock_llm):
    settings = Settings()  # type: ignore[call-arg]
    result = await run_workflow(
        settings,
        mock_llm,
        reqcons="テスト要件",
        qchar="",
        ppc="3",
        request_id="test-456",
    )
    assert set(result.step_outputs.keys()) == {"kw", "rkw", "scn", "alt", "map"}
    assert mock_llm.chat.call_count == 5
