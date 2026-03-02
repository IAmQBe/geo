from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputMediaPhoto, Message

from bot.handlers.helpers import update_or_send
from bot.keyboards import place_card_keyboard
from bot.services import PlaceService
from bot.states import BotStates
from bot.utils import format_place_card
from db.models import Place


def _pick_primary_photo_url(place: Place) -> str | None:
    if not place.photos:
        return None
    ordered = sorted(place.photos, key=lambda item: (not item.is_primary, item.sort_order, item.id))
    for photo in ordered:
        if photo.url and photo.url.startswith(("http://", "https://")):
            return photo.url
    return None


async def _update_or_send_photo(
    message: Message,
    *,
    photo_url: str,
    caption: str,
    reply_markup,
) -> None:
    media = InputMediaPhoto(media=photo_url, caption=caption, parse_mode="HTML")
    try:
        await message.edit_media(media=media, reply_markup=reply_markup)
        return
    except TelegramBadRequest:
        pass

    try:
        await message.answer_photo(photo=photo_url, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest:
        await update_or_send(message, caption, reply_markup=reply_markup)


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
    caption = format_place_card(place)
    reply_markup = place_card_keyboard(place, is_favorite=is_favorite, back_callback=back_callback)
    photo_url = _pick_primary_photo_url(place)
    if photo_url:
        await _update_or_send_photo(
            message,
            photo_url=photo_url,
            caption=caption,
            reply_markup=reply_markup,
        )
    else:
        await update_or_send(message, caption, reply_markup=reply_markup)
    await state.update_data(current_place_id=place.id, current_place_back=back_callback)
    await state.set_state(BotStates.viewing_place_card)
    return True
