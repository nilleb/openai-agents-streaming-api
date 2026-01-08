"""
Skill Validator Module

Validates skills according to the Agent Skills specification.
Based on skills-ref validation logic.
"""

import re
import logging
from pathlib import Path
from typing import Optional, List

from pydantic import ValidationError

from .models import (
    SkillConfig,
    SkillFrontmatter,
    ValidationResult,
)
from .discovery import parse_frontmatter, SkillParseError


logger = logging.getLogger(__name__)


# Validation constants from spec
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
RECOMMENDED_MAX_LINES = 500
RECOMMENDED_MAX_TOKENS = 5000

# Name pattern: lowercase alphanumeric and hyphens
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")


class SkillValidator:
    """
    Validator for Agent Skills.

    Validates SKILL.md files according to the Agent Skills specification.
    """

    def __init__(self, strict: bool = False):
        """
        Initialize the validator.

        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict

    def validate_skill_path(self, skill_path: Path) -> ValidationResult:
        """
        Validate a skill at the given path.

        Args:
            skill_path: Path to skill directory

        Returns:
            ValidationResult with validation status and issues
        """
        result = ValidationResult(is_valid=True, skill_path=skill_path)

        # Check directory exists
        if not skill_path.exists():
            result.add_error(f"Skill directory does not exist: {skill_path}")
            return result

        if not skill_path.is_dir():
            result.add_error(f"Skill path is not a directory: {skill_path}")
            return result

        # Check SKILL.md exists
        skill_md_path = skill_path / "SKILL.md"
        if not skill_md_path.exists():
            result.add_error("SKILL.md not found in skill directory")
            return result

        # Read and parse SKILL.md
        content = self._read_skill_file(skill_md_path, result)
        if content is None:
            return result

        # Parse frontmatter
        frontmatter_dict, body = self._parse_frontmatter(content, result)
        if frontmatter_dict is None:
            return result

        # Validate frontmatter
        self._validate_frontmatter(frontmatter_dict, skill_path, result)

        # Validate body content
        self._validate_body(body, result)

        # Validate optional directories
        self._validate_optional_directories(skill_path, result)

        # Apply strict mode
        if self.strict:
            for issue in result.warnings:
                result.add_error(f"[Strict] {issue.message}", issue.field, issue.line)

        return result

    def validate_skill_config(self, config: SkillConfig) -> ValidationResult:
        """
        Validate an already-loaded skill configuration.

        Args:
            config: SkillConfig to validate

        Returns:
            ValidationResult with validation status and issues
        """
        result = ValidationResult(is_valid=True, skill_path=config.skill_path)

        # Validate name
        self._validate_name(config.name, result)

        # Validate description
        self._validate_description(config.description, result)

        # Validate compatibility if present
        if config.compatibility:
            self._validate_compatibility(config.compatibility, result)

        # Validate directory name match
        if config.skill_path and config.skill_path.name != config.name:
            result.add_error(
                f"Skill name '{config.name}' must match directory name '{config.skill_path.name}'",
                field_name="name",
            )

        # Validate body content
        self._validate_body(config.instructions, result)

        return result

    def _read_skill_file(
        self, skill_md_path: Path, result: ValidationResult
    ) -> Optional[str]:
        """Read SKILL.md file content."""
        try:
            return skill_md_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            result.add_error(f"SKILL.md is not valid UTF-8: {e}")
            return None
        except IOError as e:
            result.add_error(f"Failed to read SKILL.md: {e}")
            return None

    def _parse_frontmatter(
        self, content: str, result: ValidationResult
    ) -> tuple[Optional[dict], Optional[str]]:
        """Parse and return frontmatter and body."""
        try:
            return parse_frontmatter(content)
        except SkillParseError as e:
            result.add_error(str(e))
            return None, None

    def _validate_frontmatter(
        self,
        frontmatter_dict: dict,
        skill_path: Path,
        result: ValidationResult,
    ) -> None:
        """Validate frontmatter fields."""
        # Check required fields
        if "name" not in frontmatter_dict:
            result.add_error("Required field 'name' is missing", field_name="name")
        else:
            self._validate_name(frontmatter_dict["name"], result)
            # Check name matches directory
            if frontmatter_dict["name"] != skill_path.name:
                result.add_error(
                    f"Skill name '{frontmatter_dict['name']}' must match directory name '{skill_path.name}'",
                    field_name="name",
                )

        if "description" not in frontmatter_dict:
            result.add_error(
                "Required field 'description' is missing", field_name="description"
            )
        else:
            self._validate_description(frontmatter_dict["description"], result)

        # Validate optional fields
        if "compatibility" in frontmatter_dict:
            self._validate_compatibility(frontmatter_dict["compatibility"], result)

        if "metadata" in frontmatter_dict:
            self._validate_metadata(frontmatter_dict["metadata"], result)

        if "allowed-tools" in frontmatter_dict:
            self._validate_allowed_tools(frontmatter_dict["allowed-tools"], result)

        # Try Pydantic validation for complete validation
        try:
            SkillFrontmatter(**frontmatter_dict)
        except ValidationError as e:
            for error in e.errors():
                field_name = ".".join(str(loc) for loc in error["loc"])
                result.add_error(error["msg"], field_name=field_name)

    def _validate_name(self, name: str, result: ValidationResult) -> None:
        """Validate skill name according to spec."""
        if not name:
            result.add_error("Name cannot be empty", field_name="name")
            return

        if len(name) > MAX_NAME_LENGTH:
            result.add_error(
                f"Name exceeds maximum length of {MAX_NAME_LENGTH} characters",
                field_name="name",
            )

        if not NAME_PATTERN.match(name):
            result.add_error(
                "Name may only contain lowercase letters, numbers, and hyphens",
                field_name="name",
            )

        if name.startswith("-") or name.endswith("-"):
            result.add_error(
                "Name must not start or end with a hyphen", field_name="name"
            )

        if "--" in name:
            result.add_error(
                "Name must not contain consecutive hyphens", field_name="name"
            )

    def _validate_description(self, description: str, result: ValidationResult) -> None:
        """Validate skill description."""
        if not description:
            result.add_error("Description cannot be empty", field_name="description")
            return

        if len(description) > MAX_DESCRIPTION_LENGTH:
            result.add_error(
                f"Description exceeds maximum length of {MAX_DESCRIPTION_LENGTH} characters",
                field_name="description",
            )

        # Quality warnings
        if len(description) < 50:
            result.add_warning(
                "Description is very short. Consider adding more detail about what the skill does and when to use it.",
                field_name="description",
            )

    def _validate_compatibility(
        self, compatibility: str, result: ValidationResult
    ) -> None:
        """Validate compatibility field."""
        if len(compatibility) > MAX_COMPATIBILITY_LENGTH:
            result.add_error(
                f"Compatibility exceeds maximum length of {MAX_COMPATIBILITY_LENGTH} characters",
                field_name="compatibility",
            )

    def _validate_metadata(self, metadata: dict, result: ValidationResult) -> None:
        """Validate metadata field."""
        if not isinstance(metadata, dict):
            result.add_error("Metadata must be a dictionary", field_name="metadata")
            return

        # Check for recommended metadata fields
        if "author" not in metadata:
            result.add_info(
                "Consider adding 'author' to metadata", field_name="metadata"
            )
        if "version" not in metadata:
            result.add_info(
                "Consider adding 'version' to metadata", field_name="metadata"
            )

    def _validate_allowed_tools(
        self, allowed_tools: str, result: ValidationResult
    ) -> None:
        """Validate allowed-tools field."""
        if not isinstance(allowed_tools, str):
            result.add_error(
                "allowed-tools must be a space-delimited string",
                field_name="allowed-tools",
            )

    def _validate_body(self, body: str, result: ValidationResult) -> None:
        """Validate markdown body content."""
        if not body or not body.strip():
            result.add_warning(
                "SKILL.md body is empty. Consider adding instructions.",
                field_name="body",
            )
            return

        # Check line count
        lines = body.split("\n")
        if len(lines) > RECOMMENDED_MAX_LINES:
            result.add_warning(
                f"SKILL.md body has {len(lines)} lines. "
                f"Consider keeping under {RECOMMENDED_MAX_LINES} lines and moving detailed content to references/.",
                field_name="body",
            )

        # Estimate token count (rough approximation: ~4 chars per token)
        estimated_tokens = len(body) // 4
        if estimated_tokens > RECOMMENDED_MAX_TOKENS:
            result.add_warning(
                f"SKILL.md body is approximately {estimated_tokens} tokens. "
                f"Consider keeping under {RECOMMENDED_MAX_TOKENS} tokens.",
                field_name="body",
            )

    def _validate_optional_directories(
        self, skill_path: Path, result: ValidationResult
    ) -> None:
        """Validate optional directories if present."""
        scripts_path = skill_path / "scripts"
        references_path = skill_path / "references"
        assets_path = skill_path / "assets"

        # Validate scripts/
        if scripts_path.exists():
            if not scripts_path.is_dir():
                result.add_error("'scripts' must be a directory")
            else:
                self._validate_scripts_directory(scripts_path, result)

        # Validate references/
        if references_path.exists():
            if not references_path.is_dir():
                result.add_error("'references' must be a directory")
            else:
                self._validate_references_directory(references_path, result)

        # Validate assets/
        if assets_path.exists():
            if not assets_path.is_dir():
                result.add_error("'assets' must be a directory")

    def _validate_scripts_directory(
        self, scripts_path: Path, result: ValidationResult
    ) -> None:
        """Validate scripts directory."""
        for script_file in scripts_path.iterdir():
            if script_file.is_file():
                # Check for shebang or recognized extension
                ext = script_file.suffix.lower()
                recognized_extensions = {".py", ".sh", ".bash", ".js", ".ts"}

                if ext not in recognized_extensions:
                    result.add_info(
                        f"Script '{script_file.name}' has unrecognized extension. "
                        f"Supported: {', '.join(recognized_extensions)}"
                    )

    def _validate_references_directory(
        self, references_path: Path, result: ValidationResult
    ) -> None:
        """Validate references directory."""
        for ref_file in references_path.iterdir():
            if ref_file.is_file():
                ext = ref_file.suffix.lower()
                if ext not in {".md", ".txt", ".json", ".yaml", ".yml"}:
                    result.add_info(
                        f"Reference file '{ref_file.name}' has unusual extension. "
                        "Consider using .md for documentation."
                    )


def validate_skill(skill_path: Path, strict: bool = False) -> ValidationResult:
    """
    Convenience function to validate a skill.

    Args:
        skill_path: Path to skill directory
        strict: If True, treat warnings as errors

    Returns:
        ValidationResult with validation status and issues
    """
    validator = SkillValidator(strict=strict)
    return validator.validate_skill_path(skill_path)


def validate_skills(
    skills_directory: Path, strict: bool = False, recursive: bool = True
) -> List[ValidationResult]:
    """
    Validate all skills in a directory (recursively by default).

    Args:
        skills_directory: Directory containing skill directories
        strict: If True, treat warnings as errors
        recursive: If True, search subdirectories recursively

    Returns:
        List of ValidationResult for each skill found
    """
    from .discovery import discover_skills

    results: List[ValidationResult] = []
    validator = SkillValidator(strict=strict)

    if not skills_directory.exists():
        return results

    # Use discover_skills for recursive search
    discovered = discover_skills(skills_directory, recursive=recursive)

    for skill_config in discovered:
        if skill_config.skill_path:
            result = validator.validate_skill_path(skill_config.skill_path)
            results.append(result)

    return results
