from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User as TgUser

from bot.keyboards import city_selection_keyboard, main_menu_keyboard
from bot.services import CatalogService, UserService
from bot.states import BotStates
from db.models import User

PAGE_SIZE = 5


async def ensure_user(user_service: UserService, tg_user: TgUser) -> User:
    return await user_service.touch_user(tg_user)


async def update_or_send(message: Message, text: str, **kwargs) -> None:
    try:
        await message.edit_text(text, **kwargs)
    except TelegramBadRequest:
        await message.answer(text, **kwargs)


async def show_city_selection(
    message: Message,
    catalog_service: CatalogService,
    state: FSMContext,
    text: str = "Выбери город:",
) -> None:
    cities = await catalog_service.active_cities()
    await update_or_send(message, text, reply_markup=city_selection_keyboard(cities))
    await state.set_state(BotStates.selecting_city)


async def show_main_menu(
    message: Message,
    catalog_service: CatalogService,
    state: FSMContext,
    text: str = "Выбери категорию:",
) -> None:
    categories = await catalog_service.active_categories()
    await update_or_send(message, text, reply_markup=main_menu_keyboard(categories))
    await state.set_state(BotStates.main_menu)
