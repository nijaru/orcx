"""CLI smoke tests."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from orcx import __version__
from orcx.cli import app

runner = CliRunner()


class TestVersionCommand:
    """Tests for --version flag."""

    def test_version_returns_version_string(self) -> None:
        """orcx --version should return the version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert f"orcx {__version__}" in result.stdout

    def test_version_short_flag(self) -> None:
        """orcx -V should also return version."""
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert f"orcx {__version__}" in result.stdout


class TestAgentsCommand:
    """Tests for agents command."""

    def test_agents_runs_without_error(self, temp_config_dir) -> None:
        """orcx agents should run without error even with no config."""
        result = runner.invoke(app, ["agents"])
        assert result.exit_code == 0
        assert "No agents configured" in result.stdout or "agents" in result.stdout.lower()

    def test_agents_shows_configured_agents(self, temp_config_dir) -> None:
        """orcx agents should list configured agents."""
        agents_file = temp_config_dir / "agents.yaml"
        agents_file.write_text("""
agents:
  test-agent:
    model: openai/gpt-4o
    description: Test agent for testing
""")
        result = runner.invoke(app, ["agents"])
        assert result.exit_code == 0
        assert "test-agent" in result.stdout
        assert "openai/gpt-4o" in result.stdout


class TestModelsCommand:
    """Tests for models command."""

    def test_models_runs_without_error(self) -> None:
        """orcx models should run without error."""
        result = runner.invoke(app, ["models"])
        assert result.exit_code == 0
        assert "model format" in result.stdout.lower()

    def test_models_lists_common_models(self) -> None:
        """orcx models should show example models and links."""
        result = runner.invoke(app, ["models"])
        assert result.exit_code == 0
        assert "openrouter" in result.stdout.lower()
        assert "litellm" in result.stdout.lower()


class TestRunCommand:
    """Tests for run command."""

    def test_run_no_args_shows_error(self) -> None:
        """orcx run with no args should show error."""
        result = runner.invoke(app, ["run"])
        assert result.exit_code != 0
        # Error goes to stderr via typer.echo(err=True)
        output = result.stdout + (result.stderr or "")
        assert "error" in output.lower() or "no prompt" in output.lower()

    def test_run_no_model_shows_error(self, temp_config_dir, clean_env) -> None:
        """orcx run with prompt but no model should show error."""
        result = runner.invoke(app, ["run", "test prompt"])
        assert result.exit_code != 0
        # Error goes to stderr via typer.echo(err=True)
        output = result.stdout + (result.stderr or "")
        assert "error" in output.lower()

    @patch("orcx.router.litellm")
    def test_run_with_model_calls_litellm(
        self, mock_litellm: MagicMock, mock_litellm_response: MagicMock
    ) -> None:
        """orcx run -m model 'prompt' should call litellm."""
        mock_litellm.completion.return_value = mock_litellm_response
        mock_litellm.completion_cost.return_value = 0.001

        result = runner.invoke(app, ["run", "-m", "openai/gpt-4o", "--no-stream", "test prompt"])
        assert result.exit_code == 0

        mock_litellm.completion.assert_called_once()
        call_kwargs = mock_litellm.completion.call_args.kwargs
        assert call_kwargs["model"] == "openai/gpt-4o"
        assert any(m["content"] == "test prompt" for m in call_kwargs["messages"])

    @patch("orcx.router.litellm")
    def test_run_with_system_prompt(
        self, mock_litellm: MagicMock, mock_litellm_response: MagicMock
    ) -> None:
        """orcx run with --system should include system message."""
        mock_litellm.completion.return_value = mock_litellm_response
        mock_litellm.completion_cost.return_value = 0.001

        result = runner.invoke(
            app,
            ["run", "-m", "openai/gpt-4o", "--no-stream", "-s", "You are helpful", "test prompt"],
        )
        assert result.exit_code == 0

        call_kwargs = mock_litellm.completion.call_args.kwargs
        messages = call_kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are helpful"

    @patch("orcx.router.litellm")
    def test_run_json_output(
        self, mock_litellm: MagicMock, mock_litellm_response: MagicMock
    ) -> None:
        """orcx run --json should output JSON response."""
        mock_litellm.completion.return_value = mock_litellm_response
        mock_litellm.completion_cost.return_value = 0.001

        result = runner.invoke(app, ["run", "-m", "openai/gpt-4o", "--json", "test prompt"])
        assert result.exit_code == 0
        assert '"content"' in result.stdout
        assert '"model"' in result.stdout
