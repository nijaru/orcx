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
    InvalidModelFormatError,
    MissingApiKeyError,
    NoModelSpecifiedError,
    OrcxError,
    ProviderConnectionError,
    RateLimitError,
)
from orcx.registry import load_registry
from orcx.schema import OrcxRequest

# Global debug flag
_debug = False

# Maximum file size to read (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Exception type to exit code mapping
_EXIT_CODES: dict[type, int] = {
    MissingApiKeyError: 2,
    AuthenticationError: 2,
    RateLimitError: 3,
    ProviderConnectionError: 4,
    AgentNotFoundError: 5,
    InvalidModelFormatError: 5,
    NoModelSpecifiedError: 5,
    ConfigFileError: 6,
}


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

    # Check specific exception types via mapping
    for exc_type, exit_code in _EXIT_CODES.items():
        if isinstance(e, exc_type):
            typer.echo(f"Error: {e.message}", err=True)
            raise typer.Exit(exit_code) from None

    # Generic OrcxError fallback
    if isinstance(e, OrcxError):
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(1) from None

    # Unknown exception
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
            file_size = path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                typer.echo(
                    f"Error: File too large: {path_str} ({file_size // 1024 // 1024}MB > 10MB)",
                    err=True,
                )
                raise typer.Exit(1)
            content = path.read_text()
            parts.append(f"# {path.name}\n```\n{content}\n```")
        except OSError as e:
            typer.echo(f"Error reading {path_str}: {e}", err=True)
            raise typer.Exit(1) from e
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
    continue_last: bool = typer.Option(
        False, "--continue", "-c", help="Continue last conversation"
    ),
    resume: str = typer.Option(None, "--resume", help="Resume conversation by ID"),
    no_save: bool = typer.Option(False, "--no-save", help="Don't save conversation"),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming"),
    show_cost: bool = typer.Option(False, "--cost", help="Show cost after response"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Run a prompt against an agent or model."""
    from orcx import conversation, router

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

    # Load or create conversation
    conv = None
    if resume:
        conv = conversation.get(resume)
        if not conv:
            typer.echo(f"Error: Conversation '{resume}' not found", err=True)
            raise typer.Exit(1)
    elif continue_last:
        conv = conversation.get_last()
        if not conv:
            typer.echo("Error: No conversation to continue", err=True)
            raise typer.Exit(1)

    # Build context from files
    if files:
        file_context = _read_files(files)
        context = f"{context}\n\n{file_context}" if context else file_context

    request = OrcxRequest(
        prompt=prompt,
        agent=agent if not conv else (agent or conv.agent),
        model=model if not conv else (model or conv.model),
        system_prompt=system,
        context=context,
        stream=not no_stream and not json_out,
    )

    # Build message history from conversation
    history = [{"role": m.role, "content": m.content} for m in conv.messages] if conv else []

    try:
        if request.stream:
            chunks = []
            for chunk in router.run_stream(request, history=history):
                chunks.append(chunk)
                typer.echo(chunk, nl=False)
            typer.echo()
            response_content = "".join(chunks)
            if output:
                Path(output).write_text(response_content)
            # Save conversation (no cost info in streaming)
            if not no_save:
                _save_conversation(conv, request, prompt, response_content, None, conversation)
        else:
            response = router.run(request, history=history)
            content = response.model_dump_json(indent=2) if json_out else response.content
            typer.echo(content)
            if output:
                Path(output).write_text(content)
            if show_cost and response.cost:
                typer.echo(f"\n[cost: ${response.cost:.6f}]", err=True)
            # Save conversation
            if not no_save:
                _save_conversation(conv, request, prompt, response.content, response, conversation)
    except Exception as e:
        _handle_error(e)


def _save_conversation(conv, request, prompt, response_content, response, conversation):
    """Save or update conversation after exchange."""
    from orcx.schema import Message

    if conv is None:
        # Resolve model for new conversation
        from orcx.router import resolve_model

        try:
            resolved_model, _ = resolve_model(request)
        except (NoModelSpecifiedError, InvalidModelFormatError, AgentNotFoundError):
            resolved_model = request.model or "unknown"
        conv = conversation.create(model=resolved_model, agent=request.agent)

    conv.messages.append(Message(role="user", content=prompt))
    conv.messages.append(Message(role="assistant", content=response_content))

    if response and response.usage:
        conv.total_tokens += response.usage.get("total_tokens", 0)
    if response and response.cost:
        conv.total_cost += response.cost

    # Set title from first prompt if not set
    if not conv.title:
        conv.title = prompt[:50] + "..." if len(prompt) > 50 else prompt

    conversation.update(conv)
    typer.echo(f"[{conv.id}]", err=True)


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


# Conversations subcommand group
conversations_app = typer.Typer(help="Manage conversations")
app.add_typer(conversations_app, name="conversations")


@conversations_app.callback(invoke_without_command=True)
def conversations_list(ctx: typer.Context) -> None:
    """List recent conversations."""
    if ctx.invoked_subcommand is not None:
        return

    from orcx import conversation

    convs = conversation.list_recent()
    if not convs:
        typer.echo("No conversations.")
        return

    for conv in convs:
        title = conv.title or "(no title)"
        title = title[:40] + "..." if len(title) > 40 else title
        tokens = f"{conv.total_tokens}tok" if conv.total_tokens else ""
        cost = f"${conv.total_cost:.4f}" if conv.total_cost else ""
        info = f" ({tokens} {cost})".strip() if tokens or cost else ""
        model_display = conv.model[:30] if len(conv.model) > 30 else conv.model
        typer.echo(f"{conv.id}  {model_display:<30}  {title}{info}")


@conversations_app.command("show")
def conversations_show(conv_id: str = typer.Argument(..., help="Conversation ID")) -> None:
    """Show full conversation."""
    from orcx import conversation

    conv = conversation.get(conv_id)
    if not conv:
        typer.echo(f"Error: Conversation '{conv_id}' not found", err=True)
        raise typer.Exit(1)

    typer.echo(f"ID: {conv.id}")
    typer.echo(f"Model: {conv.model}")
    if conv.agent:
        typer.echo(f"Agent: {conv.agent}")
    typer.echo(f"Created: {conv.created_at}")
    typer.echo(f"Updated: {conv.updated_at}")
    if conv.total_tokens:
        typer.echo(f"Tokens: {conv.total_tokens}")
    if conv.total_cost:
        typer.echo(f"Cost: ${conv.total_cost:.6f}")
    typer.echo()

    for msg in conv.messages:
        role = msg.role.upper()
        typer.echo(f"--- {role} ---")
        typer.echo(msg.content)
        typer.echo()


@conversations_app.command("delete")
def conversations_delete(conv_id: str = typer.Argument(..., help="Conversation ID")) -> None:
    """Delete a conversation."""
    from orcx import conversation

    if conversation.delete(conv_id):
        typer.echo(f"Deleted: {conv_id}")
    else:
        typer.echo(f"Error: Conversation '{conv_id}' not found", err=True)
        raise typer.Exit(1)


@conversations_app.command("clean")
def conversations_clean(
    days: int = typer.Option(30, "--days", "-d", help="Delete older than N days"),
) -> None:
    """Delete old conversations."""
    from orcx import conversation

    count = conversation.clean(days)
    typer.echo(f"Deleted {count} conversation(s) older than {days} days")


if __name__ == "__main__":
    app()
