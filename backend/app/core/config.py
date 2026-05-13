"""환경 설정.

`.env`를 읽어 Pydantic 설정 객체로 노출. 환경 변수는 `.env.example` 참조.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    admin_password: str = Field(default="changeme-now", alias="ADMIN_PASSWORD")
    fernet_key: str = Field(default="", alias="FERNET_KEY")
    session_secret: str = Field(default="dev-only-change-me", alias="SESSION_SECRET")

    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    sqlite_path: str = Field(default="./data/recipe.db", alias="SQLITE_PATH")

    scan_workers_global: int = Field(default=8, alias="SCAN_WORKERS_GLOBAL")
    scan_workers_per_equipment: int = Field(default=2, alias="SCAN_WORKERS_PER_EQUIPMENT")
    scan_timeout_sec: int = Field(default=30, alias="SCAN_TIMEOUT_SEC")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sqlite_url(self) -> str:
        return f"sqlite+pysqlite:///{Path(self.sqlite_path).absolute()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
