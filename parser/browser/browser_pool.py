from __future__ import annotations

from contextlib import asynccontextmanager
from urllib.parse import urlparse

from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright

from parser.anti_detection.browser_fingerprint import BrowserFingerprint


class BrowserPool:
    def __init__(self, max_contexts: int = 3) -> None:
        self.max_contexts = max_contexts
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._fingerprint = BrowserFingerprint()

    async def start(self) -> None:
        if self._browser is not None:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)

    async def close(self) -> None:
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    @asynccontextmanager
    async def context(self, user_agent: str | None = None, proxy_url: str | None = None) -> BrowserContext:
        await self.start()
        assert self._browser is not None

        proxy = self._build_proxy(proxy_url)
        ctx = await self._browser.new_context(
            viewport=self._fingerprint.random_viewport(),
            locale=self._fingerprint.random_locale(),
            user_agent=user_agent,
            proxy=proxy,
        )
        try:
            yield ctx
        finally:
            await ctx.close()

    def _build_proxy(self, proxy_url: str | None) -> dict | None:
        if not proxy_url:
            return None

        candidate = proxy_url.strip()
        if not candidate:
            return None
        if "://" not in candidate:
            candidate = f"http://{candidate}"

        parsed = urlparse(candidate)
        if not parsed.hostname:
            return None

        scheme = parsed.scheme or "http"
        server = f"{scheme}://{parsed.hostname}"
        if parsed.port:
            server = f"{server}:{parsed.port}"

        proxy: dict[str, str] = {"server": server}
        if parsed.username:
            proxy["username"] = parsed.username
        if parsed.password:
            proxy["password"] = parsed.password
        return proxy
