from typing import TYPE_CHECKING, Any, Literal

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    ForceReply,
    ReplyKeyboardRemove,
    WebAppInfo,
    LoginUrl,
    SwitchInlineQueryChosenChat,
    CopyTextButton,
    CallbackGame,
    KeyboardButtonRequestUsers,
    KeyboardButtonRequestChat,
    KeyboardButtonPollType
)
from aiogram.utils.i18n import I18n
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

if TYPE_CHECKING:
    from src.botframe.core.windows.container import WindowsContainer


def translator(
    text: str,
    i18n: I18n | None = None,
    locale: str = "en",
    **kwargs: Any,
) -> str:
    translated = (
        text
        if i18n is None
        else i18n.gettext(text, locale=locale)
    )

    return translated.format(**kwargs) if kwargs else translated


class Window:
    def __init__(
            self,
            text: str,
            i18n: I18n | None = None,
            keyboard_sizes: tuple[int, ...] = (1, ),
            locale: str = "en",
            **kwargs
    ) -> None:
        self.text = translator(text=text, i18n=i18n, locale=locale, **kwargs)
        self.keyboard: InlineKeyboardBuilder | ReplyKeyboardBuilder | ForceReply | ReplyKeyboardRemove | None = None
        self.i18n = i18n
        self.locale = locale
        self.keyboard_sizes = keyboard_sizes

    def _get_inline(self) -> InlineKeyboardBuilder:
        if self.keyboard is None:
            self.keyboard = InlineKeyboardBuilder()

        if not isinstance(self.keyboard, InlineKeyboardBuilder):
            raise TypeError(
                "Window already contains a reply keyboard or special reply markup"
            )

        return self.keyboard

    def _get_reply(self) -> ReplyKeyboardBuilder:
        if self.keyboard is None:
            self.keyboard = ReplyKeyboardBuilder()

        if not isinstance(self.keyboard, ReplyKeyboardBuilder):
            raise TypeError(
                "Window already contains an inline keyboard or special reply markup"
            )

        return self.keyboard

    def ibutton(self,
                *,
                text: str,
                icon_custom_emoji_id: str | None = None,
                style: str | None = None,
                url: str | None = None,
                callback_data: str | CallbackData | None = None,
                web_app: WebAppInfo | None = None,
                login_url: LoginUrl | None = None,
                switch_inline_query: str | None = None,
                switch_inline_query_current_chat: str | None = None,
                switch_inline_query_chosen_chat: SwitchInlineQueryChosenChat | None = None,
                copy_text: CopyTextButton | None = None,
                callback_game: CallbackGame | None = None,
                pay: bool | None = None,
                **kwargs: Any) -> "Window":
        keyboard = self._get_inline()
        keyboard.button(
            text=translator(text=text, i18n=self.i18n, locale=self.locale, **kwargs),
            icon_custom_emoji_id=icon_custom_emoji_id,
            style=style,
            url=url,
            callback_data=callback_data,
            web_app=web_app,
            login_url=login_url,
            switch_inline_query=switch_inline_query,
            switch_inline_query_current_chat=switch_inline_query_current_chat,
            switch_inline_query_chosen_chat=switch_inline_query_chosen_chat,
            copy_text=copy_text,
            callback_game=callback_game,
            pay=pay
        )
        return self

    def rbutton(
            self,
            *,
            text: str,
            icon_custom_emoji_id: str | None = None,
            style: str | None = None,
            request_users: KeyboardButtonRequestUsers | None = None,
            request_chat: KeyboardButtonRequestChat | None = None,
            request_contact: bool | None = None,
            request_location: bool | None = None,
            request_poll: KeyboardButtonPollType | None = None,
            web_app: WebAppInfo | None = None,
            **kwargs: Any,
    ) -> "Window":
        keyboard = self._get_reply()
        keyboard.button(
            text=translator(text=text, i18n=self.i18n, locale=self.locale, **kwargs),
            icon_custom_emoji_id=icon_custom_emoji_id,
            style=style,
            request_users=request_users,
            request_chat=request_chat,
            request_contact=request_contact,
            request_location=request_location,
            request_poll=request_poll,
            web_app=web_app
        )
        return self

    def force_reply(
            self,
            *,
            force_reply: Literal[True] = True,
            input_field_placeholder: str | None = None,
            selective: bool | None = None,
    ) -> "Window":
        self.keyboard = ForceReply(
            force_reply=force_reply,
            input_field_placeholder=input_field_placeholder,
            selective=selective
        )
        return self

    def remove_reply_markup(
            self,
            *,
            remove_keyboard: Literal[True] = True,
            selective: bool | None = None
    ) -> "Window":
        self.keyboard = ReplyKeyboardRemove(
            remove_keyboard=remove_keyboard,
            selective=selective
        )
        return self

    @property
    def reply_markup(self):
        if isinstance(self.keyboard, ReplyKeyboardBuilder):
            return self.keyboard.adjust(*self.keyboard_sizes).as_markup(
                resize_keyboard=True
            )

        if isinstance(self.keyboard, InlineKeyboardBuilder):
            return self.keyboard.adjust(*self.keyboard_sizes).as_markup()

        return self.keyboard


class BaseWindows:
    def __init__(self, windows: "WindowsContainer"):
        self.windows = windows
        self.i18n = windows._i18n
        self.locale = windows._locale

    def window(
            self,
            text: str,
            *keyboard_sizes: int,
            **kwargs
    ):
        return Window(
            text=text,
            i18n=self.i18n,
            locale=self.locale,
            keyboard_sizes=keyboard_sizes,
            **kwargs
        )
