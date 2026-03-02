from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import city_selection_keyboard, main_menu_keyboard
from bot.services import CatalogService, UserService
from bot.states import BotStates
from db.base import async_session_factory

router = Router(name=__name__)


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    async with async_session_factory() as session:
        user_service = UserService(session)
        catalog_service = CatalogService(session)

        user = await user_service.touch_user(message.from_user)

        if user.preferred_city_id:
            categories = await catalog_service.active_categories()
            await message.answer(
                "Добро пожаловать обратно. Выберите категорию:",
                reply_markup=main_menu_keyboard(categories),
            )
            await state.set_state(BotStates.main_menu)
            await session.commit()
            return

        cities = await catalog_service.active_cities()
        await message.answer(
            "Привет. Я подберу места по городу и настроению. Сначала выбери город:",
            reply_markup=city_selection_keyboard(cities),
        )
        await state.set_state(BotStates.selecting_city)
        await session.commit()


@router.callback_query(F.data.startswith("city:"))
async def choose_city(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.data is None:
        return

    city_id = int(callback.data.split(":", maxsplit=1)[1])

    async with async_session_factory() as session:
        user_service = UserService(session)
        catalog_service = CatalogService(session)

        user = await user_service.touch_user(callback.from_user)
        city = await catalog_service.city_by_id(city_id)
        if city is None:
            await callback.answer("Город не найден", show_alert=True)
            return

        await user_service.set_city(user_id=user.id, city_id=city.id)
        categories = await catalog_service.active_categories()
        await session.commit()

    await callback.answer(f"Город: {city.name}")
    if callback.message:
        await callback.message.answer(
            f"Город сохранён: {city.name}. Выбирай категорию:",
            reply_markup=main_menu_keyboard(categories),
        )
    await state.set_state(BotStates.main_menu)
