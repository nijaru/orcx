"""Unit tests for config module."""

import pytest

from orcx.config import OrcxConfig, ProviderKeys, _resolve_keys, load_config


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_missing_file_returns_defaults(self, temp_config_dir) -> None:
        """load_config with missing file should return default config."""
        config = load_config()
        assert isinstance(config, OrcxConfig)
        assert config.default_agent is None
        assert config.default_model is None
        assert isinstance(config.keys, ProviderKeys)

    def test_load_config_parses_yaml_file(self, temp_config_dir) -> None:
        """load_config should parse existing YAML config."""
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("""
default_model: openai/gpt-4o
default_agent: my-agent
keys:
  openai: sk-test-key-from-file
""")
        config = load_config()
        assert config.default_model == "openai/gpt-4o"
        assert config.default_agent == "my-agent"

    def test_load_config_empty_file(self, temp_config_dir) -> None:
        """load_config with empty file should return defaults."""
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("")
        config = load_config()
        assert isinstance(config, OrcxConfig)


class TestEnvVarOverride:
    """Tests for environment variable API key overrides."""

    def test_env_var_overrides_file_key(
        self, temp_config_dir, clean_env, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variable should override config file key."""
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("""
keys:
  openai: sk-file-key
""")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")

        config = load_config()
        assert config.keys.openai == "sk-env-key"

    def test_env_var_sets_key_when_file_missing(
        self, temp_config_dir, clean_env, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variable should set key when not in config file."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic-env")

        config = load_config()
        assert config.keys.anthropic == "sk-anthropic-env"

    def test_file_key_used_when_no_env_var(self, temp_config_dir, clean_env) -> None:
        """Config file key should be used when no env var set."""
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("""
keys:
  deepseek: sk-deepseek-file
""")
        config = load_config()
        assert config.keys.deepseek == "sk-deepseek-file"

    def test_all_providers_env_var_mapping(
        self, temp_config_dir, clean_env, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """All provider env vars should map correctly."""
        env_map = {
            "OPENAI_API_KEY": ("openai", "sk-openai"),
            "ANTHROPIC_API_KEY": ("anthropic", "sk-anthropic"),
            "DEEPSEEK_API_KEY": ("deepseek", "sk-deepseek"),
            "GOOGLE_API_KEY": ("google", "sk-google"),
            "MISTRAL_API_KEY": ("mistral", "sk-mistral"),
            "GROQ_API_KEY": ("groq", "sk-groq"),
            "TOGETHER_API_KEY": ("together", "sk-together"),
            "OPENROUTER_API_KEY": ("openrouter", "sk-openrouter"),
        }

        for env_var, (_provider, value) in env_map.items():
            monkeypatch.setenv(env_var, value)

        config = load_config()

        for _, (provider, value) in env_map.items():
            assert getattr(config.keys, provider) == value


class TestResolveKeys:
    """Tests for _resolve_keys helper function."""

    def test_resolve_keys_prefers_env_over_file(
        self, clean_env, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_resolve_keys should prefer env var over file value."""
        monkeypatch.setenv("OPENAI_API_KEY", "from-env")
        file_keys = ProviderKeys(openai="from-file")

        resolved = _resolve_keys(file_keys)
        assert resolved.openai == "from-env"

    def test_resolve_keys_uses_file_when_no_env(self, clean_env) -> None:
        """_resolve_keys should use file value when no env var."""
        file_keys = ProviderKeys(openai="from-file")

        resolved = _resolve_keys(file_keys)
        assert resolved.openai == "from-file"

    def test_resolve_keys_none_when_both_missing(self, clean_env) -> None:
        """_resolve_keys should return None when both env and file missing."""
        file_keys = ProviderKeys()

        resolved = _resolve_keys(file_keys)
        assert resolved.openai is None
