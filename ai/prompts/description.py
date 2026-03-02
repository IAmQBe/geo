from db.models import Place


def description_prompt(place: Place) -> str:
    return (
        "Напиши тёплое описание заведения на русском языке (2-3 предложения).\n"
        f"Название: {place.name}\n"
        f"Категория: {place.category.name_ru if place.category else 'не указана'}\n"
        f"Адрес: {place.address or 'не указан'}\n"
        f"Исходное описание: {place.description or 'нет'}\n"
        "Сделай акцент на атмосфере и сильных сторонах."
    )
