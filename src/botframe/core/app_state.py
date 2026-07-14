from typing import Literal

from aiogram import Router, BaseMiddleware
from fastapi import Request
from pydantic import BaseModel, ConfigDict

from botframe.core.bot import TelegramBot
from botframe.core.windows.container import WindowsContainer
from botframe.middlewares.i18n import I18nMiddleware


class AppState(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    bot: TelegramBot
    windows: WindowsContainer | None = None
    i18n_middleware: I18nMiddleware | None = None

    async def close(self):
        await self.bot.close_webhook()
        await self.on_close()

    async def on_close(self) -> None:
        pass

    def include_router(self, router: Router):
        self.bot.include_router(router)

    def include_middleware(
            self,
            middleware: BaseMiddleware,
            event: Literal["update", "message", "callback_query"] = "update"
    ):
        self.bot.include_middleware(middleware, event)

def get_app_state(request: Request) -> AppState:
    return request.app.state.app_state
