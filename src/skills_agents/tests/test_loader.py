"""Tests for skills_agents loader module."""

from pathlib import Path

import pytest

from ..loader import (
    load_skill_from_path,
    load_skills_from_directory,
    load_agents_config,
    load_top_level_agents,
    build_agent_from_skill_path,
)
from ..models import AgentsConfig


# Get the examples directory path
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestLoadSkillFromPath:
    """Tests for load_skill_from_path."""

    def test_load_valid_skill(self):
        """Test loading a valid skill."""
        config = load_skill_from_path(EXAMPLES_DIR / "code-review")

        assert config.name == "code-review"
        assert config.description is not None
        assert config.instructions is not None

    def test_load_skill_without_validation(self):
        """Test loading a skill without validation."""
        config = load_skill_from_path(
            EXAMPLES_DIR / "code-review",
            validate=False,
        )

        assert config.name == "code-review"

    def test_load_nonexistent_skill(self):
        """Test loading a nonexistent skill raises error."""
        with pytest.raises(FileNotFoundError):
            load_skill_from_path(EXAMPLES_DIR / "nonexistent-skill")


class TestLoadSkillsFromDirectory:
    """Tests for load_skills_from_directory."""

    def test_load_all_skills(self):
        """Test loading all skills from a directory."""
        skills = load_skills_from_directory(EXAMPLES_DIR)

        assert len(skills) >= 4
        assert "code-review" in skills
        assert "data-analysis" in skills
        assert "research-assistant" in skills
        assert "task-orchestrator" in skills

    def test_load_skills_empty_directory(self, tmp_path):
        """Test loading skills from empty directory."""
        skills = load_skills_from_directory(tmp_path)
        assert len(skills) == 0


class TestLoadAgentsConfig:
    """Tests for load_agents_config."""

    def test_load_agents_config(self):
        """Test loading agents configuration."""
        config = load_agents_config(EXAMPLES_DIR / "agents.yaml")

        assert isinstance(config, AgentsConfig)
        assert len(config.agents) > 0
        assert config.default_model == "gpt-4.1-mini"

    def test_agents_config_structure(self):
        """Test agents configuration structure."""
        config = load_agents_config(EXAMPLES_DIR / "agents.yaml")

        # Check orchestrator agent
        orchestrator = next(
            (a for a in config.agents if a.name == "Orchestrator"), None
        )
        assert orchestrator is not None
        assert orchestrator.skill == "task-orchestrator"
        assert orchestrator.sub_agents is not None
        assert len(orchestrator.sub_agents) >= 3


class TestLoadTopLevelAgents:
    """Tests for load_top_level_agents."""

    def test_load_top_level_agents(self):
        """Test loading top-level agents."""
        agents = load_top_level_agents(EXAMPLES_DIR / "agents.yaml")

        assert len(agents) > 0
        assert "Orchestrator" in agents
        assert "Code Reviewer" in agents
        assert "Data Analyst" in agents

    def test_orchestrator_has_tools(self):
        """Test that orchestrator agent has sub-agent tools."""
        agents = load_top_level_agents(EXAMPLES_DIR / "agents.yaml")

        orchestrator = agents["Orchestrator"]
        assert orchestrator.tools is not None
        assert len(orchestrator.tools) >= 3

        tool_names = [t.name for t in orchestrator.tools]
        assert "code_review" in tool_names
        assert "data_analysis" in tool_names
        assert "research_assistant" in tool_names

    def test_load_with_additional_variables(self):
        """Test loading agents with additional variables."""
        agents = load_top_level_agents(
            EXAMPLES_DIR / "agents.yaml",
            variables={"current_date": "2024-01-15"},
        )

        data_analyst = agents["Data Analyst"]
        # Variable should be rendered in instructions
        assert "2024-01-15" in data_analyst.instructions


class TestBuildAgentFromSkillPath:
    """Tests for build_agent_from_skill_path convenience function."""

    def test_build_agent_directly(self):
        """Test building an agent directly from skill path."""
        agent = build_agent_from_skill_path(EXAMPLES_DIR / "code-review")

        assert agent.name == "Code Review"
        assert agent.model == "gpt-4.1-mini"
        assert agent.instructions is not None

    def test_build_agent_with_custom_model(self):
        """Test building an agent with custom model."""
        agent = build_agent_from_skill_path(
            EXAMPLES_DIR / "code-review",
            model="gpt-4",
        )

        assert agent.model == "gpt-4"

    def test_build_agent_with_variables(self):
        """Test building an agent with variables."""
        agent = build_agent_from_skill_path(
            EXAMPLES_DIR / "data-analysis",
            variables={"current_date": "2024-06-01", "analysis_type": "Financial"},
        )

        assert "2024-06-01" in agent.instructions
        assert "Financial" in agent.instructions
