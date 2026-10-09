import random
import string


def generate_order_number() -> str:
    suffix = "".join(random.choices(string.digits, k=4))
    return f"DEMO-{suffix}"


def generate_transaction_ref() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"DEMO-TXN-{suffix}"
