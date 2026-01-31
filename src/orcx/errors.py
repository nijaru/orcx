"""Error types for orcx."""

from __future__ import annotations


class OrcxError(Exception):
    """Base exception for orcx errors."""

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class ConfigError(OrcxError):
    """Configuration-related errors."""


class ConfigFileError(ConfigError):
    """Invalid config file format."""


class AgentError(OrcxError):
    """Agent-related errors."""


class AgentNotFoundError(AgentError):
    """Agent name not found in registry."""

    def __init__(self, agent_name: str, available: list[str] | None = None):
        self.agent_name = agent_name
        self.available = available or []
        hint = ""
        if available:
            hint = f". Available agents: {', '.join(available)}"
        super().__init__(f"Agent not found: {agent_name}{hint}")


class AgentValidationError(AgentError):
    """Agent config missing required fields."""

    def __init__(self, agent_name: str, missing_fields: list[str]):
        self.agent_name = agent_name
        self.missing_fields = missing_fields
        super().__init__(
            f"Agent '{agent_name}' missing required fields: {', '.join(missing_fields)}"
        )


class ModelError(OrcxError):
    """Model-related errors."""


class InvalidModelFormatError(ModelError):
    """Model string format is invalid."""

    def __init__(self, model: str):
        self.model = model
        super().__init__(
            f"Invalid model format: '{model}'. "
            "Expected 'provider/model-name' (e.g., 'anthropic/claude-sonnet-4-20250514')"
        )


class NoModelSpecifiedError(ModelError):
    """No model specified and no default configured."""

    def __init__(self):
        super().__init__("No model specified. Use --model or --agent, or set a default in config.")


class ProviderError(OrcxError):
    """Provider-related errors."""


class MissingApiKeyError(ProviderError):
    """API key not found for provider."""

    def __init__(self, provider: str, env_var: str | None = None):
        self.provider = provider
        self.env_var = env_var
        hint = f" Set {env_var} environment variable." if env_var else ""
        super().__init__(f"Missing or invalid API key for {provider}.{hint}")


class AuthenticationError(ProviderError):
    """Authentication failed with provider."""

    def __init__(self, provider: str, details: str | None = None):
        self.provider = provider
        msg = f"Authentication failed for {provider}"
        if details:
            msg += f": {details}"
        super().__init__(msg, details)


class RateLimitError(ProviderError):
    """Rate limited by provider."""

    def __init__(self, provider: str, retry_after: float | None = None):
        self.provider = provider
        self.retry_after = retry_after
        msg = f"Rate limited by {provider}"
        if retry_after:
            msg += f". Retry after {retry_after:.1f}s"
        super().__init__(msg)


class ProviderConnectionError(ProviderError):
    """Network/connection error."""

    def __init__(self, provider: str, details: str | None = None):
        self.provider = provider
        msg = f"Connection error with {provider}"
        if details:
            msg += f": {details}"
        super().__init__(msg, details)


# Alias for backwards compatibility
ConnectionError = ProviderConnectionError


class ProviderUnavailableError(ProviderError):
    """Provider service unavailable."""

    def __init__(self, provider: str, status_code: int | None = None):
        self.provider = provider
        self.status_code = status_code
        msg = f"{provider} service unavailable"
        if status_code:
            msg += f" (HTTP {status_code})"
        super().__init__(msg)
