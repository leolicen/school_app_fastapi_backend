from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """Allowed log level values, read from the LOG_LEVEL environment variable."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and the .env file.

    Field resolution order: constructor arguments → .env file → default values.
    Fields without a default value are mandatory and raise a validation error if absent.
    """

    # -- DATABASE --
    app_name: str = "School App FastAPI Server"
    db_user: str
    db_password: str
    db_name: str
    db_host: str = "localhost"
    db_port: int = 3306

    @property
    def db_url(self) -> str:
        """SQLAlchemy-compatible MySQL connection URL.

        - charset=utf8mb4: full Unicode support.
        - pool_timeout=30: max wait for a free connection (30s).
        """
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"

    # -- JWT --
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15

    # -- REDIS --
    redis_url: str = "redis://localhost:6379/0"

    # -- REFRESH TOKEN --
    refresh_token_expire_days: int = 7

    # -- RESEND --
    resend_api_key: str
    resend_from: str
    pwd_reset_url: str  # Flutter app deep-link URL for password reset (go_router)

    # -- LOG LEVEL --
    log_level: LogLevel = "INFO"

    model_config = SettingsConfigDict( # without this property BaseSettings would only read env variables, overlooking .env
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
