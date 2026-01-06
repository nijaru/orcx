"""Unit tests for router module."""

import pytest

from orcx.errors import InvalidModelFormatError
from orcx.router import expand_alias, extract_provider, validate_model_format


class TestExtractProvider:
    """Tests for extract_provider function."""

    def test_extracts_provider_from_slash_format(self) -> None:
        """Should extract provider from model string."""
        assert extract_provider("openrouter/deepseek/deepseek-v3.2") == "openrouter"
        assert extract_provider("anthropic/claude-sonnet-4") == "anthropic"
        assert extract_provider("openai/gpt-4o") == "openai"

    def test_returns_unknown_for_no_slash(self) -> None:
        """Should return 'unknown' when no slash in model."""
        assert extract_provider("gpt-4o") == "unknown"


class TestValidateModelFormat:
    """Tests for validate_model_format function."""

    def test_valid_formats(self) -> None:
        """Valid model formats should not raise."""
        validate_model_format("openai/gpt-4o")
        validate_model_format("anthropic/claude-sonnet-4")
        validate_model_format("openrouter/deepseek/deepseek-v3.2")

    def test_missing_slash_raises(self) -> None:
        """Model without slash should raise InvalidModelFormatError."""
        with pytest.raises(InvalidModelFormatError) as exc:
            validate_model_format("gpt-4o")
        assert "gpt-4o" in str(exc.value)

    def test_empty_provider_raises(self) -> None:
        """Empty provider should raise InvalidModelFormatError."""
        with pytest.raises(InvalidModelFormatError):
            validate_model_format("/gpt-4o")

    def test_empty_model_raises(self) -> None:
        """Empty model name should raise InvalidModelFormatError."""
        with pytest.raises(InvalidModelFormatError):
            validate_model_format("openai/")


class TestExpandAlias:
    """Tests for expand_alias function."""

    def test_expands_configured_alias(self, temp_config_dir) -> None:
        """Should expand alias to full model path."""
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("""
aliases:
  ds: openrouter/deepseek/deepseek-v3.2
  claude: anthropic/claude-sonnet-4
""")
        assert expand_alias("ds") == "openrouter/deepseek/deepseek-v3.2"
        assert expand_alias("claude") == "anthropic/claude-sonnet-4"

    def test_returns_unchanged_if_no_alias(self, temp_config_dir) -> None:
        """Should return model unchanged if no alias configured."""
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("""
aliases:
  ds: openrouter/deepseek/deepseek-v3.2
""")
        assert expand_alias("anthropic/claude-sonnet-4") == "anthropic/claude-sonnet-4"

    def test_returns_unchanged_if_no_aliases(self, temp_config_dir) -> None:
        """Should return model unchanged when no aliases configured."""
        assert expand_alias("openai/gpt-4o") == "openai/gpt-4o"
