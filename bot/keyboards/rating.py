from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def rating_keyboard(place_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="⭐ 1", callback_data=f"rstar:{place_id}:1"), InlineKeyboardButton(text="⭐⭐ 2", callback_data=f"rstar:{place_id}:2")],
        [InlineKeyboardButton(text="⭐⭐⭐ 3", callback_data=f"rstar:{place_id}:3"), InlineKeyboardButton(text="⭐⭐⭐⭐ 4", callback_data=f"rstar:{place_id}:4")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 5", callback_data=f"rstar:{place_id}:5")],
        [InlineKeyboardButton(text="◀️ Назад к карточке", callback_data=f"pl:{place_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def skip_comment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Пропустить комментарий", callback_data="rskip")]]
    )
