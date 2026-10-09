"""
Shared shapes used by every AI provider and by the agent orchestrator, so
Mock/Claude/Ollama are interchangeable without the agent or tools caring
which one is active.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolSpec:
    """Describes one backend tool the AI agent may call, in a
    provider-neutral form. Claude/Ollama providers translate this into
    their own function-calling schema."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON-schema-like dict of {param: {"type":..., "description":...}}


@dataclass
class AgentDecision:
    """What the provider wants to do in response to one customer message."""

    tool_name: Optional[str] = None
    tool_arguments: Dict[str, Any] = field(default_factory=dict)
    # Set when no tool call is needed (greeting, small talk, FAQ) — the
    # agent will use this directly instead of calling a tool.
    direct_reply: Optional[str] = None
    language: str = "en"  # "en" or "bn"
