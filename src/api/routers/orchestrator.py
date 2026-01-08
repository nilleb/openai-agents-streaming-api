"""
Orchestrator Agent Router

This demonstrates loading a markdown-based agent and creating a router for it.
The orchestrator agent uses sub-agents (helper_agent and analyzer_agent) as tools.
"""

from pathlib import Path
from datetime import datetime

from ..utils.agent_router import create_agent_router

# Path to the orchestrator agent files
AGENT_PATH = (
    Path(__file__).parent.parent.parent
    / "markdown_agents"
    / "examples"
    / "orchestrator.yaml"
)

# Variables for Jinja2 templating in the markdown instructions
MARKDOWN_VARIABLES = {
    "current_date": datetime.now().strftime("%A, %B %d, %Y"),
    "user_name": "API User",
    "environment": "production",
}

# Create the router with standardized endpoints
router = create_agent_router(
    agent=str(AGENT_PATH),
    prefix="/orchestrator",
    agent_name="Orchestrator Agent",
    markdown_variables=MARKDOWN_VARIABLES,
)

# The router now automatically has these endpoints:
# POST /orchestrator/run - Synchronous execution
# POST /orchestrator/stream - Real-time streaming
# GET /orchestrator/info - Agent information
# GET /orchestrator/session/{session_id} - Get session messages
# DELETE /orchestrator/session/{session_id} - Clear session
