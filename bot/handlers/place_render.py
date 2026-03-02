from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, Message
import hashlib
import re
from urllib.parse import urlparse

from bot.handlers.helpers import update_or_send
from bot.keyboards import place_card_keyboard
from bot.services import PlaceService
from bot.states import BotStates
from bot.utils import format_place_card
from db.models import Place

ALBUM_LIMIT = 8


def _photo_quality_score(url: str) -> int:
    lowered = url.lower()
    if any(token in lowered for token in ("favicon", "logo", "sprite", "map_pin", "marker", "placeholder")):
        return -999
    if "get-discovery-int" in lowered:
        return -999
    if "photo.2gis.com/images/profile" in lowered:
        return -999
    if "/previews/" in lowered:
        return -999
    if any(token in lowered for token in ("_64x64", "_128x128", "/xxs", "/xs", "?w=64", "?h=64", "?w=320")):
        return -999

    score = 0
    if "/main/branch/" in lowered:
        score += 110
    if "/main/geo/" in lowered:
        score += 55
    if "/reviews-photos/" in lowered:
        score += 100
    if "get-altay" in lowered or "get-vh" in lowered:
        score += 65
    if any(token in lowered for token in ("_1920x", "_1280x", "/orig", "m_height")):
        score += 40
    if any(token in lowered for token in ("_960x", "_640x")):
        score += 25

    if any(token in lowered for token in ("_320x", "smart_crop")):
        score -= 35
    return score


def _photo_dedupe_key(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.lower()
    path = path.replace("/image_128x128.png", "/image.png")
    path = re.sub(r"_(?:64x64|128x128|320x|640x|960x|1280x|1920x)(?=\.)", "", path)
    path = re.sub(r"/smart_crop_[^/]+", "", path)
    if path.endswith(("/xxs", "/xs", "/s", "/m", "/l", "/xl", "/xxl", "/m_height", "/orig")):
        path = path.rsplit("/", maxsplit=1)[0]
    return f"{parsed.netloc.lower()}{path}"


def _ordered_photo_urls(place: Place) -> list[str]:
    if not place.photos:
        return []

    ranked: dict[str, tuple[int, int, int, str]] = {}
    for photo in sorted(place.photos, key=lambda item: (not item.is_primary, item.sort_order, item.id)):
        url = (photo.url or "").strip()
        if not url.startswith(("http://", "https://")):
            continue

        score = _photo_quality_score(url)
        if score < 0:
            continue

        dedupe_key = _photo_dedupe_key(url)
        candidate = (score, -photo.sort_order, -(photo.id or 0), url)
        existing = ranked.get(dedupe_key)
        if existing is None or candidate > existing:
            ranked[dedupe_key] = candidate

    ordered = sorted(ranked.values(), key=lambda row: (row[0], row[1], row[2]), reverse=True)
    return [row[3] for row in ordered]


def _album_signature(urls: list[str]) -> str:
    payload = "|".join(urls[:ALBUM_LIMIT]).encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def _album_message_ids(state_data: dict) -> list[int]:
    raw = state_data.get("current_place_album_message_ids")
    if not isinstance(raw, list):
        return []
    ids: list[int] = []
    for item in raw:
        try:
            ids.append(int(item))
        except (TypeError, ValueError):
            continue
    return ids


async def _drop_album_messages(message: Message, message_ids: list[int]) -> None:
    if message.chat is None or not message_ids:
        return
    for message_id in message_ids:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=message_id)
        except TelegramBadRequest:
            continue


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


async def _sync_album(
    message: Message,
    *,
    state: FSMContext,
    state_data: dict,
    place_id: int,
    photo_urls: list[str],
) -> None:
    previous_ids = _album_message_ids(state_data)
    previous_signature = state_data.get("current_place_album_signature")
    previous_place_id = state_data.get("current_place_id")

    if len(photo_urls) <= 1:
        if previous_ids:
            await _drop_album_messages(message, previous_ids)
        await state.update_data(current_place_album_message_ids=[], current_place_album_signature=None)
        return

    signature = _album_signature(photo_urls)
    if previous_place_id == place_id and previous_signature == signature and previous_ids:
        return

    if previous_ids:
        await _drop_album_messages(message, previous_ids)

    media = [InputMediaPhoto(media=url) for url in photo_urls[:ALBUM_LIMIT]]
    try:
        sent_messages = await message.answer_media_group(media=media)
    except TelegramBadRequest:
        await state.update_data(current_place_album_message_ids=[], current_place_album_signature=None)
        return

    await state.update_data(
        current_place_album_message_ids=[item.message_id for item in sent_messages],
        current_place_album_signature=signature,
    )


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
    photo_urls = _ordered_photo_urls(place)
    state_data = await state.get_data()
    await _sync_album(message, state=state, state_data=state_data, place_id=place.id, photo_urls=photo_urls)

    caption = format_place_card(place)
    reply_markup = place_card_keyboard(
        place,
        is_favorite=is_favorite,
        back_callback=back_callback,
    )
    if len(photo_urls) == 1:
        await _update_or_send_photo(
            message,
            photo_url=photo_urls[0],
            caption=caption,
            reply_markup=reply_markup,
        )
    else:
        await update_or_send(message, caption, reply_markup=reply_markup)
    await state.update_data(
        current_place_id=place.id,
        current_place_back=back_callback,
    )
    await state.set_state(BotStates.viewing_place_card)
    return True
