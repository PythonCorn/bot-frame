from typing import ClassVar, Self

from aiogram.utils.i18n import I18n


class WindowsContainer:

    name: ClassVar[str] = "windows"

    def __init__(self, i18n: I18n | None = None, locale: str = "en"):
        self.i18n = i18n
        self.locale = locale

    def __call__(self, locale: str) -> "Self":
        return type(self)(i18n=self.i18n, locale=locale)

