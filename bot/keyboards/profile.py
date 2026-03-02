from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏙️ Изменить город", callback_data="profile:city")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
        ]
    )
