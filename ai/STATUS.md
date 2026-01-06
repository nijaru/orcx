# Status

## Current State

| Metric  | Value   | Updated    |
| ------- | ------- | ---------- |
| Version | 0.0.1   | 2026-01-06 |
| Build   | Passing | 2026-01-06 |
| Tests   | 41 pass | 2026-01-06 |
| Lint    | Clean   | 2026-01-06 |

## Active Work

Ready for 0.0.1 release. Publish via `gh release create v0.0.1`.

## What's Working

- CLI: `orcx run`, `orcx agents`, `orcx models`
- Route to any model via litellm (100+ providers)
- Agent presets with system prompts, parameters
- OpenRouter provider preferences (quantization, provider filtering, sorting)
- File input (`-f file.py`)
- Model aliases
- Streaming output
- Cost tracking (`--cost`)
- JSON output (`--json`)
- Error handling with `--debug` flag

## Blockers

None

## Notes

- Primary use case: Claude Code delegating to cheaper/specialized models
- Keep it simple - don't become a full agent framework
- Conversations planned for 0.0.2
