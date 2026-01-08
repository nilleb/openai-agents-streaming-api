# API Routers

This directory contains FastAPI routers for different agents.

## Standard Agent Routers

These routers use the `create_agent_router` utility which provides standardized endpoints:

- `assistant.py` - General Assistant Agent (code-based)
- `chat.py` - Chat Agent (code-based)
- `research.py` - Research Agent (custom router)

## Markdown Agent Routers

These routers load agents from markdown/YAML files:

- `orchestrator.py` - Orchestrator Agent (markdown-based)
  - Loads from: `src/markdown_agents/examples/orchestrator.yaml`
  - Endpoints: `/orchestrator/*`
  - Uses sub-agents: `helper_agent`, `analyzer_agent`

- `helper.py` - Helper Agent (markdown-based)
  - Loads from: `src/markdown_agents/examples/helper_agent.yaml`
  - Endpoints: `/helper/*`
  - Simple agent without sub-agents

## Standard Endpoints

Each agent router created with `create_agent_router` automatically provides:

- `POST /{prefix}/run` - Synchronous agent execution
- `POST /{prefix}/stream` - Streaming agent execution (SSE)
- `GET /{prefix}/info` - Agent information and metadata
- `GET /{prefix}/session/{session_id}` - Get session messages
- `DELETE /{prefix}/session/{session_id}` - Clear session

## Markdown Agent Support

The `create_agent_router` function now supports loading agents from markdown/YAML files:

```python
from ..utils.agent_router import create_agent_router

router = create_agent_router(
    agent="path/to/agent.yaml",  # Path to markdown agent
    prefix="/my-agent",
    agent_name="My Agent",
    markdown_variables={  # Optional Jinja2 variables
        "current_date": "2024-01-15",
        "user_name": "API User"
    }
)
```

The function automatically detects if the `agent` parameter is a path (str or Path) and loads it as a markdown agent, otherwise treats it as a regular Agent instance.


