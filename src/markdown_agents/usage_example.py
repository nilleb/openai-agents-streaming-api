"""
Usage Example for Markdown Agents

Demonstrates how to load and use agents defined in markdown/YAML files.
"""

from pathlib import Path
from datetime import datetime
from markdown_agents import load_agent_from_path, AgentBuilder


async def example_basic_usage():
    """Basic example of loading and using an agent."""

    # Path to the example orchestrator agent
    agent_path = Path(__file__).parent / "examples" / "orchestrator"

    # Variables for Jinja2 templating
    variables = {
        "current_date": datetime.now().strftime("%A, %B %d, %Y"),
        "user_name": "John Doe",
        "environment": "development",
    }

    # Load the agent
    agent = load_agent_from_path(agent_path, variables=variables)

    print(f"Loaded agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Number of tools: {len(agent.tools) if agent.tools else 0}")

    # Use the agent (requires Runner from openai-agents)
    # from agents import Runner
    # result = await Runner.run(
    #     starting_agent=agent,
    #     input="Analyze the sales data and provide recommendations",
    #     context=your_context
    # )


def example_custom_builder():
    """Example using a custom AgentBuilder."""

    # Create a custom builder with default model
    builder = AgentBuilder(default_model="gpt-4")

    # Load agent with custom builder
    agent_path = Path(__file__).parent / "examples" / "helper_agent"
    variables = {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "task_context": "Example task",
    }

    agent = load_agent_from_path(agent_path, variables=variables, builder=builder)

    print(f"Loaded agent with custom builder: {agent.name}")
    print(f"Model: {agent.model}")


def example_subfolder_agents():
    """Example of loading agents from subfolders."""

    # Agents can be organized in subfolders
    # Reference them using relative paths in the YAML config:
    # sub_agents:
    #   - "subfolder/agent_name"
    #   - "../sibling_folder/agent_name"

    builder = AgentBuilder()
    agent_path = Path(__file__).parent / "examples" / "orchestrator"

    variables = {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "user_name": "Jane Smith",
    }

    agent = load_agent_from_path(agent_path, variables=variables, builder=builder)

    print("Orchestrator agent loaded with sub-agents")
    if agent.tools:
        print("Available tools:")
        for tool in agent.tools:
            print(f"  - {tool.name}: {tool.description}")


if __name__ == "__main__":
    print("Markdown Agents Usage Examples")
    print("=" * 50)

    # Run examples
    example_basic_usage()
    print()
    example_custom_builder()
    print()
    example_subfolder_agents()
