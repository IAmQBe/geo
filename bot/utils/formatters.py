from html import escape

from db.models import Place, VisitHistory


def format_place_list_item(place: Place) -> str:
    rating = f"⭐ {place.rating:.1f}" if place.rating is not None else "⭐ н/д"
    return f"{place.name} · {rating}"


def format_place_card(place: Place) -> str:
    rating_text = f"{place.rating:.1f}" if place.rating is not None else "н/д"
    reviews = place.review_count or 0
    category = place.category.name_ru if place.category else "Без категории"
    city = place.city.name if place.city else "Неизвестный город"
    address = place.address or "Адрес не указан"
    price = place.price_range or "—"

    return (
        f"<b>{escape(place.name)}</b>\n"
        f"⭐ {escape(rating_text)} ({reviews} отзывов)\n"
        f"📍 {escape(address)}\n"
        f"🏙️ {escape(city)}\n"
        f"🏷️ {escape(category)}\n"
        f"💰 {escape(price)}"
    )


def format_place_details(place: Place) -> str:
    description = place.ai_description or place.description or "Описание пока отсутствует."
    website = place.website or "—"
    phone = place.phone or "—"
    return (
        f"<b>Подробнее: {escape(place.name)}</b>\n\n"
        f"{escape(description)}\n\n"
        f"🌐 Сайт: {escape(website)}\n"
        f"📞 Телефон: {escape(phone)}"
    )


def format_history_item(visit: VisitHistory) -> str:
    place_name = visit.place.name if visit.place else "Удалённое место"
    day = visit.visited_at.strftime("%d.%m.%Y") if visit.visited_at else "—"
    rating = f" · ⭐ {visit.rating}" if visit.rating else ""
    return f"{day} · {place_name}{rating}"
