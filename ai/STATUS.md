# Status

## Current State

| Metric     | Value                                        | Updated    |
| ---------- | -------------------------------------------- | ---------- |
| Version    | 0.0.3                                        | 2026-01-06 |
| Published  | [PyPI](https://pypi.org/project/orcx/0.0.3/) | 2026-01-06 |
| Visibility | Public                                       | 2026-01-06 |
| Build      | Passing                                      | 2026-01-06 |
| Tests      | 56 pass                                      | 2026-01-06 |
| Lint       | Clean                                        | 2026-01-06 |

## Active Work

v0.0.3 released (0.0.2 had wrong version in --version output).

## What's Working

- CLI: `orcx run`, `orcx agents`, `orcx models`, `orcx conversations`
- Route to any model via litellm (100+ providers)
- Agent presets with system prompts, parameters
- OpenRouter provider preferences (quantization, provider filtering, sorting)
- File input (`-f file.py`)
- Output to file (`-o response.md`)
- Model aliases
- Streaming output
- Cost tracking (`--cost`)
- JSON output (`--json`)
- Conversations (`-c` continue, `--resume ID`, `--no-save`)
- Error handling with `--debug` flag

## Blockers

None

## Notes

- Primary use case: Claude Code delegating to cheaper/specialized models
- Keep it simple - don't become a full agent framework
- Repo moved to github.com/nijaru/orcx
