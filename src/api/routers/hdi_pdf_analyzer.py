"""
HDI PDF Analyzer Router

Exposes the HDI PDF analyzer agent as an API endpoint.
This agent orchestrates PDF analysis for Human Development Index reports,
extracting Gender Inequality Index (GII) data and computing European averages.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..utils.agent_router import create_agent_router
from src.skills_agents.loader import load_top_level_agents
from src.skills_agents.schemas.hdi_pdf_analyzer import HDIPDFAnalysisResult


# Path to the skills directory and agents config
SKILLS_DIR = Path(__file__).parent.parent.parent / "skills_agents" / "examples"
AGENTS_CONFIG_PATH = SKILLS_DIR / "agents.yaml"


def get_hdi_analyzer_agent():
    """
    Load the HDI PDF Analyzer agent from skills configuration.

    Returns:
        Agent instance configured for HDI PDF analysis
    """
    # Variables for Jinja2 templating in the skill instructions
    variables = {
        "current_date": datetime.now().strftime("%A, %B %d, %Y"),
        "document_url": "https://hdr.undp.org/system/files/documents/global-report-document/hdr2023-24reporten.pdf",
    }

    # Load all configured agents
    agents = load_top_level_agents(
        config_path=AGENTS_CONFIG_PATH,
        skills_directory=SKILLS_DIR,
        variables=variables,
        validate=True,
    )

    # Get the HDI PDF Analyzer agent
    if "HDI PDF Analyzer" not in agents:
        raise ValueError(
            "HDI PDF Analyzer agent not found in agents.yaml configuration"
        )

    return agents["HDI PDF Analyzer"]


# Load the agent
hdi_analyzer_agent = get_hdi_analyzer_agent()

# Create the router with standardized endpoints
router = create_agent_router(
    agent=hdi_analyzer_agent,
    prefix="/hdi-pdf-analyzer",
    agent_name="HDI PDF Analyzer",
)


# Additional endpoint-specific models for enhanced API documentation
class HDIAnalysisRequest(BaseModel):
    """Request model for HDI PDF analysis with optional document URL."""

    input: str = Field(
        default="Analyze the HDI report and extract GII data for European countries",
        description="Analysis instructions or specific query about the HDI document",
    )
    document_url: Optional[str] = Field(
        default=None,
        description="URL of the HDI PDF document to analyze (uses default if not provided)",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation memory persistence",
    )


# Export the response model for documentation
HDIAnalysisResponse = HDIPDFAnalysisResult

# The router now automatically has these endpoints:
# POST /hdi-pdf-analyzer/run - Synchronous execution
# POST /hdi-pdf-analyzer/stream - Real-time streaming
# GET /hdi-pdf-analyzer/info - Agent information
# GET /hdi-pdf-analyzer/session/{session_id} - Get session messages
# DELETE /hdi-pdf-analyzer/session/{session_id} - Clear session
