from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router(name=__name__)


@router.callback_query(F.data.startswith("category:"))
async def category_menu(callback: CallbackQuery) -> None:
    if callback.data is None:
        return

    category_slug = callback.data.split(":", maxsplit=1)[1]
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            f"Категория `{category_slug}` выбрана. Блок карточек мест будет следующим шагом реализации."
        )


@router.callback_query(F.data.startswith("menu:"))
async def service_menu(callback: CallbackQuery) -> None:
    if callback.data is None:
        return

    action = callback.data.split(":", maxsplit=1)[1]
    labels = {
        "favorites": "Избранное",
        "history": "История",
        "search": "Поиск",
        "profile": "Профиль",
    }
    await callback.answer()
    if callback.message:
        await callback.message.answer(f"Раздел «{labels.get(action, action)}» в разработке.")
