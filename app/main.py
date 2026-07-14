
from aiogram.types import Message
from aiogram.utils.i18n import I18n

from src.botframe.core import TelegramBot, Application, AppState
from src.botframe.core.windows.container import WindowsContainer
from config import settings


class Windows(WindowsContainer):
    ...



app_state = AppState(
    bot=TelegramBot(
        token=settings.BOT_TOKEN,
        base_url=settings.BASE_URL,
    ),
    windows=Windows(i18n=I18n(path="locales", default_locale="en"))

)

app = Application(app_state=app_state)


@app_state.bot.dispatcher.message()
async def catch(msg: Message, windows: Windows):
    window = windows.hello.hi()
    await msg.answer(
        text=window.text,
        reply_markup=window.reply_markup,
    )

