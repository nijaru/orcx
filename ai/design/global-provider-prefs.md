# Design: Global Routing Preferences

**Status:** Implemented (Option C)
**Updated:** 2026-01-09

## Problem

Users want global routing preferences that don't need to be repeated per-agent. Currently `provider_prefs` is per-agent only.

## Research Findings

Multiple aggregators exist that route to external providers:

| Service               | Provider Filtering       | Region           | Quantization | Sort                     |
| --------------------- | ------------------------ | ---------------- | ------------ | ------------------------ |
| OpenRouter            | Yes (ignore/only/prefer) | EU (enterprise)  | Yes (unique) | price/latency/throughput |
| Portkey               | Yes                      | geo-routing      | No           | No                       |
| LiteLLM Proxy         | Yes                      | region filtering | No           | cost/latency             |
| Cloudflare AI Gateway | Yes                      | geographic       | No           | No                       |
| Unify                 | Implicit                 | Implicit         | No           | cost/speed/quality       |

**Key findings:**

- OpenRouter is unique in having quantization filtering
- Region/location filtering is common across aggregators
- Provider selection (ignore/prefer) is common
- Sort strategies vary but cost/latency are common

## Implemented Solution: Option C

Keep `provider_prefs` as-is, add global `default_provider_prefs`:

```yaml
# ~/.config/orcx/config.yaml

default_provider_prefs:
  min_bits: 8
  ignore: [SiliconFlow, DeepInfra]
  sort: price
```

Only applies to `openrouter/*` models. Document as OpenRouter-specific for now, refactor later if needed.

**Pros:**

- Minimal change
- Backward compatible
- Works for current use case

**Cons:**

- Not designed for multiple aggregators
- May need refactoring later

## Implementation Details

### Config Changes (config.py)

```python
class OrcxConfig(BaseModel):
    default_agent: str | None = None
    default_model: str | None = None
    default_provider_prefs: ProviderPrefs | None = None  # NEW
    keys: ProviderKeys = Field(default_factory=ProviderKeys)
    aliases: dict[str, str] = Field(default_factory=dict)
```

### Merge Logic (schema.py)

Added `merge_with()` method to `ProviderPrefs`:

```python
def merge_with(self, other: ProviderPrefs | None) -> ProviderPrefs:
    """Merge with another ProviderPrefs (self takes precedence).

    Merge rules:
    - ignore, exclude_quants: union of both lists
    - prefer: self first, then other (order matters)
    - only, order, quantizations, sort: self overrides
    - min_bits: take higher value (more restrictive)
    - allow_fallbacks: self overrides
    """
```

### Router Changes (router.py)

Updated `build_params()` to:

1. Check if model is `openrouter/*`
2. Get global `default_provider_prefs` from config
3. Merge agent prefs with global prefs (agent takes precedence)
4. Apply merged prefs to request

```python
# OpenRouter provider preferences (only for openrouter/* models)
if extract_provider(model) == "openrouter":
    config = load_config()
    agent_prefs = agent.provider_prefs if agent else None
    global_prefs = config.default_provider_prefs

    # Merge: agent prefs take precedence over global defaults
    prefs = None
    if agent_prefs and global_prefs:
        prefs = agent_prefs.merge_with(global_prefs)
    elif agent_prefs:
        prefs = agent_prefs
    elif global_prefs:
        prefs = global_prefs
```

### Tests Added

- `TestProviderPrefsMergeWith` - 12 test cases for merge logic
- `TestBuildParamsProviderPrefs` - 6 test cases for router integration

## Usage Example

```yaml
# ~/.config/orcx/config.yaml

# Global defaults for all openrouter/* models
default_provider_prefs:
  min_bits: 8
  ignore: [SiliconFlow, DeepInfra, Mancer]
  sort: price

# ~/.config/orcx/agents.yaml

agents:
  deepseek:
    model: openrouter/deepseek/deepseek-v3.2
    # Agent-specific overrides (merged with global)
    provider_prefs:
      ignore: [Chutes] # Added to global ignore list
      prefer: [AtlasCloud] # Agent-specific preference
```

Result: deepseek agent ignores `[SiliconFlow, DeepInfra, Mancer, Chutes]`, prefers `AtlasCloud`, uses `min_bits: 8`, sorts by `price`.

## Future Considerations

If we add support for other aggregators (Portkey, LiteLLM Proxy, etc.), consider refactoring to Option A (layered structure) or Option B (provider-namespaced):

```yaml
# Option A: Layered
routing:
  region: us
  sort: cost
openrouter:
  min_bits: 8
  ignore: [...]

# Option B: Provider-namespaced
providers:
  openrouter:
    min_bits: 8
    ignore: [...]
```

---

## Appendix: Current ProviderPrefs Schema

```python
class ProviderPrefs(BaseModel):
    # Quantization (OpenRouter-specific)
    quantizations: list[str] | None = None
    exclude_quants: list[str] | None = None
    min_bits: int | None = None

    # Provider selection (OpenRouter-specific)
    ignore: list[str] | None = None
    only: list[str] | None = None
    prefer: list[str] | None = None
    order: list[str] | None = None
    allow_fallbacks: bool = True

    # Sorting (could be general)
    sort: str | None = None
```
