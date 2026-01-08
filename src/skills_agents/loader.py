"""
Skill Loader Module

High-level functions for loading skills and building agents.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import yaml

from agents import Agent

from .models import SkillConfig, AgentsConfig, TopLevelAgentConfig
from .discovery import discover_skill, discover_skills, find_skill_by_name
from .validator import SkillValidator, validate_skill
from .builder import SkillBuilder


logger = logging.getLogger(__name__)


def load_skill_from_path(
    skill_path: Path,
    validate: bool = True,
    strict: bool = False,
) -> SkillConfig:
    """
    Load a skill from a directory path.

    Args:
        skill_path: Path to skill directory containing SKILL.md
        validate: Whether to validate the skill
        strict: If True, treat validation warnings as errors

    Returns:
        SkillConfig with parsed skill data

    Raises:
        FileNotFoundError: If SKILL.md doesn't exist
        ValueError: If validation fails (when validate=True)
    """
    # Discover the skill
    config = discover_skill(skill_path)

    # Validate if requested
    if validate:
        validator = SkillValidator(strict=strict)
        result = validator.validate_skill_config(config)

        if not result.is_valid:
            error_messages = [e.message for e in result.errors]
            raise ValueError(
                f"Skill validation failed for '{config.name}': {'; '.join(error_messages)}"
            )

        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"Skill '{config.name}': {warning.message}")

    return config


def load_skills_from_directory(
    skills_directory: Path,
    validate: bool = True,
    strict: bool = False,
) -> Dict[str, SkillConfig]:
    """
    Load all skills from a directory.

    Args:
        skills_directory: Directory containing skill directories
        validate: Whether to validate skills
        strict: If True, treat validation warnings as errors

    Returns:
        Dictionary mapping skill names to SkillConfig objects
    """
    skills: Dict[str, SkillConfig] = {}

    discovered = discover_skills(skills_directory)

    for skill_config in discovered:
        if validate:
            if skill_config.skill_path is None:
                logger.error(
                    f"Skipping skill '{skill_config.name}': skill_path is None"
                )
                continue
            result = validate_skill(skill_config.skill_path, strict=strict)
            if not result.is_valid:
                logger.error(
                    f"Skipping invalid skill '{skill_config.name}': "
                    f"{[e.message for e in result.errors]}"
                )
                continue

            if result.warnings:
                for warning in result.warnings:
                    logger.warning(f"Skill '{skill_config.name}': {warning.message}")

        skills[skill_config.name] = skill_config

    logger.info(f"Loaded {len(skills)} skills from {skills_directory}")
    return skills


def load_agents_config(config_path: Path) -> AgentsConfig:
    """
    Load agents configuration from a YAML file.

    Args:
        config_path: Path to agents.yaml file

    Returns:
        AgentsConfig with parsed configuration
    """
    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f) or {}

    return AgentsConfig(**raw_config)


def load_top_level_agents(
    config_path: Path,
    skills_directory: Optional[Path] = None,
    variables: Optional[Dict[str, Any]] = None,
    validate: bool = True,
) -> Dict[str, Agent]:
    """
    Load top-level agents from configuration.

    This is the main entry point for loading agents from skills.

    Args:
        config_path: Path to agents.yaml configuration file
        skills_directory: Directory containing skills (defaults to config's skills_directory)
        variables: Additional variables for Jinja2 templating
        validate: Whether to validate skills

    Returns:
        Dictionary mapping agent names to Agent instances
    """
    if variables is None:
        variables = {}

    # Load agents configuration
    config = load_agents_config(config_path)

    # Determine skills directory
    if skills_directory is None:
        skills_directory = config_path.parent / config.skills_directory

    # Load all skills
    all_skills = load_skills_from_directory(
        skills_directory, validate=validate, strict=False
    )

    # Build agents
    builder = SkillBuilder(default_model=config.default_model)
    agents: Dict[str, Agent] = {}

    for agent_config in config.agents:
        agent = _build_top_level_agent(
            agent_config=agent_config,
            all_skills=all_skills,
            skills_directory=skills_directory,
            builder=builder,
            additional_variables=variables,
        )
        if agent:
            agents[agent_config.name] = agent

    logger.info(f"Loaded {len(agents)} top-level agents")
    return agents


def _build_top_level_agent(
    agent_config: TopLevelAgentConfig,
    all_skills: Dict[str, SkillConfig],
    skills_directory: Path,
    builder: SkillBuilder,
    additional_variables: Optional[Dict[str, Any]] = None,
) -> Optional[Agent]:
    """Build a single top-level agent."""
    # Find main skill
    main_skill = _resolve_skill(agent_config.skill, all_skills, skills_directory)

    if main_skill is None:
        logger.error(
            f"Skill '{agent_config.skill}' not found for agent '{agent_config.name}'"
        )
        return None

    # Find sub-skills
    sub_skills: List[SkillConfig] = []
    if agent_config.sub_agents:
        for sub_agent_ref in agent_config.sub_agents:
            sub_skill = _resolve_skill(sub_agent_ref, all_skills, skills_directory)
            if sub_skill:
                sub_skills.append(sub_skill)
            else:
                logger.warning(
                    f"Sub-skill '{sub_agent_ref}' not found for agent '{agent_config.name}'"
                )

    # Build agent
    agent = builder.build_agent_from_top_level_config(
        top_level_config=agent_config,
        skill_config=main_skill,
        sub_skill_configs=sub_skills if sub_skills else None,
        additional_variables=additional_variables,
    )

    return agent


def _resolve_skill(
    skill_reference: str,
    all_skills: Dict[str, SkillConfig],
    skills_directory: Path,
) -> Optional[SkillConfig]:
    """Resolve a skill reference to a SkillConfig."""
    # Try direct name match first
    if skill_reference in all_skills:
        return all_skills[skill_reference]

    # Try to find by path
    skill_path = Path(skill_reference)
    if skill_path.is_absolute():
        if (skill_path / "SKILL.md").exists():
            return discover_skill(skill_path)
    else:
        # Try relative to skills directory
        relative_path = skills_directory / skill_reference
        if (relative_path / "SKILL.md").exists():
            return discover_skill(relative_path)

    # Try find_skill_by_name
    found_path = find_skill_by_name(skill_reference, skills_directory)
    if found_path:
        return discover_skill(found_path)

    return None


def build_agent_from_skill_path(
    skill_path: Path,
    model: Optional[str] = None,
    variables: Optional[Dict[str, Any]] = None,
    validate: bool = True,
) -> Agent:
    """
    Convenience function to build an agent directly from a skill path.

    Args:
        skill_path: Path to skill directory
        model: Model to use (defaults to gpt-4.1-mini)
        variables: Variables for Jinja2 templating
        validate: Whether to validate the skill

    Returns:
        Agent instance
    """
    config = load_skill_from_path(skill_path, validate=validate)

    builder = SkillBuilder(default_model=model or "gpt-4.1-mini")
    return builder.build_agent_from_skill(
        config=config,
        model=model,
        variables=variables,
    )
