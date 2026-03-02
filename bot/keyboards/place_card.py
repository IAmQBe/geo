from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import Place


def place_card_keyboard(
    place: Place,
    *,
    is_favorite: bool,
    back_callback: str,
    photo_index: int = 0,
    photo_total: int = 0,
) -> InlineKeyboardMarkup:
    favorite_label = "💔 Убрать из избранного" if is_favorite else "❤️ В избранное"

    if photo_total > 1:
        prev_index = (photo_index - 1) % photo_total
        next_index = (photo_index + 1) % photo_total
        prev_callback = f"plph:{place.id}:{prev_index}"
        next_callback = f"plph:{place.id}:{next_index}"
        center_label = f"Фото {photo_index + 1}/{photo_total}"
    elif photo_total == 1:
        prev_callback = "noop"
        next_callback = "noop"
        center_label = "Фото 1/1"
    else:
        prev_callback = "noop"
        next_callback = "noop"
        center_label = "Нет фото"

    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="◀️", callback_data=prev_callback),
            InlineKeyboardButton(text=center_label, callback_data="noop"),
            InlineKeyboardButton(text="▶️", callback_data=next_callback),
        ],
        [
            InlineKeyboardButton(text="📖 Подробнее", callback_data=f"pld:{place.id}"),
            InlineKeyboardButton(text=favorite_label, callback_data=f"favtg:{place.id}"),
        ],
        [
            InlineKeyboardButton(text="✅ Был(а) здесь", callback_data=f"vist:{place.id}"),
            InlineKeyboardButton(text="⭐ Оценить", callback_data=f"rate:{place.id}"),
        ],
    ]

    if place.source_url_yandex:
        rows.append([InlineKeyboardButton(text="🗺️ Открыть в Яндекс Картах", url=place.source_url_yandex)])
    elif place.source_url_2gis:
        rows.append([InlineKeyboardButton(text="🗺️ Открыть в 2GIS", url=place.source_url_2gis)])

    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)])

    return InlineKeyboardMarkup(inline_keyboard=rows)
