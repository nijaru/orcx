# Status

## Current State

| Metric     | Value                                        | Updated    |
| ---------- | -------------------------------------------- | ---------- |
| Version    | 0.0.5                                        | 2026-01-09 |
| Published  | [PyPI](https://pypi.org/project/orcx/0.0.5/) | 2026-01-09 |
| Visibility | Public                                       | 2026-01-06 |
| Build      | Passing                                      | 2026-01-09 |
| Tests      | 74 pass                                      | 2026-01-09 |
| Lint       | Clean                                        | 2026-01-09 |

## Active Work

v0.0.5 ready for release. New features:

- Global provider preferences (`default_provider_prefs` in config.yaml)
- `--cost` flag shows applied provider prefs
- Validation warnings for typos in provider names, invalid sort/quantization values

## What's Working

- CLI: `orcx run`, `orcx agents`, `orcx models`, `orcx conversations`
- Route to any model via litellm (100+ providers)
- Agent presets with system prompts, parameters
- OpenRouter provider preferences (quantization, provider filtering, sorting)
- **Global provider preferences** (merged with agent-specific prefs)
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
- Global provider prefs only apply to OpenRouter models for now; can refactor later for other aggregators
