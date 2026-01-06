"""LLM routing via litellm."""

from collections.abc import Iterator

import litellm

from orcx.config import load_config
from orcx.registry import load_registry
from orcx.schema import AgentConfig, OrcxRequest, OrcxResponse

litellm.suppress_debug_info = True  # type: ignore[assignment]


def resolve_model(request: OrcxRequest) -> tuple[str, AgentConfig | None]:
    """Resolve model from request, checking agent config if specified."""
    if request.model:
        return request.model, None

    if request.agent:
        registry = load_registry()
        agent = registry.get(request.agent)
        if not agent:
            raise ValueError(f"Agent not found: {request.agent}")
        return agent.model, agent

    config = load_config()
    if config.default_model:
        return config.default_model, None
    if config.default_agent:
        registry = load_registry()
        agent = registry.get(config.default_agent)
        if agent:
            return agent.model, agent

    raise ValueError("No model specified and no default configured")


def build_messages(
    request: OrcxRequest,
    agent: AgentConfig | None,
) -> list[dict[str, str]]:
    """Build message list for LLM call."""
    messages = []

    system = request.system_prompt or (agent.system_prompt if agent else None)
    if system:
        messages.append({"role": "system", "content": system})

    if request.context:
        messages.append({"role": "user", "content": request.context})
        messages.append({"role": "assistant", "content": "Understood."})

    messages.append({"role": "user", "content": request.prompt})
    return messages


def build_params(
    request: OrcxRequest,
    agent: AgentConfig | None,
    model: str,
    messages: list[dict[str, str]],
    stream: bool,
) -> dict:
    """Build litellm completion params."""
    params: dict = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    max_tokens = request.max_tokens or (agent.max_tokens if agent else None)
    if max_tokens:
        params["max_tokens"] = max_tokens
    if request.temperature is not None:
        params["temperature"] = request.temperature
    elif agent and agent.temperature is not None:
        params["temperature"] = agent.temperature

    # OpenRouter provider preferences
    if agent and agent.provider_prefs:
        prefs = agent.provider_prefs
        provider_obj: dict = {}

        # Quantization
        quants = prefs.resolve_quantizations()
        if quants:
            provider_obj["quantizations"] = quants

        # Provider selection
        if prefs.ignore:
            provider_obj["ignore"] = prefs.ignore
        if prefs.only:
            provider_obj["only"] = prefs.only
        if prefs.prefer:
            provider_obj["order"] = prefs.prefer
            provider_obj["allow_fallbacks"] = True
        elif prefs.order:
            provider_obj["order"] = prefs.order
            provider_obj["allow_fallbacks"] = prefs.allow_fallbacks

        # Sorting
        if prefs.sort:
            provider_obj["sort"] = prefs.sort

        if provider_obj:
            params["extra_body"] = {"provider": provider_obj}

    return params


def run(request: OrcxRequest) -> OrcxResponse:
    """Execute a single LLM request."""
    model, agent = resolve_model(request)
    messages = build_messages(request, agent)
    params = build_params(request, agent, model, messages, stream=False)

    response = litellm.completion(**params)

    content = response.choices[0].message.content or ""
    usage = None
    cost = None

    if response.usage:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        cost = litellm.completion_cost(completion_response=response)

    return OrcxResponse(
        content=content,
        model=response.model or model,
        provider=model.split("/")[0] if "/" in model else "unknown",
        usage=usage,
        cost=cost,
    )


def run_stream(request: OrcxRequest) -> Iterator[str]:
    """Execute a streaming LLM request, yielding chunks."""
    model, agent = resolve_model(request)
    messages = build_messages(request, agent)
    params = build_params(request, agent, model, messages, stream=True)

    for chunk in litellm.completion(**params):
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
