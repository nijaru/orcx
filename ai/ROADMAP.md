# Roadmap

## 0.0.1 (Released)

Core routing functionality. Published 2026-01-06.

| Feature                               | Status |
| ------------------------------------- | ------ |
| Route to any model via litellm        | Done   |
| Agent presets (system prompt, params) | Done   |
| OpenRouter provider preferences       | Done   |
| File input (`-f`)                     | Done   |
| Model aliases                         | Done   |
| Streaming                             | Done   |
| Cost tracking                         | Done   |
| Error handling                        | Done   |
| 41 tests                              | Done   |

## 0.0.2 (Released)

Conversation support. Published 2026-01-06.

| Feature            | Status |
| ------------------ | ------ |
| SQLite storage     | Done   |
| Continue last      | Done   |
| Resume by ID       | Done   |
| List conversations | Done   |
| Output to file     | Done   |

## 0.0.3 (Released)

Version fix (0.0.2 had wrong `--version` output). Published 2026-01-06.

## 0.0.4

Structured output.

| Feature     | Description                      |
| ----------- | -------------------------------- |
| Format flag | `--format json/code/md`          |
| JSON schema | Validate response against schema |

## 0.1.0

Quality of life.

| Feature        | Description                    |
| -------------- | ------------------------------ |
| Multi-modal    | Image input support            |
| Prompt caching | Anthropic/OpenAI cache support |
| Token counting | Show tokens before sending     |

## Non-Goals

Things we're intentionally not building:

- **Full agent framework** - Use LangChain/Pydantic AI if you need that
- **File editing** - Let orchestrator agent (Claude Code) handle edits
- **Embeddings/RAG** - Use simonw/llm or dedicated tools
- **Plugins** - Keep it simple, use litellm's provider support
- **Tool execution** - Orchestrator handles tool use

## Philosophy

orcx is a **focused routing tool**, not a Swiss Army knife. The orchestrator agent (Claude Code, etc.) handles complex reasoning. orcx handles:

1. Routing prompts to cheap/fast models
2. Getting specialized knowledge from different providers
3. Code review, summarization, Q&A
4. Cost-conscious delegation
