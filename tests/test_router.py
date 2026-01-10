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


class TestBuildParamsProviderPrefs:
    """Tests for build_params with provider preferences."""

    def test_no_prefs_for_non_openrouter(self, temp_config_dir) -> None:
        """Provider prefs should not be added for non-openrouter models."""
        from orcx.router import build_params
        from orcx.schema import AgentConfig, OrcxRequest, ProviderPrefs

        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("""
default_provider_prefs:
  min_bits: 8
  ignore: [SiliconFlow]
""")
        request = OrcxRequest(prompt="test")
        agent = AgentConfig(
            name="test",
            model="anthropic/claude-sonnet-4",
            provider_prefs=ProviderPrefs(min_bits=16),
        )
        params = build_params(
            request=request,
            agent=agent,
            model="anthropic/claude-sonnet-4",
            messages=[{"role": "user", "content": "hi"}],
            stream=False,
        )
        # No extra_body for non-openrouter
        assert "extra_body" not in params

    def test_global_prefs_applied_for_openrouter(self, temp_config_dir) -> None:
        """Global provider prefs should be applied for openrouter models."""
        from orcx.router import build_params
        from orcx.schema import OrcxRequest

        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("""
default_provider_prefs:
  min_bits: 8
  ignore: [SiliconFlow, DeepInfra]
  sort: price
""")
        request = OrcxRequest(prompt="test")
        params = build_params(
            request=request,
            agent=None,
            model="openrouter/deepseek/deepseek-v3.2",
            messages=[{"role": "user", "content": "hi"}],
            stream=False,
        )
        assert "extra_body" in params
        provider = params["extra_body"]["provider"]
        assert provider["ignore"] == ["SiliconFlow", "DeepInfra"]
        assert provider["sort"] == "price"
        # min_bits=8 should resolve to quantizations
        assert "quantizations" in provider

    def test_agent_prefs_override_global(self, temp_config_dir) -> None:
        """Agent prefs should override global prefs for scalar fields."""
        from orcx.router import build_params
        from orcx.schema import AgentConfig, OrcxRequest, ProviderPrefs

        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("""
default_provider_prefs:
  min_bits: 8
  sort: price
""")
        request = OrcxRequest(prompt="test")
        agent = AgentConfig(
            name="test",
            model="openrouter/test/model",
            provider_prefs=ProviderPrefs(sort="latency"),
        )
        params = build_params(
            request=request,
            agent=agent,
            model="openrouter/test/model",
            messages=[{"role": "user", "content": "hi"}],
            stream=False,
        )
        provider = params["extra_body"]["provider"]
        # Agent sort overrides global
        assert provider["sort"] == "latency"
        # Global min_bits still applied
        assert "quantizations" in provider

    def test_ignore_lists_merged(self, temp_config_dir) -> None:
        """Agent and global ignore lists should be merged."""
        from orcx.router import build_params
        from orcx.schema import AgentConfig, OrcxRequest, ProviderPrefs

        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("""
default_provider_prefs:
  ignore: [SiliconFlow, DeepInfra]
""")
        request = OrcxRequest(prompt="test")
        agent = AgentConfig(
            name="test",
            model="openrouter/test/model",
            provider_prefs=ProviderPrefs(ignore=["Chutes", "Mancer"]),
        )
        params = build_params(
            request=request,
            agent=agent,
            model="openrouter/test/model",
            messages=[{"role": "user", "content": "hi"}],
            stream=False,
        )
        provider = params["extra_body"]["provider"]
        # Union of both lists
        ignore_set = set(provider["ignore"])
        assert ignore_set == {"Chutes", "Mancer", "SiliconFlow", "DeepInfra"}

    def test_agent_prefs_only_when_no_global(self, temp_config_dir) -> None:
        """Agent prefs should work when no global prefs configured."""
        from orcx.router import build_params
        from orcx.schema import AgentConfig, OrcxRequest, ProviderPrefs

        # Empty config
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("")

        request = OrcxRequest(prompt="test")
        agent = AgentConfig(
            name="test",
            model="openrouter/test/model",
            provider_prefs=ProviderPrefs(min_bits=16, prefer=["AtlasCloud"]),
        )
        params = build_params(
            request=request,
            agent=agent,
            model="openrouter/test/model",
            messages=[{"role": "user", "content": "hi"}],
            stream=False,
        )
        provider = params["extra_body"]["provider"]
        assert provider["order"] == ["AtlasCloud"]
        assert provider["allow_fallbacks"] is True

    def test_global_prefs_only_when_no_agent(self, temp_config_dir) -> None:
        """Global prefs should work when no agent prefs configured."""
        from orcx.router import build_params
        from orcx.schema import AgentConfig, OrcxRequest

        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("""
default_provider_prefs:
  min_bits: 8
  prefer: [NovitaAI]
""")
        request = OrcxRequest(prompt="test")
        agent = AgentConfig(name="test", model="openrouter/test/model")
        params = build_params(
            request=request,
            agent=agent,
            model="openrouter/test/model",
            messages=[{"role": "user", "content": "hi"}],
            stream=False,
        )
        provider = params["extra_body"]["provider"]
        assert provider["order"] == ["NovitaAI"]
