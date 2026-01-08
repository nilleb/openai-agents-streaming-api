"""
Skill Discovery Module

Discovers skill directories containing SKILL.md files.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import yaml

from .models import SkillConfig, SkillFrontmatter


logger = logging.getLogger(__name__)


class SkillParseError(Exception):
    """Error parsing a skill file."""

    pass


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Expected format:
    ---
    key: value
    ---
    Markdown body content...

    Returns:
        Tuple of (frontmatter_dict, body_content)

    Raises:
        SkillParseError: If frontmatter is missing or malformed
    """
    # Check for frontmatter delimiter
    if not content.startswith("---"):
        raise SkillParseError("SKILL.md must start with YAML frontmatter (---)")

    # Find the closing delimiter
    lines = content.split("\n")
    end_index = -1

    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index == -1:
        raise SkillParseError("YAML frontmatter closing delimiter (---) not found")

    # Extract frontmatter and body
    frontmatter_lines = lines[1:end_index]
    body_lines = lines[end_index + 1 :]

    frontmatter_text = "\n".join(frontmatter_lines)
    body_text = "\n".join(body_lines).strip()

    # Parse YAML frontmatter
    frontmatter_dict = yaml.safe_load(frontmatter_text) or {}

    if not isinstance(frontmatter_dict, dict):
        raise SkillParseError("YAML frontmatter must be a dictionary")

    return frontmatter_dict, body_text


def discover_skill(skill_path: Path) -> SkillConfig:
    """
    Discover and parse a single skill from a directory.

    Args:
        skill_path: Path to skill directory containing SKILL.md

    Returns:
        SkillConfig with parsed skill data

    Raises:
        FileNotFoundError: If SKILL.md doesn't exist
        SkillParseError: If SKILL.md is malformed
    """
    skill_md_path = skill_path / "SKILL.md"

    if not skill_md_path.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_path}")

    logger.debug(f"Loading skill from {skill_md_path}")

    # Read SKILL.md content
    content = skill_md_path.read_text(encoding="utf-8")

    # Parse frontmatter and body
    frontmatter_dict, body = parse_frontmatter(content)

    # Validate frontmatter with Pydantic
    frontmatter = SkillFrontmatter(**frontmatter_dict)

    # Verify skill name matches directory name
    if frontmatter.name != skill_path.name:
        logger.warning(
            f"Skill name '{frontmatter.name}' does not match directory name '{skill_path.name}'"
        )

    # Create SkillConfig
    return SkillConfig.from_frontmatter(
        frontmatter=frontmatter,
        instructions=body,
        skill_path=skill_path,
        skill_md_path=skill_md_path,
    )


def discover_skills(
    base_path: Path,
    recursive: bool = True,
    max_depth: int = 3,
) -> List[SkillConfig]:
    """
    Discover all skills in a directory.

    A skill is a directory containing a SKILL.md file.

    Args:
        base_path: Base directory to search
        recursive: Whether to search subdirectories
        max_depth: Maximum directory depth to search (for recursive)

    Returns:
        List of SkillConfig objects for discovered skills
    """
    if not base_path.exists():
        logger.warning(f"Skills directory does not exist: {base_path}")
        return []

    if not base_path.is_dir():
        logger.warning(f"Skills path is not a directory: {base_path}")
        return []

    skills: List[SkillConfig] = []

    # Search for SKILL.md files
    skill_files = _find_skill_files(base_path, recursive, max_depth, current_depth=0)

    for skill_md_path in skill_files:
        skill_path = skill_md_path.parent

        skill_config = _try_load_skill(skill_path)
        if skill_config:
            skills.append(skill_config)

    logger.info(f"Discovered {len(skills)} skills in {base_path}")
    return skills


def _find_skill_files(
    directory: Path,
    recursive: bool,
    max_depth: int,
    current_depth: int,
) -> List[Path]:
    """Find all SKILL.md files in a directory."""
    skill_files: List[Path] = []

    # Check current directory
    skill_md = directory / "SKILL.md"
    if skill_md.exists():
        skill_files.append(skill_md)

    # Search subdirectories if recursive
    if recursive and current_depth < max_depth:
        for subdir in directory.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("."):
                skill_files.extend(
                    _find_skill_files(
                        subdir,
                        recursive,
                        max_depth,
                        current_depth + 1,
                    )
                )

    return skill_files


def _try_load_skill(skill_path: Path) -> Optional[SkillConfig]:
    """Try to load a skill, returning None on failure."""
    try:
        return discover_skill(skill_path)
    except FileNotFoundError as e:
        logger.warning(f"Skill file not found: {e}")
    except SkillParseError as e:
        logger.error(f"Failed to parse skill at {skill_path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading skill at {skill_path}: {e}")
    return None


def find_skill_by_name(
    name: str,
    base_path: Path,
) -> Optional[Path]:
    """
    Find a skill directory by name.

    Args:
        name: Skill name to find
        base_path: Base directory to search

    Returns:
        Path to skill directory or None if not found
    """
    # Direct match
    direct_path = base_path / name
    if (direct_path / "SKILL.md").exists():
        return direct_path

    # Search recursively
    skills = discover_skills(base_path)
    for skill in skills:
        if skill.name == name:
            return skill.skill_path

    return None
