from __future__ import annotations

import argparse
import asyncio
import csv

from sqlalchemy import select

from db.base import async_session_factory
from db.models import Category, City, Place


async def import_csv(path: str) -> dict[str, int]:
    added = 0
    updated = 0

    with open(path, "r", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    async with async_session_factory() as session:
        cities = {city.name: city for city in (await session.execute(select(City))).scalars().all()}
        categories = {
            category.slug: category
            for category in (await session.execute(select(Category))).scalars().all()
        }

        for row in rows:
            city = cities.get(row.get("city", ""))
            category = categories.get(row.get("category_slug", ""))
            if city is None or category is None:
                continue

            query = select(Place).where(Place.name == row.get("name"), Place.city_id == city.id)
            place = (await session.execute(query)).scalar_one_or_none()
            if place is None:
                place = Place(name=row.get("name", "Unnamed"), city_id=city.id, category_id=category.id)
                session.add(place)
                added += 1
            else:
                updated += 1

            place.address = row.get("address") or place.address
            place.description = row.get("description") or place.description
            place.website = row.get("website") or place.website
            place.phone = row.get("phone") or place.phone
            place.price_range = row.get("price_range") or place.price_range
            place.rating = float(row["rating"]) if row.get("rating") else place.rating
            place.review_count = int(row["review_count"]) if row.get("review_count") else place.review_count
            place.is_active = row.get("is_active", "true").lower() == "true"

        await session.commit()

    return {"rows": len(rows), "added": added, "updated": updated}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Import places from CSV")
    parser.add_argument("path", help="Path to CSV file")
    args = parser.parse_args()

    result = await import_csv(args.path)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
