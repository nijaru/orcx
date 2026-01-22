# Provider Routing Research

Research on provider routing options for LLM aggregators and how to support them in orcx.

## OpenRouter Provider Preferences

OpenRouter offers the most comprehensive provider routing options among LLM aggregators. All options are passed via a `provider` object in the request body.

### Complete OpenRouter Provider Options

| Field                      | Type          | Description                                                       |
| -------------------------- | ------------- | ----------------------------------------------------------------- |
| `order`                    | string[]      | Provider slugs to try in order (e.g., `["anthropic", "openai"]`)  |
| `allow_fallbacks`          | boolean       | Allow backup providers when primary unavailable (default: `true`) |
| `only`                     | string[]      | Whitelist - only allow these providers                            |
| `ignore`                   | string[]      | Blacklist - skip these providers                                  |
| `quantizations`            | string[]      | Filter by quantization level (e.g., `["fp8", "fp16"]`)            |
| `sort`                     | string/object | Sort strategy: `"price"`, `"throughput"`, `"latency"`             |
| `require_parameters`       | boolean       | Only use providers supporting all request params                  |
| `data_collection`          | string        | `"allow"` or `"deny"` for data collection                         |
| `zdr`                      | boolean       | Restrict to Zero Data Retention endpoints                         |
| `enforce_distillable_text` | boolean       | Restrict to models allowing text distillation                     |
| `max_price`                | object        | Maximum pricing: `{"prompt": 1, "completion": 2}` ($/M tokens)    |
| `preferred_min_throughput` | number/object | Minimum throughput threshold (tokens/sec)                         |
| `preferred_max_latency`    | number/object | Maximum latency threshold (ms)                                    |

### Quantization Levels

| Level     | Description                   |
| --------- | ----------------------------- |
| `int4`    | Integer (4 bit)               |
| `int8`    | Integer (8 bit)               |
| `fp4`     | Floating point (4 bit)        |
| `fp6`     | Floating point (6 bit)        |
| `fp8`     | Floating point (8 bit)        |
| `fp16`    | Floating point (16 bit)       |
| `bf16`    | Brain floating point (16 bit) |
| `fp32`    | Floating point (32 bit)       |
| `unknown` | Unknown                       |

### Advanced Sort Options

When using model fallbacks, `sort` can be an object:

```python
{
    "sort": {
        "by": "throughput",  # "price", "throughput", "latency"
        "partition": "none"  # "model" (default) or "none"
    }
}
```

- `partition: "model"` - Sort within each model's providers (default)
- `partition: "none"` - Sort globally across all models (useful for "best performing model")

### Performance Thresholds

Percentile-based thresholds (p50, p75, p90, p99):

```python
{
    "preferred_min_throughput": {"p90": 50},  # 50 tokens/sec at p90
    "preferred_max_latency": {"p90": 2000}    # 2 seconds at p90
}
```

## Other LLM Aggregators

### Together AI

**No provider routing** - Together AI is a direct inference provider, not an aggregator. They host their own infrastructure and do not route to multiple providers.

Features:

- 200+ open-source models
- Dedicated endpoints for fine-tuned models
- Standard inference parameters (temperature, top_p, max_tokens, etc.)
- No provider selection or routing options

### Fireworks AI

**Direct routing only** - Fireworks AI offers infrastructure-level routing, not provider-level:

- Direct routing bypasses global load balancer for lower latency
- Region-specific deployments (US_IOWA_1, EU_FRANKFURT_1, etc.)
- Private Service Connect (GCP) and AWS PrivateLink for enterprise

No provider preferences like OpenRouter. Fireworks controls all infrastructure.

### Replicate / Anyscale / Modal

These are **compute platforms**, not aggregators. They run models on their infrastructure without routing to external providers.

### Summary: Aggregators vs Inference Providers

| Service      | Type               | Provider Routing     |
| ------------ | ------------------ | -------------------- |
| OpenRouter   | Aggregator         | Full routing options |
| Together AI  | Inference Provider | None                 |
| Fireworks AI | Inference Provider | Region-level only    |
| Replicate    | Compute Platform   | None                 |
| Anyscale     | Compute Platform   | None                 |

**Finding: OpenRouter is unique** in offering provider routing. Other services are direct providers.

## litellm Support for Provider-Specific Options

### How litellm Passes Provider Options

litellm supports provider-specific parameters in three ways:

1. **Direct kwargs** - Non-OpenAI params passed directly to provider:

   ```python
   litellm.completion(model="claude-3", top_k=3)  # top_k passed to Anthropic
   ```

2. **Provider config classes** - Global configuration:

   ```python
   litellm.OpenAIConfig(max_tokens=100)
   ```

3. **`extra_body` parameter** - Arbitrary request body additions:
   ```python
   litellm.completion(
       model="openrouter/anthropic/claude-3",
       messages=[...],
       extra_body={"provider": {"quantizations": ["fp8"]}}
   )
   ```

### OpenRouter-Specific in litellm

litellm documents passing OpenRouter params directly:

- `transforms` - Message transformations
- `models` - Model fallback list
- `route` - Routing strategy

These are passed as kwargs, but the `provider` object for routing requires `extra_body`.

### Current orcx Implementation

```python
# In router.py, build_params()
if provider_obj:
    params["extra_body"] = {"provider": provider_obj}
```

This is correct. litellm passes `extra_body` contents directly to the provider's request body.

## Design Recommendations

### Question: OpenRouter-specific vs Generic Config?

**Recommendation: Keep OpenRouter-specific, but design for extensibility.**

Rationale:

1. **OpenRouter is unique** - No other aggregator offers these routing features
2. **Generic abstraction adds complexity** - Would require mapping layer with no current benefit
3. **`extra_body` is the escape hatch** - For future providers, litellm already supports `extra_body`

### Proposed Config Structure

**Option A: Provider-namespaced (Recommended)**

```yaml
# Per-agent config
agents:
  cheap-coder:
    model: openrouter/deepseek/deepseek-coder
    provider_prefs: # OpenRouter-specific
      min_bits: 8
      ignore: [azure]
      sort: price

# Global defaults
default_provider_prefs:
  min_bits: 8 # Applied to all openrouter/* models
```

Pros:

- Clear that this is OpenRouter-specific
- No false promise of "generic" routing
- Easy to add other provider sections if needed

**Option B: Generic with provider detection**

```yaml
provider_routing:
  openrouter:
    default_quantization: fp8
    default_ignore: [azure]
  together: # Future - no options today
    dedicated: true
```

Cons:

- Implies feature parity that doesn't exist
- More complex config parsing

### Model-Pattern Based Application

Current implementation applies prefs only to agents. Consider:

```yaml
# Apply to any openrouter/* model, not just agents
model_defaults:
  "openrouter/*":
    provider_prefs:
      min_bits: 8
```

**Recommendation: Not needed yet.** Agent-level config covers the use case. If needed, add `default_provider_prefs` at config root (already supported).

### Missing OpenRouter Features to Consider

Features orcx doesn't expose yet:

| Feature                    | Priority | Notes                 |
| -------------------------- | -------- | --------------------- |
| `max_price`                | Medium   | Cost control          |
| `require_parameters`       | Low      | Ensures param support |
| `data_collection`          | Low      | Privacy control       |
| `zdr`                      | Low      | Zero data retention   |
| `preferred_min_throughput` | Medium   | Performance SLAs      |
| `preferred_max_latency`    | Medium   | Performance SLAs      |

Current orcx covers the most common use cases (quantization, provider filtering, sorting).

## Implementation Notes

### Current Schema (schema.py)

```python
class ProviderPrefs(BaseModel):
    # Quantization
    quantizations: list[str] | None = None
    exclude_quants: list[str] | None = None
    min_bits: int | None = None

    # Provider selection
    ignore: list[str] | None = None
    only: list[str] | None = None
    prefer: list[str] | None = None
    order: list[str] | None = None
    allow_fallbacks: bool = True

    # Sorting
    sort: str | None = None
```

### Suggested Additions (if needed)

```python
class ProviderPrefs(BaseModel):
    # ... existing fields ...

    # Performance thresholds (OpenRouter-specific)
    max_price: dict[str, float] | None = None  # {"prompt": 1, "completion": 2}
    preferred_min_throughput: int | dict | None = None
    preferred_max_latency: int | dict | None = None

    # Data policies
    data_collection: str | None = None  # "allow" | "deny"
    zdr: bool | None = None
    require_parameters: bool | None = None
```

## Sources

- OpenRouter Provider Routing: https://openrouter.ai/docs/provider-routing
- OpenRouter Provider Selection: https://openrouter.ai/docs/guides/routing/provider-selection
- litellm Provider-Specific Params: https://docs.litellm.ai/docs/completion/provider_specific_params
- litellm OpenRouter: https://docs.litellm.ai/docs/providers/openrouter
- Together AI Docs: https://docs.together.ai/reference/inference
- Fireworks AI Direct Routing: https://docs.fireworks.ai/deployments/direct-routing

---

**Updated:** 2026-01-09
