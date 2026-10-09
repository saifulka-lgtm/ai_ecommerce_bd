"""
Resolves natural-language references to a specific product that was already
shown to the customer in this conversation ("the second one", "প্রথমটা",
"this one"), plus fuzzy text matching by name. Never guesses a product that
was not actually returned by search_products/get_product_details.
"""
import re
from typing import Optional, Dict, Any, List

from app.services import conversation_service
from app.tools.context import ToolContext

ORDINAL_WORDS_EN = {
    "first": 0, "1st": 0, "one": 0,
    "second": 1, "2nd": 1, "two": 1,
    "third": 2, "3rd": 2, "three": 2,
    "fourth": 3, "4th": 3,
    "fifth": 4, "5th": 4,
    "last": -1,
}

ORDINAL_WORDS_BN = {
    "প্রথম": 0, "প্রথমটা": 0, "প্রথমটি": 0,
    "দ্বিতীয়": 1, "দ্বিতীয়টা": 1, "দ্বিতীয়টি": 1,
    "তৃতীয়": 2, "তৃতীয়টা": 2, "তৃতীয়টি": 2,
    "চতুর্থ": 3, "পঞ্চম": 4,
    "শেষ": -1, "শেষটা": -1,
}


def extract_ordinal_index(text: str) -> Optional[int]:
    text_lower = text.lower()
    for word, idx in {**ORDINAL_WORDS_EN, **ORDINAL_WORDS_BN}.items():
        if word in text_lower:
            return idx
    # "product 5" / "#3" / "৫ নম্বর" style references -> 1-indexed
    match = re.search(r"(?:product|item|#)\s*(\d+)", text_lower)
    if match:
        return int(match.group(1)) - 1
    return None


def resolve_from_last_shown(ctx: ToolContext, message: str) -> Optional[Dict[str, Any]]:
    """Try to resolve "the Nth one" against the products most recently shown
    in this conversation. Returns the stored product dict (as it was shown)
    or None."""
    shown = conversation_service.get_last_shown_products(ctx.db, ctx.conversation)
    if not shown:
        return None
    idx = extract_ordinal_index(message)
    if idx is None:
        return None
    try:
        return shown[idx]
    except IndexError:
        return None


def most_recently_shown_single(ctx: ToolContext) -> Optional[Dict[str, Any]]:
    """When the customer says "this one"/"এটা" with only one product shown,
    or after viewing a single product's details."""
    shown = conversation_service.get_last_shown_products(ctx.db, ctx.conversation)
    if len(shown) == 1:
        return shown[0]
    return None
