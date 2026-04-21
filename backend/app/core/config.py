from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Smart Seat Analytics API"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://smart:smart@localhost:5432/smart_place"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 8
    cors_origins: list[str | AnyHttpUrl] = Field(default_factory=lambda: ["http://localhost:3000"])
    storage_dir: Path = Path("storage")
    public_base_url: str = "http://localhost:8000"
    cv_backend: str = "mock"
    yolo_model: str = "yolov8n.pt"
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "admin12345"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    (settings.storage_dir / "uploads").mkdir(parents=True, exist_ok=True)
    (settings.storage_dir / "annotated").mkdir(parents=True, exist_ok=True)
    return settings

