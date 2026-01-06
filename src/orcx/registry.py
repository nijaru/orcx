"""Agent registry - YAML config load/save."""

import yaml
from pydantic import BaseModel

from orcx.config import AGENTS_FILE, ensure_config_dir
from orcx.schema import AgentConfig


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


def load_registry() -> AgentRegistry:
    """Load agent registry from YAML file."""
    if not AGENTS_FILE.exists():
        return AgentRegistry()

    with AGENTS_FILE.open() as f:
        data = yaml.safe_load(f) or {}

    agents = {}
    for name, config in data.get("agents", {}).items():
        config["name"] = name
        agents[name] = AgentConfig.model_validate(config)

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
