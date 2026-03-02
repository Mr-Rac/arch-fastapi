"""Application configuration via pydantic-settings.

All settings are loaded from environment variables / ``.env`` file.
Computed fields derive convenience URLs for each database.
"""

from typing import Annotated, Literal

from pydantic import AnyUrl, BeforeValidator, Field, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors(v: str | list[str]) -> list[str]:
    """Accept comma-separated string or list for CORS origins."""
    if isinstance(v, list):
        return v
    return [i.strip() for i in v.split(",") if i.strip()]


class Settings(BaseSettings):
    """Root settings - single source of truth for all configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # ── Base ──────────────────────────────────────────────────────────────
    ENVIRONMENT: Literal["dev", "staging", "prod"] = "dev"
    PROJECT_NAME: str = "Arch FastAPI"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(_parse_cors)] = []

    @computed_field
    @property
    def DEBUG(self) -> bool:  # noqa: N802
        return self.ENVIRONMENT == "dev"

    @computed_field
    @property
    def ORIGINS(self) -> list[str]:  # noqa: N802
        return [str(o).rstrip("/") for o in self.CORS_ORIGINS]

    # ── Security / JWT ────────────────────────────────────────────────────
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ISSUER: str = "arch-fastapi"
    AUDIENCE: str = "arch-fastapi"
    LEEWAY: float = 30.0
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 30
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7

    # ── Aiohttp ──────────────────────────────────────────────────────────
    AIOHTTP_TIMEOUT: int = 30

    # ── PostgreSQL ────────────────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "auth"
    PG_POOL_SIZE: int = 10
    PG_MAX_OVERFLOW: int = 20
    PG_POOL_RECYCLE: int = 1800

    @computed_field
    @property
    def POSTGRES_URL(self) -> str:  # noqa: N802
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        ).unicode_string()

    @computed_field
    @property
    def PG_ECHO(self) -> bool:  # noqa: N802
        return self.DEBUG

    # ── MongoDB ───────────────────────────────────────────────────────────
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DB: str = "arch"

    @computed_field
    @property
    def MONGO_URL(self) -> str:  # noqa: N802
        return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}"

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 20

    @computed_field
    @property
    def REDIS_URL(self) -> str:  # noqa: N802
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ── Cache ─────────────────────────────────────────────────────────────
    USER_SCOPES_CACHE_TTL: int = 300

    # ── Admin seed ────────────────────────────────────────────────────────
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    ADMIN_ROLE: str = "admin"
    ADMIN_PERMISSION: str = "admin"
    ADMIN_SCOPE: str = "admin"


settings = Settings()  # type: ignore[call-arg]
