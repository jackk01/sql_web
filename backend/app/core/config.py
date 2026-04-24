from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SQL Web Console"
    api_v1_prefix: str = "/api/v1"
    default_query_limit: int = 200
    max_query_limit: int = 1000
    max_export_limit: int = 5000
    session_cookie_name: str = "sql_web_session"
    session_ttl_hours: int = 168
    open_registration: bool = True
    app_encryption_key: str | None = None
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def data_dir(self) -> Path:
        return Path(__file__).resolve().parents[2] / "data"

    @property
    def sqlite_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def encryption_key_path(self) -> Path:
        return self.data_dir / "app.key"


@lru_cache
def get_settings() -> Settings:
    return Settings()
