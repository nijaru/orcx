# orcx

LLM orchestrator - harness-agnostic agent routing.

Route tasks to any LLM provider with unified interface, fallbacks, and cost tracking.

## Install

```bash
uv tool install orcx
```

## Usage

```bash
# Configure agents
orcx agents add trading --model deepseek/deepseek-chat --provider openrouter

# Run a task
orcx run --agent trading "Analyze MACD crossover signals"

# Pipe from stdin
echo "Review this code" | orcx run --agent code-review
```

## Features

- **Multi-provider**: OpenRouter, Anthropic, OpenAI, Google, Mistral, DeepSeek, local (Ollama)
- **BYOK**: Bring your own API keys
- **Fallbacks**: Automatic failover between providers
- **Cost tracking**: Monitor spend per agent/task
- **Cache control**: Prompt caching where supported
- **Provider preferences**: Quant levels, routing strategies

## License

MIT
