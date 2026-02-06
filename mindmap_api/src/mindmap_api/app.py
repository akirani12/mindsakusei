"""FastAPI application – POST /v1/mindmap/generate."""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from .config import Settings
from .llm_client import BaseLLMClient, create_llm_client
from .logging_setup import setup_logging
from .workflow.runner import run_workflow

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    reqcons: str = Field(..., max_length=1000)
    qchar: str = Field(default="")
    ppc: Optional[str] = Field(default=None)


class GenerateResponse(BaseModel):
    mindmap_markdown: str


# ---------------------------------------------------------------------------
# App state (populated during lifespan)
# ---------------------------------------------------------------------------

_settings: Settings | None = None
_llm_client: BaseLLMClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _settings, _llm_client
    setup_logging()
    _settings = Settings()  # type: ignore[call-arg]
    _llm_client = create_llm_client(_settings)
    logger.info("Application started")
    yield
    logger.info("Application shutting down")


app = FastAPI(title="Mindmap Generator API", version="0.1.0", lifespan=lifespan)

# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------


def _verify_api_key(x_api_key: str = Header(...)) -> None:
    assert _settings is not None
    if x_api_key != _settings.app_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@app.post(
    "/v1/mindmap/generate",
    response_model=GenerateResponse,
    dependencies=[],
)
async def generate_mindmap(
    body: GenerateRequest,
    x_api_key: str = Header(...),
) -> GenerateResponse:
    assert _settings is not None and _llm_client is not None

    _verify_api_key(x_api_key)

    request_id = uuid.uuid4().hex[:12]
    logger.info(
        "request_id=%s reqcons_len=%d",
        request_id,
        len(body.reqcons),
        extra={"request_id": request_id},
    )

    try:
        result = await asyncio.wait_for(
            run_workflow(
                _settings,
                _llm_client,
                reqcons=body.reqcons,
                qchar=body.qchar,
                ppc=body.ppc or "",
                request_id=request_id,
            ),
            timeout=_settings.api_timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.error(
            "request_id=%s timed out after %ds",
            request_id,
            _settings.api_timeout_seconds,
            extra={"request_id": request_id},
        )
        raise HTTPException(status_code=500, detail="Request timed out")
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "request_id=%s workflow failed",
            request_id,
            extra={"request_id": request_id},
        )
        raise HTTPException(status_code=500, detail="Internal workflow error")

    return GenerateResponse(mindmap_markdown=result.mindmap_markdown)
