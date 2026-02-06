"""LLM client interface."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Wrapper that carries content + optional token usage."""

    content: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class BaseLLMClient(abc.ABC):
    """Thin abstraction so the provider can be swapped via config."""

    @abc.abstractmethod
    async def chat(
        self,
        system: str,
        user: str,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
    ) -> LLMResponse:
        """Return the assistant message content and token usage."""
