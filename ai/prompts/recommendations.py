from db.models import Place


def recommendation_prompt(
    history: list[str],
    favorites: list[str],
    ratings: list[str],
    city: str,
    available_places: list[Place],
) -> str:
    place_items = [f"{place.id}: {place.name}" for place in available_places]
    return (
        "Ты опытный городской гид по кафе и ресторанам.\n"
        f"Город: {city}\n"
        f"История пользователя: {history}\n"
        f"Избранное пользователя: {favorites}\n"
        f"Оценки пользователя: {ratings}\n"
        f"Доступные места: {place_items}\n"
        "Выдай топ-5 рекомендаций в формате JSON: "
        "[{\"place_id\": int, \"score\": float, \"reason_ru\": str}]"
    )
