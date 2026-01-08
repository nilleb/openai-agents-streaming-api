# OpenAI Agents Streaming API

A FastAPI-based backend demonstrating the OpenAI Agents SDK with streaming endpoints for multiple AI agents. This project features dedicated routers per agent with real-time streaming events including agent updates, raw responses, and run items, plus **persistent conversation memory** for multi-turn interactions.

## Architecture

This project is structured with separate packages for each agent:

```
src/
├── api/                 # FastAPI application
│   ├── routers/        # Agent-specific endpoints  
│   └── utils/          # Shared utilities
├── chat_agent/         # General chat agent package
├── research_bot/       # Basic research agent package
│   ├── agents/         # Planner, Search, and Writer agents
│   └── manager.py      # Research orchestration
├── deep_research_agent/ # Advanced multi-agent research system
│   ├── agents/         # Hierarchical specialized agents
│   ├── models.py       # Comprehensive data models
│   ├── orchestrator.py # Multi-agent coordination
│   ├── tools.py        # Research function tools
│   └── config.py       # Advanced configuration system
├── markdown_agents/    # File-based agent system (legacy)
│   ├── loader.py       # YAML/Markdown agent loader
│   ├── builder.py      # Agent builder with Jinja2 support
│   └── examples/       # Example markdown agents
└── skills_agents/      # Agent Skills spec implementation
    ├── discovery.py    # Skill discovery (SKILL.md files)
    ├── validator.py    # Skill validation per spec
    ├── builder.py      # Skill-to-Agent conversion
    ├── loader.py       # High-level loading functions
    ├── cli.py          # CLI for validation/discovery
    └── examples/       # Example skills
```

Each agent package can be imported and used independently, making the system modular and scalable.

## Features

- 🚀 **Per-agent dedicated endpoints** with standardized patterns
- 📡 **Real-time streaming** with Server-Sent Events (SSE)
- 🔄 **Event types**: Raw LLM responses, semantic agent events, handoffs
- 💾 **Session Memory & Conversation History** - Persistent multi-turn conversations
- 🧩 **Modular architecture** - each agent as separate package
- 📝 **Markdown-based agents** - Define agents using YAML and Markdown files
- 🎨 **Jinja2 templating** - Dynamic instructions with variable substitution
- 🔗 **Hierarchical agents** - Sub-agents as tools with automatic loading
- 🛠️ **Agent Skills spec** - Standards-compliant skill definitions with validation
- 📚 **Auto-generated OpenAPI docs** at `/docs`
- 🔧 **Development-ready** with hot reload and comprehensive logging

### 🆕 Session Memory & Conversation Persistence

**Built-in conversational memory using OpenAI Agents SDK's SQLiteSession:**

- **Multi-turn conversations**: Agents remember context across requests
- **Session isolation**: Each user/conversation maintains separate history  
- **Persistent storage**: Conversation history survives server restarts
- **Environment-based config**: Enable with simple `ENABLE_SESSIONS=true`
- **Zero code changes**: Existing endpoints automatically support sessions
- **Production-ready**: SQLite-based storage with proper error handling

**Perfect for:** Chatbots, virtual assistants, customer support, educational apps, and any conversational AI that needs context awareness.

## Prerequisites

- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager
- **OpenAI API Key** - Set in environment variables

## Installation & Setup

### 1. Install uv (if not already installed)

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip
pip install uv
```

### 2. Clone and Setup Project

```bash
git clone https://github.com/ahmad2b/openai-agents-streaming-api.git
cd openai-agents-streaming-api

# Install project in development mode with all dependencies
# (also installs pre-commit hooks via prek)
./cli setup
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here

# Session Memory Configuration (Optional)
ENABLE_SESSIONS=true                    # Enable conversation memory
SESSION_DB_PATH=./conversations.db      # SQLite database path

# Optional: Logging level
LOG_LEVEL=INFO

# Optional: Custom port (default is 8000)
PORT=8000
```

### OpenAI Instance Configuration

This application supports both OpenAI's public API and private/self-hosted OpenAI-compatible instances. The configuration is controlled through environment variables that the OpenAI SDK reads automatically.

#### Option 1: OpenAI Public API

To use the official OpenAI API, you only need to set your API key:

```bash
# .env for OpenAI Public API
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

That's it! The SDK defaults to `https://api.openai.com/v1` when no base URL is specified.

#### Option 2: Private OpenAI Instance (e.g., Azure OpenAI, vLLM, LocalAI, Ollama)

To connect to a private or self-hosted OpenAI-compatible instance, set the base URL:

```bash
# .env for Private OpenAI Instance
OPENAI_BASE_URL=http://your-private-instance.example.com:8080/v1

# API key may be optional depending on your private instance configuration
# Set to a dummy value if your instance doesn't require authentication
OPENAI_API_KEY=not-required
```

**Examples for common private deployments:**

```bash
# Azure OpenAI Service
OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
OPENAI_API_KEY=your-azure-api-key

# vLLM Server
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=token-abc123

# LocalAI
OPENAI_BASE_URL=http://localhost:8080/v1
OPENAI_API_KEY=not-needed

# Ollama (with OpenAI compatibility)
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
```

#### Additional OpenAI Environment Variables

The OpenAI SDK also supports these optional environment variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | API key for authentication (required for public API) |
| `OPENAI_BASE_URL` | Custom base URL for private instances |
| `OPENAI_ORG_ID` | Organization ID (optional, for OpenAI enterprise) |
| `OPENAI_PROJECT` | Project ID (optional, for OpenAI project-based billing) |

> **Note:** Environment variables are loaded at application startup via `dotenv`. Ensure your `.env` file is in the project root directory.

## Running the Application

### Development Mode (Recommended)

```bash
# Using uvicorn directly (with hot reload)
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or using the module directly
uv run python -m src.api.main
```

### Production Mode

```bash
# Install production dependencies (if different)
uv pip install -e .

# Run with production settings
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using uv run (Alternative)

```bash
# Run directly with uv (manages virtual environment automatically)
uv run uvicorn src.api.main:app --reload
```

## API Endpoints

### Base URLs
- **Application**: `http://127.0.0.1:8000`
- **Interactive Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### Agent Endpoints

Each agent has standardized endpoints with **automatic session support**:

#### General Assistant (`/assistant/*`)
```bash
POST /assistant/run      # Synchronous execution
POST /assistant/stream   # Real-time streaming
GET  /assistant/info     # Agent information & session config
GET  /assistant/session/{session_id}  # Get all messages for session
DELETE /assistant/session/{session_id}  # Clear conversation history
```

#### Chat Agent (`/chat/*`)  
```bash
POST /chat/run          # Synchronous execution
POST /chat/stream       # Real-time streaming
GET  /chat/info         # Agent information & session config
GET  /chat/session/{session_id}  # Get all messages for session
DELETE /chat/session/{session_id}  # Clear conversation history
```

#### Research Agent (`/research/*`)
```bash
POST /research          # Full research pipeline
```

#### Orchestrator Agent (`/orchestrator/*`) - Markdown-based
```bash
POST /orchestrator/run      # Synchronous execution
POST /orchestrator/stream   # Real-time streaming
GET  /orchestrator/info     # Agent information & session config
GET  /orchestrator/session/{session_id}  # Get all messages for session
DELETE /orchestrator/session/{session_id}  # Clear conversation history
```

#### Helper Agent (`/helper/*`) - Markdown-based
```bash
POST /helper/run          # Synchronous execution
POST /helper/stream       # Real-time streaming
GET  /helper/info         # Agent information & session config
GET  /helper/session/{session_id}  # Get all messages for session
DELETE /helper/session/{session_id}  # Clear conversation history
```

### Example Usage

#### Basic Usage (No Memory)
```bash
# Test the chat agent without session memory
curl -X POST "http://127.0.0.1:8000/chat/run" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, how can you help me?"}'
```

#### With Session Memory (Multi-turn Conversations)
```bash
# First message with session_id - agent introduces context
curl -X POST "http://127.0.0.1:8000/chat/run" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hi, my name is Sarah and I work as a software engineer", "session_id": "user_sarah_123"}'

# Second message - agent remembers Sarah and her profession
curl -X POST "http://127.0.0.1:8000/chat/run" \
  -H "Content-Type: application/json" \
  -d '{"input": "What kind of work do I do?", "session_id": "user_sarah_123"}'

# Stream responses with conversation context
curl -X POST "http://127.0.0.1:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"input": "Give me some programming tips for my field", "session_id": "user_sarah_123"}' \
  --no-buffer
```

#### Using Markdown Agents
```bash
# Test the orchestrator agent (markdown-based with sub-agents)
curl -X POST "http://127.0.0.1:8000/orchestrator/run" \
  -H "Content-Type: application/json" \
  -d '{"input": "Analyze the sales data and provide recommendations"}'

# Test the helper agent (simple markdown agent)
curl -X POST "http://127.0.0.1:8000/helper/run" \
  -H "Content-Type: application/json" \
  -d '{"input": "Help me understand how to use this API", "session_id": "user_123"}'

# Stream from orchestrator agent
curl -X POST "http://127.0.0.1:8000/orchestrator/stream" \
  -H "Content-Type: application/json" \
  -d '{"input": "Coordinate a complex task", "session_id": "task_456"}' \
  --no-buffer
```

#### Session Management
```bash
# Get all messages for a session
curl -X GET "http://127.0.0.1:8000/chat/session/user_sarah_123"

# Get limited number of recent messages (e.g., last 10)
curl -X GET "http://127.0.0.1:8000/chat/session/user_sarah_123?limit=10"

# Clear conversation history for a user
curl -X DELETE "http://127.0.0.1:8000/chat/session/user_sarah_123"

# Check agent info and session configuration
curl -X GET "http://127.0.0.1:8000/chat/info"
```

## Session Memory & Conversation Persistence

### 🔧 Configuration

**Environment Variables:**
- `ENABLE_SESSIONS=true` - Enable conversation memory globally
- `SESSION_DB_PATH=./conversations.db` - SQLite database location (optional)

### 🎯 How It Works

**Automatic Session Handling:**
- **No session_id**: Traditional stateless interaction
- **With session_id**: Automatic conversation history using OpenAI Agents SDK's SQLiteSession
- **Session isolation**: Each session_id maintains separate conversation memory
- **Persistent storage**: History survives server restarts and deployments

### 💾 Technical Details

**Built on OpenAI Agents SDK patterns:**
- Uses `SQLiteSession` for reliable conversation storage
- Integrates with `Runner.run()` and `Runner.run_streamed()` seamlessly  
- Maintains conversation context across agent handoffs
- Supports both synchronous and streaming interactions with memory

### 🚀 Production Features

- **Environment-driven**: 12-factor app configuration
- **Zero code changes**: Works with existing agent implementations
- **Scalable storage**: SQLite for single instance, easily extensible to PostgreSQL
- **Error handling**: Graceful degradation when sessions unavailable
- **Security**: Session isolation prevents cross-user data leakage

## Development Best Practices

### Package Management with uv

```bash
# Add new dependencies
uv add package-name

# Add development dependencies  
uv add --dev pytest black isort

# Update all dependencies
uv lock --upgrade

# Install from lock file (for consistent environments)
uv pip install -r uv.lock
```

### Code Quality

Use the CLI for consistent code quality checks:

```bash
# Run all pre-commit hooks (lint, typecheck, validate, tests)
./cli prek

# Individual commands:
./cli lint       # Run ruff linter and formatter
./cli typecheck  # Run ty type checker
./cli test       # Run pytest suite
./cli validate   # Validate Agent Skills
```

Or run tools directly:

```bash
# Format and lint with ruff
uv run ruff check --fix .
uv run ruff format .

# Type checking
uv run ty check

# Run tests
uv run pytest
```

### Working with Individual Agents

Each agent can be imported and used independently, **with or without session memory**:

```python
# Using the chat agent directly (no session)
from src.chat_agent.main import chat_agent
from agents import Runner

result = await Runner.run(chat_agent, "Hello!")

# Using with session memory
from agents import SQLiteSession

session = SQLiteSession("user_123", db_path="conversations.db")
result = await Runner.run(chat_agent, "Hello!", session=session)

# Using the research bot
from src.research_bot.manager import ResearchManager

manager = ResearchManager()
report = await manager.run("AI trends 2024")

# Using markdown agents programmatically
from pathlib import Path
from src.markdown_agents import load_agent_from_path
from datetime import datetime

agent_path = Path("src/markdown_agents/examples/orchestrator.yaml")
agent = load_agent_from_path(
    agent_path,
    variables={
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "user_name": "Python User"
    }
)
result = await Runner.run(agent, "Analyze the data and provide recommendations")
```

## Project Structure Details

### Agent Router Pattern

Each agent uses the standardized `create_agent_router()` utility that provides:

- **POST `/run`** - Synchronous execution with complete response
- **POST `/stream`** - Real-time streaming with formatted events
- **DELETE `/session/{session_id}`** - Clear conversation history for specific session
- **GET `/info`** - Agent metadata, configuration, and session status

### Event Types

The streaming endpoints emit structured events:

1. **`raw_response`** - Direct from OpenAI (text deltas, function calls, etc.)
2. **`run_item`** - Semantic agent events (tool usage, handoffs, reasoning)
3. **`agent_updated`** - Agent handoff notifications
4. **`stream_complete`** - Final results with usage statistics and session info
5. **`error`** - Error handling with details

### Extending the System

#### Option 1: Code-based Agent (Traditional)

To add a new agent **with automatic session support**:

1. Create `src/your_agent/main.py` with agent definition
2. Create `src/api/routers/your_agent.py` using `create_agent_router()`
3. Include the router in `src/api/main.py`
4. **Sessions work automatically** - no additional code needed!

**Example:**
```python
# src/api/routers/your_agent.py
from agents import Agent
from ..utils.agent_router import create_agent_router

agent = Agent(
    name="Your Agent",
    instructions="Your agent instructions here"
)

router = create_agent_router(
    agent=agent,
    prefix="/your-agent",
    agent_name="Your Agent"
)
```

#### Option 2: Markdown-based Agent (File-based)

Markdown agents allow you to define agents using YAML configuration and Markdown instruction files, making them easy to version control and modify without code changes.

##### Step-by-Step Guide: Adding a New Markdown Agent

**Step 1: Create the Agent Directory Structure**

Create a directory for your agent in the `markdown_agents` folder:

```bash
mkdir -p src/markdown_agents/my_new_agent
```

**Step 2: Create the YAML Configuration File**

Create `src/markdown_agents/my_new_agent/my_new_agent.yaml`:

```yaml
# Agent Configuration
name: "My New Agent"
model: "gpt-4.1-mini"  # Optional: defaults to builder's default_model

# Optional: Reference sub-agents (they will be loaded and converted to tools)
sub_agents:
  - "helper_agent"      # Same directory
  - "subfolder/other_agent"  # Subfolder path

# Optional: Custom tool name prefix for sub-agents
tool_name_prefix: ""

# Optional: Custom descriptions for sub-agent tools
tool_descriptions:
  "Helper Agent": "A helper agent for general tasks"
  "Other Agent": "An agent for specialized tasks"
```

**Key YAML Fields:**
- `name`: Display name for your agent
- `model`: OpenAI model to use (e.g., "gpt-4.1-mini", "gpt-4")
- `sub_agents`: List of agent references (paths or names) - optional
- `tool_descriptions`: Map of agent names to tool descriptions - optional

**Step 3: Create the Markdown Instructions File**

Create `src/markdown_agents/my_new_agent/my_new_agent.md`:

```markdown
# My New Agent Instructions

You are a specialized agent designed to help users with specific tasks.

## Current Context

- **Date**: {{ current_date }}
- **User**: {{ user_name | default("Guest") }}
- **Environment**: {{ environment | default("development") }}

## Your Role

- Provide helpful assistance
- Answer questions clearly
- Use available tools when needed

## Guidelines

- Be concise but thorough
- Ask for clarification when needed
- Always confirm task completion

{% if sub_agents %}
## Available Tools

You have access to the following tools:
{% for agent in sub_agents %}
- {{ agent }}: Use this for specific tasks
{% endfor %}
{% endif %}
```

**Key Markdown Features:**
- Use `{{ variable_name }}` for variable substitution
- Use `{{ variable | default("value") }}` for default values
- Use `{% if condition %}...{% endif %}` for conditional blocks
- Use `{% for item in list %}...{% endfor %}` for loops

**Step 4: Create the Router File**

Create `src/api/routers/my_new_agent.py`:

```python
"""
My New Agent Router

This router loads a markdown-based agent and exposes it via API endpoints.
"""

from pathlib import Path
from datetime import datetime

from ..utils.agent_router import create_agent_router

# Path to the agent YAML file
AGENT_PATH = Path(__file__).parent.parent.parent / "markdown_agents" / "my_new_agent" / "my_new_agent.yaml"

# Variables for Jinja2 templating in the markdown instructions
MARKDOWN_VARIABLES = {
    "current_date": datetime.now().strftime("%A, %B %d, %Y"),
    "user_name": "API User",
    "environment": "production"
}

# Create the router with standardized endpoints
router = create_agent_router(
    agent=str(AGENT_PATH),           # Path to YAML file
    prefix="/my-new-agent",          # URL prefix for endpoints
    agent_name="My New Agent",       # Human-readable name
    markdown_variables=MARKDOWN_VARIABLES  # Variables for templating
)

# The router automatically provides these endpoints:
# POST /my-new-agent/run      - Synchronous execution
# POST /my-new-agent/stream   - Real-time streaming
# GET  /my-new-agent/info     - Agent information
# GET  /my-new-agent/session/{session_id}  - Get session messages
# DELETE /my-new-agent/session/{session_id}  - Clear session
```

**Step 5: Register the Router in Main Application**

Edit `src/api/main.py` and add your router:

```python
# Add import at the top
from .routers.my_new_agent import router as my_new_agent_router

# Add router registration with other routers
app.include_router(my_new_agent_router)  # /my-new-agent/* endpoints
```

**Step 6: Test Your Agent**

Start the server and test your new agent:

```bash
# Start the server
uv run uvicorn src.api.main:app --reload

# Test the agent
curl -X POST "http://127.0.0.1:8000/my-new-agent/run" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, can you help me?"}'

# Check agent info
curl -X GET "http://127.0.0.1:8000/my-new-agent/info"
```

##### Complete Example: Simple Agent Without Sub-agents

**File: `src/markdown_agents/simple_agent/simple_agent.yaml`**
```yaml
name: "Simple Agent"
model: "gpt-4.1-mini"
# No sub_agents - this is a standalone agent
```

**File: `src/markdown_agents/simple_agent/simple_agent.md`**
```markdown
# Simple Agent Instructions

You are a simple, helpful assistant.

Today is {{ current_date }}.

Your task is to help users with their questions.
```

**File: `src/api/routers/simple_agent.py`**
```python
from pathlib import Path
from datetime import datetime
from ..utils.agent_router import create_agent_router

AGENT_PATH = Path(__file__).parent.parent.parent / "markdown_agents" / "simple_agent" / "simple_agent.yaml"

router = create_agent_router(
    agent=str(AGENT_PATH),
    prefix="/simple",
    agent_name="Simple Agent",
    markdown_variables={
        "current_date": datetime.now().strftime("%Y-%m-%d")
    }
)
```

##### Complete Example: Agent With Sub-agents

**File: `src/markdown_agents/coordinator/coordinator.yaml`**
```yaml
name: "Task Coordinator"
model: "gpt-4.1-mini"

# Reference other agents as sub-agents
sub_agents:
  - "helper_agent"
  - "analyzer_agent"

tool_descriptions:
  "Helper Agent": "Use for general assistance tasks"
  "Analyzer Agent": "Use for data analysis tasks"
```

**File: `src/markdown_agents/coordinator/coordinator.md`**
```markdown
# Task Coordinator Instructions

You coordinate complex tasks by delegating to specialized sub-agents.

## Available Tools

- **Helper Agent**: Use `helper_agent` for general tasks
- **Analyzer Agent**: Use `analyzer_agent` for analysis tasks

## Workflow

1. Understand the user's request
2. Break it down into subtasks
3. Use appropriate sub-agents for each subtask
4. Synthesize results into final response
```

##### Benefits of Markdown Agents

- ✅ **Version control friendly** - Easy to track changes in git
- ✅ **Non-programmer friendly** - Edit instructions without Python knowledge
- ✅ **Dynamic templating** - Use Jinja2 variables for runtime customization
- ✅ **Hierarchical structure** - Reference sub-agents easily
- ✅ **Separation of concerns** - Config, instructions, and code are separate
- ✅ **Hot reload support** - Changes to markdown files can be reloaded without code changes

##### Tips and Best Practices

1. **File Naming**: Use lowercase with underscores (e.g., `my_agent.yaml`, `my_agent.md`)
2. **Path References**: Sub-agents can be referenced as:
   - Simple names: `"helper_agent"` (searches in same directory)
   - Relative paths: `"subfolder/agent_name"`
   - Absolute paths: `"/full/path/to/agent"`
3. **Variables**: Pass runtime variables through `markdown_variables` in the router
4. **Testing**: Always test your agent after creation using the `/info` endpoint first
5. **Documentation**: Document your agent's purpose in the markdown instructions file

#### Option 3: Skills-based Agent (Agent Skills Specification)

Skills agents implement the open [Agent Skills specification](https://agentskills.io/docs/spec), providing a standardized format for defining agents that can be shared and validated.

##### Quick Start

**Step 1: Create a Skill Directory**

```bash
mkdir -p src/skills_agents/examples/my-skill
```

**Step 2: Create the SKILL.md File**

Create `src/skills_agents/examples/my-skill/SKILL.md`:

```markdown
---
name: my-skill
description: A helpful skill that assists with specific tasks. Use when the user needs help with task X.
license: Apache-2.0
metadata:
  author: your-name
  version: "1.0"
---

# My Skill Instructions

You are a specialized assistant for this task.

## Context

- **Date**: {{ current_date | default("Not specified") }}
- **User**: {{ user_name | default("Guest") }}

## Guidelines

1. Be helpful and concise
2. Provide examples when useful
3. Ask clarifying questions if needed
```

**Step 3: Validate the Skill**

```bash
# Validate all skills
./cli validate

# Validate specific skill
./cli validate src/skills_agents/examples/my-skill/
```

**Step 4: Use the Skill**

```python
from pathlib import Path
from skills_agents import build_agent_from_skill_path
from agents import Runner

# Build agent from skill
agent = build_agent_from_skill_path(
    Path("src/skills_agents/examples/my-skill"),
    variables={"current_date": "2024-01-15"}
)

# Run the agent
result = await Runner.run(agent, "Help me with this task")
```

##### Configure Top-Level Agents

Create an `agents.yaml` to expose skills through the API:

```yaml
default_model: "gpt-4.1-mini"
skills_directory: "."

agents:
  - name: "Orchestrator"
    skill: "task-orchestrator"
    sub_agents:
      - "code-review"
      - "data-analysis"
    variables:
      environment: "production"

  - name: "Code Reviewer"
    skill: "code-review"
```

Load and use:

```python
from skills_agents import load_top_level_agents

agents = load_top_level_agents(Path("agents.yaml"))
orchestrator = agents["Orchestrator"]  # Has sub-skills as tools
```

##### SKILL.md Format

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | 1-64 chars, lowercase alphanumeric and hyphens |
| `description` | Yes | 1-1024 chars, what skill does and when to use |
| `license` | No | License name or file reference |
| `compatibility` | No | Environment requirements (max 500 chars) |
| `metadata` | No | Arbitrary key-value pairs |
| `allowed-tools` | No | Space-delimited pre-approved tools |

##### Name Constraints

- Lowercase letters (`a-z`), numbers (`0-9`), and hyphens (`-`)
- Cannot start or end with hyphen
- No consecutive hyphens (`--`)
- Must match directory name

✅ Valid: `my-skill`, `code-review-v2`, `data-analysis`
❌ Invalid: `My-Skill`, `-skill`, `my--skill`, `my_skill`

##### CLI Commands

```bash
# Validate all skills recursively
./cli validate

# Validate with strict mode (warnings = errors)
./cli validate --strict

# List discovered skills
uv run python -m src.skills_agents.cli list
```

##### Benefits of Skills Agents

- ✅ **Standards-compliant** - Follows the open Agent Skills specification
- ✅ **Portable** - Skills can be shared across projects
- ✅ **Validated** - Built-in validation ensures spec compliance
- ✅ **Single file** - Everything in one `SKILL.md` with frontmatter
- ✅ **Jinja2 templating** - Dynamic instructions with variables
- ✅ **Hierarchical** - Sub-agents through `agents.yaml` configuration

See `src/skills_agents/README.md` for complete documentation.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root and the virtual environment is activated
2. **OpenAI API Key**: Check that `OPENAI_API_KEY` is set in your `.env` file
3. **Port Conflicts**: Change the port in the uvicorn command if 8000 is occupied
4. **Python Version**: Ensure Python 3.13+ is installed and selected
5. **Session Memory**: Set `ENABLE_SESSIONS=true` and restart server to enable conversation memory

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG uvicorn src.api.main:app --reload

# Check agent information and session configuration
curl http://127.0.0.1:8000/chat/info

# Test session functionality
curl -X POST http://127.0.0.1:8000/chat/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Test message", "session_id": "debug_session"}'
```

### Performance Optimization

- Use `--workers N` for production deployment
- Configure appropriate `--timeout-keep-alive` for long streaming sessions
- Monitor memory usage with longer conversations
- **Session cleanup**: Implement periodic cleanup of old conversation sessions
- **Database maintenance**: Regular SQLite VACUUM for optimal performance

## Use Cases

### 🤖 Conversational AI Applications
- **Customer support chatbots** with conversation context
- **Virtual assistants** that remember user preferences
- **Educational tutors** tracking learning progress
- **Healthcare assistants** maintaining patient interaction history

### 🏢 Enterprise Applications  
- **Employee helpdesk** with persistent conversation threads
- **Sales assistants** remembering customer interactions
- **Internal knowledge bots** with user-specific context
- **Multi-turn research assistants** building on previous queries

### 🛠️ Developer Tools
- **Code assistants** with project context memory
- **Documentation bots** maintaining conversation flow
- **API testing tools** with session-based request history
- **Interactive debugging assistants** with state persistence

## Contributing

1. Follow the established package structure
2. Use the standardized agent router pattern
3. **Session memory works automatically** - no special handling needed
4. Add comprehensive logging
5. Update documentation for new agents
6. Test both sync and streaming endpoints with and without sessions

---

**Built with FastAPI, OpenAI Agents SDK (with SQLiteSession), and uv for modern Python development.**
