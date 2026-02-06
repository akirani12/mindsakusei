"""OpenAI / Azure OpenAI implementations of BaseLLMClient."""

from __future__ import annotations

import logging
from typing import Optional

import openai

from ..config import Settings
from .base import BaseLLMClient, LLMResponse

logger = logging.getLogger(__name__)


def _build_messages(system: str, user: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system.strip():
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    return messages


def _extract_response(resp) -> LLMResponse:
    content = resp.choices[0].message.content or ""
    usage = resp.usage
    return LLMResponse(
        content=content,
        prompt_tokens=usage.prompt_tokens if usage else None,
        completion_tokens=usage.completion_tokens if usage else None,
        total_tokens=usage.total_tokens if usage else None,
    )


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
    ) -> LLMResponse:
        resp = await self._client.chat.completions.create(
            model=model or self._settings.llm_default_model,
            messages=_build_messages(system, user),
            temperature=temperature if temperature is not None else self._settings.llm_default_temperature,
            timeout=timeout or self._settings.llm_timeout_seconds,
        )
        return _extract_response(resp)


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
    ) -> LLMResponse:
        resp = await self._client.chat.completions.create(
            model=model or self._settings.azure_openai_deployment or self._settings.llm_default_model,
            messages=_build_messages(system, user),
            temperature=temperature if temperature is not None else self._settings.llm_default_temperature,
            timeout=timeout or self._settings.llm_timeout_seconds,
        )
        return _extract_response(resp)


def create_llm_client(settings: Settings) -> BaseLLMClient:
    """Factory – choose provider based on settings."""
    if settings.llm_provider == "azure":
        logger.info("Using Azure OpenAI client")
        return AzureOpenAIClient(settings)
    logger.info("Using OpenAI client")
    return OpenAIClient(settings)
