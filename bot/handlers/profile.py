from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.handlers.helpers import ensure_user, show_city_selection, update_or_send
from bot.keyboards import profile_keyboard
from bot.services import CatalogService, PlaceService, UserService
from bot.states import BotStates
from db.base import async_session_factory

router = Router(name=__name__)


@router.callback_query(F.data == "menu:profile")
async def open_profile(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return

    async with async_session_factory() as session:
        user_service = UserService(session)
        catalog_service = CatalogService(session)
        place_service = PlaceService(session)

        user = await ensure_user(user_service, callback.from_user)
        counters = await place_service.user_counters(user.id)

        city_name = "не выбран"
        if user.preferred_city_id:
            city = await catalog_service.city_by_id(user.preferred_city_id)
            if city:
                city_name = city.name

        await update_or_send(
            callback.message,
            f"<b>Профиль</b>\n"
            f"Город: {city_name}\n"
            f"Избранное: {counters['favorites']}\n"
            f"История: {counters['history']}\n"
            f"Оценки: {counters['reviews']}",
            reply_markup=profile_keyboard(),
        )
        await state.set_state(BotStates.viewing_profile)
        await session.commit()

    await callback.answer()


@router.callback_query(F.data == "profile:city")
async def change_city(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return

    async with async_session_factory() as session:
        user_service = UserService(session)
        catalog_service = CatalogService(session)
        await ensure_user(user_service, callback.from_user)

        await show_city_selection(
            callback.message,
            catalog_service,
            state,
            text="Выбери новый город:",
        )

        await session.commit()

    await callback.answer()
