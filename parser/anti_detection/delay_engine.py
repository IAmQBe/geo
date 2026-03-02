import asyncio
import random


class DelayEngine:
    def __init__(self, min_delay: float, max_delay: float) -> None:
        self.min_delay = min_delay
        self.max_delay = max_delay

    async def sleep(self, factor: float = 1.0) -> None:
        low = max(0.2, self.min_delay * factor)
        high = max(low, self.max_delay * factor)
        await asyncio.sleep(random.uniform(low, high))
