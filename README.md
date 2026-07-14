# Bot Frame

A lightweight framework for building Telegram bots with **aiogram 3** and **FastAPI**.

Bot Frame combines an aiogram bot, dispatcher, FastAPI webhook endpoint, application lifecycle management, localization middleware, and a reusable window system for messages and keyboards.

> The project is currently under active development and its public API may change.

## Features

* FastAPI and aiogram integration
* Automatic Telegram webhook registration
* Automatic webhook cleanup on application shutdown
* Built-in aiogram `Dispatcher`
* Central application state
* Router and middleware registration
* Localized message windows
* Inline keyboard builder
* Reply keyboard builder
* `ForceReply` support
* Reply keyboard removal
* Dependency injection of windows into aiogram handlers
* Custom application shutdown hooks
* Docker-ready project structure

## Technology stack

* Python 3.12
* aiogram 3
* FastAPI
* Pydantic 2
* Uvicorn

## Project structure

```text
bot-frame/
├── app/
│   └── main.py
├── infra/
│   └── nginx/
│       └── nginx.conf
├── src/
│   └── botframe/
│       ├── api/
│       │   └── telegram.py
│       ├── core/
│       │   ├── app_state.py
│       │   ├── application.py
│       │   ├── bot.py
│       │   └── windows/
│       │       ├── base.py
│       │       └── container.py
│       └── middlewares/
│           ├── i18n.py
│           └── windows.py
├── config.py
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Installation

The package is not published on PyPI yet. Clone the repository and install its dependencies:

```bash
git clone https://github.com/PythonCorn/bot-frame.git
cd bot-frame

python -m venv .venv
```

Activate the virtual environment.

Linux and macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create an `.env` file in the project root:

```env
BOT_TOKEN=your_telegram_bot_token
BASE_URL=https://your-domain.example
```

`BASE_URL` must be publicly accessible through HTTPS because Telegram sends updates to the configured webhook URL.

By default, Bot Frame uses:

```text
/webhook/bot
```

The resulting webhook URL will be:

```text
https://your-domain.example/webhook/bot
```

## Quick start

```python
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.i18n import I18n

from config import settings
from src.botframe.core import AppState, Application, TelegramBot
from src.botframe.core.windows.base import BaseWindows
from src.botframe.core.windows.container import WindowsContainer


class StartWindows(BaseWindows):
    def main(self, name: str):
        return (
            self.window(
                "Hello, {name}!",
                2,
                name=name,
            )
            .ibutton(
                text="Profile",
                callback_data="profile",
            )
            .ibutton(
                text="Settings",
                callback_data="settings",
            )
        )


class Windows(WindowsContainer):
    @property
    def start(self) -> StartWindows:
        return StartWindows(self)


app_state = AppState(
    bot=TelegramBot(
        token=settings.BOT_TOKEN,
        base_url=settings.BASE_URL,
    ),
    windows=Windows(
        i18n=I18n(
            path="locales",
            default_locale="en",
        )
    ),
)

app = Application(
    app_state=app_state,
    title="Telegram Bot",
)


@app_state.bot.dispatcher.message(CommandStart())
async def start_handler(
    message: Message,
    windows: Windows,
) -> None:
    window = windows.start.main(
        name=message.from_user.full_name,
    )

    await message.answer(
        text=window.text,
        reply_markup=window.reply_markup,
    )
```

Run the application:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Core components

### `TelegramBot`

`TelegramBot` extends `aiogram.Bot` and creates its own `Dispatcher`.

```python
from src.botframe.core import TelegramBot

bot = TelegramBot(
    token="BOT_TOKEN",
    base_url="https://example.com",
    webhook_path="/webhook/bot",
)
```

Supported constructor parameters include:

```python
TelegramBot(
    token: str,
    base_url: str,
    storage: BaseStorage | None = None,
    webhook_path: str = "/webhook/bot",
    parse_mode: ParseMode = ParseMode.HTML,
)
```

The complete webhook URL is built automatically from `base_url` and `webhook_path`.

```python
bot.url
```

Example value:

```text
https://example.com/webhook/bot
```

The bot also provides helper methods for registering routers and middleware:

```python
bot.include_router(router)
```

```python
bot.include_middleware(
    middleware,
    event="message",
)
```

Supported middleware event types:

* `update`
* `message`
* `callback_query`

### `Application`

`Application` extends `FastAPI`.

It automatically:

1. Stores `AppState` inside `app.state`.
2. Registers the Telegram webhook.
3. Installs localization middleware.
4. Installs windows middleware.
5. Creates the FastAPI webhook route.
6. Removes the webhook during shutdown.
7. Closes the Telegram bot session.

```python
from src.botframe.core import Application

app = Application(
    app_state=app_state,
    title="My Bot",
)
```

Because `Application` inherits from `FastAPI`, regular FastAPI routes can be added normally:

```python
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

### `AppState`

`AppState` stores the main application dependencies:

```python
from src.botframe.core import AppState

app_state = AppState(
    bot=bot,
    windows=windows,
    i18n_middleware=i18n_middleware,
)
```

Available fields:

```python
bot: TelegramBot
windows: WindowsContainer | None
i18n_middleware: I18nMiddleware | None
```

Routers can be registered through `AppState`:

```python
app_state.include_router(router)
```

Middleware can also be registered through `AppState`:

```python
app_state.include_middleware(
    middleware,
    event="update",
)
```

## Registering routers

Create a regular aiogram router:

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer("Help")
```

Register it before the FastAPI application starts:

```python
app_state.include_router(router)
```

It can also be registered directly through the bot:

```python
app_state.bot.include_router(router)
```

## Window system

The window system provides a reusable way to define:

* message text;
* localized text;
* inline keyboards;
* reply keyboards;
* keyboard layouts;
* `ForceReply`;
* reply keyboard removal.

A window is represented by the `Window` class.

```python
window.text
window.reply_markup
```

### Creating a window group

Window groups should inherit from `BaseWindows`:

```python
from src.botframe.core.windows.base import BaseWindows


class ProfileWindows(BaseWindows):
    def main(self, username: str):
        return self.window(
            "Profile: {username}",
            username=username,
        )
```

`BaseWindows` automatically receives:

```python
self.windows
self.i18n
self.locale
```

### Registering window groups

Create a custom container by inheriting from `WindowsContainer`:

```python
from functools import cached_property

from src.botframe.core.windows.container import WindowsContainer


class Windows(WindowsContainer):
    @cached_property
    def profile(self) -> ProfileWindows:
        return ProfileWindows(self)
```

Then pass the container to `AppState`:

```python
app_state = AppState(
    bot=bot,
    windows=Windows(),
)
```

The container is injected into handlers under the name `windows`:

```python
async def handler(
    message: Message,
    windows: Windows,
) -> None:
    window = windows.profile.main(
        username=message.from_user.full_name,
    )

    await message.answer(
        text=window.text,
        reply_markup=window.reply_markup,
    )
```

The injection name is controlled by:

```python
WindowsContainer.name
```

The default value is:

```python
"windows"
```

A custom name can be defined:

```python
class UI(WindowsContainer):
    name = "ui"
```

The handler argument must then use the same name:

```python
async def handler(
    message: Message,
    ui: UI,
) -> None:
    ...
```

## Inline keyboards

Use `ibutton()` to add an inline button:

```python
window = (
    self.window("Choose an action:", 2)
    .ibutton(
        text="Profile",
        callback_data="profile",
    )
    .ibutton(
        text="Settings",
        callback_data="settings",
    )
)
```

The positional numbers passed after the text define the keyboard row sizes:

```python
self.window("Menu", 2, 1)
```

For three buttons, this produces:

```text
[ Button 1 ] [ Button 2 ]
[       Button 3       ]
```

### URL button

```python
window = (
    self.window("Open the website")
    .ibutton(
        text="Website",
        url="https://example.com",
    )
)
```

### Web App button

```python
from aiogram.types import WebAppInfo

window = (
    self.window("Open the application")
    .ibutton(
        text="Open Web App",
        web_app=WebAppInfo(
            url="https://example.com/webapp",
        ),
    )
)
```

### CallbackData

`ibutton()` accepts both a string and an aiogram `CallbackData` object:

```python
from aiogram.filters.callback_data import CallbackData


class ProfileCallback(
    CallbackData,
    prefix="profile",
):
    action: str
```

```python
window = (
    self.window("Profile")
    .ibutton(
        text="Edit",
        callback_data=ProfileCallback(
            action="edit",
        ),
    )
)
```

Other supported inline button parameters include:

* `icon_custom_emoji_id`
* `style`
* `login_url`
* `switch_inline_query`
* `switch_inline_query_current_chat`
* `switch_inline_query_chosen_chat`
* `copy_text`
* `callback_game`
* `pay`

## Reply keyboards

Use `rbutton()` to add a reply keyboard button:

```python
window = (
    self.window("Main menu", 2)
    .rbutton(text="Profile")
    .rbutton(text="Settings")
)
```

Reply keyboards are created with:

```python
resize_keyboard=True
```

Supported reply button parameters include:

* `icon_custom_emoji_id`
* `style`
* `request_users`
* `request_chat`
* `request_contact`
* `request_location`
* `request_poll`
* `web_app`

### Requesting a contact

```python
window = (
    self.window("Send your contact")
    .rbutton(
        text="Send contact",
        request_contact=True,
    )
)
```

### Requesting a location

```python
window = (
    self.window("Send your location")
    .rbutton(
        text="Send location",
        request_location=True,
    )
)
```

## ForceReply

```python
window = (
    self.window("Enter your name")
    .force_reply(
        input_field_placeholder="Your name",
    )
)
```

## Removing a reply keyboard

```python
window = (
    self.window("Keyboard removed")
    .remove_reply_markup()
)
```

## Keyboard type safety

A single window cannot contain both an inline keyboard and a reply keyboard.

This is invalid:

```python
window = (
    self.window("Invalid keyboard")
    .ibutton(
        text="Inline",
        callback_data="inline",
    )
    .rbutton(
        text="Reply",
    )
)
```

Bot Frame raises `TypeError` when different keyboard types are mixed in the same window.

## Localization

Bot Frame uses `aiogram.utils.i18n.I18n`.

Create an `I18n` instance:

```python
from aiogram.utils.i18n import I18n

i18n = I18n(
    path="locales",
    default_locale="en",
)
```

Pass it to the windows container:

```python
windows = Windows(
    i18n=i18n,
)
```

Both message text and button text are translated:

```python
window = (
    self.window(
        "Hello, {name}!",
        name="Sergey",
    )
    .ibutton(
        text="Profile",
        callback_data="profile",
    )
)
```

String formatting is applied after translation, so translated messages may contain placeholders:

```po
msgid "Hello, {name}!"
msgstr "Привет, {name}!"
```

## Custom locale middleware

To select a locale dynamically, inherit from `I18nMiddleware`:

```python
from typing import Any

from aiogram.types import TelegramObject

from src.botframe.middlewares.i18n import I18nMiddleware


class UserLocaleMiddleware(I18nMiddleware):
    async def get_locale(
        self,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> str:
        user = data.get("event_from_user")

        if user is None:
            return "en"

        return user.language_code or "en"
```

Register the middleware through `AppState`:

```python
app_state = AppState(
    bot=bot,
    windows=windows,
    i18n_middleware=UserLocaleMiddleware(),
)
```

The resolved locale is added to handler data:

```python
data["locale"]
```

The windows middleware uses that value to create a locale-specific copy of the window container.

## Custom application state

`AppState` can be extended with application-specific dependencies:

```python
from typing import Any

from pydantic import ConfigDict

from src.botframe.core import AppState


class ApplicationState(AppState):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    redis: Any
    database: Any

    async def on_close(self) -> None:
        await self.redis.aclose()
        await self.database.dispose()
```

The shutdown sequence is:

1. Delete the Telegram webhook.
2. Close the Telegram bot session.
3. Execute `AppState.on_close()`.

## Accessing AppState from FastAPI

Use `get_app_state()` as a FastAPI dependency:

```python
from typing import Annotated

from fastapi import Depends

from src.botframe.core.app_state import (
    AppState,
    get_app_state,
)


@app.get("/state")
async def state_endpoint(
    state: Annotated[
        AppState,
        Depends(get_app_state),
    ],
) -> dict[str, str]:
    return {
        "bot": str(state.bot.id),
    }
```

## Webhook processing

Bot Frame creates a FastAPI `POST` endpoint using the configured webhook path.

For example:

```python
TelegramBot(
    token="BOT_TOKEN",
    base_url="https://example.com",
    webhook_path="/telegram/webhook",
)
```

Creates:

```text
POST /telegram/webhook
```

Incoming JSON updates are passed to:

```python
dispatcher.feed_raw_update(...)
```

The endpoint returns:

```json
{
  "status": "ok"
}
```

## Adding regular FastAPI routers

Because Bot Frame uses a regular FastAPI application, additional API routers can be included normally:

```python
from fastapi import APIRouter

api_router = APIRouter(
    prefix="/api",
)


@api_router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
```

## Running with Docker

Build and start the project:

```bash
docker compose up --build
```

The included Docker Compose configuration starts:

* the FastAPI application;
* Nginx;
* Cloudflare Tunnel.

Before running it, configure:

* `.env`;
* the Cloudflare Tunnel configuration;
* the public hostname;
* `BASE_URL`.

## Development

Run the application locally:

```bash
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload
```

Format and check the project before submitting changes.

Recommended development tools:

```bash
pip install ruff mypy pytest pytest-asyncio
```

Run Ruff:

```bash
ruff check .
```

Run mypy:

```bash
mypy src
```

Run tests:

```bash
pytest
```

## Current limitations

The project is still in an early development stage.

Current limitations include:

* no PyPI release;
* no stable semantic version;
* no automated test suite;
* no generated API documentation;
* no polling mode;
* webhook secret validation is not enabled by default;
* imports currently use the repository-level `src.botframe` namespace;
* the public API may change between commits.

For production usage, pin the project to a specific commit.

## Roadmap

Planned improvements:

* `pyproject.toml` packaging;
* PyPI publishing;
* stable public imports through `botframe`;
* webhook secret token validation;
* configurable webhook lifecycle;
* improved dependency injection;
* reusable sender abstraction;
* media support for windows;
* window editing helpers;
* automated tests;
* type checking;
* CI pipeline;
* full documentation;
* complete example projects.

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make the changes.
4. Add or update tests.
5. Run the linters.
6. Open a pull request.

```bash
git checkout -b feature/my-feature
```

## Repository

GitHub:

```text
https://github.com/PythonCorn/bot-frame
```

## License

A license has not been added to the repository yet.

Before distributing or accepting third-party contributions, add a license file such as:

* MIT;
* Apache License 2.0;
* BSD 3-Clause.
