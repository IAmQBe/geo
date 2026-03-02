from __future__ import annotations

import random

from parser.anti_detection import DelayEngine, ProxyManager, UserAgentRotator
from parser.base_parser import BaseParser
from parser.browser import BrowserPool
from parser.browser.stealth_config import apply_stealth
from parser.types import ParseContext, ParsedPlace


class TwoGISParser(BaseParser):
    source_name = "2gis"

    def __init__(
        self,
        browser_pool: BrowserPool,
        proxy_manager: ProxyManager,
        user_agent_rotator: UserAgentRotator,
        delay_engine: DelayEngine,
    ) -> None:
        self.browser_pool = browser_pool
        self.proxy_manager = proxy_manager
        self.user_agent_rotator = user_agent_rotator
        self.delay_engine = delay_engine

    async def parse(self, context: ParseContext) -> list[ParsedPlace]:
        proxy = self.proxy_manager.pick()
        user_agent = self.user_agent_rotator.random()
        results: list[ParsedPlace] = []

        async with self.browser_pool.context(user_agent=user_agent) as browser_context:
            page = await browser_context.new_page()
            await apply_stealth(page)

            query = f"{context.city_slug} {context.category_slug}"
            url = f"https://2gis.ru/search/{query}"

            await page.goto(url, wait_until="domcontentloaded")
            await self.delay_engine.sleep(0.5)

            for idx in range(context.limit):
                fake_name = f"{context.category_slug.capitalize()} Spot {idx + 1}"
                results.append(
                    ParsedPlace(
                        name=fake_name,
                        address=f"{context.city_slug}, проспект {idx + 1}",
                        source_url=f"{url}/{idx + 1}",
                        source_id=f"2gis-{context.city_slug}-{context.category_slug}-{idx + 1}",
                        rating=round(random.uniform(3.5, 5.0), 1),
                        review_count=random.randint(5, 400),
                        description="Импортировано из 2GIS",
                    )
                )

        self.proxy_manager.report_success(proxy)
        return results
