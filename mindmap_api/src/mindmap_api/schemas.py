"""Pydantic request / response models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    reqcons: str = Field(..., max_length=1000)
    qchar: str = Field(default="")
    ppc: Optional[str] = Field(default=None)


class GenerateResponse(BaseModel):
    mindmap_markdown: str
