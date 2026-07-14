from typing import Any

from fastapi import APIRouter, Request, status

from botframe.core.app_state import AppState


def create_telegram_router(app_state: AppState) -> APIRouter:
    router = APIRouter(tags=["Telegram"])
    
    @router.post(
        path=app_state.bot.webhook_path,
        status_code=status.HTTP_200_OK,
    )
    async def webhook(request: Request) -> dict[str, str]:
        body: dict[str, Any] = await request.json()

        await app_state.bot.dispatcher.feed_raw_update(
            bot=app_state.bot,
            update=body,
            app_state=app_state,
        )

        return {"status": "ok"}

    return router
