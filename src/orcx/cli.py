"""CLI entrypoint for orcx."""

import typer

app = typer.Typer(
    name="orcx",
    help="LLM orchestrator - harness-agnostic agent routing",
    no_args_is_help=True,
)


@app.command()
def run(
    prompt: str = typer.Argument(None, help="Prompt to send to the agent"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent name to use"),
    model: str = typer.Option(None, "--model", "-m", help="Model to use directly"),
    stdin: bool = typer.Option(False, "--stdin", "-", help="Read prompt from stdin"),
) -> None:
    """Run a prompt against an agent or model."""
    typer.echo(f"Running with agent={agent}, model={model}")


@app.command()
def agents() -> None:
    """List configured agents."""
    from orcx.registry import load_registry

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
    """List available models."""
    typer.echo("Fetching models...")


if __name__ == "__main__":
    app()
