from collections.abc import Callable, Awaitable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from botframe.core.windows.container import WindowsContainer


class WindowsMiddleware(BaseMiddleware):
    def __init__(self, windows: WindowsContainer):
        self.windows = windows

    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> Any:
        locale = data.get("locale", "en")
        data[self.windows.name] = self.windows(locale=locale)
        return await handler(event, data)