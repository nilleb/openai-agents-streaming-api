"""
Markdown-based Agent System

A file-based agent system where agents are defined by:
- Markdown files containing instructions (with Jinja2 templating)
- YAML files containing configuration (model, sub-agents, etc.)

The filename (without extension) becomes the agent name.
"""

from .loader import load_agent_from_file, load_agent_from_path
from .builder import AgentBuilder, AgentConfig

__all__ = [
    "load_agent_from_file",
    "load_agent_from_path",
    "AgentBuilder",
    "AgentConfig",
]
