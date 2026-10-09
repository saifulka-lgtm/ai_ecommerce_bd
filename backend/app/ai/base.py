"""
The AIProvider interface. Business logic (tools, services, database) never
imports a specific provider directly — it only talks to this interface, so
swapping AI_PROVIDER=mock|claude|ollama never requires touching agent/tools
code (requirement: keep the AI provider layer modular).
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.ai.schemas import AgentDecision, ToolSpec


class AIProvider(ABC):
    @abstractmethod
    def decide_action(
        self,
        message: str,
        history: List[Dict[str, str]],
        tools: List[ToolSpec],
    ) -> AgentDecision:
        """Look at the customer's message + recent conversation history and
        decide: call a tool (and with what arguments), or reply directly
        (small talk / FAQ that needs no store data)."""
        raise NotImplementedError

    @abstractmethod
    def generate_reply(
        self,
        message: str,
        language: str,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        tool_result: Dict[str, Any],
    ) -> str:
        """Turn a tool's structured result into a short, natural-language
        reply in the customer's language. Must never state facts that are
        not present in tool_result."""
        raise NotImplementedError

    def generate_response(self, prompt: str, context: List[Dict[str, str]] | None = None) -> str:
        """Plain generation, used for simple FAQ-style replies with no tool
        call involved. Default implementation defers to generate_reply with
        an empty tool result; providers may override for something richer."""
        return self.generate_reply(prompt, "en", "none", {}, {})

    def stream_response(self, prompt: str, context: List[Dict[str, str]] | None = None):
        """Optional streaming variant. Default: yield the full response once."""
        yield self.generate_response(prompt, context)
