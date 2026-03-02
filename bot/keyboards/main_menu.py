from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import Category


def _pairwise(items: list[InlineKeyboardButton]) -> list[list[InlineKeyboardButton]]:
    rows: list[list[InlineKeyboardButton]] = []
    for idx in range(0, len(items), 2):
        rows.append(items[idx : idx + 2])
    return rows


def main_menu_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    category_buttons = [
        InlineKeyboardButton(
            text=f"{category.emoji or ''} {category.name_ru}".strip(),
            callback_data=f"category:{category.slug}",
        )
        for category in categories
    ]

    rows = _pairwise(category_buttons)
    rows.extend(
        [
            [
                InlineKeyboardButton(text="❤️ Избранное", callback_data="menu:favorites"),
                InlineKeyboardButton(text="📋 История", callback_data="menu:history"),
            ],
            [
                InlineKeyboardButton(text="🔍 Поиск", callback_data="menu:search"),
                InlineKeyboardButton(text="👤 Профиль", callback_data="menu:profile"),
            ],
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
