"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class NodeConfig(BaseSettings):
    """Per-workflow-node overrides (model / temperature)."""

    model: Optional[str] = None
    temperature: Optional[float] = None


class Settings(BaseSettings):
    model_config = {"env_prefix": "", "env_nested_delimiter": "__"}

    # --- API ---
    app_api_key: str = Field(..., description="API key for X-API-Key auth")

    # --- OpenAI ---
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_base_url: Optional[str] = Field(
        None, description="Override base URL (for Azure OpenAI etc.)"
    )

    # --- LLM defaults ---
    llm_default_model: str = Field("gpt-4o-mini", description="Default model name")
    llm_default_temperature: float = Field(0.7, description="Default temperature")
    llm_timeout_seconds: int = Field(60, description="Per-call timeout for LLM")

    # --- Per-node overrides (env: NODE_KW__MODEL, NODE_KW__TEMPERATURE …) ---
    node_kw: NodeConfig = Field(default_factory=NodeConfig)
    node_rkw: NodeConfig = Field(default_factory=NodeConfig)
    node_scn: NodeConfig = Field(default_factory=NodeConfig)
    node_alt: NodeConfig = Field(default_factory=NodeConfig)
    node_map: NodeConfig = Field(default_factory=NodeConfig)

    # --- Workflow ---
    api_timeout_seconds: int = Field(180, description="Overall API timeout")

    # --- Prompts ---
    prompts_dir: Path = Field(
        default=_PROJECT_ROOT / "prompts",
        description="Directory containing prompt .txt files",
    )

    # --- LLM provider ---
    llm_provider: str = Field(
        "openai", description="LLM provider: 'openai' or 'azure'"
    )

    # Azure-specific (only used when llm_provider == 'azure')
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_deployment: Optional[str] = None
