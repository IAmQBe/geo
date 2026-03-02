from aiogram.fsm.state import State, StatesGroup


class BotStates(StatesGroup):
    selecting_city = State()
    main_menu = State()

    browsing_category = State()
    viewing_place_list = State()
    viewing_place_card = State()
    viewing_place_details = State()

    viewing_favorites = State()
    viewing_history = State()
    viewing_history_day = State()

    rating_place = State()
    leaving_comment = State()

    entering_search_query = State()
    viewing_search_results = State()

    viewing_profile = State()
    editing_preferences = State()
