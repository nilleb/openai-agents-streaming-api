# Markdown Agents Package

A file-based agent system for defining OpenAI Agents using markdown instructions and YAML configuration files.

## Features

- **File-based Agent Definitions**: Define agents using markdown and YAML files
- **Jinja2 Templating**: Use variables in markdown instructions that are replaced at runtime
- **Hierarchical Agents**: Reference sub-agents in YAML configuration
- **Flexible Path Resolution**: Support for relative paths, subfolders, and nested agent structures

## Quick Start

### 1. Create Agent Files

Each agent requires two files:

**`agent_name.yaml`** - Configuration:
```yaml
name: "My Agent"
model: "gpt-4.1-mini"
sub_agents:
  - "helper_agent"
  - "analyzer_agent"
tool_descriptions:
  "Helper Agent": "A helper agent for general tasks"
  "Analyzer Agent": "An analyzer agent for detailed analysis"
```

**`agent_name.md`** - Instructions:
```markdown
# My Agent Instructions

You are a helpful agent.

Current date: {{ current_date }}
User: {{ user_name | default("Guest") }}

Use the helper_agent tool for general tasks.
Use the analyzer_agent tool for analysis tasks.
```

### 2. Load and Use the Agent

```python
from pathlib import Path
from markdown_agents import load_agent_from_path
from agents import Runner

# Load the agent
agent_path = Path("path/to/agent_name")
agent = load_agent_from_path(
    agent_path,
    variables={
        "current_date": "2024-01-15",
        "user_name": "John Doe"
    }
)

# Use the agent
result = await Runner.run(
    starting_agent=agent,
    input="Your task here",
    context=your_context
)
```

## File Structure

```
agents/
├── orchestrator/
│   ├── orchestrator.yaml
│   └── orchestrator.md
├── helper_agent/
│   ├── helper_agent.yaml
│   └── helper_agent.md
└── analyzer_agent/
    ├── analyzer_agent.yaml
    └── analyzer_agent.md
```

## YAML Configuration

### Required Fields

- `name`: Agent name (optional, defaults to filename)
- `model`: Model to use (optional, defaults to builder's default_model)

### Optional Fields

- `sub_agents`: List of agent references (paths or names)
- `tool_name_prefix`: Prefix for tool names when converting sub-agents to tools
- `tool_descriptions`: Dictionary mapping agent names to tool descriptions

### Example YAML

```yaml
name: "Orchestrator Agent"
model: "gpt-4.1-mini"
sub_agents:
  - "helper_agent"              # Same directory
  - "subfolder/analyzer_agent"  # Subfolder
  - "../sibling/other_agent"    # Relative path
tool_name_prefix: ""
tool_descriptions:
  "Helper Agent": "Provides general assistance"
  "Analyzer Agent": "Performs detailed analysis"
```

## Markdown Instructions

### Jinja2 Templating

Use Jinja2 syntax for variable substitution:

```markdown
# Agent Instructions

Current date: {{ current_date }}
User: {{ user_name | default("Guest") }}

{% if environment == "production" %}
This is production mode.
{% else %}
This is development mode.
{% endif %}
```

### Available Variables

Variables are passed when loading the agent:

```python
agent = load_agent_from_path(
    agent_path,
    variables={
        "current_date": "2024-01-15",
        "user_name": "John Doe",
        "environment": "production"
    }
)
```

## Sub-Agents

### Referencing Sub-Agents

In your YAML config, list sub-agents:

```yaml
sub_agents:
  - "helper_agent"              # Same directory
  - "subfolder/analyzer_agent"  # Subfolder path
```

### Path Resolution

The system supports multiple path resolution strategies:

1. **Relative paths**: `"subfolder/agent_name"`
2. **Absolute paths**: `"/full/path/to/agent"`
3. **Simple names**: `"agent_name"` (searches in current directory and subdirectories)

### Tool Conversion

Sub-agents are automatically converted to tools:

- Tool name: `tool_name_prefix + agent_name_normalized`
- Tool description: From `tool_descriptions` map or default

## API Reference

### `load_agent_from_path(agent_path, variables=None, builder=None)`

Load an agent from a file path.

**Parameters:**
- `agent_path` (Path): Path to agent directory or YAML file
- `variables` (dict, optional): Variables for Jinja2 templating
- `builder` (AgentBuilder, optional): Custom builder instance

**Returns:** Agent instance

### `load_agent_from_file(agent_file, base_path=None, variables=None, builder=None)`

Load an agent from a file path string.

**Parameters:**
- `agent_file` (str): Path to agent (directory, YAML file, or agent name)
- `base_path` (Path, optional): Base path for resolving relative references
- `variables` (dict, optional): Variables for Jinja2 templating
- `builder` (AgentBuilder, optional): Custom builder instance

**Returns:** Agent instance

### `AgentBuilder(default_model="gpt-4.1-mini")`

Builder for creating agents with custom defaults.

**Parameters:**
- `default_model` (str): Default model to use if not specified in YAML

## Examples

See the `examples/` directory for complete examples:

- `orchestrator` - Main orchestrator with sub-agents
- `helper_agent` - Simple helper agent
- `analyzer_agent` - Analysis specialist agent

## Integration with Existing Agents

This system is designed to work alongside the existing `deep_research_agent` module. You can:

1. Convert existing agents to markdown/YAML format
2. Use markdown agents as sub-agents in existing orchestrators
3. Mix and match file-based and code-based agents

## Dependencies

- `pyyaml>=6.0` - YAML parsing
- `jinja2>=3.1.0` - Template rendering
- `openai-agents>=0.2.3` - Agent framework

## License

Same as the main project.

