"""Core schemas for orcx protocol."""

from __future__ import annotations

from pydantic import BaseModel, Field

QUANT_BY_BITS: dict[int, list[str]] = {
    4: ["int4", "fp4"],
    6: ["fp6"],
    8: ["int8", "fp8"],
    16: ["fp16", "bf16"],
    32: ["fp32"],
}

# Valid quantization values
VALID_QUANTS: set[str] = {q for quants in QUANT_BY_BITS.values() for q in quants} | {"unknown"}

# Valid sort strategies
VALID_SORTS: set[str] = {"price", "throughput", "latency"}

# Known OpenRouter providers (as of 2026-01)
# Source: https://openrouter.ai/docs/guides/routing/provider-selection
KNOWN_PROVIDERS: set[str] = {
    "AI21",
    "AionLabs",
    "Alibaba",
    "Amazon",
    "Anthropic",
    "AnyScale",
    "AtlasCloud",
    "Avian",
    "Azure",
    "Cerebras",
    "Chutes",
    "Cloudflare",
    "Cohere",
    "CrushOn",
    "DeepInfra",
    "DeepSeek",
    "Fireworks",
    "Google",
    "GoogleVertex",
    "Grok",
    "HuggingFace",
    "Infermatic",
    "Inflection",
    "Lambda",
    "Lepton",
    "Lynn",
    "Mancer",
    "MiniMax",
    "Mistral",
    "NexaAI",
    "Nineteen",
    "NovitaAI",
    "OpenAI",
    "OVH",
    "Parasail",
    "Perplexity",
    "Phala",
    "Replicate",
    "SambaNova",
    "SF",
    "SiliconFlow",
    "SN",
    "Together",
    "xAI",
}


class ProviderPrefs(BaseModel):
    """OpenRouter provider routing preferences."""

    # Quantization
    quantizations: list[str] | None = None  # whitelist: fp8, fp16, etc.
    exclude_quants: list[str] | None = None  # blacklist: fp4, int4, etc.
    min_bits: int | None = None  # minimum bits (8 = fp8+, excludes fp4/fp6)

    # Provider selection
    ignore: list[str] | None = None  # blacklist providers
    only: list[str] | None = None  # whitelist providers (strict)
    prefer: list[str] | None = None  # soft preference (try first, allow fallback)
    order: list[str] | None = None  # explicit order (no fallback unless allow_fallbacks)
    allow_fallbacks: bool = True  # allow fallback when preferred unavailable

    # Sorting
    sort: str | None = None  # "price", "throughput", "latency"

    def resolve_quantizations(self) -> list[str] | None:
        """Resolve final quantization whitelist from all options."""
        if self.quantizations:
            return self.quantizations

        result: set[str] = set()

        if self.min_bits:
            for bits, quants in QUANT_BY_BITS.items():
                if bits >= self.min_bits:
                    result.update(quants)

        if self.exclude_quants and result:
            result -= set(self.exclude_quants)
        elif self.exclude_quants:
            # Exclude from all possible quants
            all_quants = {q for quants in QUANT_BY_BITS.values() for q in quants}
            result = all_quants - set(self.exclude_quants)

        return list(result) if result else None

    def merge_with(self, other: ProviderPrefs | None) -> ProviderPrefs:
        """Merge with another ProviderPrefs (self takes precedence).

        Merge rules:
        - ignore, exclude_quants: union of both lists
        - prefer: self first, then other (order matters)
        - only, order, quantizations, sort: self overrides
        - min_bits: take higher value (more restrictive)
        - allow_fallbacks: self overrides
        """
        if other is None:
            return self

        def merge_lists(a: list[str] | None, b: list[str] | None) -> list[str] | None:
            """Merge two lists, preserving order and removing duplicates."""
            if not a and not b:
                return None
            result = list(a or [])
            for item in b or []:
                if item not in result:
                    result.append(item)
            return result if result else None

        return ProviderPrefs(
            # Union lists
            ignore=merge_lists(self.ignore, other.ignore),
            exclude_quants=merge_lists(self.exclude_quants, other.exclude_quants),
            # Ordered merge (self first)
            prefer=merge_lists(self.prefer, other.prefer),
            # Self overrides
            only=self.only if self.only is not None else other.only,
            order=self.order if self.order is not None else other.order,
            quantizations=self.quantizations
            if self.quantizations is not None
            else other.quantizations,
            sort=self.sort if self.sort is not None else other.sort,
            allow_fallbacks=self.allow_fallbacks
            if self.allow_fallbacks is not True
            else other.allow_fallbacks,
            # Take higher (more restrictive)
            min_bits=max(self.min_bits or 0, other.min_bits or 0) or None,
        )


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    name: str
    model: str
    provider: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    fallback_models: list[str] = Field(default_factory=list)
    max_tokens: int | None = None
    temperature: float | None = None
    provider_prefs: ProviderPrefs | None = None


class OrcxRequest(BaseModel):
    """Request to orcx from a harness."""

    prompt: str
    agent: str | None = None
    model: str | None = None
    context: str | None = None
    system_prompt: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    cache_prefix: bool = False
    stream: bool = False


class OrcxResponse(BaseModel):
    """Response from orcx to a harness."""

    content: str
    model: str
    provider: str
    usage: dict | None = None
    cost: float | None = None
    cached: bool = False


class Message(BaseModel):
    """A single message in a conversation."""

    role: str  # "user", "assistant", "system"
    content: str


class Conversation(BaseModel):
    """A stored conversation."""

    id: str
    model: str
    agent: str | None = None
    title: str | None = None
    messages: list[Message] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0
    created_at: str
    updated_at: str


def _find_similar(name: str, known: set[str]) -> str | None:
    """Find similar name using case-insensitive prefix/substring matching."""
    name_lower = name.lower()
    # Exact case-insensitive match
    for k in known:
        if k.lower() == name_lower:
            return k
    # Prefix match
    for k in known:
        if k.lower().startswith(name_lower) or name_lower.startswith(k.lower()):
            return k
    return None


def validate_provider_prefs(prefs: ProviderPrefs, context: str = "") -> list[str]:
    """Validate provider prefs and return list of warning messages.

    Args:
        prefs: The ProviderPrefs to validate
        context: Optional context string for messages (e.g., "agent 'foo'")

    Returns:
        List of warning messages (empty if all valid)
    """
    warnings: list[str] = []
    ctx = f" in {context}" if context else ""

    # Validate provider names
    for field_name in ("ignore", "only", "prefer", "order"):
        providers = getattr(prefs, field_name, None)
        if providers:
            for provider in providers:
                if provider not in KNOWN_PROVIDERS:
                    similar = _find_similar(provider, KNOWN_PROVIDERS)
                    if similar:
                        warnings.append(
                            f"Unknown provider '{provider}'{ctx}. Did you mean '{similar}'?"
                        )
                    else:
                        warnings.append(f"Unknown provider '{provider}'{ctx}")

    # Validate sort value
    if prefs.sort and prefs.sort not in VALID_SORTS:
        warnings.append(
            f"Invalid sort '{prefs.sort}'{ctx}. Must be one of: {', '.join(sorted(VALID_SORTS))}"
        )

    # Validate quantization values
    for field_name in ("quantizations", "exclude_quants"):
        quants = getattr(prefs, field_name, None)
        if quants:
            for quant in quants:
                if quant not in VALID_QUANTS:
                    warnings.append(
                        f"Invalid quantization '{quant}'{ctx}. "
                        f"Must be one of: {', '.join(sorted(VALID_QUANTS))}"
                    )

    # Validate min_bits
    if prefs.min_bits is not None and prefs.min_bits not in QUANT_BY_BITS:
        valid_bits = sorted(QUANT_BY_BITS.keys())
        warnings.append(f"Invalid min_bits {prefs.min_bits}{ctx}. Must be one of: {valid_bits}")

    return warnings
