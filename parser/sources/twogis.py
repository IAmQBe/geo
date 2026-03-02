from __future__ import annotations

import base64
import json
import re
from urllib.parse import parse_qs, quote_plus, urlparse

import httpx
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

    _BLOCK_TOKENS = (
        "2gis captcha",
        "подозрительную активность",
        "подтвердить, что вы не робот",
        "captcha.2gis.ru/form",
    )
    _NOISY_NAME_TOKENS = (
        "подборк",
        "популярные",
        "хорошее место",
        "куда сходить",
        "справочник",
        "в москве",
        "в санкт-петербурге",
    )
    _CITY_NAMES = {"москва", "санкт-петербург", "санкт петербург", "петербург", "спб"}
    _PHOTO_URL_RE = re.compile(
        r"https://(?:i\d+\.photo\.2gis\.com/images/profile/[^\s\"'<>]+|[\w.-]*2gis\.com/previews/[^\s\"'<>]+/image(?:_\d+x\d+)?\.png)",
        flags=re.IGNORECASE,
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
        query = self._build_query(context.city_slug, context.category_slug)
        search_url = f"https://2gis.ru/search/{quote_plus(query)}"
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
            await self._enrich_missing_photos(places)
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
            await page.mouse.wheel(0, 1700)
            await self.delay_engine.sleep(0.25)
        await page.wait_for_timeout(1300)

    async def _is_blocked(self, page: Page) -> bool:
        try:
            title = (await page.title()).lower()
            if "captcha" in title:
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
                const anchors = Array.from(document.querySelectorAll('a[href*="/firm/"]'));

                for (const anchor of anchors.slice(0, 320)) {
                    const href = (anchor.href || '').trim();
                    if (!href || seen.has(href)) {
                        continue;
                    }
                    seen.add(href);

                    const card =
                        anchor.closest('article, li, div[role="listitem"], div[class*="search"], div[class*="card"], div[class*="result"]') ||
                        anchor.parentElement;

                    const nameEl = card ? card.querySelector('h1, h2, h3, [class*="title"], [class*="name"]') : null;
                    const ratingEl = card ? card.querySelector('[class*="rating"], [data-testid*="rating"]') : null;
                    const addressEl = card ? card.querySelector('[class*="address"], [class*="subtitle"], [data-address]') : null;
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
        if not source_url or not is_http_url(source_url) or "/firm/" not in source_url:
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
        lat, lon = self._extract_coordinates_from_source_url(source_url)
        photos = self._extract_photos(candidate)
        canonical_source_url = self._canonicalize_source_url(source_url)

        return ParsedPlace(
            name=name,
            address=address,
            source_url=canonical_source_url or search_url,
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
        match = re.search(r"/firm/([0-9A-Za-z_-]+)", source_url)
        if match:
            return match.group(1)

        parsed = urlparse(source_url)
        for key in ("firm_id", "id", "branch_id"):
            for value in parse_qs(parsed.query).get(key, []):
                if value:
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

    def _extract_coordinates_from_source_url(self, source_url: str) -> tuple[float | None, float | None]:
        parsed = urlparse(source_url)
        for key in ("m", "point", "ll"):
            for raw in parse_qs(parsed.query).get(key, []):
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

        for raw_stat in parse_qs(parsed.query).get("stat", []):
            decoded = self._decode_stat_payload(raw_stat)
            if not decoded:
                continue
            lat, lon = self._extract_geo_position(decoded)
            if lat is not None and lon is not None:
                return lat, lon
        return None, None

    def _extract_photos(self, candidate: dict) -> list[str]:
        raw_urls: list[str] = []
        for item in candidate.get("photos", []):
            if not isinstance(item, str) or not is_http_url(item):
                continue
            raw_urls.append(item.strip())
        return self._rank_photo_urls(raw_urls, limit=8)

    async def _enrich_missing_photos(self, places: list[ParsedPlace]) -> None:
        missing = [place for place in places if not place.photos and place.source_url and "2gis.ru" in place.source_url]
        if not missing:
            return

        headers = {"User-Agent": self.user_agent_rotator.random()}
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers) as client:
            for place in missing:
                photos = await self._fetch_photos_from_page(client, place.source_url)
                if photos:
                    place.photos = photos

    async def _fetch_photos_from_page(self, client: httpx.AsyncClient, source_url: str) -> list[str]:
        try:
            response = await client.get(source_url)
            response.raise_for_status()
            html = response.text
        except Exception:
            return []

        lowered = html.lower()
        if any(token in lowered for token in self._BLOCK_TOKENS):
            return []

        raw_urls = self._PHOTO_URL_RE.findall(html)
        if not raw_urls:
            return []

        normalized = [raw.replace("\\/", "/").strip() for raw in raw_urls]
        return self._rank_photo_urls(normalized, limit=8)

    def _canonicalize_source_url(self, source_url: str) -> str:
        parsed = urlparse(source_url)
        path = parsed.path.rstrip("/")
        if not parsed.scheme or not parsed.netloc or not path:
            return source_url
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    def _decode_stat_payload(self, raw_stat: str) -> dict | None:
        candidate = raw_stat.strip()
        if not candidate:
            return None
        padding = "=" * ((4 - len(candidate) % 4) % 4)
        payload = candidate + padding
        try:
            decoded = base64.urlsafe_b64decode(payload.encode("utf-8")).decode("utf-8")
            obj = json.loads(decoded)
        except Exception:
            return None
        return obj if isinstance(obj, dict) else None

    def _extract_geo_position(self, payload: dict) -> tuple[float | None, float | None]:
        place_item = payload.get("placeItem")
        if isinstance(place_item, dict):
            geo_position = place_item.get("geoPosition")
            if isinstance(geo_position, dict):
                lat = geo_position.get("lat")
                lon = geo_position.get("lon")
                try:
                    if lat is not None and lon is not None:
                        lat_f = float(lat)
                        lon_f = float(lon)
                        if -90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0:
                            return lat_f, lon_f
                except (TypeError, ValueError):
                    return None, None
        return None, None

    def _rank_photo_urls(self, urls: list[str], limit: int) -> list[str]:
        ranked: dict[str, tuple[int, str]] = {}
        for url in urls:
            if not url or not is_http_url(url):
                continue
            score = self._photo_score(url)
            if score < 0:
                continue
            key = self._photo_dedupe_key(url)
            candidate = (score, url)
            existing = ranked.get(key)
            if existing is None or candidate > existing:
                ranked[key] = candidate

        ordered = sorted(ranked.values(), key=lambda row: row[0], reverse=True)
        return [url for _, url in ordered[:limit]]

    def _photo_score(self, url: str) -> int:
        lowered = url.lower()
        if any(token in lowered for token in ("favicon", "logo", "sprite", "placeholder", "marker", "map_pin")):
            return -999

        score = 0
        if "photo.2gis.com/images/profile" in lowered:
            score += 30
        if any(token in lowered for token in ("_1920x", "_1280x", "/orig", "m_height")):
            score += 35
        if any(token in lowered for token in ("_960x", "_640x", "/image.png")):
            score += 20

        if any(token in lowered for token in ("/image_128x128", "_64x64", "_128x.", "_320x.", "/xxs", "/xs")):
            score -= 35
        return score

    def _photo_dedupe_key(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.lower()
        path = path.replace("/image_128x128.png", "/image.png")
        path = re.sub(r"_(?:64x64|128x128|320x|640x|960x|1280x|1920x)(?=\.)", "", path)
        if path.endswith(("/xxs", "/xs", "/s", "/m", "/l", "/xl", "/xxl", "/m_height", "/orig")):
            path = path.rsplit("/", maxsplit=1)[0]
        return f"{parsed.netloc.lower()}{path}"
