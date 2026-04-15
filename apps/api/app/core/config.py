from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Athena Content Autopilot"
    api_prefix: str = "/api"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/athena_content"
    redis_url: str = "redis://localhost:6379/0"
    auto_create_tables: bool = True
    environment: str = "development"
    openrouter_api_key: str = ""
    vk_client_id: str = ""
    vk_client_secret: str = ""
    oauth_redirect_base: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
