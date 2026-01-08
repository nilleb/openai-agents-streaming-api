# Deep Research Agent Package
# Multi-agent research system using OpenAI Agents SDK

from .models import (
    ResearchStatus,
    SearchAPI,
    MCPServerConfig,
    ResearchContext,
    ClarificationResponse,
    ResearchBriefResponse,
    ResearchTask,
    SupervisorDecision,
    CompressedResearch,
    FinalReport,
)
from .agents import (
    clarification_agent,
    research_brief_agent,
    supervisor_agent,
    researcher_agent,
    compression_agent,
    final_report_agent,
)
from .config import DeepResearchConfig

__version__ = "1.0.0"
__all__ = [
    "DeepResearchConfig",
    "ResearchStatus",
    "SearchAPI",
    "MCPServerConfig",
    "ResearchContext",
    "ClarificationResponse",
    "ResearchBriefResponse",
    "ResearchTask",
    "SupervisorDecision",
    "CompressedResearch",
    "FinalReport",
    "clarification_agent",
    "research_brief_agent",
    "supervisor_agent",
    "researcher_agent",
    "compression_agent",
    "final_report_agent",
]
