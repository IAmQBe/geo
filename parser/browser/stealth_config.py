from playwright.async_api import Page
from playwright_stealth import Stealth


async def apply_stealth(page: Page) -> None:
    await Stealth().apply_stealth_async(page)
