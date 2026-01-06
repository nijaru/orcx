# orcx

LLM orchestrator - route prompts to any model via [litellm](https://github.com/BerriAI/litellm).

## Install

```bash
uv tool install orcx
# or
pip install orcx
```

## Usage

```bash
# Direct model
orcx run -m openrouter/deepseek/deepseek-v3.2 "hello"

# Using agent preset
orcx run -a fast "summarize this"

# Pipe from stdin
cat code.py | orcx run -a reviewer "review this code"

# Show cost
orcx run -a fast "hello" --cost

# JSON output
orcx run -a fast "hello" --json
```

## Configuration

Config location: `~/.config/orcx/`

### agents.yaml

```yaml
agents:
  fast:
    model: openrouter/deepseek/deepseek-v3.2
    description: Fast, cheap reasoning
    temperature: 0.7
    max_tokens: 4096

  reviewer:
    model: openrouter/anthropic/claude-sonnet-4
    system_prompt: You are a code reviewer. Be concise.

  # With provider preferences (OpenRouter)
  quality:
    model: openrouter/deepseek/deepseek-v3.2
    provider_prefs:
      min_bits: 8 # fp8+ only (excludes fp4)
      ignore: [deepinfra] # blacklist providers
      prefer: [Together] # soft preference
      sort: throughput # or: price, latency
```

### config.yaml

```yaml
default_model: openrouter/deepseek/deepseek-v3.2
# API keys loaded from env vars first, then this file
keys:
  openrouter: sk-or-...
```

## Provider Preferences

OpenRouter-specific routing options:

| Option           | Type | Description                               |
| ---------------- | ---- | ----------------------------------------- |
| `min_bits`       | int  | Minimum quantization (8 = fp8+)           |
| `quantizations`  | list | Explicit whitelist: [fp8, fp16, bf16]     |
| `exclude_quants` | list | Blacklist: [fp4, int4]                    |
| `ignore`         | list | Blacklist providers                       |
| `only`           | list | Whitelist providers (strict)              |
| `prefer`         | list | Soft preference (tries first, falls back) |
| `order`          | list | Explicit order                            |
| `sort`           | str  | "price", "throughput", "latency"          |

## Commands

```bash
orcx run "prompt"        # run prompt
orcx agents              # list configured agents
orcx models              # list common models
orcx --version           # show version
```

## Environment Variables

API keys are loaded from standard env vars:

- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `DEEPSEEK_API_KEY`
- `GOOGLE_API_KEY`
- etc.

## License

MIT
