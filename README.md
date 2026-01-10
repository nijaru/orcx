# orcx

LLM orchestrator - route prompts to any model via [litellm](https://github.com/BerriAI/litellm).

> **Alpha** - Core functionality works, API may change.

## Why orcx?

- **100+ providers** via litellm - OpenRouter, OpenAI, Anthropic, Google, etc.
- **Agent presets** - Save model + system prompt + parameters as reusable configs
- **Conversations** - Multi-turn with `-c` continue and `--resume ID`
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

# Save response to file
orcx run -m deepseek "explain async" -o response.md
```

## Conversations

Conversations are saved automatically. Continue or resume them:

```bash
# Start a conversation (prints ID like [a1b2])
orcx run -m deepseek "explain python decorators"
# [a1b2]

# Continue last conversation
orcx run -c "show me an example"

# Resume specific conversation
orcx run --resume a1b2 "what about class decorators?"

# Don't save this exchange
orcx run --no-save -m deepseek "quick question"

# List recent conversations
orcx conversations

# Show full conversation
orcx conversations show a1b2

# Delete conversation
orcx conversations delete a1b2

# Clean old conversations (default: 30 days)
orcx conversations clean --days 7
```

Conversations are stored in `~/.config/orcx/conversations.db`.

## Configuration

Config location: `~/.config/orcx/`

### config.yaml

```yaml
# Default model (used when no -m or -a specified)
default_model: openrouter/deepseek/deepseek-v3.2

# Model aliases for shorthand
aliases:
  deepseek: deepseek/deepseek-v3.2
  sonnet: anthropic/claude-4.5-sonnet

# Global provider preferences (OpenRouter only)
# Applied to all openrouter/* models, merged with agent-specific prefs
default_provider_prefs:
  min_bits: 8
  ignore: [SiliconFlow, DeepInfra]
  sort: price

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
    model: anthropic/claude-4.5-sonnet
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

OpenRouter-specific routing options. Can be set globally in `config.yaml` (`default_provider_prefs`) or per-agent in `agents.yaml` (`provider_prefs`). Agent prefs are merged with global prefs (agent takes precedence).

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

Use `--cost` flag to see which prefs were applied to a request.

## Commands

```bash
orcx run "prompt"        # Run prompt (uses default model/agent)
orcx run -m MODEL "..."  # Use specific model or alias
orcx run -a AGENT "..."  # Use agent preset
orcx run -c "..."        # Continue last conversation
orcx agents              # List configured agents
orcx models              # Show model format and examples
orcx conversations       # List/manage conversations
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
| `--output`    | `-o`  | Write response to file        |
| `--continue`  | `-c`  | Continue last conversation    |
| `--resume`    |       | Resume conversation by ID     |
| `--no-save`   |       | Don't save conversation       |
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
