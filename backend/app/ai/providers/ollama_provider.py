"""
OllamaProvider — real tool-calling via a locally-running Ollama server
(free, no API key, runs on the developer's own machine). Used when
AI_PROVIDER=ollama. Same design as ClaudeProvider: the model decides which
tool to call, and the reply text is rendered from the tool's structured
result so nothing is invented.
"""
import json
from typing import Any, Dict, List

import httpx

from app.ai.base import AIProvider
from app.ai.schemas import AgentDecision, ToolSpec
from app.ai.reply_templates import render_reply
from app.ai.nlu import detect_language
from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = (
    "You are the shopping assistant for a Bangladeshi clothing store demo. "
    "Always use the provided tools to look up real product, stock, cart, and order "
    "information. Never invent a product, price, stock level, or order status. "
    "The customer may write in Bangla or English."
)


def _to_ollama_tool(spec: ToolSpec) -> Dict[str, Any]:
    properties = {}
    for name, schema in spec.parameters.items():
        prop = {"type": schema.get("type", "string")}
        if "description" in schema:
            prop["description"] = schema["description"]
        if "enum" in schema:
            prop["enum"] = schema["enum"]
        properties[name] = prop
    return {
        "type": "function",
        "function": {
            "name": spec.name,
            "description": spec.description,
            "parameters": {"type": "object", "properties": properties},
        },
    }


class OllamaProvider(AIProvider):
    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    def decide_action(self, message: str, history: List[Dict[str, str]], tools: List[ToolSpec]) -> AgentDecision:
        language = detect_language(message)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [
            {"role": h["role"], "content": h["content"]}
            for h in history
            if h.get("role") in ("user", "assistant")
        ]
        messages.append({"role": "user", "content": message})

        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "tools": [_to_ollama_tool(t) for t in tools],
                    "stream": False,
                },
                timeout=60,
            )
            resp.raise_for_status()
            payload = resp.json()
        except (httpx.HTTPError, ValueError) as e:
            return AgentDecision(
                direct_reply=(
                    "AI provider unavailable (couldn't reach Ollama). "
                    "Please make sure Ollama is running, or switch AI_PROVIDER to 'mock'."
                    if language == "en"
                    else "AI প্রোভাইডার এখন উপলব্ধ নয় (Ollama চালু আছে কিনা দেখুন), অথবা AI_PROVIDER=mock করুন।"
                ),
                language=language,
            )

        message_obj = payload.get("message", {})
        tool_calls = message_obj.get("tool_calls") or []
        if tool_calls:
            call = tool_calls[0]
            fn = call.get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            return AgentDecision(tool_name=fn.get("name"), tool_arguments=args or {}, language=language)

        text = message_obj.get("content", "")
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
