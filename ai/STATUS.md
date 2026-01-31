# Status

## Current State

| Metric     | Value                                        | Updated    |
| ---------- | -------------------------------------------- | ---------- |
| Version    | 0.0.5 → 0.0.6                                | 2026-01-30 |
| Published  | [PyPI](https://pypi.org/project/orcx/0.0.5/) | 2026-01-09 |
| Visibility | Public                                       | 2026-01-06 |
| Build      | Passing                                      | 2026-01-30 |
| Tests      | 74 pass                                      | 2026-01-30 |
| Lint       | Clean                                        | 2026-01-30 |

## Active Work

v0.0.6 ready for release. Changes:

- **Fix:** Forward reference NameError on Python 3.13+ (added `from __future__ import annotations` to all modules)
- **Feature:** Direct prompt syntax `orcx "prompt"` as shorthand for `orcx run "prompt"`
- **Refactor:** CLI split into smaller functions, RunOptions dataclass, better error handling

## What's Working

- CLI: `orcx run`, `orcx agents`, `orcx models`, `orcx conversations`
- **Direct prompt:** `orcx "prompt"` routes to run command
- Route to any model via litellm (100+ providers)
- Agent presets with system prompts, parameters
- OpenRouter provider preferences (quantization, provider filtering, sorting)
- Global provider preferences (merged with agent-specific prefs)
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
