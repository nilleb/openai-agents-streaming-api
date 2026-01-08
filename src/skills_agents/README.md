# Skills Agents Package

A file-based agent system implementing the [Agent Skills specification](https://agentskills.io/docs/spec).

Skills are defined by `SKILL.md` files containing YAML frontmatter and markdown instructions, following the open Agent Skills format.

## Features

- **Agent Skills Specification Compliant**: Implements the full Agent Skills spec
- **Skill Discovery**: Automatically discovers skills in a directory
- **Validation**: Validates skills according to spec constraints
- **Jinja2 Templating**: Use variables in skill instructions
- **Sub-agents as Tools**: Skills can reference other skills as sub-agents
- **Top-level Agent Configuration**: YAML configuration for API-exposed agents

## Quick Start

### 1. Create a Skill

Create a directory with a `SKILL.md` file:

```
my-skill/
└── SKILL.md
```

**`my-skill/SKILL.md`**:

```markdown
---
name: my-skill
description: A helpful skill that does something useful. Use when the user needs help with a specific task.
license: Apache-2.0
metadata:
  author: your-name
  version: "1.0"
---

# My Skill Instructions

You are a helpful assistant for this specific task.

## Current Context

- **Date**: {{ current_date | default("Not specified") }}
- **User**: {{ user_name | default("Guest") }}

## Guidelines

1. Be helpful
2. Be concise
3. Provide examples when useful
```

### 2. Load and Use the Skill

```python
from pathlib import Path
from skills_agents import load_skill_from_path, build_agent_from_skill_path
from agents import Runner

# Simple: Build agent directly
agent = build_agent_from_skill_path(
    Path("skills/my-skill"),
    variables={
        "current_date": "2024-01-15",
        "user_name": "John"
    }
)

# Use the agent
result = await Runner.run(
    starting_agent=agent,
    input="Help me with this task"
)
```

### 3. Configure Top-Level Agents

Create an `agents.yaml` file to define which agents to expose through your API:

```yaml
default_model: "gpt-4.1-mini"
skills_directory: "skills"

agents:
  - name: "My Agent"
    skill: "my-skill"
    model: "gpt-4.1-mini"
    variables:
      environment: "production"

  - name: "Orchestrator"
    skill: "orchestrator-skill"
    sub_agents:
      - "my-skill"
      - "another-skill"
    # tool_descriptions is OPTIONAL - by default, each skill's
    # frontmatter description is used as the tool description.
    # Only specify if you need to override with a different description:
    # tool_descriptions:
    #   "my-skill": "Custom shorter description for tool context"
```

Load all configured agents:

```python
from skills_agents import load_top_level_agents

agents = load_top_level_agents(
    Path("agents.yaml"),
    variables={"current_date": "2024-01-15"}
)

# Access agents by name
my_agent = agents["My Agent"]
orchestrator = agents["Orchestrator"]
```

## Skill Format

### Directory Structure

```
skill-name/
├── SKILL.md          # Required: Skill definition
├── scripts/          # Optional: Executable scripts
├── references/       # Optional: Additional documentation
└── assets/           # Optional: Static resources
```

### SKILL.md Format

```yaml
---
name: skill-name           # Required: 1-64 chars, lowercase alphanumeric and hyphens
description: Description   # Required: 1-1024 chars, what the skill does
license: Apache-2.0        # Optional: License name
compatibility: Python 3.10 # Optional: Environment requirements (max 500 chars)
metadata:                  # Optional: Arbitrary key-value pairs
  author: your-name
  version: "1.0"
allowed-tools: Read Write  # Optional: Space-delimited pre-approved tools (experimental)
---

# Markdown Instructions

Your skill instructions here. Supports Jinja2 templating.
```

### Name Constraints

The `name` field must:
- Be 1-64 characters
- Contain only lowercase letters (`a-z`), numbers (`0-9`), and hyphens (`-`)
- Not start or end with a hyphen
- Not contain consecutive hyphens (`--`)
- Match the parent directory name

Valid: `my-skill`, `data-analysis`, `code-review-v2`
Invalid: `My-Skill`, `-skill`, `skill-`, `my--skill`, `my_skill`

## API Reference

### Discovery

```python
from skills_agents import discover_skill, discover_skills

# Discover a single skill
config = discover_skill(Path("skills/my-skill"))

# Discover all skills in a directory
configs = discover_skills(Path("skills"))
```

### Validation

```python
from skills_agents import SkillValidator

validator = SkillValidator(strict=False)
result = validator.validate_skill_path(Path("skills/my-skill"))

if result.is_valid:
    print("Skill is valid!")
else:
    for error in result.errors:
        print(f"Error: {error.message}")

for warning in result.warnings:
    print(f"Warning: {warning.message}")
```

### Building Agents

```python
from skills_agents import SkillBuilder, discover_skill

builder = SkillBuilder(default_model="gpt-4.1-mini")
config = discover_skill(Path("skills/my-skill"))

# Build simple agent
agent = builder.build_agent_from_skill(
    config,
    variables={"key": "value"}
)

# Build agent with sub-skills as tools
main_config = discover_skill(Path("skills/orchestrator"))
sub_configs = [
    discover_skill(Path("skills/skill-a")),
    discover_skill(Path("skills/skill-b")),
]

# Sub-skill descriptions are automatically taken from their frontmatter
orchestrator = builder.build_agent_from_skill(
    config=main_config,
    sub_skill_configs=sub_configs,
    # tool_descriptions is optional - only use to override frontmatter descriptions:
    # tool_descriptions={"skill-a": "Custom shorter description"}
)
```

### Loading

```python
from skills_agents import (
    load_skill_from_path,
    load_skills_from_directory,
    load_top_level_agents,
)

# Load single skill
config = load_skill_from_path(Path("skills/my-skill"), validate=True)

# Load all skills
all_skills = load_skills_from_directory(Path("skills"))

# Load configured agents
agents = load_top_level_agents(Path("agents.yaml"))
```

## Jinja2 Templating

Use Jinja2 syntax in your skill instructions:

```markdown
## Context

- **Date**: {{ current_date }}
- **User**: {{ user_name | default("Guest") }}
- **Environment**: {{ environment | default("development") }}

{% if debug_mode %}
## Debug Information
Debug mode is enabled.
{% endif %}

{% for item in items %}
- {{ item }}
{% endfor %}
```

Variables are passed when building the agent:

```python
agent = build_agent_from_skill_path(
    skill_path,
    variables={
        "current_date": "2024-01-15",
        "user_name": "John",
        "environment": "production",
        "debug_mode": True,
        "items": ["Item 1", "Item 2", "Item 3"]
    }
)
```

## Integration with API

Example integration with FastAPI:

```python
from fastapi import FastAPI
from skills_agents import load_top_level_agents
from pathlib import Path

app = FastAPI()

# Load agents at startup
agents = load_top_level_agents(Path("agents.yaml"))

@app.get("/agents")
async def list_agents():
    return list(agents.keys())

@app.post("/agents/{agent_name}/run")
async def run_agent(agent_name: str, input: str):
    agent = agents.get(agent_name)
    if not agent:
        raise HTTPException(404, "Agent not found")

    result = await Runner.run(starting_agent=agent, input=input)
    return {"response": result.final_output}
```

## Examples

See the `examples/` directory for complete examples:

- `code-review/` - Code review skill
- `data-analysis/` - Data analysis skill
- `research-assistant/` - Research assistant skill
- `task-orchestrator/` - Orchestrator skill with sub-agents
- `agents.yaml` - Top-level agent configuration

## Migration from markdown_agents

If you're migrating from the `markdown_agents` package:

| markdown_agents | skills_agents |
|-----------------|---------------|
| `agent.yaml` + `agent.md` | `SKILL.md` with frontmatter |
| `name` in YAML | `name` in frontmatter |
| `model` in YAML | `model` in `agents.yaml` |
| `sub_agents` in YAML | `sub_agents` in `agents.yaml` |

Key differences:
- Single `SKILL.md` file instead of separate YAML and MD files
- Skill-specific metadata in frontmatter
- Model configuration in top-level `agents.yaml`
- Validation according to Agent Skills spec

## Dependencies

- `pyyaml>=6.0` - YAML parsing
- `jinja2>=3.1.0` - Template rendering
- `pydantic>=2.0` - Data validation
- `openai-agents>=0.2.3` - Agent framework

## License

Same as the main project.

## References

- [Agent Skills Specification](https://agentskills.io/docs/spec)
- [skills-ref Reference Implementation](https://github.com/agentskills/agentskills/tree/main/skills-ref)
