"""Core schemas for orcx protocol."""

from pydantic import BaseModel, Field

QUANT_BY_BITS: dict[int, list[str]] = {
    4: ["int4", "fp4"],
    6: ["fp6"],
    8: ["int8", "fp8"],
    16: ["fp16", "bf16"],
    32: ["fp32"],
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
