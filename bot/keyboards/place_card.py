from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import Place


def place_card_keyboard(
    place: Place,
    *,
    is_favorite: bool,
    back_callback: str,
) -> InlineKeyboardMarkup:
    favorite_label = "💔 Убрать из избранного" if is_favorite else "❤️ В избранное"

    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="◀️ Фото", callback_data="noop"),
            InlineKeyboardButton(text="Фото ▶️", callback_data="noop"),
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

    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)])

    return InlineKeyboardMarkup(inline_keyboard=rows)
