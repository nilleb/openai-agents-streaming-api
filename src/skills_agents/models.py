"""
Pydantic models for Agent Skills specification.

Based on the Agent Skills format specification:
https://agentskills.io/docs/spec
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ValidationSeverity(str, Enum):
    """Severity level for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    message: str
    severity: ValidationSeverity
    field: Optional[str] = None
    line: Optional[int] = None


@dataclass
class ValidationResult:
    """Result of skill validation."""

    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    skill_path: Optional[Path] = None

    def add_error(
        self, message: str, field_name: Optional[str] = None, line: Optional[int] = None
    ) -> None:
        """Add an error issue."""
        self.issues.append(
            ValidationIssue(
                message=message,
                severity=ValidationSeverity.ERROR,
                field=field_name,
                line=line,
            )
        )
        self.is_valid = False

    def add_warning(
        self, message: str, field_name: Optional[str] = None, line: Optional[int] = None
    ) -> None:
        """Add a warning issue."""
        self.issues.append(
            ValidationIssue(
                message=message,
                severity=ValidationSeverity.WARNING,
                field=field_name,
                line=line,
            )
        )

    def add_info(
        self, message: str, field_name: Optional[str] = None, line: Optional[int] = None
    ) -> None:
        """Add an info issue."""
        self.issues.append(
            ValidationIssue(
                message=message,
                severity=ValidationSeverity.INFO,
                field=field_name,
                line=line,
            )
        )

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]


class SkillMetadata(BaseModel):
    """
    Arbitrary key-value metadata for a skill.

    Clients can use this to store additional properties not defined by the spec.
    """

    model_config = {"extra": "allow"}


class SkillFrontmatter(BaseModel):
    """
    YAML frontmatter for a SKILL.md file.

    Based on the Agent Skills specification.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Skill name: 1-64 chars, lowercase alphanumeric and hyphens only",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Description of what the skill does and when to use it",
    )
    license: Optional[str] = Field(
        default=None,
        description="License name or reference to a bundled license file",
    )
    compatibility: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Environment requirements (product, system packages, network access)",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Arbitrary key-value mapping for additional metadata",
    )
    allowed_tools: Optional[str] = Field(
        default=None,
        alias="allowed-tools",
        description="Space-delimited list of pre-approved tools (experimental)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate skill name according to specification:
        - May only contain lowercase alphanumeric and hyphens
        - Must not start or end with hyphen
        - Must not contain consecutive hyphens
        """
        if not v:
            raise ValueError("Name cannot be empty")

        # Check for lowercase only (alphanumeric and hyphens)
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Name may only contain lowercase letters, numbers, and hyphens"
            )

        # Check for hyphen at start or end
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Name must not start or end with a hyphen")

        # Check for consecutive hyphens
        if "--" in v:
            raise ValueError("Name must not contain consecutive hyphens")

        return v


@dataclass
class SkillConfig:
    """
    Complete configuration for a loaded skill.

    Contains parsed frontmatter, markdown body, and file paths.
    """

    # Frontmatter fields
    name: str
    description: str
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    allowed_tools: Optional[List[str]] = None

    # Content
    instructions: str = ""  # Markdown body content

    # Paths
    skill_path: Optional[Path] = None  # Path to skill directory
    skill_md_path: Optional[Path] = None  # Path to SKILL.md file

    # Optional directories
    scripts_path: Optional[Path] = None
    references_path: Optional[Path] = None
    assets_path: Optional[Path] = None

    @classmethod
    def from_frontmatter(
        cls,
        frontmatter: SkillFrontmatter,
        instructions: str,
        skill_path: Path,
        skill_md_path: Path,
    ) -> "SkillConfig":
        """Create a SkillConfig from parsed frontmatter and instructions."""
        # Parse allowed_tools from space-delimited string to list
        allowed_tools = None
        if frontmatter.allowed_tools:
            allowed_tools = frontmatter.allowed_tools.split()

        # Check for optional directories
        scripts_path = skill_path / "scripts"
        references_path = skill_path / "references"
        assets_path = skill_path / "assets"

        return cls(
            name=frontmatter.name,
            description=frontmatter.description,
            license=frontmatter.license,
            compatibility=frontmatter.compatibility,
            metadata=frontmatter.metadata,
            allowed_tools=allowed_tools,
            instructions=instructions,
            skill_path=skill_path,
            skill_md_path=skill_md_path,
            scripts_path=scripts_path if scripts_path.exists() else None,
            references_path=references_path if references_path.exists() else None,
            assets_path=assets_path if assets_path.exists() else None,
        )


class TopLevelAgentConfig(BaseModel):
    """
    Configuration for a top-level agent exposed through the API.

    Defined in agents.yaml file.
    """

    name: str = Field(..., description="Agent name for the API")
    skill: str = Field(..., description="Path or name of the skill to use")
    model: str = Field(
        default="gpt-4.1-mini", description="Model to use for this agent"
    )
    sub_agents: Optional[List[str]] = Field(
        default=None, description="List of sub-agent skill references"
    )
    tool_descriptions: Optional[Dict[str, str]] = Field(
        default=None, description="Custom tool descriptions for sub-agents"
    )
    variables: Optional[Dict[str, Any]] = Field(
        default=None, description="Variables for Jinja2 templating"
    )


class AgentsConfig(BaseModel):
    """
    Root configuration for top-level agents.

    Loaded from agents.yaml file.
    """

    agents: List[TopLevelAgentConfig] = Field(
        ..., description="List of top-level agents to expose"
    )
    default_model: str = Field(
        default="gpt-4.1-mini", description="Default model for all agents"
    )
    skills_directory: str = Field(
        default="skills", description="Directory containing skill definitions"
    )
