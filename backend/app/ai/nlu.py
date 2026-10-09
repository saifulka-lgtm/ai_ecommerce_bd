"""
Lightweight rule-based natural-language understanding for Bangla + English,
used by MockAIProvider so the whole demo runs with zero API cost. This is
intentionally simple pattern matching, not a real language model — swapping
AI_PROVIDER to claude/ollama replaces this with genuine understanding
without touching tools/business logic.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

BANGLA_RANGE = re.compile(r"[ঀ-৿]")

CATEGORY_WORDS = {
    # More specific categories are listed — and checked — before the more
    # generic "shirt", so a message like "polo shirt" resolves to
    # "polo shirt" rather than matching the "shirt" substring first.
    "t-shirt": ["t-shirt", "tshirt", "t shirt", "টিশার্ট", "টি-শার্ট", "টি শার্ট"],
    "polo shirt": ["polo", "পোলো"],
    "shirt": ["shirt", "শার্ট"],
    "jeans": ["jeans", "জিন্স"],
    "pants": ["pant", "pants", "trouser", "প্যান্ট"],
    "hoodie": ["hoodie", "হুডি"],
    "jacket": ["jacket", "জ্যাকেট"],
}

COLOR_WORDS = {
    "black": ["black", "কালো"],
    "white": ["white", "সাদা"],
    "navy": ["navy", "নেভি"],
    "red": ["red", "লাল"],
    "blue": ["blue", "নীল"],
    "green": ["green", "সবুজ"],
    "grey": ["grey", "gray", "ধূসর"],
    "maroon": ["maroon", "মেরুন"],
    "beige": ["beige", "বেইজ"],
    "olive": ["olive", "অলিভ"],
}

SIZE_WORDS = ["xxl", "xl", "l", "m", "s", "2xl", "3xl"]

# Product nouns this clothing store never carries. If a customer asks for
# one of these, we must NOT silently fall back to an unfiltered/color-only
# search (which would return unrelated products) — the search should
# correctly come back empty so the AI can say "not found" instead of
# inventing a match. See spec section 19's "red shoes" example.
UNAVAILABLE_CATEGORY_WORDS = [
    "shoe", "shoes", "sneaker", "sneakers", "sandal", "sandals", "boot", "boots",
    "bag", "bags", "watch", "watches", "belt", "belts", "cap", "caps",
    "জুতা", "স্যান্ডেল", "ব্যাগ", "ঘড়ি", "বেল্ট", "টুপি",
]

PAYMENT_WORDS = {
    "demo_cod": ["cod", "cash on delivery", "cash", "ক্যাশ অন ডেলিভারি", "ক্যাশ", "নগদে"],
    "demo_mobile": ["bkash", "nagad", "rocket", "mobile payment", "মোবাইল", "বিকাশ", "নগদ", "রকেট"],
    "demo_card": ["card", "কার্ড", "visa", "mastercard"],
}

GREETING_WORDS = [
    "hi", "hello", "hey", "assalamu", "salam", "হাই", "হ্যালো", "সালাম", "আসসালামু",
]

ORDER_TRIGGER_WORDS = [
    "place the order", "i want to order", "want to order", "place order", "i want the",
    "place an order", "want to place", "place my order", "i'd like to order",
    "confirm", "checkout", "buy it", "order confirm",
    "অর্ডার করতে চাই", "অর্ডার করব", "কনফার্ম", "অর্ডার দিতে চাই",
]

CART_WORDS = ["cart", "my cart", "show my cart", "কার্ট", "ঝুড়ি"]

STOCK_WORDS = ["stock", "available", "do you have", "in stock", "স্টক", "আছে কি", "পাওয়া যাবে"]

PRICE_WORDS = ["price", "how much", "cost", "দাম", "কত টাকা", "দাম কত"]

VARIANT_WORDS = ["size", "sizes", "color", "colors", "colours", "সাইজ", "রং", "কালার"]

ADD_WORDS = ["add", "add to cart", "কার্টে যোগ", "যোগ করো", "নাও"]
REMOVE_WORDS = ["remove", "delete from cart", "বাদ দাও", "সরাও"]

STATUS_WORDS = ["order status", "status of my order", "অর্ডারের অবস্থা", "অর্ডার স্ট্যাটাস"]
CANCEL_WORDS = ["cancel", "বাতিল"]
MY_ORDERS_WORDS = ["my orders", "order history", "আমার অর্ডার", "অর্ডার হিস্ট্রি"]

# "Show me the details of my (delivered) order" -> full order details via the
# get_order tool. Only fires when the message is also about an order, so
# "product details" and "delivery charge" questions are not hijacked.
ORDER_DETAIL_WORDS = [
    "detail", "order info", "delivered",
    "ডিটেল", "ডিটেইল", "বিস্তারিত", "ডেলিভার হয়েছে", "ডেলিভারি হয়েছে", "ডেলিভার্ড",
]
RECOMMEND_WORDS = ["recommend", "suggest", "সাজেস্ট", "ভালো কিছু দেখাও"]

DISCOUNT_WORDS = [
    "discount", "sale", "on sale", "offer", "deal", "% off", "percent off",
    # "ডিসকা" alone (no closing "উন্ট"/"ইন্ট") is a broad catch-all: people
    # transliterate "discount" many different ways (ডিসকাউন্ট, ডিসকাইন্ট,
    # ডিসকান্ট...) and this prefix matches all of them without needing to
    # list every spelling.
    "ডিসকা", "ডিস্কাউন্ট", "অফার", "ছাড়", "সেল", "কমে",
]

# "Show me cheap / low-price products" → search sorted by price, lowest first.
# Must be checked BEFORE PRICE_WORDS, because "low price" contains "price".
CHEAP_WORDS = [
    "cheap", "cheapest", "low price", "low-price", "lowest price", "low cost",
    "budget", "affordable", "inexpensive",
    "কম দাম", "কমদাম", "কম মূল্য", "সস্তা", "সস্তায়", "সাশ্রয়ী",
    "লো প্রাইজ", "লো প্রাইস", "লো-প্রাইজ", "লো-প্রাইস", "লোপ্রাইজ", "লোপ্রাইস",
]
EXPENSIVE_WORDS = [
    "expensive", "high price", "high-price", "highest price", "premium",
    "দামি", "বেশি দাম", "হাই প্রাইজ", "হাই প্রাইস", "হাই-প্রাইজ", "হাই-প্রাইস",
]

PHONE_RE = re.compile(r"(?:\+?88)?01[3-9]\d{8}")
QUANTITY_RE = re.compile(
    r"(\d+)\s*(?:pcs|piece|pieces|টা|টি)?|(এক|দুই|তিন|চার|পাঁচ)\s*(?:টা|টি)"
)
BANGLA_NUMBER_WORDS = {"এক": 1, "দুই": 2, "তিন": 3, "চার": 4, "পাঁচ": 5}
MAX_PRICE_RE = re.compile(
    r"under\s*(?:৳|tk\.?|taka)?\s*(\d+)|(\d+)\s*টাকার\s*(?:মধ্যে|নিচে)|(?:৳|tk\.?)\s*(\d+)\s*(?:এর নিচে|এর মধ্যে)|below\s*(\d+)"
)


def detect_language(text: str) -> str:
    return "bn" if BANGLA_RANGE.search(text) else "en"


def _contains_any(text: str, words: List[str]) -> bool:
    """True if any trigger word/phrase appears in text. ASCII words use
    real word-boundary matching (a plain substring check would let "hi"
    false-positive-match inside "shirt", or "add" inside "address" —
    both were found as real bugs during testing). Bangla words keep
    substring containment: Bangla's combining vowel signs (matras) are
    not \\w characters, which breaks \\b boundary detection around them."""
    lower = text.lower()
    for w in words:
        if w.isascii():
            if re.search(r"(?<![a-z0-9])" + re.escape(w.lower()) + r"(?![a-z0-9])", lower):
                return True
        elif w in text:
            return True
    return False


def _contains_prefix_any(text: str, words: List[str]) -> bool:
    """Like _contains_any, but only enforces a LEFT word boundary (not
    preceded by a letter/digit) and allows anything to follow. Used for
    product-taxonomy words, where trailing suffixes are expected and
    wanted ("shirt" should still match "shirts", "shoe" should still
    match "shoes") — unlike action/intent trigger words, which use the
    stricter full-boundary _contains_any."""
    lower = text.lower()
    for w in words:
        if w.isascii():
            if re.search(r"(?<![a-z0-9])" + re.escape(w.lower()), lower):
                return True
        elif w in text:
            return True
    return False


def extract_category(text: str) -> Optional[str]:
    for canonical, variants in CATEGORY_WORDS.items():
        if _contains_prefix_any(text, variants):
            return canonical
    return None


def extract_unavailable_category(text: str) -> Optional[str]:
    """Returns the raw word if the customer asked for a product type this
    store simply doesn't sell, so the caller can force a (correctly) empty
    search rather than silently dropping the filter."""
    if _contains_prefix_any(text, UNAVAILABLE_CATEGORY_WORDS):
        lower = text.lower()
        for word in UNAVAILABLE_CATEGORY_WORDS:
            if _contains_prefix_any(lower, [word]):
                return word
    return None


def extract_color(text: str) -> Optional[str]:
    for canonical, variants in COLOR_WORDS.items():
        if _contains_prefix_any(text, variants):
            return canonical
    return None


def extract_size(text: str) -> Optional[str]:
    tokens = re.split(r"[\s,.]+", text.lower())
    for size in SIZE_WORDS:
        if size in tokens:
            return size.upper()
    return None


def extract_max_price(text: str) -> Optional[float]:
    match = MAX_PRICE_RE.search(text.lower())
    if not match:
        return None
    for group in match.groups():
        if group:
            return float(group)
    return None


def extract_price_sort(text: str) -> Optional[str]:
    """'price_asc' for cheap/low-price requests, 'price_desc' for
    expensive/premium ones, None when the customer didn't ask to rank by price."""
    lower = text.lower()
    if _contains_prefix_any(lower, CHEAP_WORDS):
        return "price_asc"
    if _contains_prefix_any(lower, EXPENSIVE_WORDS):
        return "price_desc"
    return None


def extract_on_sale(text: str) -> Optional[bool]:
    """True only when the customer actually asked about discounts/offers —
    returning None (not False) otherwise, so this never filters OUT
    non-discounted products when the topic wasn't mentioned. Uses prefix
    matching so plurals like "discounts" still match "discount"."""
    return True if _contains_prefix_any(text.lower(), DISCOUNT_WORDS) else None


def extract_quantity(text: str) -> Optional[int]:
    for bn_word, value in BANGLA_NUMBER_WORDS.items():
        if bn_word in text:
            return value
    # Note: no \b anchors here — Bengali combining vowel signs (matras) are
    # not \w characters, which breaks \b word-boundary detection right
    # after a Bengali digit+counter like "২টা" (digit + টা).
    match = re.search(r"(\d+)\s*(?:টা|টি)", text)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*(?:pcs|pieces|piece)\b", text.lower())
    if match:
        return int(match.group(1))
    # Last resort: a bare number not attached to a price/currency marker
    # ("Add 2 of the first product", "Add 99 M size black to cart") — but
    # never a number that's actually a price ("under 1000 taka", "৳650").
    for match in re.finditer(r"\b(\d+)\b", text.lower()):
        tail = text.lower()[match.end():match.end() + 12]
        head = text.lower()[max(0, match.start() - 6):match.start()]
        if re.search(r"^\s*(?:taka|৳|tk|%)", tail) or re.search(r"(?:৳|under|below)\s*$", head):
            continue
        return int(match.group(1))
    return None


def extract_phone(text: str) -> Optional[str]:
    match = PHONE_RE.search(text.replace(" ", ""))
    return match.group(0) if match else None


def extract_payment_method(text: str) -> Optional[str]:
    lower = text.lower()
    for method, variants in PAYMENT_WORDS.items():
        if _contains_any(lower, variants):
            return method
    return None


def extract_name(text: str) -> Optional[str]:
    patterns = [
        r"my name is ([A-Za-z .]+)",
        r"i am ([A-Za-z .]+)",
        r"name[:\-]\s*([A-Za-z .]+)",
        r"আমার নাম\s+([^\d,.।]+)",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip().rstrip(".،,")
    return None


def extract_address(text: str) -> Optional[str]:
    patterns = [
        r"address[:\-]?\s*(.+)",
        r"ঠিকানা[:\-]?\s*(.+)",
        r"deliver(?:y)? (?:to|at)\s+(.+)",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def extract_order_number(text: str) -> Optional[str]:
    match = re.search(r"DEMO-\d{4,10}", text.upper())
    return match.group(0) if match else None


def extract_order_fields(full_text: str) -> Dict[str, Any]:
    """Best-effort extraction of the 4 fields needed for create_demo_order,
    scanning the whole conversation text gathered so far."""
    fields = {}
    name = extract_name(full_text)
    if name:
        fields["customer_name"] = name
    phone = extract_phone(full_text)
    if phone:
        fields["customer_phone"] = phone
    address = extract_address(full_text)
    if address:
        fields["customer_address"] = address
    payment = extract_payment_method(full_text)
    if payment:
        fields["payment_method"] = payment
    return fields


def classify_intent(text: str) -> Tuple[str, str]:
    """Returns (intent, language). Order of checks matters — more specific
    intents are checked before generic 'search'."""
    language = detect_language(text)
    lower = text.lower()

    if _contains_any(lower, GREETING_WORDS) and len(text.split()) <= 4:
        return "greeting", language
    if _contains_any(lower, CANCEL_WORDS) and "order" in lower or "বাতিল" in text:
        return "cancel_order", language
    if (("order" in lower) or ("অর্ডার" in text)) and (
        _contains_prefix_any(lower, ORDER_DETAIL_WORDS)
    ):
        return "order_details", language
    if _contains_any(lower, STATUS_WORDS):
        return "order_status", language
    if _contains_any(lower, MY_ORDERS_WORDS):
        return "my_orders", language
    if _contains_any(lower, ORDER_TRIGGER_WORDS):
        return "place_order", language
    if _contains_any(lower, ADD_WORDS):
        return "add_to_cart", language
    if _contains_any(lower, REMOVE_WORDS):
        return "remove_from_cart", language
    if _contains_any(lower, CART_WORDS):
        return "view_cart", language
    if _contains_any(lower, RECOMMEND_WORDS):
        return "recommend", language
    # Checked before STOCK_WORDS: "any discounts available?" would otherwise
    # match "available" and get misrouted to check_stock. Prefix match so
    # "discounts" (plural) still matches "discount".
    if _contains_prefix_any(lower, DISCOUNT_WORDS):
        return "search", language
    # Also before PRICE_WORDS: "low price products" contains "price" and
    # would otherwise be misrouted to product_details.
    if _contains_prefix_any(lower, CHEAP_WORDS) or _contains_prefix_any(lower, EXPENSIVE_WORDS):
        return "search", language
    if _contains_any(lower, STOCK_WORDS) or _contains_any(lower, VARIANT_WORDS):
        return "check_stock", language
    if _contains_any(lower, PRICE_WORDS):
        return "product_details", language
    if extract_category(lower) or extract_color(lower) or "show" in lower or "দেখাও" in text:
        return "search", language

    return "unknown", language
