from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import City


def city_selection_keyboard(cities: list[City]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for city in cities:
        rows.append([InlineKeyboardButton(text=city.name, callback_data=f"city:{city.id}")])

    return InlineKeyboardMarkup(inline_keyboard=rows)
