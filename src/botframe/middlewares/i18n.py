from abc import abstractmethod, ABC
from collections.abc import Callable, Awaitable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class I18nMiddleware(BaseMiddleware, ABC):
    @abstractmethod
    async def get_locale(
        self,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> str:
        ...

    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["locale"] = (
            await self.get_locale(event, data)
            or "en"
        )

        return await handler(event, data)