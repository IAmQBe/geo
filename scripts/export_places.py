from __future__ import annotations

import argparse
import asyncio
import csv

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.base import async_session_factory
from db.models import Place


async def export_csv(path: str, city: str | None = None) -> dict[str, int]:
    async with async_session_factory() as session:
        query = select(Place).options(selectinload(Place.city), selectinload(Place.category)).order_by(Place.id)
        if city:
            query = query.where(Place.city.has(name=city))

        places = list((await session.execute(query)).scalars().all())

    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "id",
                "name",
                "city",
                "category_slug",
                "address",
                "description",
                "rating",
                "review_count",
                "price_range",
                "website",
                "phone",
                "is_active",
            ],
        )
        writer.writeheader()

        for place in places:
            writer.writerow(
                {
                    "id": place.id,
                    "name": place.name,
                    "city": place.city.name if place.city else "",
                    "category_slug": place.category.slug if place.category else "",
                    "address": place.address or "",
                    "description": place.description or "",
                    "rating": place.rating if place.rating is not None else "",
                    "review_count": place.review_count,
                    "price_range": place.price_range or "",
                    "website": place.website or "",
                    "phone": place.phone or "",
                    "is_active": place.is_active,
                }
            )

    return {"exported": len(places), "path": path}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Export places to CSV")
    parser.add_argument("path", help="Output CSV path")
    parser.add_argument("--city", help="Filter by city name", default=None)
    args = parser.parse_args()

    result = await export_csv(args.path, city=args.city)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
