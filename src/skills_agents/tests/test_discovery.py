"""Tests for skills_agents discovery module."""

from pathlib import Path
from textwrap import dedent

import pytest

from ..discovery import (
    parse_frontmatter,
    discover_skill,
    discover_skills,
    find_skill_by_name,
    SkillParseError,
)


# Get the examples directory path
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestParseFrontmatter:
    """Tests for frontmatter parsing."""

    def test_valid_frontmatter(self):
        """Test parsing valid frontmatter."""
        content = dedent("""
            ---
            name: test-skill
            description: A test skill.
            ---
            # Body content
            
            Some instructions here.
        """).strip()

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "A test skill."
        assert "Body content" in body

    def test_frontmatter_with_all_fields(self):
        """Test parsing frontmatter with all optional fields."""
        content = dedent("""
            ---
            name: full-skill
            description: A complete skill.
            license: MIT
            compatibility: Python 3.10+
            metadata:
              author: test
              version: "1.0"
            allowed-tools: Read Write
            ---
            Body content
        """).strip()

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["name"] == "full-skill"
        assert frontmatter["license"] == "MIT"
        assert frontmatter["compatibility"] == "Python 3.10+"
        assert frontmatter["metadata"]["author"] == "test"
        assert frontmatter["allowed-tools"] == "Read Write"

    def test_missing_frontmatter_start(self):
        """Test error when frontmatter start delimiter is missing."""
        content = "No frontmatter here"

        with pytest.raises(SkillParseError, match="must start with"):
            parse_frontmatter(content)

    def test_missing_frontmatter_end(self):
        """Test error when frontmatter end delimiter is missing."""
        content = dedent("""
            ---
            name: test-skill
            description: Missing end delimiter
        """).strip()

        with pytest.raises(SkillParseError, match="closing delimiter"):
            parse_frontmatter(content)

    def test_empty_frontmatter(self):
        """Test parsing empty frontmatter."""
        content = dedent("""
            ---
            ---
            Body only
        """).strip()

        frontmatter, body = parse_frontmatter(content)
        assert frontmatter == {}
        assert "Body only" in body


class TestDiscoverSkill:
    """Tests for discovering a single skill."""

    def test_discover_existing_skill(self):
        """Test discovering an existing skill."""
        skill_path = EXAMPLES_DIR / "code-review"
        config = discover_skill(skill_path)

        assert config.name == "code-review"
        assert "code" in config.description.lower()
        assert config.skill_path == skill_path
        assert config.skill_md_path == skill_path / "SKILL.md"

    def test_discover_skill_with_metadata(self):
        """Test discovering a skill with metadata."""
        skill_path = EXAMPLES_DIR / "code-review"
        config = discover_skill(skill_path)

        assert config.metadata is not None
        assert config.metadata.get("author") == "agentic-framework"

    def test_discover_nonexistent_skill(self):
        """Test error when skill doesn't exist."""
        skill_path = EXAMPLES_DIR / "nonexistent-skill"

        with pytest.raises(FileNotFoundError, match="SKILL.md not found"):
            discover_skill(skill_path)


class TestDiscoverSkills:
    """Tests for discovering multiple skills."""

    def test_discover_all_skills(self):
        """Test discovering all skills in examples directory."""
        skills = discover_skills(EXAMPLES_DIR)

        assert len(skills) >= 4  # We created at least 4 example skills
        skill_names = [s.name for s in skills]
        assert "code-review" in skill_names
        assert "data-analysis" in skill_names
        assert "research-assistant" in skill_names
        assert "task-orchestrator" in skill_names

    def test_discover_skills_nonexistent_directory(self):
        """Test discovering skills from nonexistent directory."""
        skills = discover_skills(Path("/nonexistent/path"))
        assert len(skills) == 0


class TestFindSkillByName:
    """Tests for finding skills by name."""

    def test_find_existing_skill(self):
        """Test finding an existing skill by name."""
        path = find_skill_by_name("code-review", EXAMPLES_DIR)

        assert path is not None
        assert path.name == "code-review"
        assert (path / "SKILL.md").exists()

    def test_find_nonexistent_skill(self):
        """Test finding a nonexistent skill."""
        path = find_skill_by_name("nonexistent-skill", EXAMPLES_DIR)
        assert path is None
