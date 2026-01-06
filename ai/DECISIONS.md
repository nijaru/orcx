## Decisions Log

### 2026-01-05: Python + litellm over Bun/TS

**Context:** Choosing implementation language for LLM orchestrator

**Decision:** Python with litellm, ty for type checking

**Rationale:**

- litellm provides 100+ provider support out of box
- Built-in fallbacks, retries, load balancing, cost tracking
- Cache control passthrough for Anthropic/etc
- OpenRouter provider preferences (quant, routing)
- ty gives type safety without runtime overhead

**Tradeoffs:**

- Bun/TS would give single binary distribution
- Vercel AI SDK cleaner API but fewer providers
- Python ecosystem more mature for this use case

---

### 2026-01-05: Name "orcx" (orchestrator)

**Context:** CLI tool name selection

**Decision:** `orcx` - available on PyPI, npm, crates.io

**Rationale:**

- `orc` and `agents` taken everywhere
- Short, memorable, evokes "orchestrator"
- Leaves room for ecosystem (orcx-\*, etc)

---
