"""CLI entrypoint for orcx."""

import sys
import traceback
from pathlib import Path
from typing import Annotated

import typer

from orcx import __version__
from orcx.errors import (
    AgentNotFoundError,
    AuthenticationError,
    ConfigFileError,
    ConnectionError,
    InvalidModelFormatError,
    MissingApiKeyError,
    NoModelSpecifiedError,
    OrcxError,
    RateLimitError,
)
from orcx.registry import load_registry
from orcx.schema import OrcxRequest

# Global debug flag
_debug = False


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"orcx {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="orcx",
    help="LLM orchestrator - route prompts to any model",
    no_args_is_help=True,
)


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", "-V", callback=version_callback, is_eager=True),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", "-d", help="Show full tracebacks on error"),
    ] = False,
) -> None:
    """LLM orchestrator - route prompts to any model."""
    global _debug
    _debug = debug


def _handle_error(e: Exception) -> None:
    """Handle errors with appropriate messages and exit codes."""
    global _debug

    if _debug:
        typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(1) from None

    if isinstance(e, MissingApiKeyError):
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(2) from None

    if isinstance(e, AuthenticationError):
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(2) from None

    if isinstance(e, RateLimitError):
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(3) from None

    if isinstance(e, ConnectionError):
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(4) from None

    if isinstance(e, AgentNotFoundError):
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(5) from None

    if isinstance(e, InvalidModelFormatError):
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(5) from None

    if isinstance(e, NoModelSpecifiedError):
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(5) from None

    if isinstance(e, ConfigFileError):
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(6) from None

    if isinstance(e, OrcxError):
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"Error: {e}", err=True)
    raise typer.Exit(1) from None


def _read_files(paths: list[str]) -> str:
    """Read and format file contents for context."""

    parts = []
    for path_str in paths:
        path = Path(path_str)
        if not path.exists():
            typer.echo(f"Error: File not found: {path_str}", err=True)
            raise typer.Exit(1)
        if not path.is_file():
            typer.echo(f"Error: Not a file: {path_str}", err=True)
            raise typer.Exit(1)
        try:
            content = path.read_text()
            parts.append(f"# {path.name}\n```\n{content}\n```")
        except Exception as e:
            typer.echo(f"Error reading {path_str}: {e}", err=True)
            raise typer.Exit(1) from None
    return "\n\n".join(parts)


@app.command()
def run(
    prompt: str = typer.Argument(None, help="Prompt to send"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent preset to use"),
    model: str = typer.Option(None, "--model", "-m", help="Model to use directly"),
    system: str = typer.Option(None, "--system", "-s", help="System prompt"),
    context: str = typer.Option(None, "--context", help="Context to prepend"),
    files: Annotated[
        list[str] | None,
        typer.Option("--file", "-f", help="Files to include"),
    ] = None,
    output: str = typer.Option(None, "--output", "-o", help="Write response to file"),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming"),
    show_cost: bool = typer.Option(False, "--cost", help="Show cost after response"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Run a prompt against an agent or model."""
    from orcx import router

    # Read from stdin if no prompt and stdin has data
    if prompt is None:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        else:
            typer.echo("Error: No prompt provided", err=True)
            raise typer.Exit(1)

    if not prompt:
        typer.echo("Error: Empty prompt", err=True)
        raise typer.Exit(1)

    # Build context from files
    if files:
        file_context = _read_files(files)
        context = f"{context}\n\n{file_context}" if context else file_context

    request = OrcxRequest(
        prompt=prompt,
        agent=agent,
        model=model,
        system_prompt=system,
        context=context,
        stream=not no_stream and not json_out,
    )

    try:
        if request.stream:
            chunks = []
            for chunk in router.run_stream(request):
                chunks.append(chunk)
                typer.echo(chunk, nl=False)
            typer.echo()
            if output:
                Path(output).write_text("".join(chunks))
        else:
            response = router.run(request)
            content = response.model_dump_json(indent=2) if json_out else response.content
            typer.echo(content)
            if output:
                Path(output).write_text(content)
            if show_cost and response.cost:
                typer.echo(f"\n[cost: ${response.cost:.6f}]", err=True)
    except Exception as e:
        _handle_error(e)


@app.command()
def agents() -> None:
    """List configured agents."""
    try:
        registry = load_registry()
    except Exception as e:
        _handle_error(e)
        return

    names = registry.list_names()

    if not names:
        typer.echo("No agents configured.")
        typer.echo("Add agents to: ~/.config/orcx/agents.yaml")
        return

    for name in names:
        agent = registry.get(name)
        if agent:
            desc = f" - {agent.description}" if agent.description else ""
            typer.echo(f"{name}: {agent.model}{desc}")


@app.command()
def models() -> None:
    """Show model format and provider links."""
    typer.echo("Model format: provider/model-name")
    typer.echo()
    typer.echo("Examples:")
    typer.echo("  anthropic/claude-4.5-sonnet")
    typer.echo("  openai/gpt-5.2")
    typer.echo("  google/gemini-3-flash-preview")
    typer.echo("  deepseek/deepseek-v3.2")
    typer.echo("  openrouter/deepseek/deepseek-v3.2  # via OpenRouter")
    typer.echo()
    typer.echo("Browse models:")
    typer.echo("  https://openrouter.ai/models")
    typer.echo("  https://docs.litellm.ai/docs/providers")


if __name__ == "__main__":
    app()
