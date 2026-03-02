from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import Place, VisitHistory


def _pagination_row(prev_callback: str, page: int, total_pages: int, next_callback: str) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(text="◀️", callback_data=prev_callback),
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"),
        InlineKeyboardButton(text="▶️", callback_data=next_callback),
    ]


def category_places_keyboard(
    places: list[Place],
    category_slug: str,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=place.name,
                callback_data=f"catpl:{place.id}:{category_slug}:{page}",
            )
        ]
        for place in places
    ]

    rows.append(
        _pagination_row(
            prev_callback=f"catp:{category_slug}:{max(1, page - 1)}",
            page=page,
            total_pages=total_pages,
            next_callback=f"catp:{category_slug}:{min(total_pages, page + 1)}",
        )
    )
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def favorites_keyboard(places: list[Place], page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=place.name, callback_data=f"favpl:{place.id}:{page}")]
        for place in places
    ]
    rows.append(
        _pagination_row(
            prev_callback=f"favp:{max(1, page - 1)}",
            page=page,
            total_pages=total_pages,
            next_callback=f"favp:{min(total_pages, page + 1)}",
        )
    )
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def history_keyboard(visits: list[VisitHistory], page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for visit in visits:
        place = visit.place
        if place is None:
            continue
        day = visit.visited_at.strftime("%d.%m") if visit.visited_at else "--"
        rows.append(
            [InlineKeyboardButton(text=f"{day} · {place.name}", callback_data=f"histpl:{place.id}:{page}")]
        )

    rows.append(
        _pagination_row(
            prev_callback=f"histp:{max(1, page - 1)}",
            page=page,
            total_pages=total_pages,
            next_callback=f"histp:{min(total_pages, page + 1)}",
        )
    )
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def search_results_keyboard(places: list[Place], page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=place.name, callback_data=f"srpl:{place.id}:{page}")]
        for place in places
    ]
    rows.append(
        _pagination_row(
            prev_callback=f"srp:{max(1, page - 1)}",
            page=page,
            total_pages=total_pages,
            next_callback=f"srp:{min(total_pages, page + 1)}",
        )
    )
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
