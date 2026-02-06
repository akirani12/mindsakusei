"""LLM client abstraction – OpenAI today, Azure OpenAI tomorrow."""

from __future__ import annotations

import abc
import logging
from typing import Optional

import openai

from .config import Settings

logger = logging.getLogger(__name__)


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
    ) -> str:
        """Return the assistant message content."""


class OpenAIClient(BaseLLMClient):
    def __init__(self, settings: Settings) -> None:
        kwargs: dict = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self._client = openai.AsyncOpenAI(**kwargs)
        self._settings = settings

    async def chat(
        self,
        system: str,
        user: str,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system.strip():
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        resp = await self._client.chat.completions.create(
            model=model or self._settings.llm_default_model,
            messages=messages,
            temperature=temperature if temperature is not None else self._settings.llm_default_temperature,
            timeout=timeout or self._settings.llm_timeout_seconds,
        )
        content = resp.choices[0].message.content or ""
        return content


class AzureOpenAIClient(BaseLLMClient):
    """Azure OpenAI client – swap-in replacement."""

    def __init__(self, settings: Settings) -> None:
        self._client = openai.AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
        self._settings = settings

    async def chat(
        self,
        system: str,
        user: str,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system.strip():
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        resp = await self._client.chat.completions.create(
            model=model or self._settings.azure_openai_deployment or self._settings.llm_default_model,
            messages=messages,
            temperature=temperature if temperature is not None else self._settings.llm_default_temperature,
            timeout=timeout or self._settings.llm_timeout_seconds,
        )
        content = resp.choices[0].message.content or ""
        return content


def create_llm_client(settings: Settings) -> BaseLLMClient:
    """Factory – choose provider based on settings."""
    if settings.llm_provider == "azure":
        logger.info("Using Azure OpenAI client")
        return AzureOpenAIClient(settings)
    logger.info("Using OpenAI client")
    return OpenAIClient(settings)
