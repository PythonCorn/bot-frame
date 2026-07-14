from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    BASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        env_file_encoding="utf-8",
    )

settings = Settings()