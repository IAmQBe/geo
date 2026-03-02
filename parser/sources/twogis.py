from __future__ import annotations

import asyncio
from urllib.parse import quote_plus

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, Response

from parser.anti_detection import DelayEngine, ProxyManager, UserAgentRotator
from parser.base_parser import BaseParser
from parser.browser import BrowserPool
from parser.browser.stealth_config import apply_stealth
from parser.sources.common import (
    collect_phones,
    collect_urls,
    find_coordinates,
    find_float,
    find_int,
    find_text,
    is_http_url,
    maybe_price_range,
    pick_external_website,
)
from parser.types import ParseContext, ParsedPlace


CATEGORY_QUERY_MAP: dict[str, str] = {
    "eat": "ресторан",
    "breakfast": "завтраки",
    "work": "кофейня с ноутбуком",
    "terrace": "кафе с террасой",
    "specialty_coffee": "спешелти кофе",
    "date": "ресторан для свидания",
    "friends": "бар",
    "dance": "ночной клуб",
    "drink": "коктейльный бар",
    "beauty": "салон красоты",
    "countryside": "загородный ресторан",
}


class TwoGISParser(BaseParser):
    source_name = "2gis"

    _NETWORK_HINTS = (
        "2gis",
        "catalog",
        "search",
        "items",
        "api",
        "graphql",
    )

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

        query = self._build_query(context.city_slug, context.category_slug)
        search_url = f"https://2gis.ru/search/{quote_plus(query)}"

        network_payloads: list[dict] = []
        pending_tasks: set[asyncio.Task] = set()

        async with self.browser_pool.context(user_agent=user_agent) as browser_context:
            page = await browser_context.new_page()
            await apply_stealth(page)
            page.on("response", lambda response: self._track_response(response, network_payloads, pending_tasks))

            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                await self._warmup_page(page)

                if pending_tasks:
                    await asyncio.gather(*pending_tasks, return_exceptions=True)

                dom_payloads = await self._extract_dom_candidates(page)
            except Exception:
                self.proxy_manager.report_failure(proxy)
                raise

        candidates = network_payloads + dom_payloads
        places = self._build_places(candidates, search_url=search_url, limit=context.limit)

        if places:
            self.proxy_manager.report_success(proxy)
        else:
            self.proxy_manager.report_failure(proxy)

        return places

    def _build_query(self, city_slug: str, category_slug: str) -> str:
        city = city_slug.replace("-", " ").strip()
        category = CATEGORY_QUERY_MAP.get(category_slug, category_slug.replace("_", " ")).strip()
        return f"{city} {category}".strip()

    def _track_response(
        self,
        response: Response,
        network_payloads: list[dict],
        pending_tasks: set[asyncio.Task],
    ) -> None:
        task = asyncio.create_task(self._collect_response_payload(response, network_payloads))
        pending_tasks.add(task)
        task.add_done_callback(pending_tasks.discard)

    async def _collect_response_payload(self, response: Response, network_payloads: list[dict]) -> None:
        url = response.url.lower()
        if response.request.resource_type not in {"xhr", "fetch"}:
            return
        if not any(token in url for token in self._NETWORK_HINTS):
            return

        content_type = (response.headers or {}).get("content-type", "")
        if "json" not in content_type and "javascript" not in content_type:
            return

        try:
            payload = await response.json()
        except Exception:
            return

        self._append_candidate_dicts(payload, network_payloads)

    def _append_candidate_dicts(self, payload: object, out: list[dict]) -> None:
        stack: list[object] = [payload]
        scanned = 0

        while stack and scanned < 5000:
            scanned += 1
            item = stack.pop()

            if isinstance(item, dict):
                if self._looks_like_place(item):
                    out.append(item)
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)

    def _looks_like_place(self, row: dict) -> bool:
        keys = {key.lower() for key in row.keys()}
        has_name = any(key in keys for key in ("name", "title", "full_name", "short_name"))
        has_location = any(
            key in keys
            for key in (
                "address",
                "point",
                "lat",
                "lon",
                "longitude",
                "latitude",
                "geometry",
            )
        )
        has_business_hint = any(key in keys for key in ("rating", "reviews", "contacts", "rubrics", "branch"))
        return has_name and (has_location or has_business_hint)

    async def _warmup_page(self, page: Page) -> None:
        await self.delay_engine.sleep(0.5)

        for _ in range(7):
            await page.mouse.wheel(0, 1600)
            await self.delay_engine.sleep(0.2)

        await page.wait_for_timeout(1800)

    async def _extract_dom_candidates(self, page: Page) -> list[dict]:
        script = """
            () => {
                const rows = [];
                const selectors = [
                    'div[class*="_zjunba"]',
                    'div[class*="searchResult"]',
                    'div[class*="miniCard"]',
                    'article'
                ];
                const nodes = new Set();
                selectors.forEach((selector) => {
                    document.querySelectorAll(selector).forEach((node) => nodes.add(node));
                });

                Array.from(nodes).slice(0, 300).forEach((node) => {
                    const nameEl = node.querySelector('a[href*="/firm/"], div[class*="title"], h1, h2');
                    const addressEl = node.querySelector('div[class*="address"], span[class*="address"]');
                    const ratingEl = node.querySelector('span[class*="rating"], div[class*="rating"]');
                    const hrefEl = node.querySelector('a[href*="/firm/"]');
                    const imgs = Array.from(node.querySelectorAll('img[src]')).slice(0, 8).map((img) => img.src);

                    const name = nameEl ? nameEl.textContent?.trim() : null;
                    if (!name) return;

                    rows.push({
                        name,
                        address: addressEl ? addressEl.textContent?.trim() : null,
                        rating: ratingEl ? ratingEl.textContent?.trim() : null,
                        source_url: hrefEl ? hrefEl.href : null,
                        photos: imgs,
                    });
                });
                return rows;
            }
        """

        try:
            payload = await page.evaluate(script)
            return [row for row in payload if isinstance(row, dict)]
        except PlaywrightError:
            return []

    def _build_places(self, candidates: list[dict], search_url: str, limit: int) -> list[ParsedPlace]:
        results: list[ParsedPlace] = []
        seen: set[str] = set()

        for candidate in candidates:
            place = self._to_place(candidate, search_url)
            if place is None:
                continue

            key = place.source_id or f"{place.name.lower()}::{(place.address or '').lower()}"
            if key in seen:
                continue

            seen.add(key)
            results.append(place)
            if len(results) >= limit:
                break

        return results

    def _to_place(self, candidate: dict, search_url: str) -> ParsedPlace | None:
        name = find_text(candidate, {"name", "title", "full_name", "short_name", "branch_name"})
        if not name or len(name) < 2:
            return None

        source_url = find_text(candidate, {"url", "source_url", "link", "permalink", "uri"})
        if not source_url or not is_http_url(source_url):
            source_url = search_url

        source_id = find_text(
            candidate,
            {"id", "oid", "businessid", "orgid", "objectid", "uid", "branch_id", "firm_id"},
        )
        if source_id:
            source_id = source_id[:120]

        rating = find_float(candidate, {"rating", "avgrating", "stars", "value"})
        review_count = find_int(candidate, {"reviewcount", "reviewscount", "reviews", "votes", "feedbackcount"})

        lat, lon = find_coordinates(candidate)
        address = find_text(candidate, {"address", "shortaddress", "fulladdress", "textaddress"})

        phones = collect_phones(candidate)
        phone = phones[0] if phones else None

        urls = collect_urls(candidate, key_tokens=("url", "link", "site", "website"), limit=20)
        website = pick_external_website(urls)

        photos = collect_urls(candidate, key_tokens=("photo", "image", "img", "avatar"), limit=12)
        description = find_text(candidate, {"description", "snippet", "about", "subtitle", "text"})
        working_hours_raw = find_text(candidate, {"workinghours", "hours", "schedule", "openinghours"})
        working_hours = {"text": working_hours_raw} if working_hours_raw else None

        return ParsedPlace(
            name=name,
            address=address,
            source_url=source_url,
            source_id=source_id,
            rating=rating,
            review_count=review_count or 0,
            lat=lat,
            lon=lon,
            phone=phone,
            website=website,
            description=description,
            working_hours=working_hours,
            price_range=maybe_price_range(candidate),
            photos=photos,
            raw_payload=candidate,
        )
