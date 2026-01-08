"""
Skill Builder Module

Converts SkillConfig objects to OpenAI Agent instances.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from jinja2 import Environment, BaseLoader

from agents import Agent

from .models import SkillConfig, TopLevelAgentConfig


logger = logging.getLogger(__name__)


class SkillReferenceLoader(BaseLoader):
    """
    Jinja2 loader that loads templates from skill references directory.
    """

    def __init__(self, skill_path: Optional[Path]):
        self.skill_path = skill_path

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, str, callable]:
        if self.skill_path is None:
            raise ValueError("No skill path set for template loading")

        # Try references directory first
        references_path = self.skill_path / "references" / template
        if references_path.exists():
            source = references_path.read_text(encoding="utf-8")
            return source, str(references_path), lambda: True

        # Try direct path
        direct_path = self.skill_path / template
        if direct_path.exists():
            source = direct_path.read_text(encoding="utf-8")
            return source, str(direct_path), lambda: True

        raise FileNotFoundError(f"Template not found: {template}")


class SkillBuilder:
    """
    Builder for creating Agent instances from skill configurations.

    Supports:
    - Jinja2 templating in skill instructions
    - Sub-agents (skills as sub-agents)
    - Reference file inclusion
    - Runtime variable substitution
    """

    def __init__(self, default_model: str = "gpt-4.1-mini"):
        """
        Initialize the skill builder.

        Args:
            default_model: Default model to use if not specified
        """
        self.default_model = default_model
        self._agent_cache: Dict[str, Agent] = {}

    def render_instructions(
        self,
        template: str,
        variables: Optional[Dict[str, Any]] = None,
        skill_path: Optional[Path] = None,
    ) -> str:
        """
        Render skill instructions with Jinja2 templating.

        Args:
            template: Markdown template string
            variables: Variables for template substitution
            skill_path: Path to skill directory (for include directives)

        Returns:
            Rendered instructions string
        """
        if variables is None:
            variables = {}

        # Create Jinja2 environment with custom loader for includes
        loader = SkillReferenceLoader(skill_path)
        env = Environment(loader=loader)

        jinja_template = env.from_string(template)
        return jinja_template.render(**variables)

    def build_agent_from_skill(
        self,
        config: SkillConfig,
        model: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        sub_skill_configs: Optional[List[SkillConfig]] = None,
        tool_descriptions: Optional[Dict[str, str]] = None,
    ) -> Agent:
        """
        Build an Agent instance from a SkillConfig.

        Args:
            config: Skill configuration
            model: Model to use (overrides default)
            variables: Variables for Jinja2 templating
            sub_skill_configs: List of sub-skills to include as tools
            tool_descriptions: Custom tool descriptions for sub-skills

        Returns:
            Agent instance
        """
        if variables is None:
            variables = {}

        if tool_descriptions is None:
            tool_descriptions = {}

        # Use cache key based on skill name and variables
        cache_key = f"{config.name}:{hash(frozenset(variables.items()))}"
        if cache_key in self._agent_cache:
            logger.debug(f"Returning cached agent for {config.name}")
            return self._agent_cache[cache_key]

        # Render instructions with Jinja2
        instructions = self.render_instructions(
            config.instructions,
            variables=variables,
            skill_path=config.skill_path,
        )

        # Prepend skill description as context
        full_instructions = self._build_full_instructions(config, instructions)

        # Determine model
        agent_model = model or self.default_model

        # Build tools from sub-skills
        tools = []
        if sub_skill_configs:
            tools = self._build_sub_skill_tools(
                sub_skill_configs, variables, tool_descriptions
            )

        # Create agent
        agent_name = self._normalize_agent_name(config.name)

        agent = Agent(
            name=agent_name,
            instructions=full_instructions,
            model=agent_model,
            tools=tools if tools else None,
        )

        # Cache the agent
        self._agent_cache[cache_key] = agent

        logger.info(f"Built agent '{agent_name}' from skill '{config.name}'")
        return agent

    def build_agent_from_top_level_config(
        self,
        top_level_config: TopLevelAgentConfig,
        skill_config: SkillConfig,
        sub_skill_configs: Optional[List[SkillConfig]] = None,
        additional_variables: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """
        Build an Agent from top-level configuration.

        Args:
            top_level_config: Top-level agent configuration from agents.yaml
            skill_config: Main skill configuration
            sub_skill_configs: Sub-skill configurations (if any)
            additional_variables: Additional variables to merge with config variables

        Returns:
            Agent instance
        """
        # Merge variables
        variables = {}
        if top_level_config.variables:
            variables.update(top_level_config.variables)
        if additional_variables:
            variables.update(additional_variables)

        return self.build_agent_from_skill(
            config=skill_config,
            model=top_level_config.model,
            variables=variables,
            sub_skill_configs=sub_skill_configs,
            tool_descriptions=top_level_config.tool_descriptions,
        )

    def _build_full_instructions(
        self, config: SkillConfig, rendered_instructions: str
    ) -> str:
        """Build complete instructions with skill context."""
        parts = []

        # Add skill description as context
        parts.append(f"# {config.name}")
        parts.append("")
        parts.append(f"**Description**: {config.description}")
        parts.append("")

        # Add compatibility info if present
        if config.compatibility:
            parts.append(f"**Compatibility**: {config.compatibility}")
            parts.append("")

        # Add separator and main instructions
        parts.append("---")
        parts.append("")
        parts.append(rendered_instructions)

        # Add reference to available resources if present
        if config.scripts_path or config.references_path or config.assets_path:
            parts.append("")
            parts.append("## Available Resources")
            parts.append("")

            if config.scripts_path:
                scripts = list(config.scripts_path.iterdir())
                if scripts:
                    parts.append("**Scripts:**")
                    for script in scripts:
                        parts.append(f"- `scripts/{script.name}`")
                    parts.append("")

            if config.references_path:
                refs = list(config.references_path.iterdir())
                if refs:
                    parts.append("**References:**")
                    for ref in refs:
                        parts.append(f"- `references/{ref.name}`")
                    parts.append("")

            if config.assets_path:
                assets = list(config.assets_path.iterdir())
                if assets:
                    parts.append("**Assets:**")
                    for asset in assets:
                        parts.append(f"- `assets/{asset.name}`")
                    parts.append("")

        return "\n".join(parts)

    def _build_sub_skill_tools(
        self,
        sub_skill_configs: List[SkillConfig],
        variables: Dict[str, Any],
        tool_descriptions: Dict[str, str],
    ) -> List:
        """Build tools from sub-skill configurations."""
        tools = []

        for sub_skill in sub_skill_configs:
            # Build sub-agent (without its own sub-agents to avoid deep nesting)
            sub_agent = self.build_agent_from_skill(
                config=sub_skill,
                variables=variables,
            )

            # Generate tool name
            tool_name = self._normalize_tool_name(sub_skill.name)

            # Get tool description (from config, skill description, or default)
            tool_description = tool_descriptions.get(
                sub_skill.name,
                tool_descriptions.get(
                    sub_agent.name,
                    sub_skill.description,  # Use skill description as default
                ),
            )

            # Convert to tool
            tool = sub_agent.as_tool(
                tool_name=tool_name,
                tool_description=tool_description,
            )
            tools.append(tool)

            logger.debug(f"Added sub-skill '{sub_skill.name}' as tool '{tool_name}'")

        return tools

    def _normalize_agent_name(self, skill_name: str) -> str:
        """Convert skill name to agent name format."""
        # Convert hyphens to spaces and title case
        return skill_name.replace("-", " ").title()

    def _normalize_tool_name(self, skill_name: str) -> str:
        """Convert skill name to tool name format."""
        # Convert hyphens to underscores
        return skill_name.replace("-", "_")

    def clear_cache(self) -> None:
        """Clear the agent cache."""
        self._agent_cache.clear()
        logger.debug("Cleared agent cache")
