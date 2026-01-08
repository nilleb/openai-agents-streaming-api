"""Tests for skills_agents builder module."""

from pathlib import Path


from ..builder import SkillBuilder
from ..discovery import discover_skill
from ..models import TopLevelAgentConfig


# Get the examples directory path
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestSkillBuilder:
    """Tests for SkillBuilder."""

    def test_build_simple_skill_agent(self):
        """Test building an agent from a simple skill."""
        builder = SkillBuilder()
        config = discover_skill(EXAMPLES_DIR / "code-review")

        agent = builder.build_agent_from_skill(config)

        assert agent.name == "Code Review"  # Normalized from code-review
        assert agent.model == "gpt-4.1-mini"
        assert agent.instructions is not None
        assert len(agent.instructions) > 0

    def test_build_agent_with_custom_model(self):
        """Test building an agent with a custom model."""
        builder = SkillBuilder()
        config = discover_skill(EXAMPLES_DIR / "code-review")

        agent = builder.build_agent_from_skill(config, model="gpt-4")

        assert agent.model == "gpt-4"

    def test_build_agent_with_variables(self):
        """Test building an agent with Jinja2 variables."""
        builder = SkillBuilder()
        config = discover_skill(EXAMPLES_DIR / "data-analysis")

        variables = {
            "current_date": "2024-01-15",
            "analysis_type": "Financial",
        }
        agent = builder.build_agent_from_skill(config, variables=variables)

        # Check that variables were rendered
        instructions = agent.instructions
        assert "2024-01-15" in instructions
        assert "Financial" in instructions
        assert "{{ current_date }}" not in instructions

    def test_build_agent_with_sub_skills(self):
        """Test building an agent with sub-skills as tools."""
        builder = SkillBuilder()

        main_config = discover_skill(EXAMPLES_DIR / "task-orchestrator")
        sub_configs = [
            discover_skill(EXAMPLES_DIR / "code-review"),
            discover_skill(EXAMPLES_DIR / "data-analysis"),
        ]

        agent = builder.build_agent_from_skill(
            config=main_config,
            sub_skill_configs=sub_configs,
        )

        assert agent.tools is not None
        assert len(agent.tools) == 2

        tool_names = [t.name for t in agent.tools]
        assert "code_review" in tool_names
        assert "data_analysis" in tool_names

    def test_custom_tool_descriptions(self):
        """Test custom tool descriptions for sub-skills."""
        builder = SkillBuilder()

        main_config = discover_skill(EXAMPLES_DIR / "task-orchestrator")
        sub_configs = [
            discover_skill(EXAMPLES_DIR / "code-review"),
        ]

        tool_descriptions = {
            "code-review": "Custom description for code review",
        }

        agent = builder.build_agent_from_skill(
            config=main_config,
            sub_skill_configs=sub_configs,
            tool_descriptions=tool_descriptions,
        )

        assert agent.tools is not None
        code_review_tool = next(t for t in agent.tools if t.name == "code_review")
        assert code_review_tool.description == "Custom description for code review"

    def test_default_tool_description_from_skill(self):
        """Test that tool description defaults to skill description."""
        builder = SkillBuilder()

        main_config = discover_skill(EXAMPLES_DIR / "task-orchestrator")
        sub_configs = [
            discover_skill(EXAMPLES_DIR / "code-review"),
        ]

        agent = builder.build_agent_from_skill(
            config=main_config,
            sub_skill_configs=sub_configs,
        )

        code_review_tool = next(t for t in agent.tools if t.name == "code_review")
        # Should use skill description
        assert "code" in code_review_tool.description.lower()

    def test_render_instructions_basic(self):
        """Test basic instruction rendering."""
        builder = SkillBuilder()

        template = "Hello {{ name }}, the date is {{ date }}."
        variables = {"name": "World", "date": "2024-01-01"}

        rendered = builder.render_instructions(template, variables)

        assert rendered == "Hello World, the date is 2024-01-01."

    def test_render_instructions_with_defaults(self):
        """Test instruction rendering with Jinja2 defaults."""
        builder = SkillBuilder()

        template = "Hello {{ name | default('Guest') }}!"
        rendered = builder.render_instructions(template, {})

        assert rendered == "Hello Guest!"

    def test_render_instructions_with_conditionals(self):
        """Test instruction rendering with conditionals."""
        builder = SkillBuilder()

        template = """{% if debug %}Debug mode{% else %}Production{% endif %}"""

        rendered_debug = builder.render_instructions(template, {"debug": True})
        rendered_prod = builder.render_instructions(template, {"debug": False})

        assert "Debug mode" in rendered_debug
        assert "Production" in rendered_prod

    def test_agent_caching(self):
        """Test that agents are cached."""
        builder = SkillBuilder()
        config = discover_skill(EXAMPLES_DIR / "code-review")

        agent1 = builder.build_agent_from_skill(config)
        agent2 = builder.build_agent_from_skill(config)

        # Should return the same cached instance
        assert agent1 is agent2

    def test_clear_cache(self):
        """Test clearing the agent cache."""
        builder = SkillBuilder()
        config = discover_skill(EXAMPLES_DIR / "code-review")

        agent1 = builder.build_agent_from_skill(config)
        builder.clear_cache()
        agent2 = builder.build_agent_from_skill(config)

        # Should be different instances after cache clear
        assert agent1 is not agent2


class TestBuildAgentFromTopLevelConfig:
    """Tests for building agents from top-level configuration."""

    def test_build_from_top_level_config(self):
        """Test building an agent from top-level config."""
        builder = SkillBuilder()

        top_level = TopLevelAgentConfig(
            name="Test Agent",
            skill="code-review",
            model="gpt-4",
            variables={"env": "test"},
        )

        skill_config = discover_skill(EXAMPLES_DIR / "code-review")

        agent = builder.build_agent_from_top_level_config(
            top_level_config=top_level,
            skill_config=skill_config,
        )

        assert agent.name == "Code Review"
        assert agent.model == "gpt-4"

    def test_build_with_additional_variables(self):
        """Test building with additional runtime variables."""
        builder = SkillBuilder()

        top_level = TopLevelAgentConfig(
            name="Data Agent",
            skill="data-analysis",
            variables={"analysis_type": "Default"},
        )

        skill_config = discover_skill(EXAMPLES_DIR / "data-analysis")

        agent = builder.build_agent_from_top_level_config(
            top_level_config=top_level,
            skill_config=skill_config,
            additional_variables={"analysis_type": "Override", "extra": "value"},
        )

        # Additional variables should override config variables
        assert "Override" in agent.instructions
