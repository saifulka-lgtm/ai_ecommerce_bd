"""
MockAIProvider — the default, free provider. Deterministic keyword/regex
rules (Bangla + English) map customer messages onto the same 15 tools a
real LLM provider would call, so the full demo in the spec works with
AI_PROVIDER=mock and no API key at all.
"""
from typing import Any, Dict, List

from app.ai.base import AIProvider
from app.ai.schemas import AgentDecision, ToolSpec
from app.ai.constants import ORDER_PENDING_MARKER
from app.ai import nlu

GREETINGS = {
    "en": "Hi! I'm your AI shopping assistant. Ask me things like \"Show me men's black T-shirts\" or \"What is my order status?\" and I'll look it up for you.",
    "bn": "হ্যালো! আমি আপনার AI শপিং অ্যাসিস্ট্যান্ট। আমাকে জিজ্ঞাসা করুন যেমন \"কালো টি-শার্ট দেখাও\" বা \"আমার অর্ডারের অবস্থা কী\" — আমি সাথে সাথে দেখে জানাবো।",
}

UNKNOWN = {
    "en": "I'm not sure I understood that — you can ask me to search products, check price/stock, manage your cart, or place/check an order.",
    "bn": "দুঃখিত, বুঝতে পারিনি — আপনি প্রোডাক্ট খুঁজতে, দাম/স্টক চেক করতে, কার্ট ম্যানেজ করতে, বা অর্ডার দিতে/চেক করতে বলতে পারেন।",
}


def _clean(args: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in args.items() if v is not None}


def _history_text(history: List[Dict[str, str]]) -> str:
    return " ".join(h.get("content", "") for h in history if h.get("role") == "user")


class MockAIProvider(AIProvider):
    def decide_action(self, message: str, history: List[Dict[str, str]], tools: List[ToolSpec]) -> AgentDecision:
        intent, language = nlu.classify_intent(message)

        pending_order = any(
            h.get("role") == "system" and ORDER_PENDING_MARKER in h.get("content", "") for h in history
        )

        if pending_order and intent not in ("cancel_order",):
            return self._continue_order_flow(message, history, language)

        if intent == "greeting":
            return AgentDecision(direct_reply=GREETINGS[language], language=language)

        if intent == "search":
            category = nlu.extract_category(message.lower()) or nlu.extract_unavailable_category(message)
            args = {
                "category": category,
                "color": nlu.extract_color(message.lower()),
                "size": nlu.extract_size(message),
                "max_price": nlu.extract_max_price(message),
                "on_sale": nlu.extract_on_sale(message),
                "sort": nlu.extract_price_sort(message),
            }
            return AgentDecision(tool_name="search_products", tool_arguments=_clean(args), language=language)

        if intent == "product_details":
            return AgentDecision(
                tool_name="get_product_details",
                tool_arguments={"reference": message, "product_query": message},
                language=language,
            )

        if intent == "check_stock":
            return AgentDecision(
                tool_name="check_product_stock",
                tool_arguments=_clean({
                    "reference": message,
                    "product_query": message,
                    "size": nlu.extract_size(message),
                    "color": nlu.extract_color(message.lower()),
                }),
                language=language,
            )

        if intent == "add_to_cart":
            return AgentDecision(
                tool_name="add_to_cart",
                tool_arguments=_clean({
                    "reference": message,
                    "product_query": message,
                    "size": nlu.extract_size(message),
                    "color": nlu.extract_color(message.lower()),
                    "quantity": nlu.extract_quantity(message) or 1,
                }),
                language=language,
            )

        if intent == "remove_from_cart":
            return AgentDecision(
                tool_name="remove_from_cart",
                tool_arguments=_clean({
                    "reference": message,
                    "product_query": message,
                    "size": nlu.extract_size(message),
                    "color": nlu.extract_color(message.lower()),
                }),
                language=language,
            )

        if intent == "view_cart":
            return AgentDecision(tool_name="get_cart", language=language)

        if intent == "recommend":
            return AgentDecision(
                tool_name="recommend_products",
                tool_arguments=_clean({"category": nlu.extract_category(message.lower())}),
                language=language,
            )

        if intent == "place_order":
            return self._continue_order_flow(message, history, language)

        if intent == "order_status":
            return AgentDecision(
                tool_name="check_order_status",
                tool_arguments=_clean({
                    "order_number": nlu.extract_order_number(message),
                    "customer_phone": nlu.extract_phone(message) or nlu.extract_phone(_history_text(history)),
                }),
                language=language,
            )

        if intent == "order_details":
            return AgentDecision(
                tool_name="get_order",
                tool_arguments=_clean({
                    "order_number": nlu.extract_order_number(message),
                    "customer_phone": nlu.extract_phone(message) or nlu.extract_phone(_history_text(history)),
                }),
                language=language,
            )

        if intent == "cancel_order":
            return AgentDecision(
                tool_name="cancel_demo_order",
                tool_arguments=_clean({
                    "order_number": nlu.extract_order_number(message),
                    "customer_phone": nlu.extract_phone(message) or nlu.extract_phone(_history_text(history)),
                }),
                language=language,
            )

        if intent == "my_orders":
            phone = nlu.extract_phone(message) or nlu.extract_phone(_history_text(history))
            return AgentDecision(
                tool_name="get_customer_orders",
                tool_arguments=_clean({"customer_phone": phone}),
                language=language,
            )

        return AgentDecision(direct_reply=UNKNOWN[language], language=language)

    def _continue_order_flow(self, message, history, language) -> AgentDecision:
        """Always calls create_demo_order (even with partial info) so the
        attempt is logged via AIToolLog — that log is what lets the agent
        recognise 'still mid-order' on the next turn via ORDER_PENDING_MARKER.
        If fields are still missing, the tool returns an error and
        reply_templates phrases the "please share X" follow-up."""
        full_text = _history_text(history) + " " + message
        fields = nlu.extract_order_fields(full_text)
        return AgentDecision(tool_name="create_demo_order", tool_arguments=fields, language=language)

    def generate_reply(
        self,
        message: str,
        language: str,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        tool_result: Dict[str, Any],
    ) -> str:
        from app.ai.reply_templates import render_reply
        return render_reply(tool_name, tool_result, language)
