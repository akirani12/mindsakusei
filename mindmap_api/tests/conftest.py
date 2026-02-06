"""Shared test fixtures."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    """Set minimal env vars so Settings() can be constructed."""
    monkeypatch.setenv("APP_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")


@pytest.fixture()
def mock_llm():
    """Return a mock LLM client that echoes step info."""
    mock_client = AsyncMock()
    call_count = 0

    async def _chat(system, user, *, model=None, temperature=None, timeout=None):
        nonlocal call_count
        call_count += 1
        return f"mock-output-{call_count}"

    mock_client.chat.side_effect = _chat
    return mock_client


@pytest.fixture()
async def client(mock_llm):
    """Async test client – manually inject settings and mock LLM."""
    import mindmap_api.app as app_module
    from mindmap_api.app import app
    from mindmap_api.config import Settings
    from mindmap_api.logging_setup import setup_logging

    setup_logging()
    app_module._settings = Settings()  # type: ignore[call-arg]
    app_module._llm_client = mock_llm

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app_module._settings = None
    app_module._llm_client = None
