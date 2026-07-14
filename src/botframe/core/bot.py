import logging
from typing import Literal

from aiogram import Bot, Dispatcher, Router, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import InputFile

from src.botframe.core.windows.container import WindowsContainer

logger = logging.getLogger(__name__)


class TelegramBot(Bot):
    def __init__(
            self,
            token: str,
            base_url: str,
            storage: BaseStorage | None = None,
            webhook_path: str = "/webhook/bot",
            parse_mode: ParseMode = ParseMode.HTML,
            **kwargs
    ):
        super().__init__(
            token=token,
            default=DefaultBotProperties(parse_mode=parse_mode),
            **kwargs
        )
        self.dispatcher = Dispatcher(storage=storage)
        self.webhook_path = webhook_path
        self.url = f"{base_url.rstrip("/")}{webhook_path}"

    async def set_webhook(
            self,
            url: str | None = None,
            certificate: InputFile | None = None,
            ip_address: str | None = None,
            max_connections: int | None = None,
            allowed_updates: list[str] | None = None,
            drop_pending_updates: bool | None = None,
            secret_token: str | None = None,
            request_timeout: int | None = None,
    ) -> bool:
        logger.info(f"Setting webhook to {self.url}")
        return await super().set_webhook(
            url=self.url,
            certificate=certificate,
            ip_address=ip_address,
            max_connections=max_connections,
            allowed_updates=allowed_updates,
            drop_pending_updates=drop_pending_updates,
            secret_token=secret_token,
            request_timeout=request_timeout
        )

    async def close_webhook(
            self,
            drop_pending_updates: bool | None = None,
            request_timeout: int | None = None
    ):
        await self.delete_webhook(
            drop_pending_updates=drop_pending_updates,
            request_timeout=request_timeout
        )
        if self.session:
            await self.session.close()

    def include_router(self, router: Router):
        self.dispatcher.include_router(router)

    def include_middleware(
            self,
            middleware: BaseMiddleware,
            event: Literal["update", "message", "callback_query"] = "update"
    ):
        if event == "update":
            self.dispatcher.update.middleware(middleware)
        elif event == "message":
            self.dispatcher.message.middleware(middleware)
        elif event == "callback_query":
            self.dispatcher.callback_query.middleware(middleware)
