from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from db.models import Category, City, ParseJob, Place, PlacePhoto
from parser.anti_detection import DelayEngine, ProxyManager, UserAgentRotator
from parser.browser import BrowserPool
from parser.pipeline import Deduplicator, Normalizer, Validator
from parser.pipeline.photo_downloader import PhotoDownloader
from parser.types import ParseContext, ParsedPlace, PipelineResult
from parser.sources import TwoGISParser, YandexMapsParser
from storage.photo_storage import PhotoStorage


@dataclass
class ParseRunner:
    session: AsyncSession

    def __post_init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.proxy_manager = ProxyManager(settings.proxy_list_url)
        self.browser_pool = BrowserPool(max_contexts=settings.max_concurrent_parsers)
        self.user_agents = UserAgentRotator()
        self.delay_engine = DelayEngine(settings.parse_delay_min, settings.parse_delay_max)
        self.validator = Validator()
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()
        self.photo_downloader = PhotoDownloader(PhotoStorage())

    async def run(self, source: str, city_slug: str, category_slug: str, limit: int = 30) -> PipelineResult:
        await self.proxy_manager.refresh()

        parse_job = ParseJob(
            source=source,
            city_slug=city_slug,
            category_slug=category_slug,
            status="running",
            started_at=datetime.now(UTC),
        )
        self.session.add(parse_job)
        await self.session.flush()

        parser = self._build_parser(source)
        context = ParseContext(source=source, city_slug=city_slug, category_slug=category_slug, limit=limit)

        try:
            parsed_places = await parser.parse(context)
            parse_job.places_found = len(parsed_places)

            prepared = self._prepare(parsed_places)
            result = await self._upsert_places(city_slug, category_slug, source, prepared)

            parse_job.places_added = result.added
            parse_job.places_updated = result.updated
            parse_job.status = "success"
            parse_job.finished_at = datetime.now(UTC)
            await self.session.commit()
            return result
        except Exception as exc:
            parse_job.status = "failed"
            parse_job.error_message = str(exc)
            parse_job.finished_at = datetime.now(UTC)
            await self.session.commit()
            raise
        finally:
            await self.browser_pool.close()

    def _build_parser(self, source: str):
        if source == "2gis":
            return TwoGISParser(
                browser_pool=self.browser_pool,
                proxy_manager=self.proxy_manager,
                user_agent_rotator=self.user_agents,
                delay_engine=self.delay_engine,
            )
        return YandexMapsParser(
            browser_pool=self.browser_pool,
            proxy_manager=self.proxy_manager,
            user_agent_rotator=self.user_agents,
            delay_engine=self.delay_engine,
        )

    def _prepare(self, places: list[ParsedPlace]) -> list[ParsedPlace]:
        prepared: list[ParsedPlace] = []
        for place in places:
            if not self.validator.validate(place):
                continue
            prepared.append(self.normalizer.normalize(place))
        return self.deduplicator.deduplicate(prepared)

    async def _upsert_places(
        self,
        city_slug: str,
        category_slug: str,
        source: str,
        parsed_places: list[ParsedPlace],
    ) -> PipelineResult:
        city = await self._city_by_slug(city_slug)
        category = await self._category_by_slug(category_slug)
        if city is None or category is None:
            raise ValueError("City or category does not exist")

        added = 0
        updated = 0

        for parsed in parsed_places:
            place = await self._find_existing_place(source=source, source_id=parsed.source_id, city_id=city.id)
            if place is None:
                place = Place(
                    name=parsed.name,
                    city_id=city.id,
                    category_id=category.id,
                )
                self.session.add(place)
                await self.session.flush()
                added += 1
            else:
                updated += 1

            place.address = parsed.address
            place.description = parsed.description
            place.rating = parsed.rating
            place.review_count = parsed.review_count
            place.phone = parsed.phone
            place.website = parsed.website
            place.price_range = parsed.price_range
            place.lat = parsed.lat
            place.lon = parsed.lon
            place.working_hours = parsed.working_hours
            place.is_active = True

            if source == "yandex":
                place.source_url_yandex = parsed.source_url
                place.source_id_yandex = parsed.source_id
            else:
                place.source_url_2gis = parsed.source_url
                place.source_id_2gis = parsed.source_id

            if parsed.photos:
                await self._upsert_place_photos(place, parsed.photos, city_slug, category_slug)

        await self.session.flush()
        return PipelineResult(found=len(parsed_places), added=added, updated=updated)

    async def _upsert_place_photos(
        self,
        place: Place,
        photo_urls: list[str],
        city_slug: str,
        category_slug: str,
    ) -> None:
        prefix = f"places/{city_slug}/{category_slug}/{place.id or 'new'}"
        try:
            storage_keys = await self.photo_downloader.download_and_store(photo_urls, prefix)
        except Exception:
            storage_keys = []

        if place.id is None:
            await self.session.flush()
        if place.id is None:
            return

        existing_rows = await self.session.execute(
            select(PlacePhoto).where(PlacePhoto.place_id == place.id)
        )
        seen_keys = {photo.storage_key for photo in existing_rows.scalars().all() if photo.storage_key}

        for idx, storage_key in enumerate(storage_keys):
            if storage_key in seen_keys:
                continue
            self.session.add(
                PlacePhoto(
                    place_id=place.id,
                    storage_key=storage_key,
                    url=photo_urls[idx] if idx < len(photo_urls) else None,
                    sort_order=idx,
                    is_primary=idx == 0,
                )
            )

    async def _find_existing_place(self, source: str, source_id: str | None, city_id: int) -> Place | None:
        if not source_id:
            return None

        if source == "yandex":
            query = select(Place).where(Place.city_id == city_id, Place.source_id_yandex == source_id)
        else:
            query = select(Place).where(Place.city_id == city_id, Place.source_id_2gis == source_id)

        return (await self.session.execute(query)).scalar_one_or_none()

    async def _city_by_slug(self, city_slug: str) -> City | None:
        query = select(City).where(City.name.ilike(city_slug.replace("-", "%")))
        return (await self.session.execute(query)).scalars().first()

    async def _category_by_slug(self, category_slug: str) -> Category | None:
        query = select(Category).where(Category.slug == category_slug)
        return (await self.session.execute(query)).scalar_one_or_none()
