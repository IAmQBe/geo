from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.handlers.helpers import PAGE_SIZE, ensure_user, update_or_send
from bot.handlers.place_render import render_place_card
from bot.keyboards import history_keyboard
from bot.services import PlaceService, UserService
from bot.states import BotStates
from db.base import async_session_factory
from db.models import User

router = Router(name=__name__)


def _empty_history_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")]]
    )


async def _render_history_page(
    message: Message,
    *,
    state: FSMContext,
    place_service: PlaceService,
    user: User,
    page: int,
) -> None:
    visits, total_pages = await place_service.list_history(user_id=user.id, page=page, page_size=PAGE_SIZE)
    if page > total_pages:
        page = total_pages
        visits, total_pages = await place_service.list_history(
            user_id=user.id,
            page=page,
            page_size=PAGE_SIZE,
        )

    if not visits:
        await update_or_send(
            message,
            "История пока пустая. Отмечай места в карточке кнопкой «Был(а) здесь».",
            reply_markup=_empty_history_keyboard(),
        )
        await state.set_state(BotStates.viewing_history)
        await state.update_data(history_page=1)
        return

    await update_or_send(
        message,
        f"<b>История посещений</b>\nСтраница {page}/{total_pages}",
        reply_markup=history_keyboard(visits, page=page, total_pages=total_pages),
    )
    await state.set_state(BotStates.viewing_history)
    await state.update_data(history_page=page)


@router.callback_query(F.data == "menu:history")
async def open_history(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return

    async with async_session_factory() as session:
        user_service = UserService(session)
        place_service = PlaceService(session)
        user = await ensure_user(user_service, callback.from_user)
        await _render_history_page(
            callback.message,
            state=state,
            place_service=place_service,
            user=user,
            page=1,
        )
        await session.commit()

    await callback.answer()


@router.callback_query(F.data.startswith("histp:"))
async def paginate_history(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    page = max(1, int(callback.data.split(":", maxsplit=1)[1]))

    async with async_session_factory() as session:
        user_service = UserService(session)
        place_service = PlaceService(session)
        user = await ensure_user(user_service, callback.from_user)
        await _render_history_page(
            callback.message,
            state=state,
            place_service=place_service,
            user=user,
            page=page,
        )
        await session.commit()

    await callback.answer()


@router.callback_query(F.data.startswith("histpl:"))
async def open_history_place(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    _, place_raw, page_raw = callback.data.split(":", maxsplit=2)
    place_id = int(place_raw)
    page = max(1, int(page_raw))

    async with async_session_factory() as session:
        user_service = UserService(session)
        place_service = PlaceService(session)
        user = await ensure_user(user_service, callback.from_user)

        await render_place_card(
            callback.message,
            place_service=place_service,
            state=state,
            user_id=user.id,
            place_id=place_id,
            back_callback=f"histp:{page}",
        )
        await session.commit()

    await callback.answer()
