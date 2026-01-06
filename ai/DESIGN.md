## System Overview

LLM orchestrator enabling any harness (Claude Code, custom agents, scripts) to route tasks to any LLM provider with unified interface, fallbacks, and cost tracking.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Harness   │────▶│    orcx     │────▶│  Providers  │
│ (Claude Code│     │  CLI/API    │     │ (via litellm│
│  scripts)   │     │             │     │  100+ LLMs) │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                    ┌─────┴─────┐
                    │  Config   │
                    │ (agents,  │
                    │  keys)    │
                    └───────────┘
```

## Components

| Component | Purpose                   | Status      |
| --------- | ------------------------- | ----------- |
| cli.py    | Typer CLI entrypoint      | Skeleton    |
| schema.py | Pydantic request/response | Skeleton    |
| registry  | Agent definitions (YAML)  | Not started |
| router    | litellm Router wrapper    | Not started |
| config    | API keys, defaults        | Not started |
| tracking  | Cost/usage monitoring     | Not started |

## Data Flow

1. Harness calls `orcx run --agent NAME "prompt"` or pipes JSON
2. orcx loads agent config from registry
3. orcx routes to provider via litellm (with fallbacks)
4. Response returned as text or structured JSON
5. Usage/cost tracked

## Key Design Decisions

→ See DECISIONS.md for rationale

## Component Details

→ See ai/design/{component}.md for detailed specs
