"""CLI entrypoint for orcx."""

import sys
from typing import Annotated

import typer

from orcx import __version__
from orcx.registry import load_registry
from orcx.schema import OrcxRequest


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
) -> None:
    """LLM orchestrator - route prompts to any model."""


@app.command()
def run(
    prompt: str = typer.Argument(None, help="Prompt to send"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent preset to use"),
    model: str = typer.Option(None, "--model", "-m", help="Model to use directly"),
    system: str = typer.Option(None, "--system", "-s", help="System prompt"),
    context: str = typer.Option(None, "--context", help="Context to prepend"),
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
            for chunk in router.run_stream(request):
                typer.echo(chunk, nl=False)
            typer.echo()  # Final newline
        else:
            response = router.run(request)
            if json_out:
                typer.echo(response.model_dump_json(indent=2))
            else:
                typer.echo(response.content)
                if show_cost and response.cost:
                    typer.echo(f"\n[cost: ${response.cost:.6f}]", err=True)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def agents() -> None:
    """List configured agents."""
    registry = load_registry()
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
    """List available models from litellm."""

    typer.echo("Common models (via litellm):")
    typer.echo()
    common = [
        "anthropic/claude-sonnet-4-20250514",
        "anthropic/claude-haiku-4-20250514",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "deepseek/deepseek-chat",
        "deepseek/deepseek-reasoner",
        "google/gemini-2.0-flash",
    ]
    for m in common:
        typer.echo(f"  {m}")
    typer.echo()
    typer.echo("See: https://docs.litellm.ai/docs/providers")


if __name__ == "__main__":
    app()
