"""Individual step functions matching spec §4.1 signatures.

Each function renders prompts, calls the LLM, and returns the raw output string.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..llm.base import BaseLLMClient, LLMResponse
from ..prompts import load_prompt


async def extract_keywords(
    client: BaseLLMClient,
    prompts_dir: Path,
    reqcons: str,
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
) -> LLMResponse:
    """KW – extract keywords (CSV, <=10)."""
    system = load_prompt(prompts_dir, "kw_system", reqcons=reqcons)
    user = load_prompt(prompts_dir, "kw_user", reqcons=reqcons)
    return await client.chat(system, user, model=model, temperature=temperature, timeout=timeout)


async def derive_factors(
    client: BaseLLMClient,
    prompts_dir: Path,
    reqcons: str,
    keywords_csv: str,
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
) -> LLMResponse:
    """RKW – derive factors from keywords + requirement (>=20)."""
    system = load_prompt(prompts_dir, "rkw_system", reqcons=reqcons, kw_output=keywords_csv)
    user = load_prompt(prompts_dir, "rkw_user", reqcons=reqcons, kw_output=keywords_csv)
    return await client.chat(system, user, model=model, temperature=temperature, timeout=timeout)


async def generate_scenarios(
    client: BaseLLMClient,
    prompts_dir: Path,
    reqcons: str,
    factors_md: str,
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
) -> LLMResponse:
    """SCN – generate usage scenarios (>=15, must include smartphone)."""
    system = load_prompt(prompts_dir, "scn_system", reqcons=reqcons, rkw_output=factors_md)
    user = load_prompt(prompts_dir, "scn_user", reqcons=reqcons, rkw_output=factors_md)
    return await client.chat(system, user, model=model, temperature=temperature, timeout=timeout)


async def generate_alternatives(
    client: BaseLLMClient,
    prompts_dir: Path,
    reqcons: str,
    factors_md: str,
    scenarios_md: str,
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
) -> LLMResponse:
    """ALT – alternative / exception / misuse / env-abnormal (<=18)."""
    system = load_prompt(
        prompts_dir, "alt_system",
        reqcons=reqcons, rkw_output=factors_md, scn_output=scenarios_md,
    )
    user = load_prompt(
        prompts_dir, "alt_user",
        reqcons=reqcons, rkw_output=factors_md, scn_output=scenarios_md,
    )
    return await client.chat(system, user, model=model, temperature=temperature, timeout=timeout)


async def generate_mindmap(
    client: BaseLLMClient,
    prompts_dir: Path,
    reqcons: str,
    qchar: str,
    ppc: str,
    keywords_csv: str,
    factors_md: str,
    scenarios_md: str,
    alt_md: str,
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
) -> LLMResponse:
    """MAP – final Mindmap Markdown (YAML front-matter, 4-level, internal refs hidden)."""
    render = dict(
        reqcons=reqcons, qchar=qchar, ppc=ppc,
        kw_output=keywords_csv, rkw_output=factors_md,
        scn_output=scenarios_md, alt_output=alt_md,
    )
    system = load_prompt(prompts_dir, "map_system", **render)
    user = load_prompt(prompts_dir, "map_user", **render)
    return await client.chat(system, user, model=model, temperature=temperature, timeout=timeout)
