# Markdown Agents Examples

This directory contains example agent definitions demonstrating the markdown-based agent system.

## Structure

Each agent consists of two files:
- `agent_name.yaml` - Configuration (model, sub-agents, etc.)
- `agent_name.md` - Instructions (with Jinja2 templating support)

## Example Agents

### Orchestrator Agent
- **Files**: `orchestrator.yaml`, `orchestrator.md`
- **Purpose**: Main orchestrator that coordinates sub-agents
- **Sub-agents**: `helper_agent`, `analyzer_agent`
- **Features**: Demonstrates Jinja2 templating with variables like `current_date`, `user_name`, `environment`

### Helper Agent
- **Files**: `helper_agent.yaml`, `helper_agent.md`
- **Purpose**: General assistance agent
- **Sub-agents**: None (leaf node)
- **Features**: Simple agent without sub-agents

### Analyzer Agent
- **Files**: `analyzer_agent.yaml`, `analyzer_agent.md`
- **Purpose**: Analysis specialist agent
- **Sub-agents**: None (leaf node)
- **Features**: Specialized agent for analysis tasks

## Usage Example

```python
from pathlib import Path
from markdown_agents import load_agent_from_path

# Load the orchestrator agent
agent_path = Path("src/markdown_agents/examples/orchestrator")
agent = load_agent_from_path(
    agent_path,
    variables={
        "current_date": "2024-01-15",
        "user_name": "John Doe",
        "environment": "production"
    }
)

# Use the agent
result = await Runner.run(
    starting_agent=agent,
    input="Analyze the sales data and provide recommendations",
    context=your_context
)
```

## Jinja2 Variables

Variables can be used in markdown files using Jinja2 syntax:
- `{{ variable_name }}` - Simple variable substitution
- `{{ variable_name | default("default_value") }}` - With default value
- `{% if condition %}...{% endif %}` - Conditional blocks

Variables are passed at runtime when loading the agent.

