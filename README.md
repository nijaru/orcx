# orcx

LLM orchestrator - route prompts to any model via [litellm](https://github.com/BerriAI/litellm).

> **Alpha** - Core functionality works, API may change.

## Why orcx?

- **100+ providers** via litellm - OpenRouter, OpenAI, Anthropic, Google, etc.
- **Agent presets** - Save model + system prompt + parameters as reusable configs
- **OpenRouter routing** - Control quantization, provider selection, sorting
- **Cost tracking** - See what each request costs
- **Simple** - Just route prompts, not a full agent framework

## Install

```bash
uv tool install orcx
# or
pip install orcx
```

## Quick Start

```bash
# Set your API key
export OPENROUTER_API_KEY=sk-or-...

# Run a prompt
orcx run -m openrouter/deepseek/deepseek-v3.2 "hello"

# With file context
orcx run -m openrouter/deepseek/deepseek-v3.2 -f code.py "review this"

# Show cost
orcx run -m openrouter/deepseek/deepseek-v3.2 "hello" --cost
```

## Usage

```bash
# Direct model (provider/model format)
orcx run -m openrouter/deepseek/deepseek-v3.2 "hello"

# Using model alias (if configured)
orcx run -m deepseek "hello"

# Using agent preset
orcx run -a reviewer "review this code"

# With file context
orcx run -a reviewer -f src/main.py "review this"

# Multiple files
orcx run -m deepseek -f code.py -f tests.py "explain the tests"

# Pipe from stdin
cat code.py | orcx run -a reviewer "review this"

# JSON output (includes usage/cost)
orcx run -m deepseek "hello" --json

# Custom system prompt
orcx run -m deepseek -s "You are a pirate" "greet me"
```

## Configuration

Config location: `~/.config/orcx/`

### config.yaml

```yaml
# Default model (used when no -m or -a specified)
default_model: openrouter/deepseek/deepseek-v3.2

# Model aliases for shorthand
aliases:
  deepseek: openrouter/deepseek/deepseek-v3.2
  sonnet: openrouter/anthropic/claude-4.5-sonnet

# API keys (env vars take precedence)
keys:
  openrouter: sk-or-...
```

### agents.yaml

```yaml
agents:
  fast:
    model: openrouter/deepseek/deepseek-v3.2
    description: Fast, cheap reasoning
    temperature: 0.7
    max_tokens: 4096

  reviewer:
    model: openrouter/anthropic/claude-4.5-sonnet
    system_prompt: You are a code reviewer. Be concise and actionable.

  # With OpenRouter provider preferences
  quality:
    model: openrouter/deepseek/deepseek-v3.2
    provider_prefs:
      min_bits: 8 # fp8+ only (excludes fp4)
      ignore: [DeepInfra] # blacklist providers
      prefer: [Together] # soft preference
      sort: throughput # or: price, latency
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
orcx run "prompt"        # Run prompt (uses default model/agent)
orcx run -m MODEL "..."  # Use specific model or alias
orcx run -a AGENT "..."  # Use agent preset
orcx agents              # List configured agents
orcx models              # List common models
orcx --version           # Show version
orcx --debug             # Show full tracebacks on error
```

## CLI Options

| Option        | Short | Description                   |
| ------------- | ----- | ----------------------------- |
| `--model`     | `-m`  | Model or alias to use         |
| `--agent`     | `-a`  | Agent preset to use           |
| `--system`    | `-s`  | System prompt                 |
| `--context`   |       | Context to prepend            |
| `--file`      | `-f`  | Files to include (repeatable) |
| `--no-stream` |       | Disable streaming output      |
| `--cost`      |       | Show cost after response      |
| `--json`      | `-j`  | Output as JSON                |

## Environment Variables

API keys loaded from env vars (take precedence over config file):

- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `DEEPSEEK_API_KEY`
- `GOOGLE_API_KEY`
- `MISTRAL_API_KEY`
- `GROQ_API_KEY`
- `TOGETHER_API_KEY`

## Model Format

Models use `provider/model-name` format. See your provider's docs for available models:

- [OpenRouter models](https://openrouter.ai/models)
- [litellm providers](https://docs.litellm.ai/docs/providers)

## License

MIT
