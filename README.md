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

# Using model alias
orcx run -m deepseek "hello"

# Using agent preset
orcx run -a fast "summarize this"

# With file context
orcx run -a reviewer -f src/main.py "review this code"

# Multiple files
orcx run -m deepseek -f code.py -f tests.py "explain the tests"

# Pipe from stdin
cat code.py | orcx run -a reviewer "review this"

# Show cost after response
orcx run -a fast "hello" --cost

# JSON output (includes usage/cost)
orcx run -a fast "hello" --json

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
  claude: anthropic/claude-sonnet-4
  gpt4: openai/gpt-4o

# API keys (env vars take precedence)
keys:
  openrouter: sk-or-...
  anthropic: sk-ant-...
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
    model: openrouter/anthropic/claude-sonnet-4
    system_prompt: You are a code reviewer. Be concise.

  # With OpenRouter provider preferences
  quality:
    model: openrouter/deepseek/deepseek-v3.2
    provider_prefs:
      min_bits: 8 # fp8+ only (excludes fp4)
      ignore: [deepinfra] # blacklist providers
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

API keys are loaded from standard env vars (take precedence over config file):

- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `DEEPSEEK_API_KEY`
- `GOOGLE_API_KEY`
- `MISTRAL_API_KEY`
- `GROQ_API_KEY`
- `TOGETHER_API_KEY`

## License

MIT
