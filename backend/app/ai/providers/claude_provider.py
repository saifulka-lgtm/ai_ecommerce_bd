"""
ClaudeProvider — real tool-calling via the Anthropic Messages API. Only
used when AI_PROVIDER=claude and ANTHROPIC_API_KEY is set. Claude decides
*which* tool to call and with what arguments (real language understanding,
Bangla + English); the actual reply text is still rendered from the tool's
structured result via reply_templates, so the AI can never state a
product/price/stock/order fact it didn't get back from the database.
"""
from typing import Any, Dict, List

import anthropic

from app.ai.base import AIProvider
from app.ai.schemas import AgentDecision, ToolSpec
from app.ai.reply_templates import render_reply
from app.ai.nlu import detect_language
from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = (
    "You are the shopping assistant for a Bangladeshi clothing store demo. "
    "You must ALWAYS use the provided tools to look up real product, stock, cart, and "
    "order information — never invent a product, price, stock level, or order status. "
    "The customer may write in Bangla or English; understand either. "
    "If a message is small talk or a general question that needs no store data, reply directly with no tool call. "
    "When resolving a reference like 'the second one' or 'দ্বিতীয়টা', pass it "
    "as the 'reference' argument to the relevant tool rather than guessing an id yourself."
)


def _to_claude_tool(spec: ToolSpec) -> Dict[str, Any]:
    properties = {}
    for name, schema in spec.parameters.items():
        prop = {"type": schema.get("type", "string")}
        if "description" in schema:
            prop["description"] = schema["description"]
        if "enum" in schema:
            prop["enum"] = schema["enum"]
        properties[name] = prop
    return {
        "name": spec.name,
        "description": spec.description,
        "input_schema": {"type": "object", "properties": properties},
    }


class ClaudeProvider(AIProvider):
    def __init__(self):
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set — cannot use AI_PROVIDER=claude")
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-5"

    def decide_action(self, message: str, history: List[Dict[str, str]], tools: List[ToolSpec]) -> AgentDecision:
        language = detect_language(message)
        claude_messages = [
            {"role": h["role"], "content": h["content"]}
            for h in history
            if h.get("role") in ("user", "assistant")
        ]
        claude_messages.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=claude_messages,
            tools=[_to_claude_tool(t) for t in tools],
        )

        for block in response.content:
            if block.type == "tool_use":
                return AgentDecision(tool_name=block.name, tool_arguments=dict(block.input), language=language)

        text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
        return AgentDecision(direct_reply=text or None, language=language)

    def generate_reply(
        self,
        message: str,
        language: str,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        tool_result: Dict[str, Any],
    ) -> str:
        return render_reply(tool_name, tool_result, language)
