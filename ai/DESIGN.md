# Design

## Overview

LLM orchestrator enabling any harness (Claude Code, scripts) to route prompts to any LLM provider with unified interface and cost tracking.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Harness   │────▶│    orcx     │────▶│  Providers  │
│ (Claude Code│     │    CLI      │     │ (via litellm│
│  scripts)   │     │             │     │  100+ LLMs) │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                    ┌─────┴─────┐
                    │  Config   │
                    │ ~/.config │
                    │  /orcx/   │
                    └───────────┘
```

## Components

| Component   | Purpose                       | File                 |
| ----------- | ----------------------------- | -------------------- |
| cli.py      | Typer CLI entrypoint          | src/orcx/cli.py      |
| router.py   | litellm routing, alias expand | src/orcx/router.py   |
| schema.py   | Pydantic request/response     | src/orcx/schema.py   |
| registry.py | Agent definitions (YAML)      | src/orcx/registry.py |
| config.py   | API keys, aliases, defaults   | src/orcx/config.py   |
| errors.py   | Custom exceptions             | src/orcx/errors.py   |

## Data Flow

1. Harness calls `orcx run -m MODEL "prompt"` or `-a AGENT "prompt"`
2. Expand model alias if configured
3. Load agent config from registry (if using agent)
4. Build messages with system prompt, context, files
5. Route to provider via litellm (with provider preferences)
6. Stream or return response
7. Optionally show cost

## Configuration

```
~/.config/orcx/
├── config.yaml    # API keys, aliases, defaults
└── agents.yaml    # Agent presets
```

## Similar Tools

| Tool               | Focus        | Differentiator                                 |
| ------------------ | ------------ | ---------------------------------------------- |
| simonw/llm         | General CLI  | SQLite logging, embeddings, plugins            |
| charmbracelet/mods | Pipelines    | Conversations, roles, beautiful TUI            |
| orcx               | Orchestrator | Provider routing, cost tracking, agent presets |

## Future Considerations

See ROADMAP.md for planned features.
