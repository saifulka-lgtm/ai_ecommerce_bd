"""
Simple admin authentication for the demo. Not meant for production use:
a single admin account configured via environment variables, and a
signed, time-limited bearer token (HMAC-SHA256) instead of a full OAuth/JWT
stack. Good enough to keep the admin panel from being wide open, while
staying easy for a beginner to read end-to-end.
"""
import base64
import hashlib
import hmac
import os
import time

from app.config import get_settings

settings = get_settings()

TOKEN_TTL_SECONDS = 60 * 60 * 8  # 8 hours


class InvalidCredentialsError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


def _sign(payload: str) -> str:
    sig = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return sig


PBKDF2_ITERATIONS = 240_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_hash(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def _password_ok(password: str) -> bool:
    if settings.admin_password_hash:
        return _verify_hash(password, settings.admin_password_hash)
    return hmac.compare_digest(password.encode(), settings.admin_password.encode())


def authenticate_admin(username: str, password: str) -> str:
    # Both checks always run and use constant-time comparison, so response
    # timing doesn't reveal which of the two was wrong.
    user_ok = hmac.compare_digest(username.encode(), settings.admin_username.encode())
    pass_ok = _password_ok(password)
    if not (user_ok and pass_ok):
        raise InvalidCredentialsError("Invalid admin username or password")

    expires_at = int(time.time()) + TOKEN_TTL_SECONDS
    payload = f"{username}:{expires_at}"
    signature = _sign(payload)
    raw_token = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(raw_token.encode()).decode()


def verify_admin_token(token: str) -> str:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        username, expires_at, signature = raw.split(":")
    except Exception:
        raise InvalidTokenError("Malformed token")

    expected_sig = _sign(f"{username}:{expires_at}")
    if not hmac.compare_digest(expected_sig, signature):
        raise InvalidTokenError("Invalid token signature")

    if int(expires_at) < int(time.time()):
        raise InvalidTokenError("Token expired")

    if username != settings.admin_username:
        raise InvalidTokenError("Unknown admin user")

    return username
