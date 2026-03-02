from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.handlers.helpers import ensure_user, update_or_send
from bot.handlers.place_render import render_place_card
from bot.services import PlaceService, UserService
from bot.utils import format_place_details
from db.base import async_session_factory

router = Router(name=__name__)


def _details_keyboard(place_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад к карточке", callback_data=f"pl:{place_id}")]]
    )


@router.callback_query(F.data.startswith("pl:"))
async def open_place_by_id(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    place_id = int(callback.data.split(":", maxsplit=1)[1])

    async with async_session_factory() as session:
        user_service = UserService(session)
        place_service = PlaceService(session)
        user = await ensure_user(user_service, callback.from_user)
        state_data = await state.get_data()
        back_callback = state_data.get("current_place_back", "menu:main")

        await render_place_card(
            callback.message,
            place_service=place_service,
            state=state,
            user_id=user.id,
            place_id=place_id,
            back_callback=back_callback,
        )
        await session.commit()

    await callback.answer()


@router.callback_query(F.data.startswith("pld:"))
async def show_place_details(callback: CallbackQuery) -> None:
    if callback.message is None or callback.data is None:
        return

    place_id = int(callback.data.split(":", maxsplit=1)[1])

    async with async_session_factory() as session:
        place_service = PlaceService(session)
        place = await place_service.place_card(place_id)
        if place is None:
            await callback.answer("Место не найдено", show_alert=True)
            return

        await update_or_send(
            callback.message,
            format_place_details(place),
            reply_markup=_details_keyboard(place_id),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("favtg:"))
async def toggle_favorite(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    place_id = int(callback.data.split(":", maxsplit=1)[1])

    async with async_session_factory() as session:
        user_service = UserService(session)
        place_service = PlaceService(session)
        user = await ensure_user(user_service, callback.from_user)
        is_now_favorite = await place_service.toggle_favorite(user.id, place_id)
        back_callback = (await state.get_data()).get("current_place_back", "menu:main")

        await render_place_card(
            callback.message,
            place_service=place_service,
            state=state,
            user_id=user.id,
            place_id=place_id,
            back_callback=back_callback,
        )
        await session.commit()

    await callback.answer("Добавлено в избранное" if is_now_favorite else "Удалено из избранного")


@router.callback_query(F.data.startswith("vist:"))
async def add_visit(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        return

    place_id = int(callback.data.split(":", maxsplit=1)[1])

    async with async_session_factory() as session:
        user_service = UserService(session)
        place_service = PlaceService(session)
        user = await ensure_user(user_service, callback.from_user)
        await place_service.add_visit(user.id, place_id)
        await session.commit()

    await callback.answer("Добавлено в историю")
