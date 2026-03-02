import random


class BrowserFingerprint:
    VIEWPORTS = [
        {"width": 1280, "height": 720},
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
        {"width": 1536, "height": 864},
    ]

    LOCALES = ["ru-RU", "en-US"]

    def random_viewport(self) -> dict[str, int]:
        return random.choice(self.VIEWPORTS)

    def random_locale(self) -> str:
        return random.choice(self.LOCALES)
