from playwright.async_api import Page
from playwright_stealth import stealth_async


async def apply_stealth(page: Page) -> None:
    await stealth_async(page)
