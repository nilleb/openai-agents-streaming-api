"""Tests for skills_agents models."""

import pytest
from pydantic import ValidationError

from ..models import (
    SkillFrontmatter,
    ValidationResult,
    TopLevelAgentConfig,
    AgentsConfig,
)


class TestSkillFrontmatter:
    """Tests for SkillFrontmatter model."""

    def test_valid_frontmatter(self):
        """Test valid frontmatter parsing."""
        frontmatter = SkillFrontmatter(
            name="test-skill",
            description="A test skill for testing purposes.",
        )
        assert frontmatter.name == "test-skill"
        assert frontmatter.description == "A test skill for testing purposes."

    def test_valid_frontmatter_with_all_fields(self):
        """Test frontmatter with all optional fields."""
        frontmatter = SkillFrontmatter(
            name="full-skill",
            description="A complete skill with all fields.",
            license="MIT",
            compatibility="Requires Python 3.10+",
            metadata={"author": "test", "version": "1.0"},
            **{"allowed-tools": "Read Write Execute"},
        )
        assert frontmatter.name == "full-skill"
        assert frontmatter.license == "MIT"
        assert frontmatter.compatibility == "Requires Python 3.10+"
        assert frontmatter.metadata == {"author": "test", "version": "1.0"}
        assert frontmatter.allowed_tools == "Read Write Execute"

    def test_invalid_name_uppercase(self):
        """Test that uppercase names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SkillFrontmatter(
                name="Test-Skill",
                description="A test skill.",
            )
        assert "lowercase" in str(exc_info.value).lower()

    def test_invalid_name_starts_with_hyphen(self):
        """Test that names starting with hyphen are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SkillFrontmatter(
                name="-test-skill",
                description="A test skill.",
            )
        assert "hyphen" in str(exc_info.value).lower()

    def test_invalid_name_ends_with_hyphen(self):
        """Test that names ending with hyphen are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SkillFrontmatter(
                name="test-skill-",
                description="A test skill.",
            )
        assert "hyphen" in str(exc_info.value).lower()

    def test_invalid_name_consecutive_hyphens(self):
        """Test that names with consecutive hyphens are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SkillFrontmatter(
                name="test--skill",
                description="A test skill.",
            )
        assert "consecutive" in str(exc_info.value).lower()

    def test_invalid_name_special_characters(self):
        """Test that names with special characters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SkillFrontmatter(
                name="test_skill",
                description="A test skill.",
            )
        assert "lowercase" in str(exc_info.value).lower() or "alphanumeric" in str(
            exc_info.value
        ).lower()

    def test_name_too_long(self):
        """Test that names exceeding 64 characters are rejected."""
        with pytest.raises(ValidationError):
            SkillFrontmatter(
                name="a" * 65,
                description="A test skill.",
            )

    def test_description_too_long(self):
        """Test that descriptions exceeding 1024 characters are rejected."""
        with pytest.raises(ValidationError):
            SkillFrontmatter(
                name="test-skill",
                description="a" * 1025,
            )

    def test_empty_name(self):
        """Test that empty names are rejected."""
        with pytest.raises(ValidationError):
            SkillFrontmatter(
                name="",
                description="A test skill.",
            )

    def test_empty_description(self):
        """Test that empty descriptions are rejected."""
        with pytest.raises(ValidationError):
            SkillFrontmatter(
                name="test-skill",
                description="",
            )


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_initial_valid_state(self):
        """Test initial valid state."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_add_error_invalidates(self):
        """Test that adding an error invalidates the result."""
        result = ValidationResult(is_valid=True)
        result.add_error("Test error")
        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_add_warning_preserves_validity(self):
        """Test that warnings don't invalidate the result."""
        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning")
        assert result.is_valid is True
        assert len(result.warnings) == 1

    def test_error_and_warning_counts(self):
        """Test error and warning filtering."""
        result = ValidationResult(is_valid=True)
        result.add_error("Error 1")
        result.add_error("Error 2")
        result.add_warning("Warning 1")
        result.add_info("Info 1")

        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert len(result.issues) == 4


class TestTopLevelAgentConfig:
    """Tests for TopLevelAgentConfig."""

    def test_minimal_config(self):
        """Test minimal configuration."""
        config = TopLevelAgentConfig(
            name="Test Agent",
            skill="test-skill",
        )
        assert config.name == "Test Agent"
        assert config.skill == "test-skill"
        assert config.model == "gpt-4.1-mini"  # default

    def test_full_config(self):
        """Test full configuration."""
        config = TopLevelAgentConfig(
            name="Orchestrator",
            skill="orchestrator-skill",
            model="gpt-4",
            sub_agents=["skill-a", "skill-b"],
            tool_descriptions={"skill-a": "Description A"},
            variables={"key": "value"},
        )
        assert config.name == "Orchestrator"
        assert config.model == "gpt-4"
        assert len(config.sub_agents) == 2
        assert config.tool_descriptions["skill-a"] == "Description A"
        assert config.variables["key"] == "value"


class TestAgentsConfig:
    """Tests for AgentsConfig."""

    def test_minimal_config(self):
        """Test minimal agents configuration."""
        config = AgentsConfig(
            agents=[
                TopLevelAgentConfig(name="Agent 1", skill="skill-1"),
            ]
        )
        assert len(config.agents) == 1
        assert config.default_model == "gpt-4.1-mini"
        assert config.skills_directory == "skills"

    def test_full_config(self):
        """Test full agents configuration."""
        config = AgentsConfig(
            agents=[
                TopLevelAgentConfig(name="Agent 1", skill="skill-1"),
                TopLevelAgentConfig(name="Agent 2", skill="skill-2"),
            ],
            default_model="gpt-4",
            skills_directory="custom-skills",
        )
        assert len(config.agents) == 2
        assert config.default_model == "gpt-4"
        assert config.skills_directory == "custom-skills"
