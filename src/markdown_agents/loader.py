"""
Agent Loader

Loads agent definitions from markdown and YAML files.
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any

from .builder import AgentConfig, AgentBuilder


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """Load YAML configuration file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_markdown_instructions(instructions_path: Path) -> str:
    """Load markdown instructions file."""
    with open(instructions_path, "r", encoding="utf-8") as f:
        return f.read()


def resolve_agent_path(base_path: Path, agent_reference: str) -> Path:
    """
    Resolve agent reference to a file path.

    Supports:
    - Relative paths: "subfolder/agent_name"
    - Absolute paths: "/full/path/to/agent"
    - Simple names: "agent_name" (searches in base_path)
    """
    if Path(agent_reference).is_absolute():
        return Path(agent_reference)

    # Try relative to base_path first
    relative_path = base_path / agent_reference
    if relative_path.exists():
        return relative_path

    # Try as direct child
    direct_path = base_path / f"{agent_reference}.yaml"
    if direct_path.exists():
        return direct_path.parent / agent_reference

    # Try in subdirectories
    for subdir in base_path.iterdir():
        if subdir.is_dir():
            potential_path = subdir / f"{agent_reference}.yaml"
            if potential_path.exists():
                return potential_path.parent / agent_reference

    # Default: assume it's relative to base_path
    return base_path / agent_reference


def load_agent_config_from_path(agent_path: Path) -> AgentConfig:
    """
    Load agent configuration from a directory or file path.

    Expected structure:
    - agent_name.yaml (configuration)
    - agent_name.md (instructions)

    Supports multiple structures:
    1. If agent_path is a YAML file: use parent directory and file stem
    2. If agent_path is a directory: look for agent_name.yaml and agent_name.md inside
    3. If agent_path is a directory but files are in parent: look in parent directory
    """
    if agent_path.is_file():
        # If it's a file, assume it's the YAML config
        agent_dir = agent_path.parent
        agent_name = agent_path.stem
        yaml_path = agent_path
    else:
        # If it's a directory, try multiple strategies
        agent_dir = agent_path
        agent_name = agent_path.name

        # Strategy 1: Files inside the directory
        yaml_path = agent_dir / f"{agent_name}.yaml"

        # Strategy 2: Files in parent directory (for flat structure)
        if not yaml_path.exists():
            yaml_path = agent_dir.parent / f"{agent_name}.yaml"
            if yaml_path.exists():
                agent_dir = agent_dir.parent

    md_path = agent_dir / f"{agent_name}.md"

    if not yaml_path.exists():
        raise FileNotFoundError(f"Agent config file not found: {yaml_path}")

    if not md_path.exists():
        raise FileNotFoundError(f"Agent instructions file not found: {md_path}")

    yaml_config = load_yaml_config(yaml_path)
    markdown_instructions = load_markdown_instructions(md_path)

    return AgentConfig(
        name=agent_name,
        base_path=agent_dir,
        yaml_config=yaml_config,
        markdown_instructions=markdown_instructions,
        yaml_path=yaml_path,
        markdown_path=md_path,
    )


def load_agent_from_path(
    agent_path: Path,
    variables: Optional[Dict[str, Any]] = None,
    builder: Optional[AgentBuilder] = None,
):
    """
    Load and build an agent from a file path.

    Args:
        agent_path: Path to agent directory or YAML file
        variables: Variables for Jinja2 templating
        builder: Optional AgentBuilder instance (creates new one if not provided)

    Returns:
        Agent instance
    """
    config = load_agent_config_from_path(agent_path)

    if builder is None:
        builder = AgentBuilder()

    return builder.build_agent(config, variables=variables)


def load_agent_from_file(
    agent_file: str,
    base_path: Optional[Path] = None,
    variables: Optional[Dict[str, Any]] = None,
    builder: Optional[AgentBuilder] = None,
):
    """
    Load and build an agent from a file path string.

    Args:
        agent_file: Path to agent (can be directory, YAML file, or agent name)
        base_path: Base path for resolving relative agent references
        variables: Variables for Jinja2 templating
        builder: Optional AgentBuilder instance

    Returns:
        Agent instance
    """
    agent_path = Path(agent_file)

    if not agent_path.is_absolute() and base_path:
        agent_path = base_path / agent_path

    return load_agent_from_path(agent_path, variables=variables, builder=builder)
