import random

from fake_useragent import UserAgent


class UserAgentRotator:
    def __init__(self) -> None:
        self.ua = UserAgent()
        self._fallback_pool = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        ]

    def random(self) -> str:
        try:
            return self.ua.random
        except Exception:
            return random.choice(self._fallback_pool)
