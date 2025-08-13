from time import time
from typing import Dict

WINDOW_SECONDS = 60
MAX_ATTEMPTS = 10

class RateLimiter:
    def __init__(self) -> None:
        self.state: Dict[str, list] = {}

    def allow(self, key: str) -> bool:
        now = time()
        window = self.state.setdefault(key, [])
        window[:] = [t for t in window if now - t < WINDOW_SECONDS]
        if len(window) >= MAX_ATTEMPTS:
            return False
        window.append(now)
        return True
