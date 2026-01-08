"""Tests for markdown_agents package."""

from pathlib import Path
from datetime import datetime

import pytest

from ..loader import (
    load_yaml_config,
    load_markdown_instructions,
    load_agent_config_from_path,
    load_agent_from_path,
)
from ..builder import AgentBuilder, AgentConfig


# Get the examples directory path
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def test_load_yaml_config():
    """Test loading YAML configuration."""
    yaml_path = EXAMPLES_DIR / "orchestrator.yaml"
    config = load_yaml_config(yaml_path)

    assert isinstance(config, dict)
    assert "name" in config
    assert "model" in config
    assert "sub_agents" in config
    assert config["name"] == "Example Orchestrator"
    assert config["model"] == "gpt-4.1-mini"
    assert isinstance(config["sub_agents"], list)


def test_load_markdown_instructions():
    """Test loading markdown instructions."""
    md_path = EXAMPLES_DIR / "orchestrator.md"
    instructions = load_markdown_instructions(md_path)

    assert isinstance(instructions, str)
    assert len(instructions) > 0
    assert "Orchestrator Agent Instructions" in instructions
    assert "{{ current_date }}" in instructions  # Jinja2 template variable


def test_load_agent_config_from_path():
    """Test loading agent configuration from path."""
    # Test with YAML file path (flat structure)
    agent_path = EXAMPLES_DIR / "helper_agent.yaml"
    config = load_agent_config_from_path(agent_path)

    assert isinstance(config, AgentConfig)
    assert config.name == "helper_agent"
    assert config.base_path == EXAMPLES_DIR
    assert "Helper Agent Instructions" in config.markdown_instructions
    assert config.yaml_config["name"] == "Helper Agent"


def test_load_agent_config_from_yaml_file():
    """Test loading agent configuration from YAML file path."""
    yaml_path = EXAMPLES_DIR / "analyzer_agent.yaml"
    config = load_agent_config_from_path(yaml_path)

    assert isinstance(config, AgentConfig)
    assert config.name == "analyzer_agent"
    assert "Analyzer Agent Instructions" in config.markdown_instructions


def test_agent_builder_render_instructions():
    """Test Jinja2 template rendering in instructions."""
    builder = AgentBuilder()

    template = "Hello {{ name }}, today is {{ date }}"
    variables = {"name": "John", "date": "2024-01-15"}

    rendered = builder.render_instructions(template, variables)

    assert "Hello John" in rendered
    assert "2024-01-15" in rendered
    assert "{{ name }}" not in rendered  # Template variable should be replaced


def test_agent_builder_render_instructions_with_defaults():
    """Test Jinja2 template rendering with default values."""
    builder = AgentBuilder()

    template = "Hello {{ name | default('Guest') }}, today is {{ date }}"
    variables = {"date": "2024-01-15"}

    rendered = builder.render_instructions(template, variables)

    assert "Hello Guest" in rendered
    assert "2024-01-15" in rendered


def test_agent_builder_build_simple_agent():
    """Test building a simple agent without sub-agents."""
    builder = AgentBuilder(default_model="gpt-4.1-mini")

    config = load_agent_config_from_path(EXAMPLES_DIR / "helper_agent.yaml")

    variables = {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "task_context": "Test task",
    }

    agent = builder.build_agent(config, variables=variables)

    assert agent.name == "Helper Agent"
    assert agent.model == "gpt-4.1-mini"
    # Check instructions (may be string or callable)
    instructions_str = (
        agent.instructions
        if isinstance(agent.instructions, str)
        else str(agent.instructions)
    )
    assert instructions_str is not None
    assert len(instructions_str) > 0
    # Check that template variables were rendered
    assert "{{ current_date }}" not in instructions_str
    assert (
        datetime.now().strftime("%Y-%m-%d") in instructions_str
        or "Test task" in instructions_str
    )


def test_agent_builder_build_agent_with_sub_agents():
    """Test building an agent with sub-agents."""
    builder = AgentBuilder(default_model="gpt-4.1-mini")

    config = load_agent_config_from_path(EXAMPLES_DIR / "orchestrator.yaml")

    variables = {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "user_name": "Test User",
        "environment": "test",
    }

    agent = builder.build_agent(config, variables=variables)

    assert agent.name == "Example Orchestrator"
    assert agent.model == "gpt-4.1-mini"
    assert agent.instructions is not None

    # Check that sub-agents were loaded and converted to tools
    assert agent.tools is not None
    assert len(agent.tools) == 2  # helper_agent and analyzer_agent

    # Check tool names
    tool_names = [tool.name for tool in agent.tools]
    assert "helper_agent" in tool_names
    assert "analyzer_agent" in tool_names

    # Check that template variables were rendered
    instructions_str = (
        agent.instructions
        if isinstance(agent.instructions, str)
        else str(agent.instructions)
    )
    assert "{{ current_date }}" not in instructions_str
    assert "{{ user_name }}" not in instructions_str


def test_load_agent_from_path():
    """Test loading agent directly from path."""
    agent_path = EXAMPLES_DIR / "helper_agent.yaml"

    variables = {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "task_context": "Test task",
    }

    agent = load_agent_from_path(agent_path, variables=variables)

    assert agent.name == "Helper Agent"
    assert agent.model == "gpt-4.1-mini"
    assert agent.instructions is not None


def test_load_agent_from_path_with_sub_agents():
    """Test loading orchestrator agent with sub-agents."""
    agent_path = EXAMPLES_DIR / "orchestrator.yaml"

    variables = {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "user_name": "Test User",
        "environment": "test",
    }

    agent = load_agent_from_path(agent_path, variables=variables)

    assert agent.name == "Example Orchestrator"
    assert agent.tools is not None
    assert len(agent.tools) == 2


def test_agent_builder_custom_default_model():
    """Test AgentBuilder with custom default model."""
    builder = AgentBuilder(default_model="gpt-4")

    config = load_agent_config_from_path(EXAMPLES_DIR / "analyzer_agent.yaml")
    # Remove model from config to test default
    config.yaml_config.pop("model", None)

    agent = builder.build_agent(config)

    assert agent.model == "gpt-4"  # Should use builder's default


def test_agent_config_yaml_overrides_default_model():
    """Test that YAML model config overrides builder default."""
    builder = AgentBuilder(default_model="gpt-4")

    config = load_agent_config_from_path(EXAMPLES_DIR / "analyzer_agent.yaml")
    # Ensure model is in config
    config.yaml_config["model"] = "gpt-4.1-mini"

    agent = builder.build_agent(config)

    assert agent.model == "gpt-4.1-mini"  # Should use YAML config, not default


def test_agent_tool_descriptions():
    """Test that tool descriptions are correctly set from YAML config."""
    builder = AgentBuilder()

    config = load_agent_config_from_path(EXAMPLES_DIR / "orchestrator.yaml")

    variables = {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "user_name": "Test User",
        "environment": "test",
    }

    agent = builder.build_agent(config, variables=variables)

    # Check that tools have descriptions
    tool_descriptions = {tool.name: tool.description for tool in agent.tools}

    assert "helper_agent" in tool_descriptions
    assert "analyzer_agent" in tool_descriptions

    # Check that descriptions match YAML config
    expected_descriptions = config.yaml_config.get("tool_descriptions", {})
    assert tool_descriptions["helper_agent"] == expected_descriptions.get(
        "Helper Agent", ""
    )


def test_missing_yaml_file_raises_error():
    """Test that missing YAML file raises FileNotFoundError."""
    fake_path = EXAMPLES_DIR / "nonexistent_agent"

    with pytest.raises(FileNotFoundError, match="Agent config file not found"):
        load_agent_config_from_path(fake_path)


def test_missing_markdown_file_raises_error(tmp_path):
    """Test that missing markdown file raises FileNotFoundError."""
    # Create a YAML file but no markdown file
    yaml_file = tmp_path / "test_agent.yaml"
    yaml_file.write_text("name: Test Agent\nmodel: gpt-4.1-mini\n")

    with pytest.raises(FileNotFoundError, match="Agent instructions file not found"):
        load_agent_config_from_path(yaml_file)


def test_jinja2_conditional_rendering():
    """Test Jinja2 conditional rendering in templates."""
    builder = AgentBuilder()

    template = """
    {% if environment == "production" %}
    Production mode enabled
    {% else %}
    Development mode
    {% endif %}
    """

    # Test production
    rendered_prod = builder.render_instructions(template, {"environment": "production"})
    assert "Production mode enabled" in rendered_prod
    assert "Development mode" not in rendered_prod

    # Test development
    rendered_dev = builder.render_instructions(template, {"environment": "development"})
    assert "Development mode" in rendered_dev
    assert "Production mode enabled" not in rendered_dev
