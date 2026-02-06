"""FastAPI application – POST /v1/mindmap/generate + Web UI."""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .auth import verify_api_key
from .config import Settings
from .llm import BaseLLMClient, create_llm_client
from .logging_setup import setup_logging
from .schemas import GenerateRequest, GenerateResponse
from .workflow.runner import run_workflow

_PACKAGE_DIR = Path(__file__).resolve().parent

logger = logging.getLogger(__name__)

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
# Static files & Web UI
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory=_PACKAGE_DIR / "static"), name="static")

_index_html = (_PACKAGE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def ui():
    return _index_html


# ---------------------------------------------------------------------------
# API Endpoint
# ---------------------------------------------------------------------------


@app.post(
    "/v1/mindmap/generate",
    response_model=GenerateResponse,
)
async def generate_mindmap(
    body: GenerateRequest,
    x_api_key: str = Header(...),
) -> GenerateResponse:
    assert _settings is not None and _llm_client is not None

    verify_api_key(_settings, x_api_key)

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
