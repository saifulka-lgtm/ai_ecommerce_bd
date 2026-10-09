"""Shared markers agent.py injects into conversation history so any
provider (mock or real) knows extra context beyond the raw message text."""

ORDER_PENDING_MARKER = "[ORDER_PENDING]"

MISSING_FIELD_PROMPTS = {
    "customer_name": {"en": "your name", "bn": "আপনার নাম"},
    "customer_phone": {"en": "your phone number", "bn": "আপনার ফোন নম্বর"},
    "customer_address": {"en": "your delivery address", "bn": "আপনার ডেলিভারি ঠিকানা"},
    "payment_method": {"en": "a payment method (Cash on Delivery / Card / Mobile)", "bn": "পেমেন্ট পদ্ধতি (Cash on Delivery / Card / Mobile)"},
}
