import asyncio

from sqlalchemy import select

from db.base import async_session_factory
from db.models import Category, City

CITIES = [
    {"name": "Москва", "region": "Московская область", "timezone": "Europe/Moscow", "is_active": True},
    {
        "name": "Санкт-Петербург",
        "region": "Ленинградская область",
        "timezone": "Europe/Moscow",
        "is_active": True,
    },
]

CATEGORIES = [
    {"slug": "eat", "name_ru": "Поесть", "emoji": "🍽️", "sort_order": 1},
    {"slug": "breakfast", "name_ru": "Завтрак", "emoji": "☕", "sort_order": 2},
    {"slug": "work", "name_ru": "Поработать с ноутбуком", "emoji": "💻", "sort_order": 3},
    {"slug": "terrace", "name_ru": "Погреться на террасах", "emoji": "🌿", "sort_order": 4},
    {"slug": "specialty_coffee", "name_ru": "Спешелти кофе", "emoji": "☕", "sort_order": 5},
    {"slug": "date", "name_ru": "Свидание", "emoji": "💑", "sort_order": 6},
    {"slug": "friends", "name_ru": "Вечер с друзьями", "emoji": "🥂", "sort_order": 7},
    {"slug": "dance", "name_ru": "Потанцевать", "emoji": "💃", "sort_order": 8},
    {"slug": "drink", "name_ru": "Выпить", "emoji": "🍸", "sort_order": 9},
    {"slug": "beauty", "name_ru": "Красота", "emoji": "💅", "sort_order": 10},
    {"slug": "countryside", "name_ru": "За городом", "emoji": "🌲", "sort_order": 11},
]


async def seed_cities() -> None:
    async with async_session_factory() as session:
        for city_data in CITIES:
            existing = await session.execute(select(City).where(City.name == city_data["name"]))
            if existing.scalar_one_or_none() is None:
                session.add(City(**city_data))
        await session.commit()


async def seed_categories() -> None:
    async with async_session_factory() as session:
        for category_data in CATEGORIES:
            existing = await session.execute(
                select(Category).where(Category.slug == category_data["slug"])
            )
            category = existing.scalar_one_or_none()
            if category is None:
                session.add(Category(**category_data))
            else:
                category.name_ru = category_data["name_ru"]
                category.emoji = category_data["emoji"]
                category.sort_order = category_data["sort_order"]
        await session.commit()


async def main() -> None:
    await seed_cities()
    await seed_categories()
    print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(main())
