"""
Agent Builder

Builds Agent instances from AgentConfig objects.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from jinja2 import Template

from agents import Agent


@dataclass
class AgentConfig:
    """Configuration for an agent loaded from files."""

    name: str
    base_path: Path
    yaml_config: Dict[str, Any]
    markdown_instructions: str
    yaml_path: Path
    markdown_path: Path


class AgentBuilder:
    """
    Builder for creating Agent instances from file-based configurations.

    Supports:
    - Jinja2 templating in markdown instructions
    - Sub-agents (hierarchical agent structure)
    - Runtime variable substitution
    """

    def __init__(self, default_model: str = "gpt-4.1-mini"):
        """
        Initialize the agent builder.

        Args:
            default_model: Default model to use if not specified in YAML
        """
        self.default_model = default_model
        self._agent_cache: Dict[str, Agent] = {}

    def render_instructions(
        self, template: str, variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render markdown instructions with Jinja2 templating.

        Args:
            template: Markdown template string
            variables: Variables for template substitution

        Returns:
            Rendered instructions string
        """
        if variables is None:
            variables = {}

        jinja_template = Template(template)
        return jinja_template.render(**variables)

    def load_sub_agents(
        self,
        sub_agent_refs: List[str],
        base_path: Path,
        variables: Optional[Dict[str, Any]] = None,
    ) -> List[Agent]:
        """
        Load sub-agents referenced in the YAML config.

        Args:
            sub_agent_refs: List of agent references (paths or names)
            base_path: Base path for resolving relative references
            variables: Variables to pass to sub-agents

        Returns:
            List of Agent instances
        """
        # Import here to avoid circular dependency
        from .loader import load_agent_config_from_path

        sub_agents = []

        for agent_ref in sub_agent_refs:
            # Resolve the agent path
            agent_path = self._resolve_agent_path(base_path, agent_ref)

            # Load and build the sub-agent recursively
            sub_config = load_agent_config_from_path(agent_path)
            sub_agent = self.build_agent(sub_config, variables=variables)
            sub_agents.append(sub_agent)

        return sub_agents

    def _resolve_agent_path(self, base_path: Path, agent_ref: str) -> Path:
        """
        Resolve agent reference to a file path.

        Supports:
        - Relative paths: "subfolder/agent_name"
        - Absolute paths: "/full/path/to/agent"
        - Simple names: "agent_name" (searches in base_path and subdirectories)
        """
        if Path(agent_ref).is_absolute():
            return Path(agent_ref)

        # If agent_ref contains path separators, treat as relative path
        if "/" in agent_ref or "\\" in agent_ref:
            relative_path = base_path / agent_ref
            if relative_path.exists():
                return relative_path
            # Try with .yaml extension
            yaml_path = base_path / f"{agent_ref}.yaml"
            if yaml_path.exists():
                return yaml_path.parent / agent_ref.split("/")[-1].split("\\")[-1]

        # Try as direct child (same directory)
        direct_yaml = base_path / f"{agent_ref}.yaml"
        if direct_yaml.exists():
            return base_path / agent_ref

        # Try in subdirectories (recursive search)
        def find_agent_in_dir(directory: Path, agent_name: str) -> Optional[Path]:
            """Recursively search for agent in directory."""
            # Check current directory
            yaml_file = directory / f"{agent_name}.yaml"
            if yaml_file.exists():
                return directory / agent_name

            # Check subdirectories
            for subdir in directory.iterdir():
                if subdir.is_dir():
                    result = find_agent_in_dir(subdir, agent_name)
                    if result:
                        return result
            return None

        found_path = find_agent_in_dir(base_path, agent_ref)
        if found_path:
            return found_path

        # Default: assume it's relative to base_path
        return base_path / agent_ref

    def build_agent(
        self,
        config: AgentConfig,
        variables: Optional[Dict[str, Any]] = None,
        context_type: Optional[type] = None,
    ) -> Agent:
        """
        Build an Agent instance from an AgentConfig.

        Args:
            config: Agent configuration loaded from files
            variables: Variables for Jinja2 templating
            context_type: Optional context type for the agent

        Returns:
            Agent instance
        """
        if variables is None:
            variables = {}

        # Render instructions with Jinja2
        instructions = self.render_instructions(
            config.markdown_instructions, variables=variables
        )

        # Extract configuration from YAML
        yaml_config = config.yaml_config

        # Get model (from YAML or default)
        model = yaml_config.get("model", self.default_model)

        # Get agent name (from YAML or use file name)
        agent_name = yaml_config.get("name", config.name)

        # Load sub-agents if specified
        sub_agents = []
        tools = []

        if "sub_agents" in yaml_config:
            sub_agent_refs = yaml_config["sub_agents"]
            if isinstance(sub_agent_refs, list):
                sub_agents = self.load_sub_agents(
                    sub_agent_refs, config.base_path, variables=variables
                )

                # Convert sub-agents to tools
                tool_descriptions_map = yaml_config.get("tool_descriptions", {})
                tool_name_prefix = yaml_config.get("tool_name_prefix", "")

                for sub_agent in sub_agents:
                    # Generate tool name: prefix + agent name (normalized)
                    agent_name_normalized = (
                        sub_agent.name.lower().replace(" ", "_").replace("-", "_")
                    )
                    tool_name = tool_name_prefix + agent_name_normalized

                    # Get tool description from config or use default
                    tool_description = tool_descriptions_map.get(
                        sub_agent.name, f"Tool for {sub_agent.name}"
                    )

                    tools.append(
                        sub_agent.as_tool(
                            tool_name=tool_name, tool_description=tool_description
                        )
                    )

        # Get additional tools if specified
        if "tools" in yaml_config:
            # Tools can be specified as module paths or function references
            # For now, we'll expect them to be imported elsewhere
            # This is a placeholder for future tool loading
            pass

        # Get output type if specified
        # Note: Output type support can be added in the future
        # It would require dynamic class loading from module paths
        if "output_type" in yaml_config:
            # Output type can be specified as a class path string
            # This would need to be imported dynamically
            # For now, we'll skip this feature
            pass

        # Build the agent
        # Note: Using type: ignore for Agent constructor due to dynamic typing
        if context_type:
            agent: Agent = Agent[context_type](  # type: ignore[misc]
                name=agent_name,
                instructions=instructions,
                model=model,
                tools=tools if tools else None,
            )
        else:
            agent = Agent(  # type: ignore[misc]
                name=agent_name,
                instructions=instructions,
                model=model,
                tools=tools if tools else None,
            )

        return agent
