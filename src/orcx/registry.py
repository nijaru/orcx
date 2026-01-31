"""Agent registry - YAML config load/save."""

from __future__ import annotations

import yaml
from pydantic import BaseModel, ValidationError

from orcx.config import AGENTS_FILE, ensure_config_dir
from orcx.errors import AgentValidationError, ConfigFileError
from orcx.schema import AgentConfig

REQUIRED_AGENT_FIELDS = ["model"]


class AgentRegistry(BaseModel):
    """Collection of configured agents."""

    agents: dict[str, AgentConfig] = {}

    def get(self, name: str) -> AgentConfig | None:
        """Get agent by name."""
        return self.agents.get(name)

    def add(self, agent: AgentConfig) -> None:
        """Add or update an agent."""
        self.agents[agent.name] = agent

    def remove(self, name: str) -> bool:
        """Remove an agent. Returns True if removed."""
        if name in self.agents:
            del self.agents[name]
            return True
        return False

    def list_names(self) -> list[str]:
        """List all agent names."""
        return list(self.agents.keys())


def _validate_agent_config(name: str, config: dict) -> None:
    """Validate agent config has required fields."""
    missing = [field for field in REQUIRED_AGENT_FIELDS if not config.get(field)]
    if missing:
        raise AgentValidationError(name, missing)


def load_registry() -> AgentRegistry:
    """Load agent registry from YAML file."""
    if not AGENTS_FILE.exists():
        return AgentRegistry()

    try:
        with AGENTS_FILE.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigFileError(
            f"Invalid YAML in agents file: {AGENTS_FILE}",
            details=str(e),
        ) from e

    if data is None:
        return AgentRegistry()

    if not isinstance(data, dict):
        raise ConfigFileError(
            f"Agents file must be a YAML mapping: {AGENTS_FILE}",
            details=f"Got {type(data).__name__} instead",
        )

    agents_data = data.get("agents", {})
    if not isinstance(agents_data, dict):
        raise ConfigFileError(
            f"'agents' key must be a mapping in: {AGENTS_FILE}",
            details=f"Got {type(agents_data).__name__} instead",
        )

    agents = {}
    for name, config in agents_data.items():
        if not isinstance(config, dict):
            raise ConfigFileError(
                f"Agent '{name}' must be a mapping in: {AGENTS_FILE}",
                details=f"Got {type(config).__name__} instead",
            )

        _validate_agent_config(name, config)
        config["name"] = name

        try:
            agent = AgentConfig.model_validate(config)
            agents[name] = agent

            # Validate provider prefs and print warnings
            if agent.provider_prefs:
                import sys

                from orcx.schema import validate_provider_prefs

                for warning in validate_provider_prefs(agent.provider_prefs, f"agent '{name}'"):
                    print(f"Warning: {warning}", file=sys.stderr)
        except ValidationError as e:
            errors = "; ".join(
                f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()
            )
            raise ConfigFileError(
                f"Invalid agent config for '{name}' in: {AGENTS_FILE}",
                details=errors,
            ) from e

    return AgentRegistry(agents=agents)


def save_registry(registry: AgentRegistry) -> None:
    """Save agent registry to YAML file."""
    ensure_config_dir()

    data = {
        "agents": {
            name: agent.model_dump(exclude={"name"}, exclude_none=True)
            for name, agent in registry.agents.items()
        }
    }

    with AGENTS_FILE.open("w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
