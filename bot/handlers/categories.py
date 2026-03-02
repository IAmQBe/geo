from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.handlers.helpers import PAGE_SIZE, ensure_user, show_city_selection, update_or_send
from bot.handlers.place_render import render_place_card
from bot.keyboards import category_places_keyboard
from bot.services import CatalogService, PlaceService, UserService
from bot.states import BotStates
from db.base import async_session_factory
from db.models import User

router = Router(name=__name__)


def _empty_category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")]]
    )


async def _render_category_page(
    message: Message,
    *,
    state: FSMContext,
    catalog_service: CatalogService,
    place_service: PlaceService,
    user: User,
    category_slug: str,
    page: int,
) -> None:
    category = await catalog_service.category_by_slug(category_slug)
    if category is None or user.preferred_city_id is None:
        await update_or_send(message, "Категория недоступна.", reply_markup=_empty_category_keyboard())
        return

    places, total_pages = await place_service.list_places_by_category(
        city_id=user.preferred_city_id,
        category_slug=category_slug,
        page=page,
        page_size=PAGE_SIZE,
    )

    if page > total_pages:
        page = total_pages
        places, total_pages = await place_service.list_places_by_category(
            city_id=user.preferred_city_id,
            category_slug=category_slug,
            page=page,
            page_size=PAGE_SIZE,
        )

    if not places:
        await update_or_send(
            message,
            f"В категории {category.emoji or ''} {category.name_ru} пока нет мест в выбранном городе.",
            reply_markup=_empty_category_keyboard(),
        )
        await state.set_state(BotStates.viewing_place_list)
        await state.update_data(current_category_slug=category_slug, current_category_page=page)
        return

    await update_or_send(
        message,
        f"{category.emoji or ''} <b>{category.name_ru}</b>\n"
        f"Выбирай место (страница {page}/{total_pages}):",
        reply_markup=category_places_keyboard(places, category_slug=category_slug, page=page, total_pages=total_pages),
    )
    await state.set_state(BotStates.viewing_place_list)
    await state.update_data(current_category_slug=category_slug, current_category_page=page)


@router.callback_query(F.data.startswith("category:"))
async def open_category(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    category_slug = callback.data.split(":", maxsplit=1)[1]

    async with async_session_factory() as session:
        user_service = UserService(session)
        catalog_service = CatalogService(session)
        place_service = PlaceService(session)
        user = await ensure_user(user_service, callback.from_user)

        if user.preferred_city_id is None:
            await show_city_selection(
                callback.message,
                catalog_service,
                state,
                text="Сначала выбери город, чтобы показать места:",
            )
        else:
            await _render_category_page(
                callback.message,
                state=state,
                catalog_service=catalog_service,
                place_service=place_service,
                user=user,
                category_slug=category_slug,
                page=1,
            )

        await session.commit()

    await callback.answer()


@router.callback_query(F.data.startswith("catp:"))
async def paginate_category(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    _, category_slug, page_raw = callback.data.split(":", maxsplit=2)
    page = max(1, int(page_raw))

    async with async_session_factory() as session:
        user_service = UserService(session)
        catalog_service = CatalogService(session)
        place_service = PlaceService(session)
        user = await ensure_user(user_service, callback.from_user)

        if user.preferred_city_id is None:
            await show_city_selection(
                callback.message,
                catalog_service,
                state,
                text="Сначала выбери город:",
            )
        else:
            await _render_category_page(
                callback.message,
                state=state,
                catalog_service=catalog_service,
                place_service=place_service,
                user=user,
                category_slug=category_slug,
                page=page,
            )

        await session.commit()

    await callback.answer()


@router.callback_query(F.data.startswith("catpl:"))
async def open_place_from_category(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    _, place_raw, category_slug, page_raw = callback.data.split(":", maxsplit=3)
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
            back_callback=f"catp:{category_slug}:{page}",
        )

        await session.commit()

    await callback.answer()
