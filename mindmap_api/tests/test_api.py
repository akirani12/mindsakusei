"""Smoke tests for the mindmap API."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_generate_returns_200(client):
    resp = await client.post(
        "/v1/mindmap/generate",
        json={"reqcons": "test requirement"},
        headers={"X-API-Key": "test-key"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "mindmap_markdown" in data
    assert len(data["mindmap_markdown"]) > 0


@pytest.mark.asyncio
async def test_generate_returns_401_bad_key(client):
    resp = await client.post(
        "/v1/mindmap/generate",
        json={"reqcons": "test requirement"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_generate_returns_422_missing_reqcons(client):
    resp = await client.post(
        "/v1/mindmap/generate",
        json={},
        headers={"X-API-Key": "test-key"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_generate_returns_422_reqcons_too_long(client):
    resp = await client.post(
        "/v1/mindmap/generate",
        json={"reqcons": "x" * 1001},
        headers={"X-API-Key": "test-key"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_workflow_produces_nonempty_output(client):
    """The mocked workflow should produce non-empty markdown (step 5 = MAP)."""
    resp = await client.post(
        "/v1/mindmap/generate",
        json={"reqcons": "AI-powered note taking app", "qchar": "student"},
        headers={"X-API-Key": "test-key"},
    )
    assert resp.status_code == 200
    assert resp.json()["mindmap_markdown"] != ""
