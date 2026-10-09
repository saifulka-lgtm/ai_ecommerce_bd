"""
Tiny in-memory sliding-window rate limiter (per client IP). Good for one
server process; with several servers use a shared store such as Redis.
"""
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request

from app.config import get_settings


class RateLimiter:
    def __init__(self, max_calls: int, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: float = None) -> bool:
        now = time.monotonic() if now is None else now
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window:
            hits.popleft()
        if len(hits) >= self.max_calls:
            return False
        hits.append(now)
        return True


def rate_limited(limiter: RateLimiter, message: str):
    """FastAPI dependency: raises 429 when the caller exceeds the limit."""
    def dependency(request: Request):
        if not get_settings().rate_limit_enabled:
            return
        ip = request.client.host if request.client else "unknown"
        if not limiter.allow(ip):
            raise HTTPException(status_code=429, detail=message, headers={"Retry-After": str(limiter.window)})
    return dependency
