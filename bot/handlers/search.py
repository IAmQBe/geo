from math import ceil

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.handlers.helpers import PAGE_SIZE, ensure_user, update_or_send
from bot.handlers.place_render import render_place_card
from bot.keyboards import search_results_keyboard
from bot.services import PlaceService, UserService
from bot.states import BotStates
from db.base import async_session_factory
from db.models import User

router = Router(name=__name__)


def _empty_search_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")]]
    )


async def _render_search_page(
    message: Message,
    *,
    state: FSMContext,
    place_service: PlaceService,
    page: int,
) -> None:
    state_data = await state.get_data()
    result_ids: list[int] = state_data.get("search_result_ids", [])

    if not result_ids:
        await update_or_send(
            message,
            "По вашему запросу пока ничего не найдено.",
            reply_markup=_empty_search_keyboard(),
        )
        await state.set_state(BotStates.viewing_search_results)
        await state.update_data(search_page=1)
        return

    total_pages = max(1, ceil(len(result_ids) / PAGE_SIZE))
    page = max(1, min(page, total_pages))
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_ids = result_ids[start:end]
    places = await place_service.places_by_ids(page_ids)

    await update_or_send(
        message,
        f"<b>Результаты поиска</b>\nСтраница {page}/{total_pages}",
        reply_markup=search_results_keyboard(places, page=page, total_pages=total_pages),
    )
    await state.set_state(BotStates.viewing_search_results)
    await state.update_data(search_page=page)


@router.callback_query(F.data == "menu:search")
async def open_search(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return

    async with async_session_factory() as session:
        user_service = UserService(session)
        await ensure_user(user_service, callback.from_user)
        await session.commit()

    await state.set_state(BotStates.entering_search_query)
    await callback.answer()
    await update_or_send(
        callback.message,
        "Напиши запрос в свободной форме, например:\n"
        "<i>уютное кафе с хорошим кофе</i>",
        reply_markup=None,
    )


@router.message(BotStates.entering_search_query)
async def handle_search_query(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    query = (message.text or "").strip()
    if not query:
        await message.answer("Введите непустой запрос.")
        return

    async with async_session_factory() as session:
        user_service = UserService(session)
        place_service = PlaceService(session)

        user = await ensure_user(user_service, message.from_user)
        if user.preferred_city_id is None:
            await message.answer("Сначала выбери город через /start.")
            await session.commit()
            return

        results = await place_service.search_places(user.preferred_city_id, query)
        await state.update_data(search_result_ids=[place.id for place in results], search_query=query)
        await _render_search_page(message, state=state, place_service=place_service, page=1)
        await session.commit()


@router.callback_query(F.data.startswith("srp:"))
async def paginate_search_results(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    page = max(1, int(callback.data.split(":", maxsplit=1)[1]))

    async with async_session_factory() as session:
        user_service = UserService(session)
        place_service = PlaceService(session)
        await ensure_user(user_service, callback.from_user)
        await _render_search_page(callback.message, state=state, place_service=place_service, page=page)
        await session.commit()

    await callback.answer()


@router.callback_query(F.data.startswith("srpl:"))
async def open_search_place(callback: CallbackQuery, state: FSMContext) -> None:
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
            back_callback=f"srp:{page}",
        )
        await session.commit()

    await callback.answer()
