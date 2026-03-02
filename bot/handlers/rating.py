from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_user
from bot.handlers.place_render import render_place_card
from bot.keyboards import rating_keyboard, skip_comment_keyboard
from bot.services import PlaceService, UserService
from bot.states import BotStates
from db.base import async_session_factory

router = Router(name=__name__)


@router.callback_query(F.data.startswith("rate:"))
async def start_rating(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    place_id = int(callback.data.split(":", maxsplit=1)[1])

    async with async_session_factory() as session:
        user_service = UserService(session)
        await ensure_user(user_service, callback.from_user)
        await session.commit()

    await state.set_state(BotStates.rating_place)
    await state.update_data(rating_place_id=place_id)
    await callback.answer()
    await callback.message.answer("Оцени место:", reply_markup=rating_keyboard(place_id))


@router.callback_query(F.data.startswith("rstar:"))
async def select_rating(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.data is None:
        return

    _, place_raw, rating_raw = callback.data.split(":", maxsplit=2)
    place_id = int(place_raw)
    rating = int(rating_raw)

    await state.update_data(rating_place_id=place_id, rating_value=rating)
    await state.set_state(BotStates.leaving_comment)
    await callback.answer()
    await callback.message.answer(
        "Напиши комментарий к оценке или пропусти:",
        reply_markup=skip_comment_keyboard(),
    )


@router.callback_query(F.data == "rskip")
async def skip_comment(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        return

    state_data = await state.get_data()
    place_id = state_data.get("rating_place_id")
    rating = state_data.get("rating_value")
    if not place_id or not rating:
        await callback.answer("Не удалось сохранить оценку", show_alert=True)
        return

    async with async_session_factory() as session:
        user_service = UserService(session)
        place_service = PlaceService(session)
        user = await ensure_user(user_service, callback.from_user)
        await place_service.rate_place(user.id, int(place_id), int(rating), None)

        back_callback = state_data.get("current_place_back", "menu:main")
        await render_place_card(
            callback.message,
            place_service=place_service,
            state=state,
            user_id=user.id,
            place_id=int(place_id),
            back_callback=back_callback,
        )

        await session.commit()

    await state.set_state(BotStates.viewing_place_card)
    await state.update_data(rating_place_id=None, rating_value=None)
    await callback.answer("Оценка сохранена")


@router.message(BotStates.leaving_comment)
async def save_comment(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    state_data = await state.get_data()
    place_id = state_data.get("rating_place_id")
    rating = state_data.get("rating_value")
    if not place_id or not rating:
        await message.answer("Не удалось сохранить оценку. Попробуй ещё раз из карточки места.")
        return

    comment = (message.text or "").strip() or None

    async with async_session_factory() as session:
        user_service = UserService(session)
        place_service = PlaceService(session)
        user = await ensure_user(user_service, message.from_user)

        await place_service.rate_place(user.id, int(place_id), int(rating), comment)

        back_callback = state_data.get("current_place_back", "menu:main")
        await render_place_card(
            message,
            place_service=place_service,
            state=state,
            user_id=user.id,
            place_id=int(place_id),
            back_callback=back_callback,
        )
        await session.commit()

    await state.set_state(BotStates.viewing_place_card)
    await state.update_data(rating_place_id=None, rating_value=None)
