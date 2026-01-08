"""
Helper Agent Router

This demonstrates loading a simple markdown-based agent without sub-agents.
"""

from pathlib import Path
from datetime import datetime

from ..utils.agent_router import create_agent_router

# Path to the helper agent files
AGENT_PATH = (
    Path(__file__).parent.parent.parent
    / "markdown_agents"
    / "examples"
    / "helper_agent.yaml"
)

# Variables for Jinja2 templating in the markdown instructions
MARKDOWN_VARIABLES = {
    "current_date": datetime.now().strftime("%A, %B %d, %Y"),
    "task_context": "API request",
}

# Create the router with standardized endpoints
router = create_agent_router(
    agent=str(AGENT_PATH),
    prefix="/helper",
    agent_name="Helper Agent",
    markdown_variables=MARKDOWN_VARIABLES,
)

# The router now automatically has these endpoints:
# POST /helper/run - Synchronous execution
# POST /helper/stream - Real-time streaming
# GET /helper/info - Agent information
# GET /helper/session/{session_id} - Get session messages
# DELETE /helper/session/{session_id} - Clear session
