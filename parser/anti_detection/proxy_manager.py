from __future__ import annotations

import random
from dataclasses import dataclass

import httpx


@dataclass
class ProxyItem:
    url: str
    score: float = 1.0


class ProxyManager:
    def __init__(self, proxy_list_url: str) -> None:
        self._proxy_list_url = proxy_list_url
        self._pool: list[ProxyItem] = []

    @property
    def size(self) -> int:
        return len(self._pool)

    async def refresh(self) -> None:
        if not self._proxy_list_url:
            self._pool = []
            return

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(self._proxy_list_url)
            response.raise_for_status()
            rows = [row.strip() for row in response.text.splitlines() if row.strip()]
            normalized: list[str] = []
            seen: set[str] = set()
            for row in rows:
                value = row
                if "://" not in value:
                    value = f"http://{value}"
                if value in seen:
                    continue
                seen.add(value)
                normalized.append(value)

            self._pool = [ProxyItem(url=row) for row in normalized]

    def pick(self) -> str | None:
        if not self._pool:
            return None
        weighted = sorted(self._pool, key=lambda item: item.score, reverse=True)
        top = weighted[: max(1, len(weighted) // 3)]
        return random.choice(top).url

    def report_success(self, proxy_url: str | None) -> None:
        if proxy_url is None:
            return
        for proxy in self._pool:
            if proxy.url == proxy_url:
                proxy.score = min(proxy.score + 0.05, 2.0)
                return

    def report_failure(self, proxy_url: str | None) -> None:
        if proxy_url is None:
            return
        for proxy in self._pool:
            if proxy.url == proxy_url:
                proxy.score = max(proxy.score - 0.3, 0.1)
                return
