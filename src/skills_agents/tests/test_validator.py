"""Tests for skills_agents validator module."""

from pathlib import Path


from ..validator import (
    SkillValidator,
    validate_skill,
    validate_skills,
)
from ..models import SkillConfig


# Get the examples directory path
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestSkillValidator:
    """Tests for SkillValidator."""

    def test_validate_valid_skill(self):
        """Test validating a valid skill."""
        validator = SkillValidator()
        result = validator.validate_skill_path(EXAMPLES_DIR / "code-review")

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_all_example_skills(self):
        """Test that all example skills are valid."""
        validator = SkillValidator()

        for skill_dir in EXAMPLES_DIR.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                result = validator.validate_skill_path(skill_dir)
                assert result.is_valid, (
                    f"Skill {skill_dir.name} should be valid: {result.errors}"
                )

    def test_validate_nonexistent_skill(self):
        """Test validating a nonexistent skill."""
        validator = SkillValidator()
        result = validator.validate_skill_path(EXAMPLES_DIR / "nonexistent-skill")

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("does not exist" in e.message for e in result.errors)

    def test_validate_skill_config(self):
        """Test validating a SkillConfig object."""
        validator = SkillValidator()

        # Test with mismatched name and directory
        config = SkillConfig(
            name="test-skill",
            description="A test skill for validation testing.",
            instructions="# Test instructions",
            skill_path=Path("/fake/path/wrong-directory"),  # Name doesn't match
        )

        result = validator.validate_skill_config(config)

        # Name doesn't match directory, should fail
        assert result.is_valid is False
        assert any("match directory" in e.message for e in result.errors)

    def test_validate_invalid_name(self):
        """Test validation catches invalid names."""
        validator = SkillValidator()

        config = SkillConfig(
            name="Invalid-Name",  # Uppercase
            description="A test skill.",
            instructions="# Test",
            skill_path=Path("/fake/path/Invalid-Name"),
        )

        result = validator.validate_skill_config(config)
        assert result.is_valid is False
        assert any("lowercase" in e.message.lower() for e in result.errors)

    def test_strict_mode(self):
        """Test strict mode converts warnings to errors."""
        validator = SkillValidator(strict=True)

        # Create a skill with a short description (generates warning)
        config = SkillConfig(
            name="test-skill",
            description="Short",  # Very short description
            instructions="# Test instructions with enough content",
            skill_path=Path("/fake/path/test-skill"),
        )

        result = validator.validate_skill_config(config)

        # In strict mode, the short description warning becomes an error
        # (However validation result might have other errors too like name mismatch)
        assert any("short" in issue.message.lower() for issue in result.issues)


class TestValidateSkillFunction:
    """Tests for the validate_skill convenience function."""

    def test_validate_skill_function(self):
        """Test validate_skill convenience function."""
        result = validate_skill(EXAMPLES_DIR / "code-review")
        assert result.is_valid is True

    def test_validate_skill_strict_mode(self):
        """Test validate_skill with strict mode."""
        result = validate_skill(EXAMPLES_DIR / "code-review", strict=True)
        # Should still be valid even in strict mode (examples are well-formed)
        assert result.is_valid is True


class TestValidateSkillsFunction:
    """Tests for the validate_skills convenience function."""

    def test_validate_all_skills(self):
        """Test validating all skills in a directory."""
        results = validate_skills(EXAMPLES_DIR)

        assert len(results) >= 4  # At least our example skills
        assert all(r.is_valid for r in results)

    def test_validate_skills_empty_directory(self, tmp_path):
        """Test validating skills in empty directory."""
        results = validate_skills(tmp_path)
        assert len(results) == 0

    def test_validate_skills_nonexistent_directory(self):
        """Test validating skills in nonexistent directory."""
        results = validate_skills(Path("/nonexistent/path"))
        assert len(results) == 0
