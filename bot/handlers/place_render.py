from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, Message
import re
from urllib.parse import urlparse

from bot.handlers.helpers import update_or_send
from bot.keyboards import place_card_keyboard
from bot.services import PlaceService
from bot.states import BotStates
from bot.utils import format_place_card
from db.models import Place


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


def _resolve_photo_index(value: object, total: int) -> int:
    if total <= 0:
        return 0
    try:
        index = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        index = 0
    return index % total


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
    photo_index: int | None = None,
) -> bool:
    place = await place_service.place_card(place_id)
    if place is None:
        await update_or_send(message, "Место не найдено или было удалено.")
        return False

    is_favorite = await place_service.is_favorite(user_id=user_id, place_id=place_id)
    photo_urls = _ordered_photo_urls(place)
    photo_total = len(photo_urls)
    state_data = await state.get_data()
    if photo_total:
        if photo_index is None:
            state_place_id = state_data.get("current_place_id")
            state_index = state_data.get("current_place_photo_index", 0)
            if state_place_id == place.id:
                photo_index = _resolve_photo_index(state_index, photo_total)
            else:
                photo_index = 0
        photo_index = _resolve_photo_index(photo_index, photo_total)
        photo_url = photo_urls[photo_index]
    else:
        photo_index = 0
        photo_url = None

    caption = format_place_card(place)
    reply_markup = place_card_keyboard(
        place,
        is_favorite=is_favorite,
        back_callback=back_callback,
        photo_index=photo_index,
        photo_total=photo_total,
    )
    if photo_url:
        await _update_or_send_photo(
            message,
            photo_url=photo_url,
            caption=caption,
            reply_markup=reply_markup,
        )
    else:
        await update_or_send(message, caption, reply_markup=reply_markup)
    await state.update_data(
        current_place_id=place.id,
        current_place_back=back_callback,
        current_place_photo_index=photo_index,
    )
    await state.set_state(BotStates.viewing_place_card)
    return True
