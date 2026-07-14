from functools import cached_property
from typing import ClassVar

from aiogram.utils.i18n import I18n

from src.botframe.core.windows.base import BaseWindows


class Hello(BaseWindows):
    def hi(self):
        window = self.window(text="Hello")
        window.ibutton(text="Hi button", callback_data="Hi button")
        return window


class WindowsContainer:

    name: ClassVar[str] = "windows"

    def __init__(self, i18n: I18n | None = None, locale: str = "en"):
        self.i18n = i18n
        self.locale = locale

    @cached_property
    def hello(self) -> Hello:
        return Hello(self)

    def __call__(self, locale: str) -> "WindowsContainer":
        return WindowsContainer(i18n=self.i18n, locale=locale)

