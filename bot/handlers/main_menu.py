from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.handlers.helpers import ensure_user, show_city_selection, show_main_menu
from bot.services import CatalogService, UserService
from db.base import async_session_factory

router = Router(name=__name__)


@router.callback_query(F.data == "menu:main")
async def open_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return

    async with async_session_factory() as session:
        user_service = UserService(session)
        catalog_service = CatalogService(session)
        user = await ensure_user(user_service, callback.from_user)

        if user.preferred_city_id is None:
            await show_city_selection(
                callback.message,
                catalog_service,
                state,
                text="Чтобы показать меню, сначала выбери город:",
            )
        else:
            await show_main_menu(callback.message, catalog_service, state)

        await session.commit()

    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()
