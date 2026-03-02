from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParseContext:
    source: str
    city_slug: str
    category_slug: str
    limit: int = 50


@dataclass
class ParsedPlace:
    name: str
    address: str | None
    source_url: str
    source_id: str | None
    rating: float | None = None
    review_count: int = 0
    lat: float | None = None
    lon: float | None = None
    phone: str | None = None
    website: str | None = None
    description: str | None = None
    working_hours: dict | None = None
    price_range: str | None = None
    photos: list[str] = field(default_factory=list)
    raw_payload: dict = field(default_factory=dict)


@dataclass
class PipelineResult:
    found: int
    added: int
    updated: int
