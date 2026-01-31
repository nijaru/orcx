"""LLM routing via litellm."""

from __future__ import annotations

import contextlib
import warnings
from collections.abc import Iterator

import litellm

from orcx.config import ENV_KEY_MAP, load_config
from orcx.errors import (
    AgentNotFoundError,
    AuthenticationError,
    InvalidModelFormatError,
    NoModelSpecifiedError,
    RateLimitError,
)
from orcx.registry import load_registry
from orcx.schema import AgentConfig, OrcxRequest, OrcxResponse, ProviderPrefs

litellm.suppress_debug_info = True  # type: ignore[assignment]

# Suppress litellm's internal Pydantic serialization warnings
# These occur when OpenRouter returns fewer fields than litellm expects
warnings.filterwarnings(
    "ignore", message=".*PydanticSerializationUnexpectedValue.*", module="litellm"
)


def extract_provider(model: str) -> str:
    """Extract provider name from model string."""
    if "/" in model:
        return model.split("/")[0]
    return "unknown"


def validate_model_format(model: str) -> None:
    """Validate model string format (provider/model-name)."""
    if "/" not in model:
        raise InvalidModelFormatError(model)
    parts = model.split("/", 1)
    if not parts[0] or not parts[1]:
        raise InvalidModelFormatError(model)


def expand_alias(model: str) -> str:
    """Expand model alias if configured."""
    config = load_config()
    return config.aliases.get(model, model)


def resolve_model(request: OrcxRequest) -> tuple[str, AgentConfig | None]:
    """Resolve model from request, checking agent config if specified."""
    if request.model:
        model = expand_alias(request.model)
        validate_model_format(model)
        return model, None

    if request.agent:
        registry = load_registry()
        agent = registry.get(request.agent)
        if not agent:
            available = registry.list_names()
            raise AgentNotFoundError(request.agent, available)
        validate_model_format(agent.model)
        return agent.model, agent

    config = load_config()
    if config.default_model:
        validate_model_format(config.default_model)
        return config.default_model, None
    if config.default_agent:
        registry = load_registry()
        agent = registry.get(config.default_agent)
        if agent:
            validate_model_format(agent.model)
            return agent.model, agent

    raise NoModelSpecifiedError()


def build_messages(
    request: OrcxRequest,
    agent: AgentConfig | None,
    history: list[dict] | None = None,
) -> list[dict[str, str]]:
    """Build message list for LLM call."""
    messages = []

    system = request.system_prompt or (agent.system_prompt if agent else None)
    if system:
        messages.append({"role": "system", "content": system})

    if request.context:
        messages.append({"role": "user", "content": request.context})
        messages.append({"role": "assistant", "content": "Understood."})

    # Add conversation history
    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": request.prompt})
    return messages


def get_effective_prefs(model: str, agent: AgentConfig | None) -> ProviderPrefs | None:
    """Get the effective provider prefs for a model/agent combination.

    Only returns prefs for openrouter/* models. Returns None otherwise.
    """
    if extract_provider(model) != "openrouter":
        return None

    config = load_config()
    agent_prefs = agent.provider_prefs if agent else None
    global_prefs = config.default_provider_prefs

    if agent_prefs and global_prefs:
        return agent_prefs.merge_with(global_prefs)
    elif agent_prefs:
        return agent_prefs
    elif global_prefs:
        return global_prefs
    return None


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

    # OpenRouter provider preferences (only for openrouter/* models)
    prefs = get_effective_prefs(model, agent)
    if prefs:
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


def _wrap_litellm_error(e: Exception, model: str) -> Exception:
    """Convert litellm exceptions to orcx errors."""
    import os

    from orcx.errors import MissingApiKeyError, ProviderConnectionError, ProviderUnavailableError

    provider = extract_provider(model)
    env_var = ENV_KEY_MAP.get(provider)

    if isinstance(e, litellm.AuthenticationError):
        # Check if env var is actually missing vs other auth errors
        if env_var and not os.environ.get(env_var):
            return MissingApiKeyError(provider, env_var)
        return AuthenticationError(provider, str(e))

    if isinstance(e, litellm.RateLimitError):
        retry_after = None
        if hasattr(e, "response") and e.response:
            retry_after_str = e.response.headers.get("retry-after")
            if retry_after_str:
                with contextlib.suppress(ValueError):
                    retry_after = float(retry_after_str)
        return RateLimitError(provider, retry_after)

    if isinstance(e, litellm.APIConnectionError):
        return ProviderConnectionError(provider, str(e))

    if isinstance(e, litellm.APIError):
        status = getattr(e, "status_code", None)
        if status and status >= 500:
            return ProviderUnavailableError(provider, status)

    return e


def run(request: OrcxRequest, history: list[dict] | None = None) -> OrcxResponse:
    """Execute a single LLM request."""
    model, agent = resolve_model(request)
    messages = build_messages(request, agent, history)
    params = build_params(request, agent, model, messages, stream=False)

    try:
        response = litellm.completion(**params)
    except Exception as e:
        raise _wrap_litellm_error(e, model) from e

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
        provider=extract_provider(model),
        usage=usage,
        cost=cost,
    )


def run_stream(request: OrcxRequest, history: list[dict] | None = None) -> Iterator[str]:
    """Execute a streaming LLM request, yielding chunks."""
    model, agent = resolve_model(request)
    messages = build_messages(request, agent, history)
    params = build_params(request, agent, model, messages, stream=True)

    try:
        for chunk in litellm.completion(**params):
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        raise _wrap_litellm_error(e, model) from e
