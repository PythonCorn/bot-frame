import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from botframe.api import create_telegram_router
from botframe import AppState
from botframe.middlewares.windows import WindowsMiddleware

logger = logging.getLogger(__name__)


class Application(FastAPI):
    def __init__(
            self,
            app_state: AppState,
            **kwargs
    ):
        self.app_state = app_state

        super().__init__(
            lifespan=self.lifespan,
            **kwargs
        )

    @asynccontextmanager
    async def lifespan(self, app: "Application"):
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

        app.state.app_state = self.app_state

        await self.app_state.bot.set_webhook(
            allowed_updates=(
                self.app_state.bot.dispatcher.resolve_used_update_types()
            ),
        )
        if self.app_state.i18n_middleware is not None:
            self.app_state.include_middleware(
                self.app_state.i18n_middleware,
                event="update"
            )

        if self.app_state.windows is not None:
            self.app_state.include_middleware(
                WindowsMiddleware(
                    windows=self.app_state.windows,
                )
            )
        app.include_router(create_telegram_router(self.app_state))
        try:
            yield
        finally:
            await self.app_state.close()
