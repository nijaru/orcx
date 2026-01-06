"""Pytest configuration and fixtures."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary config directory for tests."""
    config_dir = tmp_path / ".config" / "orcx"
    config_dir.mkdir(parents=True)

    # Patch both config and registry modules since they import these at module level
    monkeypatch.setattr("orcx.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("orcx.config.CONFIG_FILE", config_dir / "config.yaml")
    monkeypatch.setattr("orcx.config.AGENTS_FILE", config_dir / "agents.yaml")
    monkeypatch.setattr("orcx.registry.AGENTS_FILE", config_dir / "agents.yaml")

    return config_dir


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Remove all API key env vars for isolated testing."""
    env_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "DEEPSEEK_API_KEY",
        "GOOGLE_API_KEY",
        "MISTRAL_API_KEY",
        "GROQ_API_KEY",
        "TOGETHER_API_KEY",
        "OPENROUTER_API_KEY",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    yield


@pytest.fixture
def mock_litellm_response() -> MagicMock:
    """Create a mock litellm completion response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "Test response"
    response.model = "test/model"
    response.usage = MagicMock()
    response.usage.prompt_tokens = 10
    response.usage.completion_tokens = 20
    response.usage.total_tokens = 30
    return response
