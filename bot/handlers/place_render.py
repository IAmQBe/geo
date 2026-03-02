from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.helpers import update_or_send
from bot.keyboards import place_card_keyboard
from bot.services import PlaceService
from bot.states import BotStates
from bot.utils import format_place_card


async def render_place_card(
    message: Message,
    *,
    place_service: PlaceService,
    state: FSMContext,
    user_id: int,
    place_id: int,
    back_callback: str,
) -> bool:
    place = await place_service.place_card(place_id)
    if place is None:
        await update_or_send(message, "Место не найдено или было удалено.")
        return False

    is_favorite = await place_service.is_favorite(user_id=user_id, place_id=place_id)
    await update_or_send(
        message,
        format_place_card(place),
        reply_markup=place_card_keyboard(place, is_favorite=is_favorite, back_callback=back_callback),
    )
    await state.update_data(current_place_id=place.id, current_place_back=back_callback)
    await state.set_state(BotStates.viewing_place_card)
    return True
