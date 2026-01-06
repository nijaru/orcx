# orcx

LLM orchestrator - harness-agnostic agent routing. Route tasks to any LLM provider with unified interface, fallbacks, and cost tracking.

## Project Structure

| Directory | Purpose                                             |
| --------- | --------------------------------------------------- |
| src/orcx/ | Package source                                      |
| ai/       | AI session context - state tracking across sessions |
| tests/    | Test suite (pytest)                                 |

### AI Context Organization

**Session files** (read every session):

- ai/STATUS.md — Current state, metrics, blockers
- ai/DESIGN.md — System architecture, components
- ai/DECISIONS.md — Architectural decisions with rationale
- ai/TODO.md — Task tracking

**Reference files** (loaded on demand):

- ai/research/ — External research
- ai/design/ — Component specs
- ai/tmp/ — Temporary artifacts (gitignored)

## Technology Stack

| Component       | Technology  |
| --------------- | ----------- |
| Language        | Python 3.14 |
| Package Manager | uv          |
| LLM Routing     | litellm     |
| CLI Framework   | typer       |
| Schemas         | pydantic    |
| HTTP            | httpx       |
| Config          | pyyaml      |
| Type Checking   | ty          |
| Linting         | ruff        |

## Commands

```bash
# Install dependencies
uv sync

# Run CLI
uv run orcx --help
uv run orcx run --agent NAME "prompt"

# Build
uv build

# Lint
uv run ruff check src/
uv run ruff format src/

# Type check
uv run ty check src/

# Test
uv run pytest -v
```

## Verification Steps

- Build: `uv build` (zero errors)
- Lint: `uv run ruff check src/` (zero errors)
- Types: `uv run ty check src/` (zero errors)
- Tests: `uv run pytest` (zero failures)

## Code Standards

| Aspect     | Standard                          |
| ---------- | --------------------------------- |
| Formatting | ruff format, 100 char line length |
| Imports    | ruff isort                        |
| Types      | ty strict, Pydantic models        |
| Errors     | Explicit exceptions, no bare try  |
| Naming     | snake_case funcs, PascalCase cls  |

## Key Patterns

### Provider Routing (litellm)

```python
from litellm import Router

router = Router(
    model_list=[
        {"model_name": "deepseek", "litellm_params": {"model": "deepseek/deepseek-chat"}},
        {"model_name": "claude", "litellm_params": {"model": "anthropic/claude-sonnet-4-20250514"}},
    ],
    fallbacks=[{"deepseek": ["claude"]}],
)
```

### Pydantic Schemas

```python
from pydantic import BaseModel

class OrcxRequest(BaseModel):
    prompt: str
    agent: str | None = None
    model: str | None = None
    stream: bool = False
```

## Development Workflow

1. Research best practices → ai/research/{topic}.md
2. Synthesize to DESIGN.md or design/{component}.md
3. Document decision → DECISIONS.md
4. Implement → src/orcx/
5. Update STATUS.md with learnings

## Current Focus

See ai/STATUS.md for current state, ai/DESIGN.md for architecture
