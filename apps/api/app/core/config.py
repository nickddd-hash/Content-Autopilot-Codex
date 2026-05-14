from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Athena Content Autopilot"
    api_prefix: str = "/api"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/athena_content"
    redis_url: str = "redis://localhost:6379/0"
    media_storage_dir: str = "/var/lib/athena-content/media"
    auto_create_tables: bool = True
    environment: str = "development"
    openrouter_api_key: str = ""
    google_api_key: str = ""
    telegram_api_id: int | None = None
    telegram_api_hash: str = ""
    telegram_phone: str = ""
    telegram_session_dir: str = "/var/lib/athena-content/sessions"
    vk_client_id: str = ""
    vk_client_secret: str = ""
    oauth_redirect_base: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
