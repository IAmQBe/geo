from __future__ import annotations

import re
from urllib.parse import parse_qs, quote_plus, urlparse

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from parser.anti_detection import DelayEngine, ProxyManager, UserAgentRotator
from parser.base_parser import BaseParser
from parser.browser import BrowserPool
from parser.browser.stealth_config import apply_stealth
from parser.sources.common import find_text, is_http_url
from parser.types import ParseContext, ParsedPlace


CATEGORY_QUERY_MAP: dict[str, str] = {
    "eat": "ресторан",
    "breakfast": "завтраки",
    "work": "кафе с ноутбуком",
    "terrace": "кафе с террасой",
    "specialty_coffee": "спешелти кофе",
    "date": "ресторан для свидания",
    "friends": "бар с друзьями",
    "dance": "танцы клуб",
    "drink": "коктейльный бар",
    "beauty": "салон красоты",
    "countryside": "загородный ресторан",
}


class YandexMapsParser(BaseParser):
    source_name = "yandex"

    _BLOCK_TOKENS = (
        "вы не робот",
        "smartcaptcha",
        "подтвердите, что запросы отправляли вы",
        "captcha",
    )
    _NOISY_NAME_TOKENS = (
        "хорошее место",
        "подборк",
        "популярные",
        "в москве",
        "в санкт-петербурге",
        "с наградой",
        "куда сходить",
        "достопримечательности",
    )
    _CITY_NAMES = {"москва", "санкт-петербург", "санкт петербург", "петербург", "спб"}

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
        query = self._build_query(context.city_slug, context.category_slug)
        search_url = f"https://yandex.ru/maps/?mode=search&text={quote_plus(query)}"
        attempts = 1 if self.proxy_manager.size == 0 else min(self.proxy_manager.size, 8)

        for _ in range(attempts):
            proxy = self.proxy_manager.pick()
            user_agent = self.user_agent_rotator.random()

            try:
                async with self.browser_pool.context(user_agent=user_agent, proxy_url=proxy) as browser_context:
                    page = await browser_context.new_page()
                    await apply_stealth(page)

                    await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                    if await self._is_blocked(page):
                        self.proxy_manager.report_failure(proxy)
                        continue

                    await self._warmup_page(page)
                    if await self._is_blocked(page):
                        self.proxy_manager.report_failure(proxy)
                        continue

                    candidates = await self._extract_dom_candidates(page)
            except Exception:
                self.proxy_manager.report_failure(proxy)
                continue

            places = self._build_places(candidates, search_url=search_url, limit=context.limit)
            if places:
                self.proxy_manager.report_success(proxy)
                return places

            self.proxy_manager.report_failure(proxy)

        return []

    def _build_query(self, city_slug: str, category_slug: str) -> str:
        city = city_slug.replace("-", " ").strip()
        category = CATEGORY_QUERY_MAP.get(category_slug, category_slug.replace("_", " ")).strip()
        return f"{city} {category}".strip()

    async def _warmup_page(self, page: Page) -> None:
        await self.delay_engine.sleep(0.5)
        for _ in range(6):
            await page.mouse.wheel(0, 1600)
            await self.delay_engine.sleep(0.25)
        await page.wait_for_timeout(1200)

    async def _is_blocked(self, page: Page) -> bool:
        try:
            title = (await page.title()).lower()
            if "не робот" in title or "captcha" in title:
                return True
            text = await page.evaluate(
                "() => (document.body && document.body.innerText ? document.body.innerText.slice(0, 2000) : '')"
            )
        except PlaywrightError:
            return True

        lowered = str(text).lower()
        return any(token in lowered for token in self._BLOCK_TOKENS)

    async def _extract_dom_candidates(self, page: Page) -> list[dict]:
        script = """
            () => {
                const rows = [];
                const seen = new Set();
                const anchors = Array.from(document.querySelectorAll('a[href*="/org/"]'));

                for (const anchor of anchors.slice(0, 300)) {
                    const href = (anchor.href || '').trim();
                    if (!href || seen.has(href)) {
                        continue;
                    }
                    seen.add(href);

                    const card =
                        anchor.closest('li, article, div[role="listitem"], div[class*="search-snippet-view"], div[class*="search-business-snippet-view"]') ||
                        anchor.parentElement;

                    const nameEl = card ? card.querySelector('h1, h2, h3, [class*="title"], [class*="name"]') : null;
                    const ratingEl = card ? card.querySelector('[class*="rating"], [aria-label*="Рейтинг"], [data-testid*="rating"]') : null;
                    const addressEl = card ? card.querySelector('[class*="address"], [class*="subtitle"], [aria-label*="Адрес"]') : null;
                    const lines = card && card.innerText
                        ? card.innerText.split('\\n').map((line) => line.trim()).filter(Boolean).slice(0, 24)
                        : [];
                    const photos = card
                        ? Array.from(card.querySelectorAll('img[src]')).map((img) => img.src).filter(Boolean).slice(0, 8)
                        : [];

                    rows.push({
                        name: ((anchor.textContent || '') || (nameEl ? nameEl.textContent || '' : '')).trim(),
                        source_url: href,
                        address: (addressEl && addressEl.textContent ? addressEl.textContent : '').trim(),
                        rating_text: (ratingEl && ratingEl.textContent ? ratingEl.textContent : '').trim(),
                        lines,
                        photos,
                    });
                }

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
        raw_name = find_text(candidate, {"name", "title"}) or ""
        name = " ".join(raw_name.split())
        if not self._is_valid_name(name):
            return None

        source_url = find_text(candidate, {"source_url", "url", "link"})
        if not source_url or not is_http_url(source_url) or "/org/" not in source_url:
            return None
        source_id = self._extract_source_id(source_url)
        if not source_id:
            return None

        lines = [line for line in candidate.get("lines", []) if isinstance(line, str)]
        rating = self._extract_rating(candidate, lines)
        review_count = self._extract_review_count(lines)
        address = self._extract_address(candidate, lines, name)
        description = self._extract_description(lines, name)
        working_hours = self._extract_working_hours(lines)
        price_range = self._extract_price_range(lines)
        lat, lon = self._extract_coordinates_from_url(source_url)
        photos = self._extract_photos(candidate)

        return ParsedPlace(
            name=name,
            address=address,
            source_url=source_url or search_url,
            source_id=source_id[:100],
            rating=rating,
            review_count=review_count,
            lat=lat,
            lon=lon,
            description=description,
            working_hours=working_hours,
            price_range=price_range,
            photos=photos,
            raw_payload=candidate,
        )

    def _is_valid_name(self, name: str) -> bool:
        if not name or len(name) < 2 or len(name) > 100:
            return False
        lowered = name.lower()
        if lowered in self._CITY_NAMES:
            return False
        if not re.search(r"[a-zа-яё]", lowered):
            return False
        if any(token in lowered for token in self._NOISY_NAME_TOKENS):
            return False
        if len(name) > 55 and re.search(r"\b(рестораны|кафе|бары|пабы|завтраки|клубы)\b", lowered):
            return False
        return True

    def _extract_source_id(self, source_url: str) -> str | None:
        for pattern in (
            r"/org/[^/]+/(\d+)",
            r"/org/(\d+)",
            r"[?&]oid=(\d+)",
            r"[?&]orgid=(\d+)",
        ):
            match = re.search(pattern, source_url)
            if match:
                return match.group(1)

        parsed = urlparse(source_url)
        for value in parse_qs(parsed.query).get("oid", []):
            if value.isdigit():
                return value
        return None

    def _extract_rating(self, candidate: dict, lines: list[str]) -> float | None:
        parts = [find_text(candidate, {"rating_text", "rating"}) or ""] + lines
        for part in parts:
            for match in re.finditer(r"(?<!\\d)([0-5](?:[\\.,]\\d)?)(?!\\d)", part):
                value = float(match.group(1).replace(",", "."))
                if 0.0 <= value <= 5.0:
                    return round(value, 1)
        return None

    def _extract_review_count(self, lines: list[str]) -> int:
        text = " | ".join(lines)
        for pattern in (
            r"(\\d[\\d\\s]{0,8})\\s*(?:отзыв|оценк|review)",
            r"(?:отзыв|оценк|review)[^\\d]{0,6}(\\d[\\d\\s]{0,8})",
        ):
            match = re.search(pattern, text.lower())
            if not match:
                continue
            digits = "".join(ch for ch in match.group(1) if ch.isdigit())
            if digits:
                value = int(digits)
                return value if value <= 2_000_000 else 0
        return 0

    def _extract_address(self, candidate: dict, lines: list[str], name: str) -> str | None:
        options: list[str] = []
        direct = find_text(candidate, {"address", "street"})
        if direct:
            options.append(direct)
        options.extend(lines)

        for option in options:
            normalized = " ".join(option.split())
            lowered = normalized.lower()
            if not normalized or normalized == name:
                continue
            if any(
                token in lowered
                for token in (
                    "отзыв",
                    "оценк",
                    "рейтинг",
                    "маршрут",
                    "показать",
                    "закрыто",
                    "открыто",
                    "сайт",
                    "телефон",
                    "доставка",
                )
            ):
                continue
            if 4 <= len(normalized) <= 140:
                return normalized
        return None

    def _extract_description(self, lines: list[str], name: str) -> str | None:
        for line in lines:
            lowered = line.lower()
            if line == name:
                continue
            if any(token in lowered for token in ("отзыв", "оценк", "рейтинг", "маршрут", "телефон")):
                continue
            if 15 <= len(line) <= 180:
                return line
        return None

    def _extract_working_hours(self, lines: list[str]) -> dict | None:
        for line in lines:
            lowered = line.lower()
            if "открыто" in lowered or "закрыто" in lowered or "круглосуточно" in lowered:
                return {"text": line}
        return None

    def _extract_price_range(self, lines: list[str]) -> str | None:
        for line in lines:
            match = re.search(r"(₽{1,4})", line)
            if match:
                return match.group(1)
        return None

    def _extract_coordinates_from_url(self, source_url: str) -> tuple[float | None, float | None]:
        parsed = urlparse(source_url)
        for raw in parse_qs(parsed.query).get("ll", []):
            parts = raw.split(",")
            if len(parts) != 2:
                continue
            try:
                lon = float(parts[0])
                lat = float(parts[1])
            except ValueError:
                continue
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                return lat, lon
        return None, None

    def _extract_photos(self, candidate: dict) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in candidate.get("photos", []):
            if not isinstance(item, str) or not is_http_url(item):
                continue
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
            if len(out) >= 8:
                break
        return out
