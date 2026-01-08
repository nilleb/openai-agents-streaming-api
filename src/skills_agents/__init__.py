"""
Skills-based Agent System

A file-based agent system implementing the Agent Skills specification.
Skills are defined by:
- SKILL.md files containing frontmatter (name, description) and markdown instructions
- Optional directories: scripts/, references/, assets/

This system discovers, validates, and converts skills to OpenAI Agents.
"""

from .models import SkillConfig, SkillMetadata, ValidationResult
from .discovery import discover_skills, discover_skill
from .validator import SkillValidator
from .builder import SkillBuilder
from .loader import (
    load_skill_from_path,
    load_skills_from_directory,
    load_top_level_agents,
)

__all__ = [
    # Models
    "SkillConfig",
    "SkillMetadata",
    "ValidationResult",
    # Discovery
    "discover_skills",
    "discover_skill",
    # Validation
    "SkillValidator",
    # Building
    "SkillBuilder",
    # Loading
    "load_skill_from_path",
    "load_skills_from_directory",
    "load_top_level_agents",
]
