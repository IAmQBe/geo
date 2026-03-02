import asyncio

from sqlalchemy import select

from db.base import async_session_factory
from db.models import Category, City, Place

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

DEMO_PLACES = [
    {
        "name": "Skuratov Coffee",
        "city": "Москва",
        "category": "specialty_coffee",
        "address": "ул. Покровка, 10",
        "description": "Кофейня со спокойной атмосферой и фильтр-кофе.",
        "price_range": "₽₽",
        "rating": 4.7,
        "review_count": 238,
    },
    {
        "name": "Северяне",
        "city": "Москва",
        "category": "eat",
        "address": "Большая Никитская, 12",
        "description": "Современная кухня с акцентом на локальные продукты.",
        "price_range": "₽₽₽",
        "rating": 4.6,
        "review_count": 180,
    },
    {
        "name": "Table",
        "city": "Москва",
        "category": "breakfast",
        "address": "Лесная, 20",
        "description": "Популярное место для поздних завтраков в центре.",
        "price_range": "₽₽",
        "rating": 4.5,
        "review_count": 145,
    },
    {
        "name": "Практика by Darvin",
        "city": "Москва",
        "category": "work",
        "address": "Садовая-Кудринская, 25",
        "description": "Рабочее кафе с розетками и стабильным Wi‑Fi.",
        "price_range": "₽₽",
        "rating": 4.4,
        "review_count": 96,
    },
    {
        "name": "Mendeleev Bar",
        "city": "Москва",
        "category": "drink",
        "address": "Петровка, 20/1",
        "description": "Коктейльный бар с авторскими миксами.",
        "price_range": "₽₽₽",
        "rating": 4.6,
        "review_count": 167,
    },
    {
        "name": "Терраса 32.05",
        "city": "Москва",
        "category": "terrace",
        "address": "Сад Эрмитаж",
        "description": "Летняя терраса в зелёном окружении.",
        "price_range": "₽₽",
        "rating": 4.3,
        "review_count": 121,
    },
    {
        "name": "Mad Espresso Team",
        "city": "Санкт-Петербург",
        "category": "specialty_coffee",
        "address": "Литейный пр., 40",
        "description": "Спешелти кофе и десерты в камерной атмосфере.",
        "price_range": "₽₽",
        "rating": 4.8,
        "review_count": 201,
    },
    {
        "name": "Birch",
        "city": "Санкт-Петербург",
        "category": "eat",
        "address": "Кирочная, 3",
        "description": "Небольшой ресторан современной кухни.",
        "price_range": "₽₽₽",
        "rating": 4.7,
        "review_count": 220,
    },
    {
        "name": "Civil Coffee",
        "city": "Санкт-Петербург",
        "category": "work",
        "address": "Гражданская, 13",
        "description": "Тихая кофейня для работы и встреч.",
        "price_range": "₽₽",
        "rating": 4.5,
        "review_count": 88,
    },
    {
        "name": "КоКоКо Bistro",
        "city": "Санкт-Петербург",
        "category": "date",
        "address": "ул. Некрасова, 8",
        "description": "Уютный вариант для свидания в центре города.",
        "price_range": "₽₽₽",
        "rating": 4.6,
        "review_count": 134,
    },
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


async def seed_places() -> None:
    async with async_session_factory() as session:
        city_rows = await session.execute(select(City))
        category_rows = await session.execute(select(Category))
        city_map = {city.name: city for city in city_rows.scalars().all()}
        category_map = {category.slug: category for category in category_rows.scalars().all()}

        for place_data in DEMO_PLACES:
            city = city_map.get(place_data["city"])
            category = category_map.get(place_data["category"])
            if city is None or category is None:
                continue

            existing = await session.execute(
                select(Place).where(Place.name == place_data["name"], Place.city_id == city.id)
            )
            place = existing.scalar_one_or_none()
            if place is None:
                place = Place(
                    name=place_data["name"],
                    city_id=city.id,
                    category_id=category.id,
                )
                session.add(place)

            place.address = place_data["address"]
            place.description = place_data["description"]
            place.price_range = place_data["price_range"]
            place.rating = place_data["rating"]
            place.review_count = place_data["review_count"]
            place.is_active = True
            place.is_verified = True

        await session.commit()


async def main() -> None:
    await seed_cities()
    await seed_categories()
    await seed_places()
    print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(main())
