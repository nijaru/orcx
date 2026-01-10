"""Configuration management for orcx."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError

from orcx.errors import ConfigFileError
from orcx.schema import ProviderPrefs

CONFIG_DIR = Path.home() / ".config" / "orcx"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
AGENTS_FILE = CONFIG_DIR / "agents.yaml"


class ProviderKeys(BaseModel):
    """API keys for LLM providers."""

    openai: str | None = None
    anthropic: str | None = None
    deepseek: str | None = None
    google: str | None = None
    mistral: str | None = None
    groq: str | None = None
    together: str | None = None
    openrouter: str | None = None


class OrcxConfig(BaseModel):
    """Root configuration for orcx."""

    default_agent: str | None = None
    default_model: str | None = None
    default_provider_prefs: ProviderPrefs | None = None
    keys: ProviderKeys = Field(default_factory=ProviderKeys)
    aliases: dict[str, str] = Field(default_factory=dict)


ENV_KEY_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "google": "GOOGLE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "together": "TOGETHER_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def load_config() -> OrcxConfig:
    """Load config from file, with env var overrides for API keys."""
    config = OrcxConfig()

    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open() as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigFileError(
                f"Invalid YAML in config file: {CONFIG_FILE}",
                details=str(e),
            ) from e

        if data is None:
            data = {}

        if not isinstance(data, dict):
            raise ConfigFileError(
                f"Config file must be a YAML mapping: {CONFIG_FILE}",
                details=f"Got {type(data).__name__} instead",
            )

        try:
            config = OrcxConfig.model_validate(data)
        except ValidationError as e:
            errors = "; ".join(
                f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()
            )
            raise ConfigFileError(
                f"Invalid config file format: {CONFIG_FILE}",
                details=errors,
            ) from e

    config.keys = _resolve_keys(config.keys)

    # Validate provider prefs and print warnings
    if config.default_provider_prefs:
        import sys

        from orcx.schema import validate_provider_prefs

        for warning in validate_provider_prefs(
            config.default_provider_prefs, "default_provider_prefs"
        ):
            print(f"Warning: {warning}", file=sys.stderr)

    return config


def _resolve_keys(file_keys: ProviderKeys) -> ProviderKeys:
    """Resolve API keys: env vars take precedence over config file."""
    resolved = {}
    for provider, env_var in ENV_KEY_MAP.items():
        env_value = os.environ.get(env_var)
        file_value = getattr(file_keys, provider, None)
        resolved[provider] = env_value or file_value
    return ProviderKeys(**resolved)


def get_api_key(provider: str) -> str | None:
    """Get API key for a provider."""
    config = load_config()
    return getattr(config.keys, provider, None)


def ensure_config_dir() -> Path:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def save_config(config: OrcxConfig) -> None:
    """Save config to file."""
    ensure_config_dir()
    with CONFIG_FILE.open("w") as f:
        yaml.safe_dump(config.model_dump(exclude_none=True), f, default_flow_style=False)
