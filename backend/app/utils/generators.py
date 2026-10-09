import random
import secrets
import string


def generate_order_number() -> str:
    # 8 random digits (100 million combinations) from a cryptographically
    # secure source, so order numbers can't be guessed or enumerated.
    suffix = "".join(secrets.choice(string.digits) for _ in range(8))
    return f"DEMO-{suffix}"


def generate_transaction_ref() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"DEMO-TXN-{suffix}"
