from bot.keyboards.main_menu import main_menu_keyboard


class DummyCategory:
    def __init__(self, slug: str, name_ru: str, emoji: str):
        self.slug = slug
        self.name_ru = name_ru
        self.emoji = emoji


def test_main_menu_keyboard_builds_buttons() -> None:
    categories = [
        DummyCategory("eat", "Поесть", "🍽️"),
        DummyCategory("work", "Поработать", "💻"),
    ]
    kb = main_menu_keyboard(categories)
    assert kb.inline_keyboard
    assert kb.inline_keyboard[0][0].callback_data == "category:eat"
