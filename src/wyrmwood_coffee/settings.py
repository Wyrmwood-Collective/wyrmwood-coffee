import logging
import sys
from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Environment(StrEnum):
    STAGING = "staging"
    DEV = "dev"
    TEST = "test"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    app_environment: Environment = Environment.DEV
    staging_database_url: str | None = None
    dev_database_url: str | None = None
    test_database_url: str | None = None
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    log_level: LogLevel = LogLevel.WARNING

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def database_url(self) -> str:
        url = None
        match self.app_environment:
            case Environment.DEV:
                url = self.dev_database_url
            case Environment.TEST:
                url = self.test_database_url

        if not url:
            logger.critical(
                f"Error: database URL is not set for {self.app_environment} "
                "environment. Please configure it before running."
            )
            sys.exit(1)
        return url


settings = Settings()  # type: ignore[call-arg]
