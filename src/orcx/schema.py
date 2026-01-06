"""Core schemas for orcx protocol."""

from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    name: str
    model: str
    provider: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    fallback_models: list[str] = []
    max_tokens: int | None = None
    temperature: float | None = None


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
